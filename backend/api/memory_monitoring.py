"""
Memory monitoring endpoints for system health and optimization
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from coordination.enhanced_orchestrator import get_enhanced_orchestrator
from task_queue.enhanced_queue_manager import queue_manager

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stats")
async def get_memory_stats():
    """Get comprehensive memory system statistics"""
    orchestrator = get_enhanced_orchestrator()
    if not orchestrator or not orchestrator.memory_manager:
        raise HTTPException(status_code=404, detail="Memory manager not initialized")
    
    try:
        stats = await orchestrator.memory_manager.get_memory_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

@router.get("/redis-usage")
async def get_redis_usage():
    """Get Redis memory usage statistics"""
    orchestrator = get_enhanced_orchestrator()
    if not orchestrator or not orchestrator.memory_manager:
        raise HTTPException(status_code=404, detail="Memory manager not initialized")
    
    try:
        redis_stats = await orchestrator.memory_manager.get_redis_memory_usage()
        return redis_stats
    except Exception as e:
        logger.error(f"Failed to get Redis usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Redis usage: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_memories(days: int = 30):
    """Clean up memories older than specified days"""
    orchestrator = get_enhanced_orchestrator()
    if not orchestrator or not orchestrator.memory_manager:
        raise HTTPException(status_code=404, detail="Memory manager not initialized")
    
    try:
        await orchestrator.memory_manager.cleanup_old_memories(days)
        return {"status": "success", "message": f"Cleaned up memories older than {days} days"}
    except Exception as e:
        logger.error(f"Failed to clean up memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up memories: {str(e)}")

@router.post("/optimize-redis")
async def optimize_redis():
    """Optimize Redis memory usage by setting TTLs and cleaning up"""
    if not hasattr(queue_manager, 'redis') or not queue_manager.redis:
        raise HTTPException(status_code=404, detail="Redis not available")
    
    try:
        # Get all memory cache keys
        keys = await queue_manager.redis.keys("memory_cache:*")
        
        # Set TTL for keys without one
        no_ttl_count = 0
        for key in keys:
            ttl = await queue_manager.redis.ttl(key)
            if ttl == -1:  # No TTL set
                await queue_manager.redis.expire(key, 86400)  # 24 hours
                no_ttl_count += 1
        
        # Get memory info before and after
        before_info = await queue_manager.redis.info("memory")
        
        return {
            "status": "success",
            "total_keys": len(keys),
            "keys_optimized": no_ttl_count,
            "memory_usage": before_info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        logger.error(f"Failed to optimize Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize Redis: {str(e)}")