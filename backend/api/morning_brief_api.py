"""
Morning Brief API - Provides consolidated overnight activities and decision queue

This API module implements endpoints for the Morning Executive Brief feature,
providing consolidated information about overnight agent activities, priority alerts,
cross-functional dependencies, and decisions requiring attention.

The Morning Brief serves as a central information hub for users to quickly understand
the current state of their agent ecosystem and take necessary actions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from flows.orchestrator import AgentOrchestrator
from memory.memory_manager import OptimizedMemoryManager
from task_queue.enhanced_queue_manager import queue_manager
from collaboration.cross_agent_comm import CrossAgentComm
from memory.shared_context_manager import SharedContextManager

router = APIRouter(prefix="/api/morning-brief", tags=["morning-brief"])

class AgentActivity(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    tasks_completed: int = Field(0, description="Number of tasks completed in the time period")
    tasks_failed: int = Field(0, description="Number of tasks that failed in the time period")
    key_achievements: List[str] = Field(default_factory=list, description="Key achievements during the time period")
    issues_encountered: List[str] = Field(default_factory=list, description="Issues encountered during the time period")
    time_active: float = Field(0.0, description="Hours the agent was active during the time period")

class PriorityAlert(BaseModel):
    id: str = Field(..., description="Unique identifier for the alert")
    type: str = Field(..., description="Type of alert: conflict, deadline, resource_shortage, error")
    severity: str = Field(..., description="Severity level: high, medium, low")
    title: str = Field(..., description="Short title describing the alert")
    description: str = Field(..., description="Detailed description of the alert")
    agents_involved: List[str] = Field(default_factory=list, description="Agents involved in the alert")
    created_at: str = Field(..., description="ISO format timestamp when the alert was created")
    requires_attention: bool = Field(False, description="Whether the alert requires human attention")

class CrossFunctionalDependency(BaseModel):
    id: str = Field(..., description="Unique identifier for the dependency")
    source_agent: str = Field(..., description="Agent that depends on another agent")
    target_agent: str = Field(..., description="Agent that is depended upon")
    dependency_type: str = Field(..., description="Type of dependency: data, approval, resource, coordination")
    description: str = Field(..., description="Description of the dependency")
    status: str = Field(..., description="Status of the dependency: pending, in_progress, completed, blocked")
    created_at: str = Field(..., description="ISO format timestamp when the dependency was created")
    deadline: Optional[str] = Field(None, description="Optional deadline for resolving the dependency")

class DecisionItem(BaseModel):
    id: str = Field(..., description="Unique identifier for the decision")
    title: str = Field(..., description="Short title describing the decision")
    description: str = Field(..., description="Detailed description of the decision")
    decision_type: str = Field(..., description="Type of decision: strategic, operational, resource_allocation, conflict_resolution")
    agents_involved: List[str] = Field(default_factory=list, description="Agents involved in the decision")
    options: List[Dict[str, Any]] = Field(default_factory=list, description="Available options for the decision")
    recommendation: Optional[Dict[str, Any]] = Field(None, description="Optional recommended option")
    priority: str = Field("medium", description="Priority level: high, medium, low")
    deadline: Optional[str] = Field(None, description="Optional deadline for making the decision")
    created_at: str = Field(..., description="ISO format timestamp when the decision was created")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the decision")

class MorningBrief(BaseModel):
    date: str = Field(..., description="Date of the morning brief in YYYY-MM-DD format")
    time_period: Dict[str, str] = Field(..., description="Start and end times of the period covered")
    summary: Dict[str, Any] = Field(..., description="Summary statistics of agent activities")
    agent_activities: List[AgentActivity] = Field(default_factory=list, description="List of agent activities during the period")
    priority_alerts: List[PriorityAlert] = Field(default_factory=list, description="List of priority alerts requiring attention")
    cross_functional_dependencies: List[CrossFunctionalDependency] = Field(default_factory=list, description="List of cross-functional dependencies between agents")
    decision_queue: List[DecisionItem] = Field(default_factory=list, description="List of decisions requiring attention")
    recommendations: List[str] = Field(default_factory=list, description="List of actionable recommendations")
    generated_at: str = Field(..., description="ISO format timestamp when the brief was generated")

@router.get("/today", response_model=MorningBrief)
async def get_morning_brief(
    hours_back: int = 24,
    include_weekend: bool = True
) -> MorningBrief:
    """Get consolidated morning brief for today"""
    try:
        # Calculate time period
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Skip weekends if requested
        if not include_weekend and end_time.weekday() >= 5:  # Saturday or Sunday
            return await _generate_weekend_brief(start_time, end_time)
        
        # Generate comprehensive morning brief
        brief = await _generate_morning_brief(start_time, end_time)
        return brief
        
    except Exception as e:
        logger.error(f"Error generating morning brief: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[PriorityAlert])
async def get_priority_alerts(
    severity_filter: Optional[str] = None,
    agent_filter: Optional[str] = None
) -> List[PriorityAlert]:
    """Get current priority alerts"""
    try:
        alerts = await _detect_priority_alerts()
        
        # Apply filters
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        
        if agent_filter:
            alerts = [a for a in alerts if agent_filter in a.agents_involved]
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting priority alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dependencies", response_model=List[CrossFunctionalDependency])
async def get_cross_functional_dependencies(
    status_filter: Optional[str] = None,
    agent_filter: Optional[str] = None
) -> List[CrossFunctionalDependency]:
    """Get cross-functional dependencies"""
    try:
        dependencies = await _identify_cross_functional_dependencies()
        
        # Apply filters
        if status_filter:
            dependencies = [d for d in dependencies if d.status == status_filter]
        
        if agent_filter:
            dependencies = [d for d in dependencies 
                          if agent_filter in [d.source_agent, d.target_agent]]
        
        return dependencies
        
    except Exception as e:
        logger.error(f"Error getting cross-functional dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decision-queue", response_model=List[DecisionItem])
async def get_decision_queue(
    priority_filter: Optional[str] = None,
    decision_type_filter: Optional[str] = None
) -> List[DecisionItem]:
    """Get pending decisions requiring attention"""
    try:
        decisions = await _build_decision_queue()
        
        # Apply filters
        if priority_filter:
            decisions = [d for d in decisions if d.priority == priority_filter]
        
        if decision_type_filter:
            decisions = [d for d in decisions if d.decision_type == decision_type_filter]
        
        # Sort by priority and deadline
        priority_order = {"high": 3, "medium": 2, "low": 1}
        decisions.sort(key=lambda d: (
            priority_order.get(d.priority, 0),
            d.deadline or "9999-12-31"
        ), reverse=True)
        
        return decisions
        
    except Exception as e:
        logger.error(f"Error getting decision queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decision-queue/{decision_id}/resolve")
async def resolve_decision(
    decision_id: str,
    resolution_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Resolve a pending decision"""
    try:
        # Get the decision
        decisions = await _build_decision_queue()
        decision = next((d for d in decisions if d.id == decision_id), None)
        
        if not decision:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
        
        # Process the resolution
        cross_agent_comm = CrossAgentComm()
        
        # If it's a collaborative decision, use cross-agent communication
        if len(decision.agents_involved) > 1:
            resolution_result = await cross_agent_comm.finalize_decision(
                decision_id=decision_id,
                timeout=30.0
            )
        else:
            # Single agent decision
            resolution_result = {
                "decision_id": decision_id,
                "resolution": resolution_data,
                "resolved_by": "human",
                "resolved_at": datetime.now().isoformat()
            }
        
        # Store resolution in memory
        memory_manager = OptimizedMemoryManager()
        await memory_manager.store_agent_memory(
            agent_name="system",
            memory_type="decision_resolution",
            content={
                "decision_id": decision_id,
                "original_decision": decision.dict(),
                "resolution": resolution_result,
                "resolved_at": datetime.now().isoformat()
            },
            is_shared=True
        )
        
        return {
            "status": "resolved",
            "decision_id": decision_id,
            "resolution": resolution_result,
            "resolved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_brief_summary(hours_back: int = 24) -> Dict[str, Any]:
    """Get a quick summary of overnight activities"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get basic metrics
        orchestrator = AgentOrchestrator()
        memory_manager = OptimizedMemoryManager()
        
        # Initialize queue manager if needed
        if not queue_manager.is_initialized:
            await queue_manager.initialize()
        
        # Get activity summary
        total_tasks = 0
        total_errors = 0
        active_agents = 0
        
        for agent_name in orchestrator.agents.keys():
            queue_status = await queue_manager.get_queue_status(agent_name.lower())
            
            # Count completed tasks (approximate from queue status)
            completed_jobs = queue_status.get("completed_jobs", 0)
            failed_jobs = queue_status.get("failed_jobs", 0)
            
            total_tasks += completed_jobs
            total_errors += failed_jobs
            
            if queue_status.get("active_jobs", 0) > 0:
                active_agents += 1
        
        # Get alerts and decisions
        alerts = await _detect_priority_alerts()
        high_priority_alerts = len([a for a in alerts if a.severity == "high"])
        
        decisions = await _build_decision_queue()
        pending_decisions = len([d for d in decisions if d.priority == "high"])
        
        return {
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours_back
            },
            "activity_summary": {
                "total_tasks_completed": total_tasks,
                "total_errors": total_errors,
                "active_agents": active_agents,
                "total_agents": len(orchestrator.agents)
            },
            "alerts_summary": {
                "total_alerts": len(alerts),
                "high_priority_alerts": high_priority_alerts
            },
            "decisions_summary": {
                "total_pending": len(decisions),
                "high_priority_pending": pending_decisions
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting brief summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_morning_brief(start_time: datetime, end_time: datetime) -> MorningBrief:
    """Generate comprehensive morning brief"""
    try:
        # Get agent activities
        agent_activities = await _analyze_agent_activities(start_time, end_time)
        
        # Get priority alerts
        priority_alerts = await _detect_priority_alerts()
        
        # Get cross-functional dependencies
        dependencies = await _identify_cross_functional_dependencies()
        
        # Get decision queue
        decision_queue = await _build_decision_queue()
        
        # Generate summary
        summary = {
            "total_agents": len(agent_activities),
            "active_agents": len([a for a in agent_activities if a.tasks_completed > 0]),
            "total_tasks_completed": sum(a.tasks_completed for a in agent_activities),
            "total_issues": sum(len(a.issues_encountered) for a in agent_activities),
            "high_priority_alerts": len([a for a in priority_alerts if a.severity == "high"]),
            "pending_decisions": len([d for d in decision_queue if d.priority == "high"])
        }
        
        # Generate recommendations
        recommendations = await _generate_recommendations(
            agent_activities, priority_alerts, dependencies, decision_queue
        )
        
        return MorningBrief(
            date=end_time.strftime("%Y-%m-%d"),
            time_period={
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            summary=summary,
            agent_activities=agent_activities,
            priority_alerts=priority_alerts,
            cross_functional_dependencies=dependencies,
            decision_queue=decision_queue,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating morning brief: {e}")
        raise

async def _generate_weekend_brief(start_time: datetime, end_time: datetime) -> MorningBrief:
    """Generate simplified weekend brief"""
    return MorningBrief(
        date=end_time.strftime("%Y-%m-%d"),
        time_period={
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        summary={"note": "Weekend - Limited activity expected"},
        agent_activities=[],
        priority_alerts=[],
        cross_functional_dependencies=[],
        decision_queue=[],
        recommendations=["Enjoy your weekend! Systems are monitoring automatically."],
        generated_at=datetime.now().isoformat()
    )

async def _analyze_agent_activities(start_time: datetime, end_time: datetime) -> List[AgentActivity]:
    """Analyze agent activities during the time period"""
    try:
        orchestrator = AgentOrchestrator()
        memory_manager = OptimizedMemoryManager()
        activities = []
        
        for agent_name in orchestrator.agents.keys():
            # Get agent's memory for the time period
            agent_memories = await memory_manager.query_agent_memory(
                agent_name=agent_name,
                memory_type=None,  # All types
                include_shared=False
            )
            
            # Filter by time period
            period_memories = []
            for memory in agent_memories:
                memory_time = datetime.fromisoformat(memory.get("timestamp", ""))
                if start_time <= memory_time <= end_time:
                    period_memories.append(memory)
            
            # Analyze activities
            tasks_completed = len([m for m in period_memories if m.get("type") == "task_completion"])
            tasks_failed = len([m for m in period_memories if m.get("type") == "task_failure"])
            
            # Extract key achievements and issues
            achievements = []
            issues = []
            
            for memory in period_memories:
                content = memory.get("content", {})
                if memory.get("type") == "task_completion":
                    if "achievement" in content:
                        achievements.append(content["achievement"])
                elif memory.get("type") == "error" or memory.get("type") == "task_failure":
                    if "error" in content:
                        issues.append(content["error"])
            
            # Calculate time active (approximate)
            time_active = len(period_memories) * 0.1  # Rough estimate: 0.1 hours per memory
            
            activity = AgentActivity(
                agent_name=agent_name,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                key_achievements=achievements[:5],  # Top 5
                issues_encountered=issues[:5],  # Top 5
                time_active=time_active
            )
            activities.append(activity)
        
        return activities
        
    except Exception as e:
        logger.error(f"Error analyzing agent activities: {e}")
        return []

async def _detect_priority_alerts() -> List[PriorityAlert]:
    """Detect current priority alerts"""
    try:
        alerts = []
        orchestrator = AgentOrchestrator()
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        
        # Initialize queue manager if needed
        if not queue_manager.is_initialized:
            await queue_manager.initialize()
        
        # Check for agent errors and failures
        for agent_name in orchestrator.agents.keys():
            queue_status = await queue_manager.get_queue_status(agent_name.lower())
            
            failed_jobs = queue_status.get("failed_jobs", 0)
            if failed_jobs > 0:
                alert = PriorityAlert(
                    id=f"agent_failures_{agent_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    type="error",
                    severity="high" if failed_jobs > 5 else "medium",
                    title=f"{agent_name} Agent Failures",
                    description=f"{agent_name} has {failed_jobs} failed jobs requiring attention",
                    agents_involved=[agent_name],
                    created_at=datetime.now().isoformat(),
                    requires_attention=True
                )
                alerts.append(alert)
        
        # Check for resource conflicts from task flow API
        from api.task_flow_api import _detect_priority_conflicts
        conflicts = await _detect_priority_conflicts()
        
        for conflict in conflicts:
            if conflict.status == "active":
                alert = PriorityAlert(
                    id=f"conflict_{conflict.id}",
                    type="conflict",
                    severity=conflict.priority_level,
                    title=f"Priority Conflict: {conflict.conflict_type}",
                    description=conflict.description,
                    agents_involved=conflict.agents_involved,
                    created_at=conflict.created_at,
                    requires_attention=True
                )
                alerts.append(alert)
        
        # Check for alerts in shared context
        shared_alerts = await shared_context_manager.get_shared_context(
            context_type="priority_alert",
            query=None,
            requesting_agent="system",
            limit=20
        )
        
        # Process alerts from shared context
        for shared_alert in shared_alerts:
            content = shared_alert.get("content", {})
            
            # Skip alerts that have been resolved
            if content.get("status") == "resolved":
                continue
                
            # Convert to PriorityAlert model
            if all(k in content for k in ["id", "type", "severity", "title", "description"]):
                alert = PriorityAlert(
                    id=content["id"],
                    type=content["type"],
                    severity=content["severity"],
                    title=content["title"],
                    description=content["description"],
                    agents_involved=content.get("agents_involved", []),
                    created_at=content.get("created_at", shared_alert.get("timestamp", datetime.now().isoformat())),
                    requires_attention=content.get("requires_attention", True)
                )
                
                # Check if this alert is already in our list
                if not any(a.id == alert.id for a in alerts):
                    alerts.append(alert)
        
        # Check for deadline alerts
        current_time = datetime.now()
        upcoming_deadlines = await shared_context_manager.get_shared_context(
            context_type="deadline",
            query=None,
            requesting_agent="system",
            limit=10
        )
        
        for deadline in upcoming_deadlines:
            content = deadline.get("content", {})
            deadline_time = content.get("deadline_time")
            
            if deadline_time:
                try:
                    deadline_dt = datetime.fromisoformat(deadline_time)
                    time_remaining = deadline_dt - current_time
                    
                    # Alert if deadline is within 24 hours
                    if 0 < time_remaining.total_seconds() < 86400:  # 24 hours in seconds
                        hours_remaining = time_remaining.total_seconds() / 3600
                        
                        # Determine severity based on time remaining
                        if hours_remaining < 2:
                            severity = "high"
                        elif hours_remaining < 8:
                            severity = "medium"
                        else:
                            severity = "low"
                            
                        alert = PriorityAlert(
                            id=f"deadline_{content.get('id', deadline.get('id', ''))}",
                            type="deadline",
                            severity=severity,
                            title=f"Approaching Deadline: {content.get('title', 'Unknown Task')}",
                            description=f"Deadline in {int(hours_remaining)} hours for: {content.get('description', 'Unknown task')}",
                            agents_involved=content.get("assigned_agents", []),
                            created_at=datetime.now().isoformat(),
                            requires_attention=hours_remaining < 4  # Require attention if less than 4 hours
                        )
                        alerts.append(alert)
                except (ValueError, TypeError):
                    # Skip invalid datetime formats
                    pass
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error detecting priority alerts: {e}")
        return []

async def _identify_cross_functional_dependencies() -> List[CrossFunctionalDependency]:
    """Identify cross-functional dependencies between agents"""
    try:
        dependencies = []
        memory_manager = OptimizedMemoryManager()
        shared_context_manager = SharedContextManager(memory_manager)
        
        # Get recent agent communications
        communications = await memory_manager.query_agent_memory(
            agent_name="*",
            memory_type="agent_message",
            include_shared=True
        )
        
        # Analyze communications for dependencies
        for comm in communications[-20:]:  # Last 20 communications
            content = comm.get("content", {})
            message_data = content.get("message", {})
            
            if message_data and message_data.get("message_type") == "request":
                from_agent = message_data.get("from_agent")
                to_agent = message_data.get("to_agent")
                request_content = message_data.get("content", {})
                request_id = message_data.get("request_id", "")
                
                if from_agent and to_agent:
                    # Check if there's a response to this request
                    status = "pending"
                    
                    # Look for responses in the communications
                    for resp_comm in communications:
                        resp_content = resp_comm.get("content", {})
                        resp_message = resp_content.get("message", {})
                        
                        if (resp_message.get("message_type") == "response" and 
                            resp_message.get("request_id") == request_id):
                            status = "completed"
                            break
                    
                    dependency = CrossFunctionalDependency(
                        id=f"dep_{from_agent}_{to_agent}_{request_id}",
                        source_agent=from_agent,
                        target_agent=to_agent,
                        dependency_type=request_content.get("request_type", "coordination"),
                        description=f"{from_agent} waiting for {request_content.get('request_type', 'response')} from {to_agent}",
                        status=status,
                        created_at=message_data.get("timestamp", datetime.now().isoformat())
                    )
                    dependencies.append(dependency)
        
        # Get explicit dependencies from shared context
        explicit_dependencies = await shared_context_manager.get_shared_context(
            context_type="dependency",
            query=None,
            requesting_agent="system",
            limit=20
        )
        
        # Process explicit dependencies from shared context
        for dep in explicit_dependencies:
            content = dep.get("content", {})
            
            # Skip dependencies that have been completed or are invalid
            if content.get("status") == "completed":
                continue
                
            # Convert to CrossFunctionalDependency model
            if all(k in content for k in ["id", "source_agent", "target_agent", "dependency_type"]):
                dependency = CrossFunctionalDependency(
                    id=content["id"],
                    source_agent=content["source_agent"],
                    target_agent=content["target_agent"],
                    dependency_type=content["dependency_type"],
                    description=content.get("description", f"Dependency between {content['source_agent']} and {content['target_agent']}"),
                    status=content.get("status", "pending"),
                    created_at=content.get("created_at", dep.get("timestamp", datetime.now().isoformat())),
                    deadline=content.get("deadline")
                )
                
                # Check if this dependency is already in our list
                if not any(d.id == dependency.id for d in dependencies):
                    dependencies.append(dependency)
        
        # Get workflow dependencies from task flow
        try:
            from api.task_flow_api import _get_task_dependencies
            workflow_dependencies = await _get_task_dependencies()
            
            for wf_dep in workflow_dependencies:
                # Convert workflow dependency to CrossFunctionalDependency
                dependency = CrossFunctionalDependency(
                    id=f"workflow_dep_{wf_dep.id}",
                    source_agent=wf_dep.source_agent,
                    target_agent=wf_dep.target_agent,
                    dependency_type="workflow",
                    description=wf_dep.description,
                    status=wf_dep.status,
                    created_at=wf_dep.created_at,
                    deadline=wf_dep.deadline
                )
                
                # Check if this dependency is already in our list
                if not any(d.id == dependency.id for d in dependencies):
                    dependencies.append(dependency)
        except Exception as wf_error:
            logger.warning(f"Could not get workflow dependencies: {wf_error}")
        
        return dependencies
        
    except Exception as e:
        logger.error(f"Error identifying cross-functional dependencies: {e}")
        return []

async def _build_decision_queue() -> List[DecisionItem]:
    """Build queue of pending decisions"""
    try:
        decisions = []
        memory_manager = OptimizedMemoryManager()
        
        # Get collaborative decisions from cross-agent communication
        cross_agent_comm = CrossAgentComm()
        
        # Check for pending collaborative decisions
        if hasattr(cross_agent_comm, 'collaborative_decision_trees'):
            for decision_id, decision_data in cross_agent_comm.collaborative_decision_trees.items():
                if decision_data.get("status") == "pending":
                    decision = DecisionItem(
                        id=decision_id,
                        title=decision_data.get("topic", "Collaborative Decision"),
                        description=decision_data.get("description", "Pending collaborative decision"),
                        decision_type="collaborative",
                        agents_involved=decision_data.get("agents_involved", []),
                        options=decision_data.get("options", []),
                        recommendation=decision_data.get("recommendation"),
                        priority=decision_data.get("priority", "medium"),
                        deadline=decision_data.get("deadline"),
                        created_at=decision_data.get("created_at", datetime.now().isoformat()),
                        context=decision_data.get("context", {})
                    )
                    decisions.append(decision)
        
        # Get unresolved conflicts that need decisions
        conflicts = await _detect_priority_alerts()
        for alert in conflicts:
            if alert.type == "conflict" and alert.requires_attention:
                decision = DecisionItem(
                    id=f"conflict_decision_{alert.id}",
                    title=f"Resolve {alert.title}",
                    description=f"Decision needed to resolve: {alert.description}",
                    decision_type="conflict_resolution",
                    agents_involved=alert.agents_involved,
                    options=[
                        {"option": "auto_resolve", "description": "Let system auto-resolve"},
                        {"option": "manual_intervention", "description": "Require manual intervention"},
                        {"option": "escalate", "description": "Escalate to higher authority"}
                    ],
                    priority=alert.severity,
                    created_at=alert.created_at,
                    context={"alert_id": alert.id, "alert_type": alert.type}
                )
                decisions.append(decision)
        
        return decisions
        
    except Exception as e:
        logger.error(f"Error building decision queue: {e}")
        return []

async def _generate_recommendations(
    activities: List[AgentActivity],
    alerts: List[PriorityAlert],
    dependencies: List[CrossFunctionalDependency],
    decisions: List[DecisionItem]
) -> List[str]:
    """Generate actionable recommendations based on the brief data"""
    try:
        recommendations = []
        
        # Analyze agent performance
        total_tasks = sum(a.tasks_completed for a in activities)
        total_failures = sum(a.tasks_failed for a in activities)
        
        if total_failures > total_tasks * 0.1 and total_tasks > 0:  # More than 10% failure rate
            recommendations.append(
                f"High failure rate detected ({total_failures}/{total_tasks}). "
                "Consider reviewing agent configurations and error handling."
            )
        
        # Check for overloaded agents
        overloaded_agents = [a for a in activities if a.time_active > 8]  # More than 8 hours
        if overloaded_agents:
            agent_names = [a.agent_name for a in overloaded_agents]
            recommendations.append(
                f"Agents {', '.join(agent_names)} show high activity levels. "
                "Consider workload balancing or scaling."
            )
        
        # Check for high priority alerts
        high_priority_alerts = [a for a in alerts if a.severity == "high"]
        if high_priority_alerts:
            recommendations.append(
                f"{len(high_priority_alerts)} high-priority alerts require immediate attention. "
                "Review alert details and take corrective action."
            )
        
        # Check for blocked dependencies
        blocked_deps = [d for d in dependencies if d.status == "blocked"]
        if blocked_deps:
            recommendations.append(
                f"{len(blocked_deps)} cross-functional dependencies are blocked. "
                "Review and resolve to maintain workflow efficiency."
            )
        
        # Check for urgent decisions
        urgent_decisions = [d for d in decisions if d.priority == "high"]
        if urgent_decisions:
            recommendations.append(
                f"{len(urgent_decisions)} high-priority decisions are pending. "
                "Review decision queue and provide guidance."
            )
        
        # Check for inactive agents
        inactive_agents = [a for a in activities if a.tasks_completed == 0 and a.time_active < 0.5]
        if inactive_agents and len(inactive_agents) < len(activities):  # Don't report if all agents are inactive
            agent_names = [a.agent_name for a in inactive_agents]
            recommendations.append(
                f"Agents {', '.join(agent_names)} show low activity levels. "
                "Consider checking their status or assigning tasks."
            )
        
        # Check for cross-functional collaboration opportunities
        agent_pairs = []
        for i, dep in enumerate(dependencies):
            pair = (dep.source_agent, dep.target_agent)
            if pair not in agent_pairs and (pair[1], pair[0]) not in agent_pairs:
                agent_pairs.append(pair)
        
        if len(agent_pairs) < 3 and len(activities) > 3:  # If few collaborations but many agents
            recommendations.append(
                "Limited cross-functional collaboration detected. "
                "Consider creating workflows that encourage agent interaction."
            )
        
        # Default recommendation if everything looks good
        if not recommendations:
            recommendations.append(
                "All systems operating normally. Continue monitoring for any changes."
            )
        
        # Store recommendations in shared context for agents to access
        try:
            shared_context_manager = SharedContextManager(OptimizedMemoryManager())
            await shared_context_manager.store_shared_context(
                context_type="recommendations",
                content={
                    "recommendations": recommendations,
                    "generated_at": datetime.now().isoformat(),
                    "based_on": {
                        "activities_count": len(activities),
                        "alerts_count": len(alerts),
                        "dependencies_count": len(dependencies),
                        "decisions_count": len(decisions)
                    }
                },
                source_agent="system",
                access_control={"read": "*", "write": "system"}  # All agents can read, only system can write
            )
        except Exception as context_error:
            logger.warning(f"Failed to store recommendations in shared context: {context_error}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return ["Error generating recommendations. Please review system status manually."]
clas
s AlertResolutionRequest(BaseModel):
    """Request model for resolving priority alerts"""
    resolution_type: str = Field(..., description="Type of resolution: resolved, ignored, escalated")
    resolution_notes: Optional[str] = Field(None, description="Optional notes about the resolution")
    assigned_to: Optional[str] = Field(None, description="Optional agent or user assigned to handle the alert")

@router.post("/alerts/{alert_id}/resolve", response_model=Dict[str, Any])
async def resolve_priority_alert(
    alert_id: str,
    resolution_data: AlertResolutionRequest
) -> Dict[str, Any]:
    """Resolve a priority alert"""
    try:
        # Get the alert
        alerts = await _detect_priority_alerts()
        alert = next((a for a in alerts if a.id == alert_id), None)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        # Process the resolution
        resolution_result = {
            "alert_id": alert_id,
            "resolution_type": resolution_data.resolution_type,
            "resolution_notes": resolution_data.resolution_notes,
            "assigned_to": resolution_data.assigned_to,
            "resolved_at": datetime.now().isoformat(),
            "resolved_by": "human"  # Could be enhanced to track the actual user
        }
        
        # Store resolution in shared context
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        await shared_context_manager.store_shared_context(
            context_type="alert_resolution",
            content={
                "alert_id": alert_id,
                "original_alert": alert.dict(),
                "resolution": resolution_result
            },
            source_agent="system",
            access_control={"read": "*", "write": "system"}  # All agents can read, only system can write
        )
        
        # If this was a conflict alert, update any related decisions
        if alert.type == "conflict":
            decisions = await _build_decision_queue()
            related_decision = next((d for d in decisions if d.context.get("alert_id") == alert_id), None)
            
            if related_decision:
                cross_agent_comm = CrossAgentComm()
                await cross_agent_comm.broadcast_message(
                    from_agent="system",
                    message_type="alert_resolution",
                    content={
                        "alert_id": alert_id,
                        "decision_id": related_decision.id,
                        "resolution": resolution_result
                    },
                    target_agents=alert.agents_involved
                )
        
        return {
            "status": "resolved",
            "alert_id": alert_id,
            "resolution": resolution_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/{agent_name}", response_model=Dict[str, Any])
async def get_agent_specific_brief(
    agent_name: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """Get morning brief specific to a single agent"""
    try:
        # Calculate time period
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get agent-specific activities
        orchestrator = AgentOrchestrator()
        if agent_name not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get agent's activities
        agent_activities = await _analyze_agent_activities(start_time, end_time)
        agent_activity = next((a for a in agent_activities if a.agent_name == agent_name), None)
        
        if not agent_activity:
            # Create empty activity if none found
            agent_activity = AgentActivity(
                agent_name=agent_name,
                tasks_completed=0,
                tasks_failed=0,
                key_achievements=[],
                issues_encountered=[],
                time_active=0.0
            )
        
        # Get agent-specific alerts
        all_alerts = await _detect_priority_alerts()
        agent_alerts = [a for a in all_alerts if agent_name in a.agents_involved]
        
        # Get agent-specific dependencies
        all_dependencies = await _identify_cross_functional_dependencies()
        agent_dependencies = [d for d in all_dependencies 
                            if agent_name in [d.source_agent, d.target_agent]]
        
        # Get agent-specific decisions
        all_decisions = await _build_decision_queue()
        agent_decisions = [d for d in all_decisions if agent_name in d.agents_involved]
        
        # Get agent-specific context from shared context manager
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        agent_context = await shared_context_manager.get_agent_specific_context(
            agent_name=agent_name,
            context_type=None,  # All types
            query=None  # No specific query
        )
        
        # Filter context to relevant items only
        relevant_context = []
        for ctx in agent_context:
            # Only include context items from the time period
            if "timestamp" in ctx:
                ctx_time = datetime.fromisoformat(ctx["timestamp"])
                if start_time <= ctx_time <= end_time:
                    relevant_context.append(ctx)
        
        return {
            "date": end_time.strftime("%Y-%m-%d"),
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "agent_name": agent_name,
            "activity": agent_activity.dict(),
            "alerts": [a.dict() for a in agent_alerts],
            "dependencies": [d.dict() for d in agent_dependencies],
            "decisions": [d.dict() for d in agent_decisions],
            "shared_context": relevant_context[:10],  # Limit to 10 most recent items
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent-specific brief for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DependencyUpdateRequest(BaseModel):
    """Request model for updating cross-functional dependencies"""
    status: str = Field(..., description="New status: pending, in_progress, completed, blocked")
    notes: Optional[str] = Field(None, description="Optional notes about the update")
    deadline: Optional[str] = Field(None, description="Optional updated deadline")

@router.post("/dependencies/{dependency_id}/update", response_model=Dict[str, Any])
async def update_dependency_status(
    dependency_id: str,
    update_data: DependencyUpdateRequest
) -> Dict[str, Any]:
    """Update the status of a cross-functional dependency"""
    try:
        # Get the dependency
        dependencies = await _identify_cross_functional_dependencies()
        dependency = next((d for d in dependencies if d.id == dependency_id), None)
        
        if not dependency:
            raise HTTPException(status_code=404, detail=f"Dependency {dependency_id} not found")
        
        # Process the update
        update_result = {
            "dependency_id": dependency_id,
            "previous_status": dependency.status,
            "new_status": update_data.status,
            "notes": update_data.notes,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "human"  # Could be enhanced to track the actual user
        }
        
        if update_data.deadline:
            update_result["new_deadline"] = update_data.deadline
        
        # Store update in shared context
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        await shared_context_manager.store_shared_context(
            context_type="dependency_update",
            content={
                "dependency_id": dependency_id,
                "original_dependency": dependency.dict(),
                "update": update_result
            },
            source_agent="system",
            access_control={"read": "*", "write": "system"}  # All agents can read, only system can write
        )
        
        # Notify involved agents
        cross_agent_comm = CrossAgentComm()
        await cross_agent_comm.broadcast_message(
            from_agent="system",
            message_type="dependency_update",
            content=update_result,
            target_agents=[dependency.source_agent, dependency.target_agent]
        )
        
        return {
            "status": "updated",
            "dependency_id": dependency_id,
            "update": update_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dependency {dependency_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/refresh", response_model=Dict[str, Any])
async def refresh_morning_brief() -> Dict[str, Any]:
    """Force a refresh of the morning brief data"""
    try:
        # Clear any cached data
        # This implementation assumes there might be caching in the future
        
        # Generate a fresh brief
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        brief = await _generate_morning_brief(start_time, end_time)
        
        # Store the refreshed brief in shared context for all agents to access
        shared_context_manager = SharedContextManager(OptimizedMemoryManager())
        await shared_context_manager.store_shared_context(
            context_type="morning_brief",
            content={
                "brief_date": brief.date,
                "summary": brief.summary,
                "recommendations": brief.recommendations,
                "generated_at": brief.generated_at
            },
            source_agent="system",
            access_control={"read": "*", "write": "system"}  # All agents can read, only system can write
        )
        
        return {
            "status": "refreshed",
            "brief_date": brief.date,
            "generated_at": brief.generated_at,
            "message": "Morning brief data has been refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing morning brief: {e}")
        raise HTTPException(status_code=500, detail=str(e))