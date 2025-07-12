"""
Unified Memory Manager - Coordinates graph and vector memory systems
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from .graph_memory import GraphMemory
from .vector_memory import VectorMemory


class OptimizedMemoryManager:
    """Optimized memory manager with caching and lazy loading"""
    
    def __init__(self):
        self._graph_memory = None
        self._vector_memory = None
        self._cache = {}
        self._cache_ttl = {}
        self._ttl_seconds = 300  # 5 minutes
        self.output_dir = Path("./data")
        self.output_dir.mkdir(exist_ok=True)
    
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
    
    async def get_with_cache(self, key: str, fetch_func):
        """Get data with caching"""
        import time
        now = time.time()
        
        if key in self._cache and now - self._cache_ttl.get(key, 0) < self._ttl_seconds:
            return self._cache[key]
        
        result = await fetch_func()
        self._cache[key] = result
        self._cache_ttl[key] = now
        return result
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
        else:
            self._cache.clear()
            self._cache_ttl.clear()
    
    async def store_agent_memory(self, agent_name: str, memory_type: str, content: Dict[str, Any], 
                               metadata: Optional[Dict[str, Any]] = None, is_shared: bool = False,
                               confidence: float = 1.0) -> str:
        """Store memory in both graph and vector systems with cache invalidation"""
        
        # Store in graph memory
        if is_shared:
            timestamp = await self.graph_memory.write_shared_memory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content,
                confidence=confidence
            )
        else:
            timestamp = await self.graph_memory.write_private_memory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content
            )
        
        # Store in vector memory for semantic search
        if isinstance(content, dict) and any(isinstance(v, str) and len(v) > 50 for v in content.values()):
            # Only store in vector memory if there's substantial text content
            text_content = self._extract_text_content(content)
            if text_content:
                doc_metadata = {
                    "agent": agent_name,
                    "type": memory_type,
                    "timestamp": str(timestamp),
                    "is_shared": is_shared,
                    "confidence": confidence,
                    **(metadata or {})
                }
                
                await self.vector_memory.add_document(
                    text=text_content,
                    metadata=doc_metadata,
                    doc_id=f"{agent_name}_{memory_type}_{timestamp}"
                )
        
        # Invalidate relevant cache entries
        self.invalidate_cache("shared_context")
        self.invalidate_cache("search_")
        
        return str(timestamp)
    
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
        """Perform semantic search across memories with caching"""
        cache_key = f"search_{hash(query)}_{agent_name}_{memory_type}_{limit}"
        
        async def perform_search():
            # Build filter conditions
            filter_conditions = {}
            if agent_name:
                filter_conditions["agent"] = agent_name
            if memory_type:
                filter_conditions["type"] = memory_type
            
            # Search vector memory
            search_results = await self.vector_memory.search(
                query=query,
                limit=limit,
                filter_conditions=filter_conditions if filter_conditions else None
            )
            
            return search_results
        
        return await self.get_with_cache(cache_key, perform_search)
    
    async def get_shared_context(self, min_confidence: float = 0.7) -> Dict[str, Any]:
        """Get current shared context for agents with caching"""
        cache_key = f"shared_context_{min_confidence}"
        
        async def fetch_shared_context():
            shared_memories = await self.graph_memory.query_shared_memory(min_confidence=min_confidence)
            
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
                # Sort by confidence first, then by timestamp
                memories.sort(key=lambda x: (x["confidence"], x["timestamp"]), reverse=True)
                consolidated_context[mem_type] = memories[0]["content"]
            
            return consolidated_context
        
        return await self.get_with_cache(cache_key, fetch_shared_context)
    
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
            "exports": {
                "output_directory": str(self.output_dir),
                "available_files": [f.name for f in self.output_dir.glob("*") if f.is_file()]
            }
        }
    
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
    
    def close(self):
        """Close all memory system connections"""
        if self._graph_memory:
            self._graph_memory.close()
        # Vector memory client will be closed automatically
        self._cache.clear()
        self._cache_ttl.clear()

# Backward compatibility alias
MemoryManager = OptimizedMemoryManager