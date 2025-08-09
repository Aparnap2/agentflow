"""
Shared Context API - Endpoints for managing shared context across agents
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from memory.memory_manager import OptimizedMemoryManager
from memory.shared_context_manager import SharedContextManager
from memory.memory_manager_integration import MemoryManagerIntegration

# Initialize router
router = APIRouter(prefix="/api/shared-context", tags=["shared-context"])

# Initialize memory manager
memory_manager = OptimizedMemoryManager()
memory_integration = MemoryManagerIntegration(memory_manager)
shared_context_manager = SharedContextManager(memory_manager)

# Models
class ContextCreateRequest(BaseModel):
    """Request model for creating shared context"""
    context_type: str
    content: Dict[str, Any]
    source_agent: str
    access_control: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

class ContextUpdateRequest(BaseModel):
    """Request model for updating shared context"""
    updates: Dict[str, Any]
    updating_agent: str
    change_description: Optional[str] = None

class AccessControlRequest(BaseModel):
    """Request model for access control changes"""
    granting_agent: str
    target_role: str
    access_type: str

@router.post("/")
async def create_shared_context(request: ContextCreateRequest):
    """Create new shared context"""
    try:
        context_id = await memory_integration.store_shared_context(
            context_type=request.context_type,
            content=request.content,
            source_agent=request.source_agent,
            access_control=request.access_control,
            confidence=request.confidence
        )
        
        return {
            "success": True,
            "context_id": context_id,
            "message": f"Created shared context of type {request.context_type}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create shared context: {str(e)}")

@router.get("/")
async def get_shared_contexts(
    context_type: Optional[str] = None,
    query: Optional[str] = None,
    requesting_agent: str = Query(..., description="Agent requesting the context"),
    version_id: Optional[str] = None,
    limit: int = 10
):
    """Get shared contexts accessible to the requesting agent"""
    try:
        contexts = await memory_integration.get_shared_context(
            context_type=context_type,
            query=query,
            requesting_agent=requesting_agent,
            version_id=version_id,
            limit=limit
        )
        
        return {
            "success": True,
            "contexts": contexts,
            "count": len(contexts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shared contexts: {str(e)}")

@router.put("/{context_id}")
async def update_shared_context(context_id: str, request: ContextUpdateRequest):
    """Update existing shared context"""
    try:
        result = await memory_integration.update_shared_context(
            context_id=context_id,
            updates=request.updates,
            updating_agent=request.updating_agent,
            change_description=request.change_description
        )
        
        if "error" in result:
            raise HTTPException(status_code=403, detail=result["message"])
        
        return {
            "success": True,
            "context_id": context_id,
            "message": f"Updated shared context {context_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update shared context: {str(e)}")

@router.get("/{context_id}/history")
async def get_context_history(
    context_id: str,
    requesting_agent: str = Query(..., description="Agent requesting the history"),
    limit: int = 10
):
    """Get version history for a specific context"""
    try:
        history = await memory_integration.get_context_history(
            context_id=context_id,
            requesting_agent=requesting_agent,
            limit=limit
        )
        
        return {
            "success": True,
            "context_id": context_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context history: {str(e)}")

@router.get("/agent/{agent_name}")
async def get_agent_specific_context(
    agent_name: str,
    context_type: Optional[str] = None,
    query: Optional[str] = None
):
    """Get context specific to an agent, including relevant shared context"""
    try:
        context = await memory_integration.get_agent_specific_context(
            agent_name=agent_name,
            context_type=context_type,
            query=query
        )
        
        return {
            "success": True,
            "agent_name": agent_name,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent-specific context: {str(e)}")

@router.post("/{context_id}/access/grant")
async def grant_access(context_id: str, request: AccessControlRequest):
    """Grant access to a role for a specific context"""
    try:
        result = await memory_integration.grant_access(
            context_id=context_id,
            granting_agent=request.granting_agent,
            target_role=request.target_role,
            access_type=request.access_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=403, detail=result["message"])
        
        return {
            "success": True,
            "context_id": context_id,
            "message": f"Granted {request.access_type} access to {request.target_role}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grant access: {str(e)}")

@router.post("/{context_id}/access/revoke")
async def revoke_access(context_id: str, request: AccessControlRequest):
    """Revoke access from a role for a specific context"""
    try:
        result = await memory_integration.revoke_access(
            context_id=context_id,
            revoking_agent=request.granting_agent,
            target_role=request.target_role,
            access_type=request.access_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=403, detail=result["message"])
        
        return {
            "success": True,
            "context_id": context_id,
            "message": f"Revoked {request.access_type} access from {request.target_role}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke access: {str(e)}")