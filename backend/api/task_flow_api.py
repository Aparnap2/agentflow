"""
Task Flow API - Provides endpoints for retrieving cross-agent task flow and visualization data

This API enables visualization of cross-agent task flow showing how work moves between agents,
detection of priority conflicts between agents, and real-time monitoring of agent activities.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from loguru import logger

from flows.orchestrator import AgentOrchestrator
from communication.event_bus import event_bus
from memory.memory_manager import OptimizedMemoryManager
from memory.shared_context_manager import SharedContextManager
from task_queue.enhanced_queue_manager import queue_manager
from task_queue.task_router import TaskRouter
from task_queue.cross_agent_validator import CrossAgentValidator
from collaboration.cross_agent_comm import CrossAgentComm

router = APIRouter(prefix="/api/task-flow", tags=["task-flow"])

class TaskFlowNode(BaseModel):
    id: str
    agent_name: str
    task_type: str
    status: str  # pending, active, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    dependencies: List[str] = []
    metadata: Dict[str, Any] = {}

class TaskFlowEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str  # dependency, communication, handoff
    metadata: Dict[str, Any] = {}

class TaskFlowGraph(BaseModel):
    nodes: List[TaskFlowNode]
    edges: List[TaskFlowEdge]
    metadata: Dict[str, Any]

class PriorityConflict(BaseModel):
    id: str
    agents_involved: List[str]
    conflict_type: str
    description: str
    priority_level: str  # high, medium, low
    created_at: str
    status: str  # active, resolved, escalated
    resolution: Optional[Dict[str, Any]] = None
    impact_assessment: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[Dict[str, Any]]] = None

class TaskFlowVisualizationData(BaseModel):
    graph: TaskFlowGraph
    conflicts: List[PriorityConflict]
    statistics: Dict[str, Any]
    timestamp: str

# WebSocket connection manager for task flow updates
class TaskFlowConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Task flow WebSocket connection established. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Task flow WebSocket connection closed. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting task flow message: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

task_flow_manager = TaskFlowConnectionManager()

@router.get("/current", response_model=TaskFlowVisualizationData)
async def get_current_task_flow() -> TaskFlowVisualizationData:
    """Get current cross-agent task flow"""
    try:
        orchestrator = AgentOrchestrator()
        
        # Initialize components if needed
        if not queue_manager.is_initialized:
            await queue_manager.initialize()
        
        # Get task flow data
        graph = await _build_task_flow_graph()
        conflicts = await _detect_priority_conflicts()
        statistics = await _calculate_flow_statistics(graph)
        
        return TaskFlowVisualizationData(
            graph=graph,
            conflicts=conflicts,
            statistics=statistics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting current task flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_task_flow_history(
    hours: int = 24,
    agent_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Get historical task flow data"""
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get historical data from memory manager
        memory_manager = OptimizedMemoryManager()
        
        # Query task history
        task_history = await memory_manager.query_agent_memory(
            agent_name=agent_filter or "*",
            memory_type="task_execution",
            include_shared=True
        )
        
        # Filter by time range
        filtered_history = []
        for task in task_history:
            task_time = datetime.fromisoformat(task.get("timestamp", ""))
            if start_time <= task_time <= end_time:
                filtered_history.append(task)
        
        # Build historical flow graph
        historical_graph = await _build_historical_flow_graph(filtered_history)
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "task_count": len(filtered_history),
            "graph": historical_graph,
            "agent_filter": agent_filter
        }
        
    except Exception as e:
        logger.error(f"Error getting task flow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conflicts", response_model=List[PriorityConflict])
