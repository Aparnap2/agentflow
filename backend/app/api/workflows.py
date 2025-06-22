from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.models.workflow import WorkflowDefinition, WorkflowRunRequest, WorkflowStateResponse
from app.services.langgraph_integration import LangGraphOrchestrator, WorkflowConfig
from app.services.hil_service import HumanInLoopService, HILStatus
from app.services.qdrant_client import QdrantClient
from app.services.neo4j_client import Neo4jClient
from app.core.config import settings

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Initialize services
qdrant_client = QdrantClient(
    host=settings.QDRANT_URL.replace("http://", "").split(":")[0],
    port=int(settings.QDRANT_URL.split(":")[-1]) if ":" in settings.QDRANT_URL else 6333,
    api_key=settings.QDRANT_API_KEY
)

neo4j_client = Neo4jClient(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD
)

orchestrator = LangGraphOrchestrator(qdrant_client=qdrant_client, neo4j_client=neo4j_client)
hil_service = HumanInLoopService()

# Pydantic models for request/response
class WorkflowCreateRequest(BaseModel):
    name: str
    description: str
    agents: List[str]
    entry_point: str
    human_in_loop_points: List[str] = []
    max_iterations: int = 50

class HILRequestCreate(BaseModel):
    workflow_id: str
    thread_id: str
    agent_id: str
    request_type: str
    title: str
    description: str
    context: Dict[str, Any]
    proposed_action: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    priority: str = "medium"
    timeout_minutes: Optional[int] = None

class HILResponseSubmit(BaseModel):
    status: HILStatus
    response_data: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    responded_by: str = "human"

class UserTaskRequest(BaseModel):
    user_intent: str
    name: Optional[str] = "User Submitted Task"
    description: Optional[str] = None


# Predefined ID for the main Virtual Office workflow
# This workflow should be defined within the LangGraphOrchestrator or loaded at startup.
VIRTUAL_OFFICE_WORKFLOW_ID = "virtual_office_main_workflow_v1"


# Workflow Management Endpoints
@router.post("/submit-task")
async def submit_user_task(task_request: UserTaskRequest):
    """
    Submits a user's task (intent) to the predefined Virtual Office workflow.
    """
    try:
        input_data = {"user_intent": task_request.user_intent, "title": task_request.name}
        if task_request.description:
            input_data["description"] = task_request.description

        # This assumes VIRTUAL_OFFICE_WORKFLOW_ID is known and defined in the orchestrator
        result = await orchestrator.run_workflow(VIRTUAL_OFFICE_WORKFLOW_ID, input_data)

        # The result structure from run_workflow needs to be known.
        # Assuming it returns a dict with at least a 'thread_id' or 'run_id'.
        # Example: {"thread_id": "some_uuid", "status": "started", ...}
        # For now, let's assume it returns the whole result dict which might contain the ID.
        return {
            "message": "Task submitted successfully to the Virtual Office workflow.",
            "workflow_id": VIRTUAL_OFFICE_WORKFLOW_ID, # Static ID of the definition used
            "run_details": result # Contains thread_id, initial state, etc.
        }
    except Exception as e:
        # Log the exception for debugging
        # logger.error(f"Error submitting user task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get("/runs/active")
async def list_active_runs(workflow_id: Optional[str] = None):
    """
    List all active (running or paused) workflow runs.
    Optionally filters by workflow_definition_id.
    """
    try:
        # If filtering by specific workflow_id, pass it to orchestrator
        # For the Virtual Office, we might often want to see runs for VIRTUAL_OFFICE_WORKFLOW_ID
        active_runs = await orchestrator.list_active_workflow_runs(workflow_id_filter=workflow_id)
        return {"active_runs": active_runs}
    except Exception as e:
        # logger.error(f"Error listing active workflow runs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list active runs: {str(e)}")


