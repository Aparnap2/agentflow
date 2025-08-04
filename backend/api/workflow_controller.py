"""Workflow API Controller"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from workflows.langgraph_orchestrator import LangGraphOrchestrator
from flows.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

class WorkflowRequest(BaseModel):
    vision: str
    user_id: str = "default"

@router.post("/execute")
async def execute_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    """Execute LangGraph workflow"""
    try:
        # Use existing orchestrator
        orchestrator = AgentOrchestrator()
        
        # Try LangGraph first, fallback to regular orchestrator
        try:
            langgraph_orchestrator = LangGraphOrchestrator(orchestrator.agents)
            result = await langgraph_orchestrator.execute_workflow({
                "project_vision": request.vision
            })
            return {"status": "success", "workflow_type": "langgraph", **result}
        except Exception as e:
            # Fallback to regular orchestrator
            result = await orchestrator.auto_execute_from_vision(request.vision)
            return {"status": "success", "workflow_type": "standard", **result}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_workflow_status() -> Dict[str, Any]:
    """Get workflow execution status"""
    try:
        orchestrator = AgentOrchestrator()
        status = await orchestrator.get_auto_execution_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))