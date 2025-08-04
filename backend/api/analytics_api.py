"""
Analytics API endpoints for dashboard metrics
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from analytics.analytics_service import analytics_service

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
)

@router.get("/metrics")
async def get_analytics_metrics() -> Dict[str, Any]:
    """Get all analytics metrics"""
    try:
        return await analytics_service.get_all_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics metrics: {str(e)}")

@router.get("/agent-performance")
async def get_agent_performance() -> Dict[str, Any]:
    """Get agent performance metrics"""
    try:
        return await analytics_service.get_agent_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent performance metrics: {str(e)}")

@router.get("/user-interactions")
async def get_user_interactions() -> Dict[str, Any]:
    """Get user interaction metrics"""
    try:
        return await analytics_service.get_user_interaction_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user interaction metrics: {str(e)}")

@router.get("/errors")
async def get_error_metrics() -> Dict[str, Any]:
    """Get error metrics"""
    try:
        return await analytics_service.get_error_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error metrics: {str(e)}")