@router.post("/")
async def create_workflow(workflow_request: WorkflowCreateRequest):
    """Create a new workflow definition"""
    try:
        workflow_config = workflow_request.dict()
        workflow_id = await orchestrator.define_workflow(workflow_config)
        return {
            "status": "created",
            "workflow_id": workflow_id,
            "name": workflow_request.name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def list_workflows():
    """List all defined workflows"""
    try:
        workflows = await orchestrator.list_workflows()
        return {"workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, thread_id: Optional[str] = None):
    """Get workflow details and state"""
    try:
        state = await orchestrator.get_workflow_state(workflow_id, thread_id)
        return state
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, input_data: Dict[str, Any]):
    """Run a workflow with given input data"""
    try:
        result = await orchestrator.run_workflow(workflow_id, input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        success = await orchestrator.delete_workflow(workflow_id)
        if success:
            return {"status": "deleted", "workflow_id": workflow_id}
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Human-in-the-Loop Endpoints
@router.post("/hil/requests")
async def create_hil_request(hil_request: HILRequestCreate):
    """Create a human-in-the-loop request"""
    try:
        request_id = await hil_service.create_hil_request(
            workflow_id=hil_request.workflow_id,
            thread_id=hil_request.thread_id,
            agent_id=hil_request.agent_id,
            request_type=hil_request.request_type,
            title=hil_request.title,
            description=hil_request.description,
            context=hil_request.context,
            proposed_action=hil_request.proposed_action,
            options=hil_request.options,
            priority=hil_request.priority,
            timeout_minutes=hil_request.timeout_minutes
        )
        return {"status": "created", "request_id": request_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hil/requests")
async def list_hil_requests(workflow_id: Optional[str] = None):
    """List pending HIL requests"""
    try:
        requests = await hil_service.list_pending_requests(workflow_id)
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hil/requests/{request_id}")
async def get_hil_request(request_id: str):
    """Get a specific HIL request"""
    try:
        request = await hil_service.get_hil_request(request_id)
        if request:
            return request
        else:
            raise HTTPException(status_code=404, detail="HIL request not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hil/requests/{request_id}/respond")
async def respond_to_hil_request(request_id: str, response: HILResponseSubmit):
    """Respond to a HIL request"""
    try:
        result = await hil_service.respond_to_hil_request(
            request_id=request_id,
            status=response.status,
            response_data=response.response_data,
            comments=response.comments,
            responded_by=response.responded_by
        )
        # Potentially, this response should then trigger orchestrator.resume_workflow
        # if the HIL request was blocking a graph execution.
        # For now, HIL service is separate from graph pause/resume.
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/runs/{thread_id}/pause")
async def pause_workflow_run(workflow_id: str, thread_id: str, reason: Optional[str] = "Paused via API"):
    """Pause a specific workflow run (thread)"""
    try:
        # orchestrator.pause_workflow expects thread_id
        result = await orchestrator.pause_workflow(thread_id=thread_id)
        # Could also update HIL service if pause is HIL related
        # await hil_service.pause_workflow(workflow_id=workflow_id, reason=reason, thread_id=thread_id)
        return result
    except ValueError as ve: # If orchestrator raises ValueError for not found
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{workflow_id}/runs/{thread_id}/resume")
async def resume_workflow_run(workflow_id: str, thread_id: str, human_input: Optional[Dict[str, Any]] = None):
    """Resume a paused workflow run (thread)"""
    try:
        # orchestrator.resume_workflow expects thread_id and human_input
        result = await orchestrator.resume_workflow(thread_id=thread_id, human_input=human_input)
        # await hil_service.resume_workflow(thread_id=thread_id, human_input=human_input, workflow_id_context=workflow_id)
        return result
    except ValueError as ve: # If orchestrator raises ValueError for not found
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}/hil/status")
async def get_workflow_hil_status(workflow_id: str):
    """Get HIL status for a workflow"""
    try:
        status = await hil_service.get_workflow_hil_status(workflow_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoints for backward compatibility
@router.post("/define")
async def define_workflow_legacy(defn: WorkflowDefinition):
    """Legacy endpoint for defining workflows"""
    try:
        workflow_config = {
            "name": defn.name,
            "description": f"Legacy workflow: {defn.name}",
            "agents": ["cofounder", "manager"],  # Default agents
            "entry_point": "cofounder"
        }
        workflow_id = await orchestrator.define_workflow(workflow_config)
        return {"status": "defined", "name": defn.name, "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/run")
async def run_workflow_legacy(req: WorkflowRunRequest):
    """Legacy endpoint for running workflows"""
    try:
        result = await orchestrator.run_workflow(req.workflow_id, req.input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/state/{workflow_id}")
async def get_workflow_state_legacy(workflow_id: str):
    """Legacy endpoint for getting workflow state"""
    try:
        state = await orchestrator.get_workflow_state(workflow_id)
        return WorkflowStateResponse(
            workflow_id=workflow_id,
            state=state.get("status", "unknown"),
            details=state
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/hil/pause/{workflow_id}")
async def pause_workflow_legacy(workflow_id: str):
    """Legacy endpoint for pausing workflows"""
    try:
        result = await hil_service.pause_workflow(workflow_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hil/resume/{workflow_id}")
async def resume_workflow_legacy(workflow_id: str):
    """Legacy endpoint for resuming workflows"""
    try:
        result = await hil_service.resume_workflow(workflow_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hil/status/{workflow_id}")
async def hil_status_legacy(workflow_id: str):
    """Legacy endpoint for HIL status"""
    try:
        return hil_service.get_status(workflow_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 