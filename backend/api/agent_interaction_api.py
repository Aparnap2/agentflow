"""
Agent Interaction API - Provides endpoints for collaborative decisions, meetings, and human override
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from loguru import logger

from flows.orchestrator import AgentOrchestrator
from collaboration.cross_agent_comm import CrossAgentComm
from memory.shared_context_manager import SharedContextManager
from memory.memory_manager import OptimizedMemoryManager
from communication.event_bus import event_bus

router = APIRouter(prefix="/api/agent-interaction", tags=["agent-interaction"])

class CollaborativeDecisionRequest(BaseModel):
    topic: str
    description: str
    agents_involved: List[str]
    context: Dict[str, Any] = {}
    decision_criteria: Dict[str, Any] = {}
    timeout: float = 300.0  # 5 minutes default
    priority: str = "medium"

class DecisionContribution(BaseModel):
    agent_name: str
    perspective: Dict[str, Any]
    recommendation: Optional[str] = None
    confidence: float = 1.0

class AgentMeetingRequest(BaseModel):
    topic: str
    agents_involved: List[str]
    agenda: List[Dict[str, Any]]
    duration_minutes: int = 30
    priority: str = "medium"

class MeetingMessage(BaseModel):
    agent_name: str
    message: str
    message_type: str = "discussion"  # discussion, proposal, question, decision
    timestamp: Optional[str] = None

class HumanOverrideRequest(BaseModel):
    target_agent: str
    override_type: str  # task_assignment, parameter_change, workflow_modification, emergency_stop
    instructions: Dict[str, Any]
    reason: str
    duration_minutes: Optional[int] = None  # None for permanent override

class CollaborativeDecisionResponse(BaseModel):
    decision_id: str
    status: str  # pending, in_progress, completed, timeout, failed
    topic: str
    agents_involved: List[str]
    contributions: List[DecisionContribution] = []
    final_decision: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None

class AgentMeetingResponse(BaseModel):
    meeting_id: str
    status: str  # scheduled, active, completed, cancelled
    topic: str
    agents_involved: List[str]
    messages: List[MeetingMessage] = []
    decisions_made: List[Dict[str, Any]] = []
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

class HumanOverrideResponse(BaseModel):
    override_id: str
    status: str  # active, completed, expired, cancelled
    target_agent: str
    override_type: str
    instructions: Dict[str, Any]
    reason: str
    created_at: str
    expires_at: Optional[str] = None
    completed_at: Optional[str] = None

# WebSocket connection manager for real-time interactions
class InteractionConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # topic -> connections

    async def connect(self, websocket: WebSocket, topic: str):
        await websocket.accept()
        if topic not in self.active_connections:
            self.active_connections[topic] = []
        self.active_connections[topic].append(websocket)
        logger.info(f"WebSocket connected to topic {topic}. Total: {len(self.active_connections[topic])}")

    def disconnect(self, websocket: WebSocket, topic: str):
        if topic in self.active_connections and websocket in self.active_connections[topic]:
            self.active_connections[topic].remove(websocket)
        logger.info(f"WebSocket disconnected from topic {topic}")

    async def broadcast_to_topic(self, topic: str, message: str):
        if topic not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[topic]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to topic {topic}: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection, topic)

interaction_manager = InteractionConnectionManager()

# Collaborative Decision Endpoints

@router.post("/collaborative-decision", response_model=CollaborativeDecisionResponse)
async def create_collaborative_decision(request: CollaborativeDecisionRequest) -> CollaborativeDecisionResponse:
    """Create a new collaborative decision process"""
    try:
        # Validate agents exist
        orchestrator = AgentOrchestrator()
        for agent_name in request.agents_involved:
            if agent_name not in orchestrator.agents:
                raise HTTPException(status_code=400, detail=f"Agent {agent_name} not found")
        
        # Create decision using cross-agent communication
        cross_agent_comm = CrossAgentComm()
        decision_id = str(uuid.uuid4())
        
        # Store decision in cross-agent communication system
        decision_data = {
            "decision_id": decision_id,
            "topic": request.topic,
            "description": request.description,
            "agents_involved": request.agents_involved,
            "context": request.context,
            "decision_criteria": request.decision_criteria,
            "timeout": request.timeout,
            "priority": request.priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "contributions": []
        }
        
        # Initialize collaborative decision
        await cross_agent_comm.create_collaborative_decision(
            decision_id=decision_id,
            topic=request.topic,
            agents_involved=request.agents_involved,
            context=request.context,
            decision_criteria=request.decision_criteria
        )
        
        # Store in memory for tracking
        memory_manager = OptimizedMemoryManager()
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="collaborative_decision",
            content=decision_data,
            is_shared=True
        )
        
        # Broadcast to WebSocket clients
        await interaction_manager.broadcast_to_topic(
            f"decision_{decision_id}",
            json.dumps({
                "type": "decision_created",
                "data": decision_data,
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return CollaborativeDecisionResponse(
            decision_id=decision_id,
            status="pending",
            topic=request.topic,
            agents_involved=request.agents_involved,
            created_at=decision_data["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collaborative decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborative-decision/{decision_id}/contribute")
async def contribute_to_decision(
    decision_id: str,
    contribution: DecisionContribution
) -> Dict[str, Any]:
    """Contribute to a collaborative decision"""
    try:
        # Get cross-agent communication instance
        cross_agent_comm = CrossAgentComm()
        
        # Contribute to decision
        result = await cross_agent_comm.contribute_to_decision(
            decision_id=decision_id,
            agent_name=contribution.agent_name,
            perspective=contribution.perspective
        )
        
        # Broadcast contribution to WebSocket clients
        await interaction_manager.broadcast_to_topic(
            f"decision_{decision_id}",
            json.dumps({
                "type": "decision_contribution",
                "data": {
                    "decision_id": decision_id,
                    "contribution": contribution.dict()
                },
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return {
            "status": "contribution_recorded",
            "decision_id": decision_id,
            "agent_name": contribution.agent_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error contributing to decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborative-decision/{decision_id}/finalize")
async def finalize_collaborative_decision(decision_id: str) -> Dict[str, Any]:
    """Finalize a collaborative decision"""
    try:
        # Get cross-agent communication instance
        cross_agent_comm = CrossAgentComm()
        
        # Finalize decision
        result = await cross_agent_comm.finalize_decision(decision_id=decision_id)
        
        # Broadcast finalization to WebSocket clients
        await interaction_manager.broadcast_to_topic(
            f"decision_{decision_id}",
            json.dumps({
                "type": "decision_finalized",
                "data": {
                    "decision_id": decision_id,
                    "result": result
                },
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return {
            "status": "finalized",
            "decision_id": decision_id,
            "result": result,
            "finalized_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error finalizing decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaborative-decision/{decision_id}", response_model=CollaborativeDecisionResponse)
async def get_collaborative_decision(decision_id: str) -> CollaborativeDecisionResponse:
    """Get details of a collaborative decision"""
    try:
        # Get decision from memory
        memory_manager = OptimizedMemoryManager()
        decisions = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="collaborative_decision",
            include_shared=True
        )
        
        # Find the specific decision
        decision_data = None
        for decision in decisions:
            content = decision.get("content", {})
            if content.get("decision_id") == decision_id:
                decision_data = content
                break
        
        if not decision_data:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
        
        return CollaborativeDecisionResponse(**decision_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaborative-decision", response_model=List[CollaborativeDecisionResponse])
async def list_collaborative_decisions(
    status: Optional[str] = None,
    agent: Optional[str] = None,
    limit: int = 20
) -> List[CollaborativeDecisionResponse]:
    """List all collaborative decisions with optional filtering"""
    try:
        # Get all decisions from memory
        memory_manager = OptimizedMemoryManager()
        decisions = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="collaborative_decision",
            include_shared=True
        )
        
        # Convert to response model and filter
        decision_list = []
        for decision in decisions:
            content = decision.get("content", {})
            
            # Apply filters if specified
            if status and content.get("status") != status:
                continue
                
            if agent and agent not in content.get("agents_involved", []):
                continue
                
            decision_list.append(CollaborativeDecisionResponse(**content))
        
        # Sort by creation time (newest first) and limit
        decision_list.sort(key=lambda d: d.created_at, reverse=True)
        return decision_list[:limit]
        
    except Exception as e:
        logger.error(f"Error listing collaborative decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Meeting Endpoints

@router.post("/meeting", response_model=AgentMeetingResponse)
async def create_agent_meeting(request: AgentMeetingRequest) -> AgentMeetingResponse:
    """Create a new agent meeting"""
    try:
        # Validate agents exist
        orchestrator = AgentOrchestrator()
        for agent_name in request.agents_involved:
            if agent_name not in orchestrator.agents:
                raise HTTPException(status_code=400, detail=f"Agent {agent_name} not found")
        
        meeting_id = str(uuid.uuid4())
        
        # Create meeting using cross-agent communication
        cross_agent_comm = CrossAgentComm()
        
        meeting_data = {
            "meeting_id": meeting_id,
            "topic": request.topic,
            "agents_involved": request.agents_involved,
            "agenda": request.agenda,
            "duration_minutes": request.duration_minutes,
            "priority": request.priority,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "decisions_made": []
        }
        
        # Create meeting space
        await cross_agent_comm.create_agent_meeting(
            meeting_id=meeting_id,
            topic=request.topic,
            agents_involved=request.agents_involved,
            agenda=request.agenda
        )
        
        # Store in memory
        memory_manager = OptimizedMemoryManager()
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="agent_meeting",
            content=meeting_data,
            is_shared=True
        )
        
        # Broadcast meeting creation
        await interaction_manager.broadcast_to_topic(
            f"meeting_{meeting_id}",
            json.dumps({
                "type": "meeting_created",
                "data": meeting_data,
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return AgentMeetingResponse(**meeting_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/{meeting_id}/message")
async def add_meeting_message(
    meeting_id: str,
    message: MeetingMessage
) -> Dict[str, Any]:
    """Add a message to an agent meeting"""
    try:
        # Add timestamp if not provided
        if not message.timestamp:
            message.timestamp = datetime.now().isoformat()
        
        # Store message in memory
        memory_manager = OptimizedMemoryManager()
        await memory_manager.store_agent_memory(
            agent_name=message.agent_name,
            memory_type="meeting_message",
            content={
                "meeting_id": meeting_id,
                "message": message.dict()
            },
            is_shared=True
        )
        
        # Broadcast message to WebSocket clients
        await interaction_manager.broadcast_to_topic(
            f"meeting_{meeting_id}",
            json.dumps({
                "type": "meeting_message",
                "data": {
                    "meeting_id": meeting_id,
                    "message": message.dict()
                },
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return {
            "status": "message_added",
            "meeting_id": meeting_id,
            "message_id": str(uuid.uuid4()),
            "timestamp": message.timestamp
        }
        
    except Exception as e:
        logger.error(f"Error adding message to meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting/{meeting_id}", response_model=AgentMeetingResponse)
async def get_agent_meeting(meeting_id: str) -> AgentMeetingResponse:
    """Get details of an agent meeting"""
    try:
        # Get meeting from memory
        memory_manager = OptimizedMemoryManager()
        meetings = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="agent_meeting",
            include_shared=True
        )
        
        # Find the specific meeting
        meeting_data = None
        for meeting in meetings:
            content = meeting.get("content", {})
            if content.get("meeting_id") == meeting_id:
                meeting_data = content
                break
        
        if not meeting_data:
            raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
        
        # Get meeting messages
        messages = await memory_manager.query_agent_memory(
            agent_name="*",
            memory_type="meeting_message",
            include_shared=True
        )
        
        meeting_messages = []
        for msg in messages:
            content = msg.get("content", {})
            if content.get("meeting_id") == meeting_id:
                meeting_messages.append(MeetingMessage(**content["message"]))
        
        # Sort messages by timestamp
        meeting_messages.sort(key=lambda m: m.timestamp or "")
        
        meeting_data["messages"] = [m.dict() for m in meeting_messages]
        
        return AgentMeetingResponse(**meeting_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting", response_model=List[AgentMeetingResponse])
async def list_agent_meetings(
    status: Optional[str] = None,
    agent: Optional[str] = None,
    limit: int = 20
) -> List[AgentMeetingResponse]:
    """List all agent meetings with optional filtering"""
    try:
        # Get all meetings from memory
        memory_manager = OptimizedMemoryManager()
        meetings = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="agent_meeting",
            include_shared=True
        )
        
        # Convert to response model and filter
        meeting_list = []
        for meeting in meetings:
            content = meeting.get("content", {})
            
            # Apply filters if specified
            if status and content.get("status") != status:
                continue
                
            if agent and agent not in content.get("agents_involved", []):
                continue
                
            # Don't include messages in the list view for performance
            content_copy = content.copy()
            content_copy["messages"] = []
            
            meeting_list.append(AgentMeetingResponse(**content_copy))
        
        # Sort by creation time (newest first) and limit
        meeting_list.sort(key=lambda m: m.created_at, reverse=True)
        return meeting_list[:limit]
        
    except Exception as e:
        logger.error(f"Error listing agent meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/{meeting_id}/status")
async def update_meeting_status(
    meeting_id: str,
    status: str
) -> Dict[str, Any]:
    """Update the status of an agent meeting (start, end, cancel)"""
    try:
        # Validate status
        valid_statuses = ["scheduled", "active", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get meeting from memory
        memory_manager = OptimizedMemoryManager()
        meetings = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="agent_meeting",
            include_shared=True
        )
        
        # Find the specific meeting
        meeting_data = None
        for meeting in meetings:
            content = meeting.get("content", {})
            if content.get("meeting_id") == meeting_id:
                meeting_data = content
                break
        
        if not meeting_data:
            raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
        
        # Update status and timestamps
        current_time = datetime.now().isoformat()
        
        if status == "active" and meeting_data.get("status") != "active":
            meeting_data["started_at"] = current_time
        elif status == "completed" or status == "cancelled":
            meeting_data["ended_at"] = current_time
        
        meeting_data["status"] = status
        
        # Update in memory
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="agent_meeting",
            content=meeting_data,
            is_shared=True
        )
        
        # Broadcast status update
        await interaction_manager.broadcast_to_topic(
            f"meeting_{meeting_id}",
            json.dumps({
                "type": "meeting_status_updated",
                "data": {
                    "meeting_id": meeting_id,
                    "status": status,
                    "timestamp": current_time
                },
                "timestamp": current_time
            })
        )
        
        return {
            "meeting_id": meeting_id,
            "status": status,
            "updated_at": current_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating meeting status for {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Human Override Endpoints

@router.post("/human-override", response_model=HumanOverrideResponse)
async def create_human_override(request: HumanOverrideRequest) -> HumanOverrideResponse:
    """Create a human override for an agent"""
    try:
        # Validate target agent exists
        orchestrator = AgentOrchestrator()
        if request.target_agent not in orchestrator.agents:
            raise HTTPException(status_code=400, detail=f"Agent {request.target_agent} not found")
        
        override_id = str(uuid.uuid4())
        
        # Calculate expiration time if duration is specified
        expires_at = None
        if request.duration_minutes:
            expires_at = (datetime.now() + timedelta(minutes=request.duration_minutes)).isoformat()
        
        override_data = {
            "override_id": override_id,
            "status": "active",
            "target_agent": request.target_agent,
            "override_type": request.override_type,
            "instructions": request.instructions,
            "reason": request.reason,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at
        }
        
        # Store override in memory
        memory_manager = OptimizedMemoryManager()
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="human_override",
            content=override_data,
            is_shared=True
        )
        
        # Apply override to target agent (implementation depends on override type)
        await _apply_human_override(request.target_agent, request.override_type, request.instructions)
        
        # Broadcast override creation
        await interaction_manager.broadcast_to_topic(
            f"override_{request.target_agent}",
            json.dumps({
                "type": "override_created",
                "data": override_data,
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return HumanOverrideResponse(**override_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating human override: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/human-override/{override_id}/cancel")
async def cancel_human_override(override_id: str) -> Dict[str, Any]:
    """Cancel an active human override"""
    try:
        # Get override from memory
        memory_manager = OptimizedMemoryManager()
        overrides = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="human_override",
            include_shared=True
        )
        
        # Find the specific override
        override_data = None
        for override in overrides:
            content = override.get("content", {})
            if content.get("override_id") == override_id:
                override_data = content
                break
        
        if not override_data:
            raise HTTPException(status_code=404, detail=f"Override {override_id} not found")
        
        if override_data["status"] != "active":
            raise HTTPException(status_code=400, detail=f"Override {override_id} is not active")
        
        # Cancel override
        override_data["status"] = "cancelled"
        override_data["completed_at"] = datetime.now().isoformat()
        
        # Update in memory
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="human_override",
            content=override_data,
            is_shared=True
        )
        
        # Remove override from target agent
        await _remove_human_override(override_data["target_agent"], override_data["override_type"])
        
        # Broadcast cancellation
        await interaction_manager.broadcast_to_topic(
            f"override_{override_data['target_agent']}",
            json.dumps({
                "type": "override_cancelled",
                "data": override_data,
                "timestamp": datetime.now().isoformat()
            })
        )
        
        return {
            "status": "cancelled",
            "override_id": override_id,
            "cancelled_at": override_data["completed_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling override {override_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human-override/{agent_name}")
async def get_agent_overrides(agent_name: str) -> List[HumanOverrideResponse]:
    """Get all overrides for a specific agent"""
    try:
        # Get overrides from memory
        memory_manager = OptimizedMemoryManager()
        overrides = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="human_override",
            include_shared=True
        )
        
        # Filter by target agent
        agent_overrides = []
        for override in overrides:
            content = override.get("content", {})
            if content.get("target_agent") == agent_name:
                agent_overrides.append(HumanOverrideResponse(**content))
        
        # Sort by creation time (newest first)
        agent_overrides.sort(key=lambda o: o.created_at, reverse=True)
        
        return agent_overrides
        
    except Exception as e:
        logger.error(f"Error getting overrides for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human-override", response_model=List[HumanOverrideResponse])
async def get_all_overrides() -> List[HumanOverrideResponse]:
    """Get all active human overrides across all agents"""
    try:
        # Get all overrides from memory
        memory_manager = OptimizedMemoryManager()
        overrides = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="human_override",
            include_shared=True
        )
        
        # Filter to active overrides only
        active_overrides = []
        for override in overrides:
            content = override.get("content", {})
            if content.get("status") == "active":
                active_overrides.append(HumanOverrideResponse(**content))
        
        # Sort by creation time (newest first)
        active_overrides.sort(key=lambda o: o.created_at, reverse=True)
        
        return active_overrides
        
    except Exception as e:
        logger.error(f"Error getting all overrides: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoints

@router.websocket("/ws/decision/{decision_id}")
async def decision_websocket(websocket: WebSocket, decision_id: str):
    """WebSocket for real-time decision updates"""
    topic = f"decision_{decision_id}"
    await interaction_manager.connect(websocket, topic)
    
    try:
        while True:
            try:
                # Wait for client messages (heartbeat)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Decision WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        interaction_manager.disconnect(websocket, topic)

@router.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    """WebSocket for real-time meeting updates"""
    topic = f"meeting_{meeting_id}"
    await interaction_manager.connect(websocket, topic)
    
    try:
        while True:
            try:
                # Wait for client messages
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages (e.g., new meeting messages)
                try:
                    data = json.loads(message)
                    if data.get("type") == "meeting_message":
                        # Broadcast to other participants
                        await interaction_manager.broadcast_to_topic(topic, message)
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Meeting WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        interaction_manager.disconnect(websocket, topic)

@router.websocket("/ws/override/{agent_name}")
async def override_websocket(websocket: WebSocket, agent_name: str):
    """WebSocket for real-time human override updates for a specific agent"""
    topic = f"override_{agent_name}"
    await interaction_manager.connect(websocket, topic)
    
    try:
        # Send initial active overrides for this agent
        memory_manager = OptimizedMemoryManager()
        overrides = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="human_override",
            include_shared=True
        )
        
        # Filter by target agent and active status
        active_overrides = []
        for override in overrides:
            content = override.get("content", {})
            if content.get("target_agent") == agent_name and content.get("status") == "active":
                active_overrides.append(content)
        
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "initial_overrides",
            "data": active_overrides,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Listen for updates
        while True:
            try:
                # Wait for client messages (heartbeat)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Override WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        interaction_manager.disconnect(websocket, topic)

@router.websocket("/ws/overrides")
async def all_overrides_websocket(websocket: WebSocket):
    """WebSocket for real-time human override updates across all agents"""
    topic = "overrides_all"
    await interaction_manager.connect(websocket, topic)
    
    try:
        # Send initial active overrides for all agents
        memory_manager = OptimizedMemoryManager()
        overrides = await memory_manager.query_agent_memory(
            agent_name="system",
            memory_type="human_override",
            include_shared=True
        )
        
        # Filter by active status
        active_overrides = []
        for override in overrides:
            content = override.get("content", {})
            if content.get("status") == "active":
                active_overrides.append(content)
        
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "initial_overrides",
            "data": active_overrides,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Listen for updates
        while True:
            try:
                # Wait for client messages (heartbeat)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"All overrides WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        interaction_manager.disconnect(websocket, topic)

# Helper Functions

async def _apply_human_override(agent_name: str, override_type: str, instructions: Dict[str, Any]):
    """Apply human override to target agent"""
    try:
        # Implementation depends on override type
        if override_type == "emergency_stop":
            # Stop agent processing
            logger.info(f"Emergency stop applied to {agent_name}")
            # Implementation would pause agent's queue processing
            
        elif override_type == "task_assignment":
            # Override task assignment logic
            logger.info(f"Task assignment override applied to {agent_name}")
            # Implementation would modify agent's task routing
            
        elif override_type == "parameter_change":
            # Change agent parameters
            logger.info(f"Parameter change override applied to {agent_name}")
            # Implementation would update agent configuration
            
        elif override_type == "workflow_modification":
            # Modify agent workflow
            logger.info(f"Workflow modification override applied to {agent_name}")
            # Implementation would update agent's workflow logic
            
    except Exception as e:
        logger.error(f"Error applying override to {agent_name}: {e}")
        raise

async def _remove_human_override(agent_name: str, override_type: str):
    """Remove human override from target agent"""
    try:
        # Implementation depends on override type
        if override_type == "emergency_stop":
            # Resume agent processing
            logger.info(f"Emergency stop removed from {agent_name}")
            
        elif override_type == "task_assignment":
            # Restore normal task assignment
            logger.info(f"Task assignment override removed from {agent_name}")
            
        elif override_type == "parameter_change":
            # Restore original parameters
            logger.info(f"Parameter change override removed from {agent_name}")
            
        elif override_type == "workflow_modification":
            # Restore original workflow
            logger.info(f"Workflow modification override removed from {agent_name}")
            
    except Exception as e:
        logger.error(f"Error removing override from {agent_name}: {e}")
        raise