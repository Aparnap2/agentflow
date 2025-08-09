"""
Memory Optimization API - Monitor and test the optimized caching system
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from loguru import logger

from memory.memory_manager import MemoryManager
from memory.cache_events import cache_events

router = APIRouter(prefix="/memory", tags=["memory-optimization"])

class TestMemoryRequest(BaseModel):
    agent_name: str
    memory_type: str
    content: Dict[str, Any]
    confidence: Optional[float] = 1.0
    is_shared: Optional[bool] = False

@router.get("/cache-stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    try:
        # Create a temporary memory manager to get stats
        memory_manager = MemoryManager()
        
        stats = {
            "local_cache_size": len(memory_manager._local_cache),
            "hot_cache_size": len(memory_manager._hot_cache),
            "cache_hits": memory_manager._local_cache_hits,
            "cache_misses": memory_manager._local_cache_misses,
            "hit_ratio": (
                memory_manager._local_cache_hits / 
                (memory_manager._local_cache_hits + memory_manager._local_cache_misses)
                if (memory_manager._local_cache_hits + memory_manager._local_cache_misses) > 0 
                else 0
            ),
            "pending_invalidations": len(cache_events.pending_invalidations),
            "pending_patterns": list(cache_events.pending_invalidations)
        }
        
        return {
            "cache_performance": stats,
            "optimization_status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-storage")
async def test_storage_optimization(request: TestMemoryRequest):
    """Test the storage optimization with sample data"""
    try:
        memory_manager = MemoryManager()
        
        # Store the memory and measure what happens
        timestamp = await memory_manager.store_agent_memory(
            agent_name=request.agent_name,
            memory_type=request.memory_type,
            content=request.content,
            is_shared=request.is_shared,
            confidence=request.confidence
        )
        
        # Check what was cached
        cache_key = f"agent_memory:{request.agent_name}:{request.memory_type}"
        
        # Determine storage decision
        text_content = memory_manager._extract_text_content(request.content)
        should_store_global = (
            request.is_shared or 
            request.confidence > 0.8 or 
            request.memory_type in ["vision", "plan", "strategy", "result"] or
            request.agent_name in ["cofounder", "manager", "finance"]
        )
        
        storage_decision = {
            "stored_globally": should_store_global,
            "stored_in_vector_db": (
                should_store_global and 
                len(text_content) > 100 and 
                request.confidence > 0.7
            ),
            "text_length": len(text_content),
            "confidence": request.confidence,
            "reasoning": []
        }
        
        # Add reasoning
        if request.confidence > 0.8:
            storage_decision["reasoning"].append("High confidence score")
        if request.memory_type in ["vision", "plan", "strategy", "result"]:
            storage_decision["reasoning"].append("Important memory type")
        if request.agent_name in ["cofounder", "manager", "finance"]:
            storage_decision["reasoning"].append("High-priority agent")
        if len(text_content) > 100:
            storage_decision["reasoning"].append("Substantial text content")
        
        return {
            "timestamp": timestamp,
            "storage_decision": storage_decision,
            "cache_key": cache_key,
            "optimized_content_size": len(str(memory_manager._optimize_for_redis(request.content, request.memory_type)))
        }
        
    except Exception as e:
        logger.error(f"Error testing storage optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shared-context")
async def get_shared_context_info(min_confidence: float = 0.7):
    """Get shared context with caching info"""
    try:
        memory_manager = MemoryManager()
        
        # Get shared context (will use cache if available)
        context = await memory_manager.get_shared_context(min_confidence=min_confidence)
        
        # Check if DB access was needed
        cache_key = f"shared_context_{min_confidence}"
        db_access_needed = await cache_events.should_access_db(cache_key)
        
        return {
            "shared_context": context,
            "cache_info": {
                "db_access_needed": db_access_needed,
                "cache_key": cache_key,
                "context_types": list(context.keys()) if context else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting shared context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-cache-refresh")
async def trigger_cache_refresh(pattern: Optional[str] = None):
    """Trigger cache refresh for testing"""
    try:
        if pattern:
            cache_events.pending_invalidations.add(pattern)
            message = f"Added {pattern} to pending invalidations"
        else:
            cache_events.pending_invalidations.add("shared_context")
            cache_events.pending_invalidations.add("search_*")
            message = "Triggered refresh for shared context and search cache"
        
        return {
            "message": message,
            "pending_invalidations": list(cache_events.pending_invalidations)
        }
        
    except Exception as e:
        logger.error(f"Error triggering cache refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory-stats")
async def get_memory_system_stats():
    """Get comprehensive memory system statistics"""
    try:
        memory_manager = MemoryManager()
        
        # Get memory stats
        stats = await memory_manager.get_memory_stats()
        
        # Add cache optimization info
        stats["cache_optimization"] = {
            "local_cache_entries": len(memory_manager._local_cache),
            "hot_cache_entries": len(memory_manager._hot_cache),
            "pending_events": len(cache_events.pending_invalidations),
            "cache_hit_ratio": (
                memory_manager._local_cache_hits / 
                (memory_manager._local_cache_hits + memory_manager._local_cache_misses)
                if (memory_manager._local_cache_hits + memory_manager._local_cache_misses) > 0 
                else 0
            )
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup-cache")
async def cleanup_cache_events():
    """Clean up old cache events"""
    try:
        await cache_events.cleanup_pending_events()
        
        return {
            "message": "Cache events cleaned up",
            "remaining_events": len(cache_events.pending_invalidations)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))