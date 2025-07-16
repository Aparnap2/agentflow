"""
Event-Driven Cache Manager - Optimized for minimal DB access
Only accesses Qdrant/Neo4j on specific events, uses Redis cache otherwise
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from loguru import logger
from enum import Enum

from task_queue.enhanced_queue_manager import queue_manager

class CacheEvent(Enum):
    UPDATE = "update"
    NEW_UPLOAD = "new_upload" 
    DELETE = "delete"
    AGENT_DECISION = "agent_decision"
    CONTEXT_CHANGE = "context_change"

class EventCacheManager:
    """Event-driven cache manager with minimal DB access"""
    
    def __init__(self):
        self.cache_prefix = "agentflow_cache"
        self.context_ttl = 1800  # 30 minutes for context data
        self.memory_ttl = 300    # 5 minutes for memory data
        self.hot_keys: Set[str] = set()
        
        # Event subscribers
        self.event_handlers = {
            CacheEvent.UPDATE: self._handle_update_event,
            CacheEvent.NEW_UPLOAD: self._handle_new_upload_event,
            CacheEvent.DELETE: self._handle_delete_event,
            CacheEvent.AGENT_DECISION: self._handle_agent_decision_event,
            CacheEvent.CONTEXT_CHANGE: self._handle_context_change_event
        }
        
        # Track what's in cache vs needs DB fetch
        self.cache_status = {}
        
    async def get_cached_data(self, key: str, fetch_func=None) -> Optional[Any]:
        """Get data from cache, only fetch from DB if cache miss and event triggered"""
        cache_key = f"{self.cache_prefix}:{key}"
        
        try:
            if queue_manager.redis:
                # Try cache first
                cached = await queue_manager.redis.get(cache_key)
                if cached:
                    self.hot_keys.add(key)
                    return json.loads(cached)
                
                # Check if this key should be fetched from DB
                if not self._should_fetch_from_db(key):
                    logger.debug(f"Skipping DB fetch for {key} - no triggering event")
                    return None
                    
                # Fetch from DB only if event-triggered
                if fetch_func:
                    data = await fetch_func()
                    if data:
                        await self._cache_data(cache_key, data, key)
                    return data
                    
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            
        return None
    
    async def cache_agent_memory(self, agent_name: str, memory_type: str, content: Any) -> bool:
        """Cache agent memory with minimal payload"""
        key = f"agent_memory:{agent_name}:{memory_type}"
        
        # Only store essential data in Redis (not full vectors)
        cache_data = {
            "content": content if isinstance(content, (str, dict)) else str(content),
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "type": memory_type
        }
        
        return await self._cache_data(f"{self.cache_prefix}:{key}", cache_data, key)
    
    async def cache_shared_context(self, context_type: str, content: Any, confidence: float = 1.0) -> bool:
        """Cache shared context data"""
        key = f"shared_context:{context_type}"
        
        cache_data = {
            "content": content,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "cached_at": time.time()
        }
        
        # Mark as hot key for frequent access
        self.hot_keys.add(key)
        
        return await self._cache_data(f"{self.cache_prefix}:{key}", cache_data, key, ttl=self.context_ttl)
    
    async def trigger_event(self, event: CacheEvent, data: Dict[str, Any]) -> None:
        """Trigger cache event and handle accordingly"""
        try:
            handler = self.event_handlers.get(event)
            if handler:
                await handler(data)
                logger.debug(f"Handled cache event: {event.value}")
            else:
                logger.warning(f"No handler for event: {event.value}")
        except Exception as e:
            logger.error(f"Error handling cache event {event.value}: {e}")
    
    async def _handle_update_event(self, data: Dict[str, Any]) -> None:
        """Handle update events - invalidate related cache"""
        agent_name = data.get("agent_name")
        memory_type = data.get("memory_type")
        
        if agent_name:
            # Invalidate agent-specific cache
            await self._invalidate_pattern(f"agent_memory:{agent_name}*")
            
        if memory_type:
            # Invalidate type-specific cache
            await self._invalidate_pattern(f"*:{memory_type}")
    
    async def _handle_new_upload_event(self, data: Dict[str, Any]) -> None:
        """Handle new upload events - clear relevant cache, trigger DB sync"""
        # Mark that DB needs to be accessed for this type of data
        content_type = data.get("content_type", "general")
        self.cache_status[f"needs_db_sync:{content_type}"] = True
        
        # Invalidate related cache
        await self._invalidate_pattern(f"*{content_type}*")
        
        logger.info(f"New upload event triggered for {content_type}")
    
    async def _handle_delete_event(self, data: Dict[str, Any]) -> None:
        """Handle delete events - remove from cache and mark for DB cleanup"""
        keys_to_delete = data.get("keys", [])
        
        for key in keys_to_delete:
            await self._invalidate_key(key)
            
        # Mark for DB cleanup
        self.cache_status["needs_db_cleanup"] = True
    
    async def _handle_agent_decision_event(self, data: Dict[str, Any]) -> None:
        """Handle agent decision events - update cache based on agent choice"""
        decision = data.get("decision")  # "global" or "local"
        content = data.get("content")
        agent_name = data.get("agent_name")
        
        if decision == "global":
            # Cache as shared context
            await self.cache_shared_context(
                context_type=data.get("context_type", "agent_decision"),
                content=content,
                confidence=data.get("confidence", 0.8)
            )
            # Mark for vector DB upload
            self.cache_status[f"needs_vector_upload:{agent_name}"] = content
        else:
            # Cache as local agent memory
            await self.cache_agent_memory(
                agent_name=agent_name,
                memory_type=data.get("memory_type", "local_decision"),
                content=content
            )
    
    async def _handle_context_change_event(self, data: Dict[str, Any]) -> None:
        """Handle context change events - refresh shared context cache"""
        # Invalidate all shared context
        await self._invalidate_pattern("shared_context:*")
        
        # Mark that shared context needs refresh from DB
        self.cache_status["needs_context_refresh"] = True
    
    async def _cache_data(self, cache_key: str, data: Any, original_key: str, ttl: Optional[int] = None) -> bool:
        """Cache data with appropriate TTL"""
        try:
            if queue_manager.redis:
                ttl = ttl or (self.context_ttl if original_key in self.hot_keys else self.memory_ttl)
                
                await queue_manager.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(data, default=str)
                )
                
                # Track cache status
                self.cache_status[original_key] = {
                    "cached_at": time.time(),
                    "ttl": ttl
                }
                
                return True
        except Exception as e:
            logger.warning(f"Failed to cache data for {original_key}: {e}")
            
        return False
    
    async def _invalidate_key(self, key: str) -> None:
        """Invalidate specific cache key"""
        try:
            if queue_manager.redis:
                cache_key = f"{self.cache_prefix}:{key}"
                await queue_manager.redis.delete(cache_key)
                
                # Remove from tracking
                if key in self.cache_status:
                    del self.cache_status[key]
                    
                self.hot_keys.discard(key)
                
        except Exception as e:
            logger.warning(f"Failed to invalidate key {key}: {e}")
    
    async def _invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache keys matching pattern"""
        try:
            if queue_manager.redis:
                # Get keys matching pattern
                full_pattern = f"{self.cache_prefix}:{pattern}"
                
                # For Upstash compatibility, we'll track keys manually
                keys_to_delete = []
                for tracked_key in list(self.cache_status.keys()):
                    if self._pattern_match(tracked_key, pattern):
                        keys_to_delete.append(f"{self.cache_prefix}:{tracked_key}")
                        
                if keys_to_delete:
                    await queue_manager.redis.delete(*keys_to_delete)
                    
                # Clean up tracking
                for key in keys_to_delete:
                    clean_key = key.replace(f"{self.cache_prefix}:", "")
                    if clean_key in self.cache_status:
                        del self.cache_status[clean_key]
                    self.hot_keys.discard(clean_key)
                    
        except Exception as e:
            logger.warning(f"Failed to invalidate pattern {pattern}: {e}")
    
    def _pattern_match(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys"""
        if "*" not in pattern:
            return key == pattern
            
        # Convert pattern to regex-like matching
        pattern_parts = pattern.split("*")
        
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            return key.startswith(prefix) and key.endswith(suffix)
        elif pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return key.endswith(pattern[1:])
            
        return False
    
    def _should_fetch_from_db(self, key: str) -> bool:
        """Determine if we should fetch from DB based on events and cache status"""
        # Always fetch if explicitly marked for DB sync
        if any(key.endswith(k.split(":")[-1]) for k in self.cache_status.keys() if k.startswith("needs_db_sync")):
            return True
            
        # Fetch if it's a hot key and cache is stale
        if key in self.hot_keys:
            cache_info = self.cache_status.get(key)
            if cache_info:
                age = time.time() - cache_info.get("cached_at", 0)
                return age > cache_info.get("ttl", self.memory_ttl)
                
        # Don't fetch for non-critical data
        return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "hot_keys_count": len(self.hot_keys),
            "tracked_keys_count": len(self.cache_status),
            "cache_events_pending": len([k for k in self.cache_status.keys() if k.startswith("needs_")]),
            "hot_keys": list(self.hot_keys)[:10],  # First 10 hot keys
        }
    
    async def cleanup_expired_tracking(self) -> None:
        """Clean up expired cache tracking entries"""
        now = time.time()
        expired_keys = []
        
        for key, info in self.cache_status.items():
            if isinstance(info, dict) and "cached_at" in info:
                age = now - info["cached_at"]
                if age > info.get("ttl", self.memory_ttl) * 2:  # Double TTL for cleanup
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_status[key]
            self.hot_keys.discard(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache tracking entries")

# Global instance
event_cache_manager = EventCacheManager()