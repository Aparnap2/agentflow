"""
API controller for LangGraph workflows
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from workflows.langgraph_workflow import LangGraphWorkflow
from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from auth.auth_service import get_current_user

# Request/response models
class WorkflowRequest(BaseModel):
    vision: str
    agents: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    agent: str
    session_id: Optional[str] = None

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str

class ChatResponse(BaseModel):
    session_id: str
    agent: str
    message: str
    confidence: float

# Initialize router
router = APIRouter(prefix="/api/langgraph", tags=["langgraph"])

# Components will be initialized lazily
memory_manager = None
approval_manager = None
workflow_manager = None

async def get_workflow_manager():
    """Get or initialize workflow manager"""
    global memory_manager, approval_manager, workflow_manager
    if workflow_manager is None:
        from core.init_langgraph import get_factory
        memory_manager = MemoryManager()
        approval_manager = ApprovalManager()
        workflow_manager = LangGraphWorkflow(memory_manager, approval_manager)
    return workflow_manager

@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Create a new workflow"""
    try:
        # Get workflow manager
        wf_manager = await get_workflow_manager()
        
        # Create workflow config
        workflow_config = {
            "vision": request.vision,
            "agents": request.agents or ["cofounder", "manager", "product", "finance", "marketing", "legal"],
            "context": request.context or {},
            "user_id": user.id
        }
        
        # Create workflow
        workflow_id = await wf_manager.create_workflow(workflow_config)
        
        # Execute workflow in background
        background_tasks.add_task(wf_manager.execute_workflow, workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow_status(workflow_id: str, user = Depends(get_current_user)):
    """Get workflow status"""
    try:
        # Get workflow manager
        wf_manager = await get_workflow_manager()
        
        status = await wf_manager.get_workflow_status(workflow_id)
        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Workflow not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/result", response_model=Dict[str, Any])
async def get_workflow_result(workflow_id: str, user = Depends(get_current_user)):
    """Get workflow result"""
    try:
        # Get workflow manager
        wf_manager = await get_workflow_manager()
        
        result = await wf_manager.get_workflow_result(workflow_id)
        if result["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Workflow not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/cancel", response_model=Dict[str, Any])
async def cancel_workflow(workflow_id: str, user = Depends(get_current_user)):
    """Cancel a workflow"""
    try:
        # Get workflow manager
        wf_manager = await get_workflow_manager()
        
        result = await wf_manager.cancel_workflow(workflow_id)
        if result["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Workflow not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, user = Depends(get_current_user)):
    """Chat with a specific agent"""
    try:
        # Get workflow manager
        wf_manager = await get_workflow_manager()
        
        result = await wf_manager.chat_with_agent(
            agent_type=request.agent,
            message=request.message,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))