"""
Unified Memory Manager - Coordinates graph and vector memory systems
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from .graph_memory import GraphMemory
from .vector_memory import VectorMemory
from .cache_events import cache_events
from task_queue.enhanced_queue_manager import queue_manager
from .event_cache_manager import EventCacheManager

event_cache_manager = EventCacheManager()


class OptimizedMemoryManager:
    """Optimized memory manager with multi-level caching and lazy loading"""
    
    def __init__(self):
        self._graph_memory = None
        self._vector_memory = None
        self._ttl_seconds = 300  # 5 minutes
        self.output_dir = Path("./data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Enhanced multi-level caching system
        self._local_cache = {}
        self._local_cache_ttl = 60  # 1 minute TTL for local cache
        self._local_cache_hits = 0
        self._local_cache_misses = 0
        self._last_cache_cleanup = time.time()
        
        # Frequently accessed data cache (permanent until invalidated)
        self._hot_cache = {}
        
        # Start background cache cleanup tasks
        asyncio.create_task(self._periodic_cache_cleanup())
        asyncio.create_task(self._periodic_redis_cleanup())
    
    @property
    def graph_memory(self):
        """Lazy initialization of graph memory"""
        if self._graph_memory is None:
            self._graph_memory = GraphMemory()
        return self._graph_memory
    
    @property
    def vector_memory(self):
        """Lazy initialization of vector memory"""
        if self._vector_memory is None:
            self._vector_memory = VectorMemory()
        return self._vector_memory
    
    async def get_with_cache(self, key: str, fetch_func, force_db_access: bool = None):
        """Get data with multi-level caching and event-driven DB access"""
        # Check if DB access is needed based on events
        if force_db_access is None:
            force_db_access = await cache_events.should_access_db(key)
        
        # Skip cache if force_db_access is True (for event-triggered updates)
        if not force_db_access:
            # First check hot cache for critical data
            hot_cache_key = f"hot:{key}"
            if hot_cache_key in self._hot_cache:
                self._local_cache_hits += 1
                return self._hot_cache[hot_cache_key]
            
            # Then check local cache for ultra-fast access
            local_cache_key = f"local:{key}"
            if local_cache_key in self._local_cache:
                cache_entry = self._local_cache[local_cache_key]
                if time.time() - cache_entry["timestamp"] <= self._local_cache_ttl:
                    self._local_cache_hits += 1
                    return cache_entry["data"]
                else:
                    # Expired local cache entry
                    del self._local_cache[local_cache_key]
                    self._local_cache_misses += 1
            else:
                self._local_cache_misses += 1
        
        # Determine if this is a frequent key that should be in hot cache
        is_frequent_key = key.startswith("shared_context") or key.startswith("global_")
        
        try:
            # Check Redis cache only if not forcing DB access
            if not force_db_access and hasattr(queue_manager, 'redis') and queue_manager.redis:
                try:
                    # Try to get from Redis cache with timeout
                    cached_data = await asyncio.wait_for(
                        queue_manager.redis.get(f"memory_cache:{key}"),
                        timeout=2.0  # Reduced timeout for faster fallback
                    )
                    if cached_data:
                        # Parse data
                        parsed_data = json.loads(cached_data)
                        
                        # Store in appropriate cache level
                        if is_frequent_key:
                            self._hot_cache[hot_cache_key] = parsed_data
                        else:
                            self._local_cache[local_cache_key] = {
                                "data": parsed_data,
                                "timestamp": time.time()
                            }
                        return parsed_data
                except asyncio.TimeoutError:
                    logger.debug(f"Redis cache timeout for {key}, fetching from DB")
                except Exception as redis_error:
                    logger.debug(f"Redis cache error for {key}: {redis_error}")
            
            # Fetch from DB (only when cache miss or event-triggered)
            result = await fetch_func()
            
            # Mark that DB was accessed
            await cache_events.mark_db_accessed(key)
            
            # Store in appropriate cache level
            if is_frequent_key:
                self._hot_cache[hot_cache_key] = result
            
            # Always store in local cache
            self._local_cache[local_cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            # Store in Redis cache if available (fire-and-forget)
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                asyncio.create_task(self._async_cache_store(key, result))
            
            return result
            
        except Exception as e:
            logger.warning(f"Cache error for {key}: {e}")
            # Try to return stale cache data if available
            local_cache_key = f"local:{key}"
            if local_cache_key in self._local_cache:
                logger.info(f"Returning stale cache data for {key}")
                return self._local_cache[local_cache_key]["data"]
            
            # Last resort: try fetch_func
            try:
                return await fetch_func()
            except Exception as fetch_error:
                logger.error(f"Both cache and fetch failed for {key}: {fetch_error}")
                return None
    
    async def invalidate_cache(self, pattern: str = None):
        """Invalidate Redis cache entries with timeout protection"""
        try:
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                try:
                    if pattern:
                        # Get all cache keys matching pattern with timeout
                        keys = await asyncio.wait_for(
                            queue_manager.redis.keys(f"memory_cache:*{pattern}*"),
                            timeout=3.0
                        )
                        if keys:
                            await asyncio.wait_for(
                                queue_manager.redis.delete(*keys),
                                timeout=3.0
                            )
                    else:
                        # Clear all memory cache keys with timeout
                        keys = await asyncio.wait_for(
                            queue_manager.redis.keys("memory_cache:*"),
                            timeout=3.0
                        )
                        if keys:
                            await asyncio.wait_for(
                                queue_manager.redis.delete(*keys),
                                timeout=3.0
                            )
                except asyncio.TimeoutError:
                    logger.warning(f"Cache invalidation timeout - operation skipped")
                except Exception as redis_error:
                    logger.warning(f"Cache invalidation Redis error: {redis_error}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def store_agent_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any], 
                               metadata: Optional[Dict[str, Any]] = None, is_shared: bool = False,
                               confidence: float = 1.0) -> str:
        """Store memory with intelligent decision-making and minimal DB access"""
        
        # Estimate content size before optimization
        content_size_estimate = len(json.dumps(content, default=str))
        
        # More selective decision logic based on content size and importance
        should_store_global = (
            (is_shared and content_size_estimate < 5_000_000) or  # Only store reasonably sized shared content
            (confidence > 0.9 and content_size_estimate < 10_000_000) or  # Higher confidence threshold for large content
            (memory_type in ["vision", "plan", "strategy", "result"] and content_size_estimate < 8_000_000) or
            (agent_name in ["cofounder", "manager", "finance"] and content_size_estimate < 5_000_000)
        )
        
        # For extremely large content, create a summary instead of storing the full content
        if content_size_estimate > 10_000_000:
            logger.warning(f"Content for {agent_name}/{memory_type} is extremely large ({content_size_estimate/1_000_000:.2f}MB), creating summary")
            
            # Create a summary of the content
            summary_content = {
                "original_size_bytes": content_size_estimate,
                "summary": f"Large content ({content_size_estimate/1_000_000:.2f}MB) - summary only",
                "keys_available": list(content.keys())[:20],
                "timestamp": datetime.now().isoformat()
            }
            
            # Add some key fields if available
            for key in ["id", "name", "type", "summary", "result", "confidence"]:
                if key in content:
                    # Truncate if needed
                    value = content[key]
                    if isinstance(value, str) and len(value) > 500:
                        value = value[:500] + "..."
                    summary_content[key] = value
            
            # Replace content with summary for storage
            content = summary_content
            
            # Log this event
            logger.warning(f"Replaced large content with summary for {agent_name}/{memory_type}")
        
        # Optimize content for Redis storage (keep only essential data)
        optimized_content = self._optimize_for_redis(content, memory_type)
        
        # Cache selectively based on size and importance
        cache_key = f"agent_memory:{agent_name}:{memory_type}"
        
        # Only cache if the optimized content is reasonably sized or important
        optimized_size = len(json.dumps(optimized_content, default=str))
        should_cache = (
            optimized_size < 5_000_000 or  # Cache if under 5MB
            memory_type in ["vision", "plan", "strategy", "result"] or  # Always cache important types
            agent_name in ["cofounder", "manager", "finance"]  # Always cache important agents
        )
        
        if should_cache:
            try:
                # Store in Redis cache with compression/chunking handled by adapter
                if hasattr(queue_manager, 'redis') and queue_manager.redis:
                    await queue_manager.redis.setex(
                        f"memory_cache:{cache_key}",
                        self._ttl_seconds,
                        json.dumps(optimized_content, default=str)
                    )
            except Exception as e:
                logger.warning(f"Failed to cache {agent_name}/{memory_type}: {e}")
        else:
            logger.info(f"Skipped caching large content for {agent_name}/{memory_type} ({optimized_size/1_000_000:.2f}MB)")
        
        timestamp = None
        
        # Store in graph memory based on decision
        if should_store_global:
            timestamp = await self.graph_memory.write_shared_memory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content,  # Use full content for DB
                confidence=confidence
            )
            
            # Invalidate shared context cache
            await self.invalidate_cache("shared_context")
            
            # Store in vector memory only for important content with substantial text
            # Be more selective about what goes into vector DB
            text_content = self._extract_text_content(content)
            text_length = len(text_content)
            
            if text_length > 100 and text_length < 100000 and confidence > 0.8:  # More strict criteria
                doc_metadata = {
                    "agent": agent_name,
                    "type": memory_type,
                    "timestamp": str(timestamp),
                    "is_shared": True,
                    "confidence": confidence,
                    **(metadata or {})
                }
                
                doc_id = f"{agent_name}_{memory_type}_{timestamp}"
                # Fire-and-forget vector storage
                asyncio.create_task(self._async_vector_store(
                    text_content=text_content[:100000],  # Limit text size for vector DB
                    metadata=doc_metadata,
                    doc_id=doc_id
                ))
                
                # Trigger new upload event
                await cache_events.trigger_new_upload_event(memory_type, agent_name)
                
                logger.info(f"Stored {agent_name}/{memory_type} in global context + vector DB")
            else:
                logger.debug(f"Skipped vector DB for {agent_name}/{memory_type}: text too short/long or low confidence")
            
            # Trigger cache update event
            await cache_events.trigger_update_event(agent_name, memory_type, is_shared=True)
        else:
            # Store only in private memory
            timestamp = await self.graph_memory.write_private_memory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content
            )
            # Trigger cache update event for private memory
            await cache_events.trigger_update_event(agent_name, memory_type, is_shared=False)
            
            logger.debug(f"Stored {agent_name}/{memory_type} in private memory only")
        
        return str(timestamp) if timestamp else str(int(time.time()))
        
    async def _async_vector_store(self, text_content: str, metadata: Dict[str, Any], doc_id: str):
        """Asynchronous vector storage to avoid blocking main operations"""
        try:
            await self.vector_memory.add_document(
                text=text_content,
                metadata=metadata,
                doc_id=doc_id
            )
        except Exception as e:
            logger.warning(f"Async vector storage failed for {doc_id}: {e}")
    
    async def query_agent_memory(self, agent_name: str, memory_type: Optional[str] = None,
                               include_shared: bool = True) -> List[Dict[str, Any]]:
        """Query agent's memory from graph system"""
        
        # Get private memories
        private_memories = await self.graph_memory.query_private_memory(agent_name, memory_type)
        
        memories = []
        for mem in private_memories:
            memories.append({
                **mem,
                "source": "private",
                "agent": agent_name
            })
        
        # Get shared memories if requested
        if include_shared:
            shared_memories = await self.graph_memory.query_shared_memory(memory_type)
            for mem in shared_memories:
                memories.append({
                    **mem,
                    "source": "shared"
                })
        
        # Sort by timestamp
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories
    
    async def semantic_search(self, query: str, agent_name: Optional[str] = None,
                            memory_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search with event-driven caching"""
        query_hash = hash(f"{query}_{agent_name}_{memory_type}_{limit}")
        cache_key = f"search_{query_hash}"
        
        # Use event cache manager
        cached_results = await event_cache_manager.get_cached_data(
            key=cache_key,
            fetch_func=lambda: self._perform_vector_search(query, agent_name, memory_type, limit)
        )
        
        if cached_results:
            return cached_results
        
        # Fallback to direct search
        return await self._perform_vector_search(query, agent_name, memory_type, limit)
    
    async def _perform_vector_search(self, query: str, agent_name: Optional[str], 
                                   memory_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Perform actual vector search (only called when needed)"""
        try:
            filter_conditions = {}
            if agent_name:
                filter_conditions["agent"] = agent_name
            if memory_type:
                filter_conditions["type"] = memory_type
            
            search_results = await asyncio.wait_for(
                self.vector_memory.search(
                    query=query,
                    limit=limit,
                    filter_conditions=filter_conditions if filter_conditions else None
                ),
                timeout=10.0
            )
            
            return search_results
            
        except asyncio.TimeoutError:
            logger.warning(f"Vector search timeout for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def get_shared_context(self, min_confidence: float = 0.7, force_refresh: bool = False) -> Dict[str, Any]:
        """Get current shared context with optimized caching"""
        cache_key = f"shared_context_{min_confidence}"
        
        # Use existing cache system with force_db_access for event-driven updates
        return await self.get_with_cache(
            key=cache_key,
            fetch_func=lambda: self._fetch_shared_context_from_db(min_confidence),
            force_db_access=force_refresh
        )
    
    async def _fetch_shared_context_from_db(self, min_confidence: float) -> Dict[str, Any]:
        """Fetch shared context from database (only called when cache miss or event triggered)"""
        try:
            shared_memories = await asyncio.wait_for(
                self.graph_memory.query_shared_memory(min_confidence=min_confidence),
                timeout=8.0
            )
            
            # Organize by memory type
            context = {}
            for memory in shared_memories:
                mem_type = memory.get("type", "general")
                if mem_type not in context:
                    context[mem_type] = []
                
                context[mem_type].append({
                    "content": memory["content"],
                    "author": memory["author"],
                    "confidence": memory["confidence"],
                    "timestamp": memory["timestamp"]
                })
            
            # Get the most recent/highest confidence entry for each type
            consolidated_context = {}
            for mem_type, memories in context.items():
                memories.sort(key=lambda x: (x["confidence"], x["timestamp"]), reverse=True)
                consolidated_context[mem_type] = memories[0]["content"]
            
            # Cache the result
            await event_cache_manager.cache_shared_context(
                context_type="consolidated",
                content=consolidated_context,
                confidence=min_confidence
            )
            
            return consolidated_context
            
        except asyncio.TimeoutError:
            logger.warning("Shared context DB fetch timeout")
            return {}
        except Exception as e:
            logger.error(f"Error fetching shared context from DB: {e}")
            return {}
    
    async def export_all_outputs(self) -> Dict[str, str]:
        """Export all memory data to various formats"""
        
        exported_files = {}
        
        # Export to YAML
        yaml_files = await self.graph_memory.export_to_yaml(str(self.output_dir))
        exported_files.update(yaml_files)
        
        # Export to GraphML
        graphml_path = await self.graph_memory.export_to_graphml(str(self.output_dir / "graph.graphml"))
        exported_files["graph"] = graphml_path
        
        # Export consolidated outputs by agent
        await self._export_agent_outputs()
        
        # Create timeline export
        timeline_path = await self._export_timeline()
        exported_files["timeline"] = timeline_path
        
        # Cleanup old exports
        await self.graph_memory.cleanup_old_exports(str(self.output_dir))
        
        logger.info(f"Exported {len(exported_files)} files to {self.output_dir}")
        return exported_files
    
    async def _export_agent_outputs(self):
        """Export final outputs for each agent"""
        
        # Get all agents and their shared contributions
        graph_state = await self.graph_memory.get_graph_state()
        
        for agent_info in graph_state["agents"]:
            agent_name = agent_info["name"]
            
            # Get agent's shared memories
            shared_memories = await self.graph_memory.query_shared_memory()
            agent_memories = [m for m in shared_memories if m["author"] == agent_name]
            
            if agent_memories:
                # Organize by type and get the latest/highest confidence
                agent_outputs = {}
                for memory in agent_memories:
                    mem_type = memory.get("type", "general")
                    if mem_type not in agent_outputs or memory["confidence"] > agent_outputs[mem_type]["confidence"]:
                        agent_outputs[mem_type] = {
                            "content": memory["content"],
                            "confidence": memory["confidence"],
                            "timestamp": str(memory["timestamp"])
                        }
                
                # Export agent's final outputs
                if agent_outputs:
                    output_file = self.output_dir / f"{agent_name.lower()}.json"
                    with open(output_file, 'w') as f:
                        json.dump({
                            "agent": agent_name,
                            "outputs": agent_outputs,
                            "exported_at": datetime.now().isoformat()
                        }, f, indent=2)
    
    async def _export_timeline(self) -> str:
        """Export execution timeline"""
        
        # Get all memories sorted by timestamp
        all_memories = []
        
        # Get shared memories
        shared_memories = await self.graph_memory.query_shared_memory()
        for memory in shared_memories:
            all_memories.append({
                "timestamp": str(memory["timestamp"]),
                "agent": memory["author"],
                "type": memory.get("type", "unknown"),
                "action": "shared_memory_write",
                "confidence": memory["confidence"],
                "content_preview": str(memory["content"])[:100] + "..." if len(str(memory["content"])) > 100 else str(memory["content"])
            })
        
        # Sort by timestamp
        all_memories.sort(key=lambda x: x["timestamp"])
        
        timeline_data = {
            "timeline": all_memories,
            "summary": {
                "total_events": len(all_memories),
                "agents_involved": list(set(m["agent"] for m in all_memories)),
                "memory_types": list(set(m["type"] for m in all_memories)),
                "exported_at": datetime.now().isoformat()
            }
        }
        
        timeline_path = self.output_dir / "timeline.json"
        with open(timeline_path, 'w') as f:
            json.dump(timeline_data, f, indent=2)
        
        return str(timeline_path)
    
    def _extract_text_content(self, content: Dict[str, Any]) -> str:
        """Extract text content for vector storage"""
        
        text_parts = []
        
        def extract_text_recursive(obj, prefix=""):
            if isinstance(obj, str):
                if len(obj) > 10:  # Only include substantial text
                    text_parts.append(f"{prefix}: {obj}" if prefix else obj)
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    extract_text_recursive(value, key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_text_recursive(item, f"{prefix}[{i}]" if prefix else f"item_{i}")
        
        extract_text_recursive(content)
        return " ".join(text_parts)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        
        graph_state = await self.graph_memory.get_graph_state()
        vector_stats = await self.vector_memory.get_collection_info()
        
        # Get Redis memory stats if available
        redis_stats = await self.get_redis_memory_usage()
        
        return {
            "graph_memory": {
                "agents": len(graph_state["agents"]),
                "total_private_memories": sum(agent["private_memories"] for agent in graph_state["agents"]),
                "total_shared_memories": sum(agent["shared_contributions"] for agent in graph_state["agents"]),
                "recent_activity": len(graph_state["recent_shared"])
            },
            "vector_memory": {
                "total_documents": vector_stats.get("vectors_count", 0),
                "collection_status": vector_stats.get("status", "unknown")
            },
            "redis_memory": redis_stats,
            "exports": {
                "output_directory": str(self.output_dir),
                "available_files": [f.name for f in self.output_dir.glob("*") if f.is_file()]
            }
        }
    
    async def get_redis_memory_usage(self) -> Dict[str, Any]:
        """Get Redis memory usage statistics"""
        if not hasattr(queue_manager, 'redis') or not queue_manager.redis:
            return {"status": "unavailable"}
           
        try:
            # Get memory info
            info = await queue_manager.redis.info("memory")
            return {
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "unknown"),
                "total_system_memory_human": info.get("total_system_memory_human", "unknown"),
                "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to get Redis memory usage: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cleanup_old_memories(self, days_old: int = 30):
        """Clean up memories older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        # Clean up graph memory
        if self._graph_memory:
            with self._graph_memory.driver.session() as session:
                session.run("""
                    MATCH (o:Output)
                    WHERE o.created_at < $cutoff
                    DETACH DELETE o
                """, cutoff=cutoff_date)
        
        # Clean up Redis cache
        if hasattr(queue_manager, 'redis') and queue_manager.redis:
            # Get all memory cache keys
            keys = await queue_manager.redis.keys("memory_cache:*")
            for key in keys:
                try:
                    value = await queue_manager.redis.get(key)
                    if value:
                        data = json.loads(value)
                        if isinstance(data, dict) and "timestamp" in data:
                            if data["timestamp"] < cutoff_date:
                                await queue_manager.redis.delete(key)
                except Exception:
                    pass
        
        logger.info(f"Cleaned up memories older than {days_old} days")
    
    async def clear_all_memory(self):
        """Clear all memory systems - USE WITH CAUTION"""
        
        await self.graph_memory.clear_all_memory()
        await self.vector_memory.clear_collection()
        
        # Clear output files
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        
        logger.warning("All memory systems cleared")
    
    async def store_agent_private_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any]) -> str:
        """Store agent's private memory in Neo4j"""
        return await self.graph_memory.write_private_memory(
            agent_name=agent_name,
            memory_type=memory_type,
            content=content
        )
    
    async def get_agent_private_memory(self, agent_name: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get agent's private memory from Neo4j"""
        return await self.graph_memory.query_private_memory(
            agent_name=agent_name,
            memory_type=memory_type,
            limit=limit
        )
    
    async def get_global_context_for_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Get relevant global context for agent using RAG"""
        # Semantic search in Qdrant for relevant context
        search_results = await self.semantic_search(
            query=query,
            limit=5
        )
        
        # Get shared context from Neo4j
        shared_context = await self.get_shared_context()
        
        return {
            "semantic_results": search_results,
            "shared_context": shared_context,
            "agent_focus": agent_name
        }
    
    async def _periodic_cache_cleanup(self):
        """Periodically clean up expired entries in local cache"""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                await self._cleanup_local_cache()
            except Exception as e:
                logger.error(f"Error in periodic cache cleanup: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    async def _periodic_redis_cleanup(self):
        """Periodically clean up old Redis keys"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                if hasattr(queue_manager, 'redis') and queue_manager.redis:
                    # Get all memory cache keys
                    keys = await queue_manager.redis.keys("memory_cache:*")
                    # Set TTL for keys without one
                    for key in keys:
                        ttl = await queue_manager.redis.ttl(key)
                        if ttl == -1:  # No TTL set
                            await queue_manager.redis.expire(key, 86400)  # 24 hours
                    logger.info(f"Redis cleanup: set TTL for {len(keys)} keys")
            except Exception as e:
                logger.error(f"Redis cleanup error: {e}")
                await asyncio.sleep(3600)  # Wait an hour on error
    
    async def _cleanup_local_cache(self):
        """Clean up expired entries in local cache"""
        now = time.time()
        expired_keys = []
        
        # Only run cleanup if enough time has passed
        if now - self._last_cache_cleanup < 30:
            return
            
        self._last_cache_cleanup = now
        
        for key, entry in self._local_cache.items():
            if now - entry["timestamp"] > self._local_cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._local_cache[key]
        
        # Log cache efficiency metrics
        total_ops = self._local_cache_hits + self._local_cache_misses
        hit_ratio = self._local_cache_hits / total_ops if total_ops > 0 else 0
        
        if expired_keys or total_ops > 100:
            logger.debug(f"Cache stats: {len(self._local_cache)} entries, {hit_ratio:.2%} hit ratio, cleaned {len(expired_keys)} expired entries")
    
    async def _async_cache_store(self, key: str, data: Any):
        """Asynchronously store data in Redis cache"""
        try:
            await queue_manager.redis.setex(
                f"memory_cache:{key}",
                self._ttl_seconds,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.debug(f"Async cache store failed for {key}: {e}")
    
    def _optimize_for_redis(self, content: Any, memory_type: str) -> Any:
        """Optimize content for Redis storage (keep only essential data)"""
        # Extremely aggressive size limits for Upstash Redis
        MAX_STRING_LENGTH = 250  # Drastically reduced from 500
        MAX_LIST_ITEMS = 5       # Reduced from 10
        MAX_DICT_ITEMS = 8       # Reduced from 15
        MAX_TOTAL_SIZE = 1_000_000  # 1MB max total size
        
        # Estimate initial size
        initial_size = len(json.dumps(content, default=str))
        
        # For extremely large content, create a summary instead
        if initial_size > 5_000_000:  # 5MB
            if isinstance(content, dict):
                keys_summary = ", ".join(list(content.keys())[:10])
                if len(content.keys()) > 10:
                    keys_summary += f"... ({len(content.keys()) - 10} more keys)"
                
                return {
                    "_extreme_size_summary": True,
                    "_original_size_bytes": initial_size,
                    "_content_type": memory_type,
                    "_keys_available": keys_summary,
                    "summary": f"Content too large for Redis storage ({initial_size/1_000_000:.2f}MB)",
                    "timestamp": datetime.now().isoformat()
                }
        
        def truncate_recursive(obj, depth=0, size_so_far=0):
            """Recursively truncate nested objects to reduce size"""
            # Emergency exit if we're already too big
            if size_so_far > MAX_TOTAL_SIZE:
                return "[content truncated: too large]"
                
            # Limit recursion depth
            if depth > 2:  # Reduced from 3
                return "[nested content truncated]"
                
            if isinstance(obj, str):
                # More aggressive string truncation
                if len(obj) > MAX_STRING_LENGTH:
                    # For very long strings, be even more aggressive
                    if len(obj) > 10000:
                        return f"[long text: {len(obj)} chars]"
                    return obj[:MAX_STRING_LENGTH] + "..."
                return obj
                
            elif isinstance(obj, dict):
                # For large dictionaries, be very selective
                if len(obj) > MAX_DICT_ITEMS:
                    # Prioritize known important keys
                    important_keys = ["id", "name", "type", "content", "summary", "result", "confidence"]
                    result = {}
                    
                    # First add important keys
                    for key in important_keys:
                        if key in obj:
                            result[key] = truncate_recursive(obj[key], depth + 1, size_so_far)
                            size_so_far += len(str(result[key]))
                    
                    # Then add other keys up to the limit
                    remaining_slots = MAX_DICT_ITEMS - len(result)
                    for key, value in list(obj.items())[:remaining_slots]:
                        if key not in result:
                            result[key] = truncate_recursive(value, depth + 1, size_so_far)
                            size_so_far += len(str(result[key]))
                            
                            # Emergency exit if getting too large
                            if size_so_far > MAX_TOTAL_SIZE:
                                result["_size_limit_reached"] = True
                                break
                    
                    result["_truncated"] = True
                    result["_original_size"] = len(obj)
                    return result
                
                # Process normal sized dict
                result = {}
                for k, v in obj.items():
                    result[k] = truncate_recursive(v, depth + 1, size_so_far)
                    size_so_far += len(str(result[k]))
                    
                    # Emergency exit if getting too large
                    if size_so_far > MAX_TOTAL_SIZE:
                        result["_size_limit_reached"] = True
                        break
                
                return result
                
            elif isinstance(obj, list):
                # More aggressive list truncation
                if len(obj) > MAX_LIST_ITEMS:
                    truncated = []
                    for i, item in enumerate(obj[:MAX_LIST_ITEMS]):
                        if size_so_far > MAX_TOTAL_SIZE:
                            break
                        truncated_item = truncate_recursive(item, depth + 1, size_so_far)
                        truncated.append(truncated_item)
                        size_so_far += len(str(truncated_item))
                    
                    truncated.append(f"... ({len(obj) - len(truncated)} more items)")
                    return truncated
                
                result = []
                for item in obj:
                    if size_so_far > MAX_TOTAL_SIZE:
                        result.append("[remaining items truncated: too large]")
                        break
                    truncated_item = truncate_recursive(item, depth + 1, size_so_far)
                    result.append(truncated_item)
                    size_so_far += len(str(truncated_item))
                
                return result
            
            # For other types (int, float, bool, None)
            return obj
            
        if isinstance(content, dict):
            # Keep only essential fields for Redis
            essential_fields = ["content", "output", "result", "summary", "confidence", "type"]
            optimized = {}
            
            # First pass: extract only essential fields
            for field in essential_fields:
                if field in content:
                    optimized[field] = content[field]
            
            # If we have very few essential fields, include some others
            if len(optimized) < 3:
                # Add a few more fields but limit total
                additional_fields = list(content.keys())[:5]
                for field in additional_fields:
                    if field not in optimized:
                        optimized[field] = content[field]
            
            # Second pass: truncate all values recursively
            optimized = truncate_recursive(optimized)
            
            # Add metadata
            optimized["memory_type"] = memory_type
            optimized["cached_at"] = datetime.now().isoformat()
            return optimized
        
        elif isinstance(content, str):
            # Truncate long strings more aggressively
            if len(content) > MAX_STRING_LENGTH:
                return {
                    "content": content[:MAX_STRING_LENGTH] + "...",
                    "truncated": True,
                    "original_length": len(content)
                }
            return content
        
        # For other types, apply recursive truncation
        return truncate_recursive(content)
    
    async def _store_in_redis_cache(self, key: str, content: Any, confidence: float):
        """Store content in Redis cache with metadata"""
        try:
            if hasattr(queue_manager, 'redis') and queue_manager.redis:
                cache_data = {
                    "content": content,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                    "cached_at": time.time()
                }
                
                await queue_manager.redis.setex(
                    f"memory_cache:{key}",
                    self._ttl_seconds,
                    json.dumps(cache_data, default=str)
                )
        except Exception as e:
            logger.debug(f"Redis cache store failed for {key}: {e}")
    
    def close(self):
        """Close all memory system connections"""
        if self._graph_memory:
            self._graph_memory.close()
        # Clear local cache
        self._local_cache.clear()
        self._hot_cache.clear()
        # Vector memory client will be closed automatically
        # Redis cache is managed by queue_manager

# Backward compatibility alias
MemoryManager = OptimizedMemoryManager