async def get_priority_conflicts() -> List[PriorityConflict]:
    """Get current priority conflicts between agents"""
    try:
        return await _detect_priority_conflicts()
        
    except Exception as e:
        logger.error(f"Error getting priority conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_priority_conflict(
    conflict_id: str,
    resolution_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Resolve a priority conflict"""
    try:
        # Get cross-agent communication instance
        cross_agent_comm = CrossAgentComm()
        
        # Find the conflict
        conflicts = await _detect_priority_conflicts()
        conflict = next((c for c in conflicts if c.id == conflict_id), None)
        
        if not conflict:
            raise HTTPException(status_code=404, detail=f"Conflict {conflict_id} not found")
        
        # Resolve the conflict using cross-agent communication
        resolution_result = await cross_agent_comm.resolve_conflict(
            conflict_type=conflict.conflict_type,
            agents_involved=conflict.agents_involved,
            conflict_data=resolution_data
        )
        
        # Update conflict status
        resolved_conflict = conflict.copy()
        resolved_conflict.status = "resolved"
        resolved_conflict.resolution = resolution_result
        
        # Broadcast resolution to WebSocket clients
        await task_flow_manager.broadcast(json.dumps({
            "type": "conflict_resolved",
            "data": {
                "conflict_id": conflict_id,
                "resolution": resolution_result
            },
            "timestamp": datetime.now().isoformat()
        }))
        
        return {
            "status": "resolved",
            "conflict_id": conflict_id,
            "resolution": resolution_result,
            "resolved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict {conflict_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization-data")
async def get_visualization_data(
    include_history: bool = False,
    history_hours: int = 24,
    visualization_format: str = Query("default", description="Format of visualization data (default, d3, cytoscape, mermaid)")
) -> Dict[str, Any]:
    """Get formatted data for task flow visualization in various formats"""
    try:
        # Get current flow
        current_flow = await get_current_task_flow()
        
        result = {
            "current": current_flow.dict(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Add historical data if requested
        if include_history:
            history = await get_task_flow_history(hours=history_hours)
            result["history"] = history
        
        # Format data for specific visualization libraries if requested
        if visualization_format != "default":
            result["formatted_data"] = await _format_visualization_data(
                current_flow, 
                visualization_format
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization-formats")
async def get_visualization_formats() -> Dict[str, Any]:
    """Get available visualization formats and their schemas"""
    return {
        "available_formats": {
            "default": "Raw task flow data structure",
            "d3": "Formatted for D3.js force-directed graph",
            "cytoscape": "Formatted for Cytoscape.js",
            "mermaid": "Formatted as Mermaid flowchart syntax"
        },
        "examples": {
            "d3": {
                "nodes": [{"id": "agent_name", "group": 1}],
                "links": [{"source": "agent1", "target": "agent2", "value": 1}]
            },
            "cytoscape": {
                "nodes": [{"data": {"id": "agent_name"}}],
                "edges": [{"data": {"id": "edge1", "source": "agent1", "target": "agent2"}}]
            },
            "mermaid": "graph TD\\n  A[Agent1] --> B[Agent2]"
        }
    }

@router.websocket("/ws")
async def task_flow_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time task flow updates"""
    await task_flow_manager.connect(websocket)
    
    try:
        # Send initial task flow data
        initial_flow = await get_current_task_flow()
        await websocket.send_text(json.dumps({
            "type": "task_flow",
            "data": initial_flow.dict(),
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle updates
        while True:
            try:
                # Wait for client message or timeout for periodic updates
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send periodic update
                try:
                    current_flow = await get_current_task_flow()
                    await websocket.send_text(json.dumps({
                        "type": "task_flow",
                        "data": current_flow.dict(),
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error sending task flow update: {e}")
                    break
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Task flow WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Task flow WebSocket connection error: {e}")
    finally:
        task_flow_manager.disconnect(websocket)

async def _build_task_flow_graph() -> TaskFlowGraph:
    """Build current task flow graph"""
    try:
        orchestrator = AgentOrchestrator()
        nodes = []
        edges = []
        
        # Get current tasks from all agent queues
        for agent_name in orchestrator.agents.keys():
            queue_status = await queue_manager.get_queue_status(agent_name.lower())
            
            # Create node for agent
            node = TaskFlowNode(
                id=f"agent_{agent_name.lower()}",
                agent_name=agent_name,
                task_type="agent_node",
                status="active" if queue_status.get("active_jobs", 0) > 0 else "idle",
                metadata={
                    "queue_status": queue_status,
                    "active_jobs": queue_status.get("active_jobs", 0),
                    "pending_jobs": queue_status.get("pending_jobs", 0)
                }
            )
            nodes.append(node)
        
        # Get task dependencies and communications from memory
        memory_manager = OptimizedMemoryManager()
        
        # Query recent agent communications
        recent_comms = await memory_manager.query_agent_memory(
            agent_name="*",
            memory_type="agent_message",
            include_shared=True
        )
        
        # Build edges from communications
        for comm in recent_comms[-50:]:  # Last 50 communications
            content = comm.get("content", {})
            message_data = content.get("message", {})
            
            if message_data:
                from_agent = message_data.get("from_agent")
                to_agent = message_data.get("to_agent")
                message_type = message_data.get("message_type")
                
                if from_agent and to_agent:
                    edge = TaskFlowEdge(
                        id=f"comm_{from_agent}_{to_agent}_{message_data.get('request_id', '')}",
                        source=f"agent_{from_agent.lower()}",
                        target=f"agent_{to_agent.lower()}",
                        relationship_type=message_type or "communication",
                        metadata={
                            "message_type": message_type,
                            "timestamp": message_data.get("timestamp"),
                            "priority": message_data.get("priority", "normal")
                        }
                    )
                    edges.append(edge)
        
        return TaskFlowGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error building task flow graph: {e}")
        return TaskFlowGraph(nodes=[], edges=[], metadata={"error": str(e)})

async def _detect_priority_conflicts() -> List[PriorityConflict]:
    """Detect priority conflicts between agents"""
    try:
        conflicts = []
        
        # Get all agent queue statuses
        orchestrator = AgentOrchestrator()
        agent_workloads = {}
        
        for agent_name in orchestrator.agents.keys():
            queue_status = await queue_manager.get_queue_status(agent_name.lower())
            agent_workloads[agent_name] = {
                "active_jobs": queue_status.get("active_jobs", 0),
                "pending_jobs": queue_status.get("pending_jobs", 0),
                "failed_jobs": queue_status.get("failed_jobs", 0)
            }
        
        # Detect workload imbalance conflicts
        total_jobs = sum(w["active_jobs"] + w["pending_jobs"] for w in agent_workloads.values())
        if total_jobs > 0:
            avg_jobs = total_jobs / len(agent_workloads)
            
            overloaded_agents = []
            underloaded_agents = []
            
            for agent, workload in agent_workloads.items():
                agent_jobs = workload["active_jobs"] + workload["pending_jobs"]
                if agent_jobs > avg_jobs * 1.5:  # 50% above average
                    overloaded_agents.append(agent)
                elif agent_jobs < avg_jobs * 0.5:  # 50% below average
                    underloaded_agents.append(agent)
            
            if overloaded_agents and underloaded_agents:
                conflict = PriorityConflict(
                    id=f"workload_imbalance_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    agents_involved=overloaded_agents + underloaded_agents,
                    conflict_type="workload_imbalance",
                    description=f"Workload imbalance detected: {overloaded_agents} overloaded, {underloaded_agents} underloaded",
                    priority_level="medium",
                    created_at=datetime.now().isoformat(),
                    status="active"
                )
                conflicts.append(conflict)
        
        # Detect resource conflicts from memory
        memory_manager = OptimizedMemoryManager()
        
        # Query recent conflict resolutions
        recent_conflicts = await memory_manager.query_agent_memory(
            agent_name="*",
            memory_type="conflict_resolution",
            include_shared=True
        )
        
        # Add unresolved conflicts
        for conflict_data in recent_conflicts[-10:]:  # Last 10 conflicts
            content = conflict_data.get("content", {})
            if content.get("status") == "unresolved":
                conflict = PriorityConflict(
                    id=content.get("conflict_id", f"conflict_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    agents_involved=content.get("agents_involved", []),
                    conflict_type=content.get("conflict_type", "unknown"),
                    description=content.get("description", "Unresolved conflict"),
                    priority_level=content.get("priority_level", "medium"),
                    created_at=content.get("created_at", datetime.now().isoformat()),
                    status="active"
                )
                conflicts.append(conflict)
        
        # Detect priority disagreements between agents
        await _detect_priority_disagreements(conflicts)
        
        # Detect resource allocation conflicts
        await _detect_resource_allocation_conflicts(conflicts)
        
        # Detect deadline conflicts
        await _detect_deadline_conflicts(conflicts)
        
        # Detect dependency conflicts
        await _detect_dependency_conflicts(conflicts)
        
        return conflicts
        
    except Exception as e:
        logger.error(f"Error detecting priority conflicts: {e}")
        return []

async def _detect_priority_disagreements(conflicts: List[PriorityConflict]) -> None:
    """Detect priority disagreements between agents"""
    try:
        # Get shared context manager
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        
        # Query recent agent priorities
        agent_priorities = await shared_context_manager.get_shared_context(
            context_type="agent_priorities",
            limit=20
        )
        
        # Group priorities by task
        task_priorities = {}
        for priority in agent_priorities:
            task_id = priority.get("task_id")
            if not task_id:
                continue
                
            if task_id not in task_priorities:
                task_priorities[task_id] = []
                
            task_priorities[task_id].append({
                "agent": priority.get("agent_name"),
                "priority": priority.get("priority_level"),
                "timestamp": priority.get("timestamp")
            })
        
        # Check for disagreements
        for task_id, priorities in task_priorities.items():
            if len(priorities) < 2:
                continue
                
            # Check if agents disagree on priority
            priority_levels = set(p["priority"] for p in priorities)
            if len(priority_levels) > 1:
                agents_involved = [p["agent"] for p in priorities]
                
                # Create conflict
                conflict = PriorityConflict(
                    id=f"priority_disagreement_{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    agents_involved=agents_involved,
                    conflict_type="priority_disagreement",
                    description=f"Agents disagree on priority for task {task_id}: {', '.join([f'{p['agent']}: {p['priority']}' for p in priorities])}",
                    priority_level="high",
                    created_at=datetime.now().isoformat(),
                    status="active"
                )
                conflicts.append(conflict)
                
    except Exception as e:
        logger.error(f"Error detecting priority disagreements: {e}")

async def _detect_resource_allocation_conflicts(conflicts: List[PriorityConflict]) -> None:
    """Detect resource allocation conflicts between agents"""
    try:
        # Get shared context manager
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        
        # Query resource allocations
        resource_allocations = await shared_context_manager.get_shared_context(
            context_type="resource_allocation",
            limit=20
        )
        
        # Group allocations by resource
        resource_requests = {}
        for allocation in resource_allocations:
            resource_id = allocation.get("resource_id")
            if not resource_id:
                continue
                
            if resource_id not in resource_requests:
                resource_requests[resource_id] = []
                
            resource_requests[resource_id].append({
                "agent": allocation.get("agent_name"),
                "amount": allocation.get("amount", 1),
                "timestamp": allocation.get("timestamp")
            })
        
        # Check for conflicts
        for resource_id, requests in resource_requests.items():
            if len(requests) < 2:
                continue
                
            # Get resource capacity
            resource_capacity = next((r.get("capacity", 1) for r in resource_allocations if r.get("resource_id") == resource_id), 1)
            
            # Calculate total requested
            total_requested = sum(r["amount"] for r in requests)
            
            # Check if requests exceed capacity
            if total_requested > resource_capacity:
                agents_involved = [r["agent"] for r in requests]
                
                # Create conflict
                conflict = PriorityConflict(
                    id=f"resource_conflict_{resource_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    agents_involved=agents_involved,
                    conflict_type="resource_conflict",
                    description=f"Resource allocation conflict for {resource_id}: {total_requested} requested, {resource_capacity} available",
                    priority_level="high",
                    created_at=datetime.now().isoformat(),
                    status="active"
                )
                conflicts.append(conflict)
                
    except Exception as e:
        logger.error(f"Error detecting resource allocation conflicts: {e}")

async def _detect_deadline_conflicts(conflicts: List[PriorityConflict]) -> None:
    """Detect deadline conflicts between agents"""
    try:
        # Get shared context manager
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        
        # Query task deadlines
        task_deadlines = await shared_context_manager.get_shared_context(
            context_type="task_deadlines",
            limit=20
        )
        
        # Group tasks by agent
        agent_tasks = {}
        for task in task_deadlines:
            agent = task.get("agent_name")
            if not agent:
                continue
                
            if agent not in agent_tasks:
                agent_tasks[agent] = []
                
            agent_tasks[agent].append({
                "task_id": task.get("task_id"),
                "deadline": task.get("deadline"),
                "estimated_completion": task.get("estimated_completion")
            })
        
        # Check for deadline conflicts within each agent
        for agent, tasks in agent_tasks.items():
            # Sort tasks by deadline
            sorted_tasks = sorted(tasks, key=lambda t: t["deadline"] if t["deadline"] else "9999-12-31")
            
            # Check for conflicts
            for i, task in enumerate(sorted_tasks):
                if i == 0 or not task["estimated_completion"] or not task["deadline"]:
                    continue
                    
                # Check if previous task's estimated completion is after this task's deadline
                prev_task = sorted_tasks[i-1]
                if prev_task["estimated_completion"] and prev_task["estimated_completion"] > task["deadline"]:
                    # Create conflict
                    conflict = PriorityConflict(
                        id=f"deadline_conflict_{agent}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        agents_involved=[agent],
                        conflict_type="deadline_conflict",
                        description=f"Deadline conflict for {agent}: Task {prev_task['task_id']} estimated completion ({prev_task['estimated_completion']}) is after task {task['task_id']} deadline ({task['deadline']})",
                        priority_level="medium",
                        created_at=datetime.now().isoformat(),
                        status="active"
                    )
                    conflicts.append(conflict)
                    break  # Only report one deadline conflict per agent
                
    except Exception as e:
        logger.error(f"Error detecting deadline conflicts: {e}")

async def _detect_dependency_conflicts(conflicts: List[PriorityConflict]) -> None:
    """Detect dependency conflicts between agents"""
    try:
        # Get shared context manager
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        
        # Query task dependencies
        task_dependencies = await shared_context_manager.get_shared_context(
            context_type="task_dependencies",
            limit=50
        )
        
        # Build dependency graph
        dependency_graph = {}
        task_agents = {}
        
        for dep in task_dependencies:
            task_id = dep.get("task_id")
            depends_on = dep.get("depends_on", [])
            agent = dep.get("agent_name")
            
            if not task_id or not agent:
                continue
                
            task_agents[task_id] = agent
            
            if task_id not in dependency_graph:
                dependency_graph[task_id] = []
                
            dependency_graph[task_id].extend(depends_on)
        
        # Check for circular dependencies
        visited = set()
        path = set()
        
        def check_circular(task_id):
            if task_id in path:
                # Found circular dependency
                cycle = []
                for t in path:
                    cycle.append(t)
                    if t == task_id:
                        break
                return cycle
            
            if task_id in visited:
                return None
                
            visited.add(task_id)
            path.add(task_id)
            
            for dep in dependency_graph.get(task_id, []):
                cycle = check_circular(dep)
                if cycle:
                    return cycle
            
            path.remove(task_id)
            return None
        
        # Check each task for circular dependencies
        for task_id in dependency_graph:
            cycle = check_circular(task_id)
            if cycle:
                # Get agents involved
                agents_involved = []
                for t in cycle:
                    agent = task_agents.get(t)
                    if agent and agent not in agents_involved:
                        agents_involved.append(agent)
                
                if len(agents_involved) > 1:
                    # Create conflict
                    conflict = PriorityConflict(
                        id=f"dependency_conflict_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        agents_involved=agents_involved,
                        conflict_type="dependency_conflict",
                        description=f"Circular dependency detected: {' -> '.join(cycle)}",
                        priority_level="high",
                        created_at=datetime.now().isoformat(),
                        status="active"
                    )
                    conflicts.append(conflict)
                
                # Only report one circular dependency
                break
                
    except Exception as e:
        logger.error(f"Error detecting dependency conflicts: {e}")

async def _calculate_flow_statistics(graph: TaskFlowGraph) -> Dict[str, Any]:
    """Calculate statistics for the task flow graph"""
    try:
        stats = {
            "total_agents": len(graph.nodes),
            "active_agents": len([n for n in graph.nodes if n.status == "active"]),
            "idle_agents": len([n for n in graph.nodes if n.status == "idle"]),
            "total_communications": len(graph.edges),
            "communication_types": {},
            "agent_activity": {}
        }
        
        # Count communication types
        for edge in graph.edges:
            comm_type = edge.relationship_type
            stats["communication_types"][comm_type] = stats["communication_types"].get(comm_type, 0) + 1
        
        # Calculate agent activity
        for node in graph.nodes:
            agent_name = node.agent_name
            metadata = node.metadata
            stats["agent_activity"][agent_name] = {
                "status": node.status,
                "active_jobs": metadata.get("active_jobs", 0),
                "pending_jobs": metadata.get("pending_jobs", 0)
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating flow statistics: {e}")
        return {"error": str(e)}

async def _build_historical_flow_graph(task_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build historical flow graph from task history"""
    try:
        # Group tasks by agent and time
        agent_timeline = {}
        
        for task in task_history:
            agent = task.get("author", "unknown")
            timestamp = task.get("timestamp", "")
            
            if agent not in agent_timeline:
                agent_timeline[agent] = []
            
            agent_timeline[agent].append({
                "timestamp": timestamp,
                "task_type": task.get("type", "unknown"),
                "content": task.get("content", {})
            })
        
        # Sort by timestamp
        for agent in agent_timeline:
            agent_timeline[agent].sort(key=lambda x: x["timestamp"])
        
        return {
            "agent_timeline": agent_timeline,
            "total_tasks": len(task_history),
            "agents_involved": list(agent_timeline.keys())
        }
        
    except Exception as e:
        logger.error(f"Error building historical flow graph: {e}")
        return {"error": str(e)}

# Event handlers for real-time updates
async def _handle_task_flow_update(event_data: Dict[str, Any]):
    """Handle task flow update events"""
    try:
        message = json.dumps({
            "type": "task_flow_update",
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        })
        await task_flow_manager.broadcast(message)
    except Exception as e:
        logger.error(f"Error broadcasting task flow update: {e}")

# Subscribe to relevant events
event_bus.subscribe("task_started", _handle_task_flow_update)
event_bus.subscribe("task_completed", _handle_task_flow_update)
event_bus.subscribe("agent_message", _handle_task_flow_update)
event_bus.subscribe("conflict_detected", _handle_task_flow_update)
asyn
c def _format_visualization_data(flow_data: TaskFlowVisualizationData, format_type: str) -> Dict[str, Any]:
    """Format task flow data for specific visualization libraries"""
    try:
        if format_type == "d3":
            return _format_for_d3(flow_data)
        elif format_type == "cytoscape":
            return _format_for_cytoscape(flow_data)
        elif format_type == "mermaid":
            return _format_for_mermaid(flow_data)
        else:
            return {"error": f"Unsupported visualization format: {format_type}"}
    except Exception as e:
        logger.error(f"Error formatting visualization data: {e}")
        return {"error": str(e)}

def _format_for_d3(flow_data: TaskFlowVisualizationData) -> Dict[str, Any]:
    """Format task flow data for D3.js force-directed graph"""
    nodes = []
    links = []
    
    # Map agent types to groups for coloring
    agent_groups = {
        "Cofounder": 1,
        "Manager": 2,
        "Marketing": 3,
        "Finance": 4,
        "Legal": 5,
        "Strategy": 6
    }
    
    # Create nodes
    for node in flow_data.graph.nodes:
        agent_type = node.agent_name.split("_")[0] if "_" in node.agent_name else node.agent_name
        group = agent_groups.get(agent_type, 0)
        
        nodes.append({
            "id": node.id,
            "name": node.agent_name,
            "group": group,
            "status": node.status,
            "active_jobs": node.metadata.get("active_jobs", 0),
            "pending_jobs": node.metadata.get("pending_jobs", 0)
        })
    
    # Create links
    for edge in flow_data.graph.edges:
        links.append({
            "source": edge.source,
            "target": edge.target,
            "value": 1,  # Default strength
            "type": edge.relationship_type
        })
    
    # Add conflict links with higher value for emphasis
    for conflict in flow_data.conflicts:
        if len(conflict.agents_involved) >= 2:
            for i in range(len(conflict.agents_involved) - 1):
                source = f"agent_{conflict.agents_involved[i].lower()}"
                target = f"agent_{conflict.agents_involved[i+1].lower()}"
                
                links.append({
                    "source": source,
                    "target": target,
                    "value": 3,  # Stronger connection for conflicts
                    "type": "conflict",
                    "conflict_id": conflict.id,
                    "priority_level": conflict.priority_level
                })
    
    return {
        "nodes": nodes,
        "links": links
    }

def _format_for_cytoscape(flow_data: TaskFlowVisualizationData) -> Dict[str, Any]:
    """Format task flow data for Cytoscape.js"""
    elements = {
        "nodes": [],
        "edges": []
    }
    
    # Create nodes
    for node in flow_data.graph.nodes:
        elements["nodes"].append({
            "data": {
                "id": node.id,
                "name": node.agent_name,
                "status": node.status,
                "active_jobs": node.metadata.get("active_jobs", 0),
                "pending_jobs": node.metadata.get("pending_jobs", 0)
            },
            "classes": node.status  # For CSS styling
        })
    
    # Create edges
    for edge in flow_data.graph.edges:
        elements["edges"].append({
            "data": {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "relationship_type": edge.relationship_type
            },
            "classes": edge.relationship_type  # For CSS styling
        })
    
    # Add conflict edges
    for conflict in flow_data.conflicts:
        if len(conflict.agents_involved) >= 2:
            for i in range(len(conflict.agents_involved) - 1):
                source = f"agent_{conflict.agents_involved[i].lower()}"
                target = f"agent_{conflict.agents_involved[i+1].lower()}"
                
                elements["edges"].append({
                    "data": {
                        "id": f"conflict_{conflict.id}_{i}",
                        "source": source,
                        "target": target,
                        "relationship_type": "conflict",
                        "conflict_id": conflict.id,
                        "priority_level": conflict.priority_level
                    },
                    "classes": f"conflict {conflict.priority_level}"  # For CSS styling
                })
    
    return elements

def _format_for_mermaid(flow_data: TaskFlowVisualizationData) -> Dict[str, Any]:
    """Format task flow data as Mermaid flowchart syntax"""
    mermaid_lines = ["graph TD"]
    
    # Node style mapping
    node_styles = {
        "active": "fill:#a3cfbb,stroke:#56a777",
        "idle": "fill:#e0e0e0,stroke:#9e9e9e",
        "pending": "fill:#fff59d,stroke:#fbc02d",
        "failed": "fill:#ef9a9a,stroke:#e57373"
    }
    
    # Create nodes
    for node in flow_data.graph.nodes:
        node_id = node.id
        node_label = f"{node.agent_name} ({node.metadata.get('active_jobs', 0)} active)"
        node_style = node_styles.get(node.status, "")
        
        if node_style:
            mermaid_lines.append(f"    {node_id}[\"{node_label}\"]::::{node.status}")
        else:
            mermaid_lines.append(f"    {node_id}[\"{node_label}\"]")
    
    # Create edges
    for edge in flow_data.graph.edges:
        edge_label = edge.relationship_type
        mermaid_lines.append(f"    {edge.source} -->|{edge_label}| {edge.target}")
    
    # Add conflict edges with different style
    for conflict in flow_data.conflicts:
        if len(conflict.agents_involved) >= 2:
            for i in range(len(conflict.agents_involved) - 1):
                source = f"agent_{conflict.agents_involved[i].lower()}"
                target = f"agent_{conflict.agents_involved[i+1].lower()}"
                
                mermaid_lines.append(f"    {source} -.->|conflict| {target}")
    
    # Add style definitions
    mermaid_lines.append("    classDef active fill:#a3cfbb,stroke:#56a777")
    mermaid_lines.append("    classDef idle fill:#e0e0e0,stroke:#9e9e9e")
    mermaid_lines.append("    classDef pending fill:#fff59d,stroke:#fbc02d")
    mermaid_lines.append("    classDef failed fill:#ef9a9a,stroke:#e57373")
    
    return {
        "mermaid_syntax": "\n".join(mermaid_lines),
        "preview_url": f"https://mermaid.ink/img/encoded/{mermaid_lines}"
    }

@router.get("/priority-conflicts/analysis")
async def analyze_priority_conflicts() -> Dict[str, Any]:
    """Get detailed analysis of priority conflicts between agents"""
    try:
        conflicts = await _detect_priority_conflicts()
        
        # Get cross-agent validator for conflict analysis
        validator = CrossAgentValidator()
        
        # Analyze each conflict
        analyzed_conflicts = []
        for conflict in conflicts:
            # Get shared context for the conflict
            shared_context_manager = SharedContextManager(OptimizedMemoryManager())
            context = await shared_context_manager.get_shared_context(
                context_type="conflict_resolution",
                query=conflict.conflict_type
            )
            
            # Analyze impact
            impact_assessment = await validator.assess_conflict_impact(
                conflict_type=conflict.conflict_type,
                agents_involved=conflict.agents_involved,
                context=context
            )
            
            # Generate suggested actions
            suggested_actions = await _generate_conflict_resolution_actions(conflict)
            
            # Add analysis to conflict
            analyzed_conflict = conflict.dict()
            analyzed_conflict["impact_assessment"] = impact_assessment
            analyzed_conflict["suggested_actions"] = suggested_actions
            analyzed_conflicts.append(analyzed_conflict)
        
        return {
            "conflicts": analyzed_conflicts,
            "total_conflicts": len(analyzed_conflicts),
            "priority_distribution": {
                "high": len([c for c in conflicts if c.priority_level == "high"]),
                "medium": len([c for c in conflicts if c.priority_level == "medium"]),
                "low": len([c for c in conflicts if c.priority_level == "low"])
            },
            "conflict_types": {c.conflict_type: 0 for c in conflicts},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing priority conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_conflict_resolution_actions(conflict: PriorityConflict) -> List[Dict[str, Any]]:
    """Generate suggested actions for resolving a priority conflict"""
    try:
        actions = []
        
        if conflict.conflict_type == "workload_imbalance":
            # Suggest task redistribution
            overloaded = [a for a in conflict.agents_involved if a in conflict.description and "overloaded" in conflict.description]
            underloaded = [a for a in conflict.agents_involved if a in conflict.description and "underloaded" in conflict.description]
            
            if overloaded and underloaded:
                actions.append({
                    "action_type": "redistribute_tasks",
                    "description": f"Redistribute tasks from {', '.join(overloaded)} to {', '.join(underloaded)}",
                    "from_agents": overloaded,
                    "to_agents": underloaded
                })
        
        elif conflict.conflict_type == "resource_conflict":
            # Suggest resource allocation
            actions.append({
                "action_type": "allocate_resources",
                "description": "Allocate additional resources based on priority",
                "priority_based": True
            })
        
        elif conflict.conflict_type == "priority_disagreement":
            # Suggest manager intervention
            actions.append({
                "action_type": "manager_decision",
                "description": "Escalate to Manager agent for priority decision",
                "escalate_to": "Manager"
            })
        
        # Add generic actions
        actions.append({
            "action_type": "human_override",
            "description": "Request human override for conflict resolution",
            "requires_human": True
        })
        
        return actions
        
    except Exception as e:
        logger.error(f"Error generating conflict resolution actions: {e}")
        return []

@router.get("/task-flow/metrics")
async def get_task_flow_metrics() -> Dict[str, Any]:
    """Get metrics about the task flow and agent performance"""
    try:
        # Get current flow
        current_flow = await get_current_task_flow()
        
        # Calculate basic metrics
        basic_metrics = {
            "total_agents": len(current_flow.graph.nodes),
            "active_agents": len([n for n in current_flow.graph.nodes if n.status == "active"]),
            "total_communications": len(current_flow.graph.edges),
            "active_conflicts": len([c for c in current_flow.conflicts if c.status == "active"])
        }
        
        # Calculate agent efficiency
        agent_efficiency = {}
        for node in current_flow.graph.nodes:
            agent_name = node.agent_name
            active_jobs = node.metadata.get("active_jobs", 0)
            pending_jobs = node.metadata.get("pending_jobs", 0)
            
            if active_jobs + pending_jobs > 0:
                efficiency = active_jobs / (active_jobs + pending_jobs)
            else:
                efficiency = 1.0  # No backlog
                
            agent_efficiency[agent_name] = {
                "efficiency_score": efficiency,
                "active_jobs": active_jobs,
                "pending_jobs": pending_jobs
            }
        
        # Calculate communication patterns
        communication_patterns = {}
        for edge in current_flow.graph.edges:
            source_agent = edge.source.replace("agent_", "")
            target_agent = edge.target.replace("agent_", "")
            relationship = edge.relationship_type
            
            if source_agent not in communication_patterns:
                communication_patterns[source_agent] = {}
            
            if target_agent not in communication_patterns[source_agent]:
                communication_patterns[source_agent][target_agent] = {}
            
            if relationship not in communication_patterns[source_agent][target_agent]:
                communication_patterns[source_agent][target_agent][relationship] = 0
                
            communication_patterns[source_agent][target_agent][relationship] += 1
        
        return {
            "basic_metrics": basic_metrics,
            "agent_efficiency": agent_efficiency,
            "communication_patterns": communication_patterns,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting task flow metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))