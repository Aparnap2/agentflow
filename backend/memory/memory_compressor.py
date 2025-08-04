"""
Memory Compressor - Compresses multiple memory items into summaries
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

class MemoryCompressor:
    """Compresses multiple memory items into summaries to reduce storage and token usage"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def compress_memories(self, memory_items: List[Dict[str, Any]], max_items: int = 5) -> List[Dict[str, Any]]:
        """Compress multiple memory items into a smaller set"""
        if len(memory_items) <= max_items:
            return memory_items
            
        # Group similar items
        clusters = self._cluster_items(memory_items)
        
        # Compress each cluster
        compressed_items = []
        for cluster in clusters:
            if len(cluster) == 1:
                # Single item, no compression needed
                compressed_items.append(cluster[0])
            else:
                # Compress cluster
                summary = await self._summarize_cluster(cluster)
                compressed_items.append({
                    "type": "compressed_memory",
                    "content": summary,
                    "source_count": len(cluster),
                    "timestamp": max(item.get("timestamp", datetime.now().isoformat()) for item in cluster),
                    "compressed": True,
                    "original_types": list(set(item.get("type", "unknown") for item in cluster))
                })
                
        # If we still have too many items, prioritize by recency and importance
        if len(compressed_items) > max_items:
            # Sort by importance and recency
            compressed_items.sort(
                key=lambda x: (
                    x.get("source_count", 1),  # More sources = more important
                    x.get("timestamp", "")     # More recent = more important
                ),
                reverse=True
            )
            compressed_items = compressed_items[:max_items]
        
        return compressed_items
    
    def _cluster_items(self, items: List[Dict[str, Any]], similarity_threshold: float = 0.7) -> List[List[Dict[str, Any]]]:
        """Group similar memory items into clusters"""
        clusters = []
        
        for item in items:
            # Extract content for comparison
            content = self._extract_content(item)
            if not content:
                # Skip items without content
                continue
                
            # Find best matching cluster
            best_match = None
            best_score = 0
            
            for i, cluster in enumerate(clusters):
                # Compare with first item in cluster
                cluster_content = self._extract_content(cluster[0])
                similarity = self._calculate_similarity(content, cluster_content)
                
                if similarity > similarity_threshold and similarity > best_score:
                    best_match = i
                    best_score = similarity
            
            if best_match is not None:
                # Add to existing cluster
                clusters[best_match].append(item)
            else:
                # Create new cluster
                clusters.append([item])
                
        return clusters
    
    def _extract_content(self, item: Dict[str, Any]) -> str:
        """Extract text content from a memory item"""
        # Try different common content fields
        for field in ["content", "text", "message", "data"]:
            if field in item:
                content = item[field]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict):
                    # Try to extract text from dict
                    for subfield in ["text", "content", "message", "summary"]:
                        if subfield in content and isinstance(content[subfield], str):
                            return content[subfield]
                    # If no specific field found, convert dict to string
                    return json.dumps(content)
                elif isinstance(content, list) and all(isinstance(x, str) for x in content):
                    # List of strings
                    return " ".join(content)
        
        # Fallback: convert whole item to string
        return json.dumps(item)
    
    async def _summarize_cluster(self, cluster: List[Dict[str, Any]]) -> str:
        """Summarize a cluster of similar memory items"""
        # Extract content from cluster
        contents = [self._extract_content(item) for item in cluster]
        combined = "\n\n".join(contents)
        
        # If LLM service is available, use it for summarization
        if self.llm_service:
            try:
                summary = await self.llm_service.generate(
                    system_prompt="You are a memory compression system. Summarize the following related memories into a concise summary that preserves the key information.",
                    user_message=f"Please summarize these related memories:\n\n{combined}",
                    temperature=0.3,
                    max_tokens=200
                )
                return summary
            except Exception as e:
                logger.error(f"LLM summarization failed: {e}")
                # Fall back to simple summarization
        
        # Simple summarization: keep first item and note the count
        first_item = self._extract_content(cluster[0])
        if len(first_item) > 500:
            first_item = first_item[:500] + "..."
            
        return f"[Group of {len(cluster)} similar items] {first_item}"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple implementation using word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        return len(intersection) / (len(words1) + len(words2) - len(intersection))
    
    async def compress_agent_memory(self, agent_name: str, memory_manager, max_items_per_type: int = 5) -> Dict[str, Any]:
        """Compress an agent's memory by type"""
        # Get agent's memory
        memories = await memory_manager.query_agent_memory(agent_name)
        
        # Group by type
        memories_by_type = {}
        for memory in memories:
            mem_type = memory.get("type", "general")
            if mem_type not in memories_by_type:
                memories_by_type[mem_type] = []
            memories_by_type[mem_type].append(memory)
        
        # Compress each type
        compressed_memory = {}
        for mem_type, items in memories_by_type.items():
            if len(items) > max_items_per_type:
                compressed_items = await self.compress_memories(items, max_items_per_type)
                compressed_memory[mem_type] = compressed_items
            else:
                compressed_memory[mem_type] = items
        
        return compressed_memory