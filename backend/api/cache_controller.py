"""
Cache Controller - API endpoints for cache management and monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger

from memory.event_cache_manager import event_cache_manager, CacheEvent
from memory.context_decision_agent import context_decision_agent
from memory.memory_manager import MemoryManager

router = APIRouter(prefix="/cache", tags=["cache"])

class CacheEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]

class StorageDecisionRequest(BaseModel):
    content: Any
    agent_name: str
    memory_type: str
    metadata: Optional[Dict[str, Any]] = None

@router.get("/stats")
async def get_cache_stats():
    """Get cache statistics and performance metrics"""
    try:
        cache_stats = await event_cache_manager.get_cache_stats()
        decision_recommendations = context_decision_agent.get_storage_recommendations()
        
        return {
            "cache_stats": cache_stats,
            "storage_recommendations": decision_recommendations,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-event")
async def trigger_cache_event(request: CacheEventRequest, background_tasks: BackgroundTasks):
    """Trigger a cache event for testing"""
    try:
        # Validate event type
        try:
            event = CacheEvent(request.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")
        
        # Trigger event in background
        background_tasks.add_task(
            event_cache_manager.trigger_event,
            event,
            request.data
        )
        
        return {
            "message": f"Cache event {request.event_type} triggered",
            "data": request.data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering cache event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decide-storage")
async def decide_storage_strategy(request: StorageDecisionRequest):
    """Get storage strategy recommendation for content"""
    try:
        decision = await context_decision_agent.decide_storage_strategy(
            content=request.content,
            agent_name=request.agent_name,
            memory_type=request.memory_type,
            metadata=request.metadata
        )
        
        return {
            "decision": decision,
            "timestamp": decision["metadata"]["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error deciding storage strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invalidate")
async def invalidate_cache(pattern: Optional[str] = None):
    """Invalidate cache entries"""
    try:
        if pattern:
            await event_cache_manager._invalidate_pattern(pattern)
            message = f"Invalidated cache entries matching pattern: {pattern}"
        else:
            # Trigger context change event to refresh all shared context
            await event_cache_manager.trigger_event(CacheEvent.CONTEXT_CHANGE, {
                "reason": "manual_invalidation",
                "timestamp": "now"
            })
            message = "Triggered context refresh event"
        
        return {"message": message}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hot-keys")
async def get_hot_keys():
    """Get frequently accessed cache keys"""
    try:
        stats = await event_cache_manager.get_cache_stats()
        return {
            "hot_keys": stats.get("hot_keys", []),
            "hot_keys_count": stats.get("hot_keys_count", 0)
        }
    except Exception as e:
        logger.error(f"Error getting hot keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_cache(background_tasks: BackgroundTasks):
    """Trigger cache cleanup"""
    try:
        background_tasks.add_task(event_cache_manager.cleanup_expired_tracking)
        
        return {"message": "Cache cleanup triggered"}
    except Exception as e:
        logger.error(f"Error triggering cache cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-decision-agent")
async def test_decision_agent():
    """Test the context decision agent with sample data"""
    try:
        # Test cases
        test_cases = [
            {
                "content": {"vision": "Build a revolutionary AI platform that transforms business operations"},
                "agent_name": "cofounder",
                "memory_type": "vision"
            },
            {
                "content": {"debug_log": "Connection established"},
                "agent_name": "system",
                "memory_type": "log"
            },
            {
                "content": {"analysis": "Market research shows 85% growth potential in AI automation sector"},
                "agent_name": "marketing",
                "memory_type": "analysis"
            },
            {
                "content": "Quick update",
                "agent_name": "assistant",
                "memory_type": "update"
            }
        ]
        
        results = []
        for test_case in test_cases:
            decision = await context_decision_agent.decide_storage_strategy(**test_case)
            results.append({
                "test_case": test_case,
                "decision": {
                    "strategy": decision["strategy"],
                    "score": decision["score"],
                    "reasoning": decision["reasoning"]
                }
            })
        
        return {
            "test_results": results,
            "summary": {
                "global_strategies": len([r for r in results if r["decision"]["strategy"] in ["global", "both"]]),
                "local_strategies": len([r for r in results if r["decision"]["strategy"] == "local"]),
                "cache_only": len([r for r in results if r["decision"]["strategy"] == "cache_only"])
            }
        }
    except Exception as e:
        logger.error(f"Error testing decision agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))