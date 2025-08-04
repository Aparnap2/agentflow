"""
Optimized Vector Search - Enhanced vector search with filtering and caching
"""

import asyncio
import hashlib
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from cachetools import TTLCache
from loguru import logger

class OptimizedVectorSearch:
    """Optimized vector search with advanced filtering and caching"""
    
    def __init__(self, vector_memory):
        self.vector_memory = vector_memory
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
        self.batch_size = 10  # Number of queries to batch together
        self.batch_queue = []
        self.batch_results = {}
        self.batch_event = asyncio.Event()
        self.processing_batch = False
        
        # Start background batch processor
        asyncio.create_task(self._batch_processor())
    
    async def search(self, query: str, agent_name: Optional[str] = None, 
                   memory_type: Optional[str] = None, limit: int = 5,
                   min_score: float = 0.7) -> List[Dict[str, Any]]:
        """Search for relevant vectors with optimized filtering and caching"""
        # Generate cache key
        cache_key = self._generate_cache_key(query, agent_name, memory_type, limit, min_score)
        
        # Check cache first
        if cache_key in self.cache:
            logger.debug(f"Vector search cache hit for: {query[:30]}...")
            return self.cache[cache_key]
        
        # Build filter
        filter_conditions = {}
        if agent_name:
            filter_conditions["agent"] = agent_name
        if memory_type:
            filter_conditions["type"] = memory_type
        
        try:
            # Execute search with optimized parameters
            results = await self.vector_memory.search(
                query=query,
                limit=limit,
                filter_conditions=filter_conditions if filter_conditions else None,
                score_threshold=min_score
            )
            
            # Cache results
            self.cache[cache_key] = results
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def batch_search(self, queries: List[str], agent_name: Optional[str] = None,
                         memory_type: Optional[str] = None, limit: int = 5) -> List[List[Dict[str, Any]]]:
        """Perform multiple searches in a single batch for efficiency"""
        if not queries:
            return []
            
        # Generate unique IDs for each query
        query_ids = [self._generate_query_id(q, agent_name, memory_type, limit) for q in queries]
        
        # Check which queries are already cached
        results = []
        uncached_indices = []
        uncached_queries = []
        
        for i, (query, query_id) in enumerate(zip(queries, query_ids)):
            cache_key = self._generate_cache_key(query, agent_name, memory_type, limit)
            if cache_key in self.cache:
                results.append(self.cache[cache_key])
            else:
                results.append(None)  # Placeholder
                uncached_indices.append(i)
                uncached_queries.append(query)
        
        if not uncached_queries:
            return results  # All results were cached
        
        # Add uncached queries to batch queue
        batch_items = []
        for i, query in zip(uncached_indices, uncached_queries):
            query_id = query_ids[i]
            batch_items.append({
                "query": query,
                "query_id": query_id,
                "agent_name": agent_name,
                "memory_type": memory_type,
                "limit": limit,
                "result_index": i
            })
            
        # Add to batch queue and wait for results
        for item in batch_items:
            self.batch_queue.append(item)
            
        # Wait for batch processing to complete
        if not self.processing_batch:
            self.batch_event.set()
        
        # Wait for results with timeout
        start_time = datetime.now()
        timeout = timedelta(seconds=10)
        
        while datetime.now() - start_time < timeout:
            # Check if all results are available
            all_available = True
            for item in batch_items:
                if item["query_id"] not in self.batch_results:
                    all_available = False
                    break
                    
            if all_available:
                break
                
            await asyncio.sleep(0.1)
        
        # Fill in results
        for item in batch_items:
            query_id = item["query_id"]
            index = item["result_index"]
            
            if query_id in self.batch_results:
                results[index] = self.batch_results[query_id]
                
                # Cache the result
                cache_key = self._generate_cache_key(
                    item["query"], 
                    item["agent_name"], 
                    item["memory_type"], 
                    item["limit"]
                )
                self.cache[cache_key] = self.batch_results[query_id]
                
                # Clean up
                del self.batch_results[query_id]
            else:
                # Timeout or error - provide empty result
                results[index] = []
        
        return results
    
    async def _batch_processor(self):
        """Background task to process batched search queries"""
        while True:
            # Wait for items in the queue
            if not self.batch_queue:
                self.batch_event.clear()
                await self.batch_event.wait()
            
            self.processing_batch = True
            
            try:
                # Process items in batches
                while self.batch_queue:
                    # Take a batch of items
                    batch = self.batch_queue[:self.batch_size]
                    self.batch_queue = self.batch_queue[self.batch_size:]
                    
                    # Group by agent_name and memory_type to minimize API calls
                    grouped_batches = {}
                    for item in batch:
                        key = (item["agent_name"], item["memory_type"])
                        if key not in grouped_batches:
                            grouped_batches[key] = []
                        grouped_batches[key].append(item)
                    
                    # Process each group
                    for (agent_name, memory_type), items in grouped_batches.items():
                        queries = [item["query"] for item in items]
                        
                        try:
                            # Build filter
                            filter_conditions = {}
                            if agent_name:
                                filter_conditions["agent"] = agent_name
                            if memory_type:
                                filter_conditions["type"] = memory_type
                            
                            # Get max limit
                            max_limit = max(item["limit"] for item in items)
                            
                            # Execute batch search
                            batch_results = await self.vector_memory.batch_search(
                                queries=queries,
                                limit=max_limit,
                                filter_conditions=filter_conditions if filter_conditions else None
                            )
                            
                            # Store results
                            for i, item in enumerate(items):
                                query_id = item["query_id"]
                                limit = item["limit"]
                                
                                if i < len(batch_results):
                                    # Limit results to requested limit
                                    self.batch_results[query_id] = batch_results[i][:limit]
                                else:
                                    self.batch_results[query_id] = []
                                    
                        except Exception as e:
                            logger.error(f"Batch search error: {e}")
                            # Set empty results for failed batch
                            for item in items:
                                self.batch_results[item["query_id"]] = []
                    
                    # Small delay between batches
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
            
            self.processing_batch = False
            await asyncio.sleep(0.1)
    
    def _generate_cache_key(self, query: str, agent_name: Optional[str], 
                          memory_type: Optional[str], limit: int,
                          min_score: float = 0.7) -> str:
        """Generate cache key for a query"""
        key_parts = [
            query[:100],  # Limit query length for key
            str(agent_name),
            str(memory_type),
            str(limit),
            str(min_score)
        ]
        return hashlib.md5(json.dumps(key_parts).encode()).hexdigest()
    
    def _generate_query_id(self, query: str, agent_name: Optional[str],
                         memory_type: Optional[str], limit: int) -> str:
        """Generate unique ID for a query in a batch"""
        return hashlib.md5(f"{query}:{agent_name}:{memory_type}:{limit}:{datetime.now().timestamp()}".encode()).hexdigest()
    
    async def semantic_search_with_fallback(self, query: str, agent_name: Optional[str] = None,
                                         memory_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search with fallback mechanisms"""
        try:
            # Try primary search
            results = await self.search(query, agent_name, memory_type, limit)
            
            # If we got results, return them
            if results:
                return results
                
            # If no results, try without agent filter
            if agent_name:
                logger.debug(f"No results for {query[:30]}... with agent {agent_name}, trying without agent filter")
                results = await self.search(query, None, memory_type, limit)
                if results:
                    return results
            
            # If still no results, try without memory_type filter
            if memory_type:
                logger.debug(f"No results for {query[:30]}... with type {memory_type}, trying without type filter")
                results = await self.search(query, agent_name, None, limit)
                if results:
                    return results
            
            # If still no results, try with no filters and lower score threshold
            logger.debug(f"No results for {query[:30]}..., trying with no filters and lower threshold")
            results = await self.search(query, None, None, limit, min_score=0.5)
            return results
            
        except Exception as e:
            logger.error(f"Semantic search with fallback error: {e}")
            return []
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cache.clear()
        logger.info("Vector search cache cleared")