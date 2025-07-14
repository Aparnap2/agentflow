"""Enhanced Session API Controller"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
from flows.orchestrator import AgentOrchestrator
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/enhanced", tags=["enhanced"])

# In-memory session storage (in production, use Redis/database)
sessions = {}

class StartSessionRequest(BaseModel):
    user_id: str
    message: str

class ContinueSessionRequest(BaseModel):
    message: str

@router.post("/start-session")
async def start_enhanced_session(request: StartSessionRequest) -> Dict[str, Any]:
    """Start enhanced session with Cofounder agent"""
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        
        # Get Cofounder agent response
        cofounder = orchestrator.agents.get("Cofounder")
        if not cofounder:
            raise HTTPException(status_code=500, detail="Cofounder agent not available")
        
        # Create initial task
        task = {
            "id": f"cofounder_start_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_message": request.message,
            "session_id": session_id,
            "mode": "conversation_start"
        }
        
        # Execute Cofounder agent
        result = await cofounder.execute(task)
        
        # Store session
        sessions[session_id] = {
            "user_id": request.user_id,
            "messages": [
                {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": result.get("output", {}).get("response", "Hello! Let's discuss your project."), "timestamp": datetime.now().isoformat()}
            ],
            "conversation_id": f"conv_{session_id}",
            "created_at": datetime.now().isoformat(),
            "message_count": 1
        }
        
        return {
            "session_id": session_id,
            "conversation_id": sessions[session_id]["conversation_id"],
            "response": result.get("output", {}).get("response", "Hello! Let's discuss your project."),
            "ready_for_approval": sessions[session_id]["message_count"] >= 3,
            "project_plan": result.get("output", {}).get("project_plan") if sessions[session_id]["message_count"] >= 3 else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue-session")
async def continue_enhanced_session(
    request: ContinueSessionRequest,
    session_id: str = Query(...)
) -> Dict[str, Any]:
    """Continue enhanced session"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        
        # Get Cofounder agent
        cofounder = orchestrator.agents.get("Cofounder")
        if not cofounder:
            raise HTTPException(status_code=500, detail="Cofounder agent not available")
        
        # Create task with conversation context
        task = {
            "id": f"cofounder_continue_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_message": request.message,
            "session_id": session_id,
            "conversation_history": session["messages"],
            "mode": "conversation_continue"
        }
        
        # Execute Cofounder agent
        result = await cofounder.execute(task)
        
        # Update session
        session["messages"].extend([
            {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": result.get("output", {}).get("response", "I understand. Please continue."), "timestamp": datetime.now().isoformat()}
        ])
        session["message_count"] += 1
        
        return {
            "session_id": session_id,
            "response": result.get("output", {}).get("response", "I understand. Please continue."),
            "ready_for_approval": session["message_count"] >= 3,
            "project_plan": result.get("output", {}).get("project_plan") if session["message_count"] >= 3 else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve-and-execute")
async def approve_and_execute(session_id: str = Query(...)) -> Dict[str, Any]:
    """Approve session and execute workflow"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Extract vision from conversation
        user_messages = [msg["content"] for msg in session["messages"] if msg["role"] == "user"]
        vision = " ".join(user_messages)
        
        # Execute workflow using existing workflow controller
        from api.workflow_controller import execute_workflow, WorkflowRequest
        
        workflow_request = WorkflowRequest(
            vision=vision,
            user_id=session["user_id"]
        )
        
        result = await execute_workflow(workflow_request)
        
        # Update session with execution results
        session["execution_started"] = True
        session["workflow_result"] = result
        session["approved_at"] = datetime.now().isoformat()
        
        return {
            "status": "approved_and_executing",
            "session_id": session_id,
            "workflow_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-status")
async def get_session_status(session_id: str = Query(...)) -> Dict[str, Any]:
    """Get session status"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": "executing" if session.get("execution_started") else "planning",
            "message_count": session["message_count"],
            "ready_for_approval": session["message_count"] >= 3,
            "created_at": session["created_at"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-results")
async def get_session_results(session_id: str = Query(...)) -> Dict[str, Any]:
    """Get session execution results"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if not session.get("execution_started"):
            raise HTTPException(status_code=400, detail="Session not executed yet")
        
        return {
            "session_id": session_id,
            "workflow_result": session.get("workflow_result", {}),
            "messages": session["messages"],
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))