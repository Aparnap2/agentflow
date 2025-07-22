"""
Enhanced Manager Agent - Primary orchestrator for the agent ecosystem
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from agents.manager_agent import ManagerAgent
from task_queue.task_router import TaskRouter
from task_queue.cross_agent_validator import CrossAgentValidator

class EnhancedManagerAgent(ManagerAgent):
    """Enhanced Manager agent with meta-orchestration capabilities"""
    
    def __init__(self, memory_manager, approval_manager, event_bus=None):
        super().__init__(memory_manager, approval_manager)
        
        # Initialize task router and cross-agent validator
        self.task_router = TaskRouter(memory_manager, event_bus)
        self.cross_agent_validator = CrossAgentValidator(memory_manager, event_bus)
        self.event_bus = event_bus
        
        # Add meta-orchestration capabilities to role actions
        self.role_actions.update({
            "route_task": self.route_task,
            "validate_results": self.validate_cross_agent_results,
            "manage_project": self.manage_multi_agent_project,
            "resolve_conflict": self.resolve_resource_conflict,
            "optimize_workflow": self.optimize_workflow_performance,
            "coordinate_learning": self.coordinate_learning
        })
    
    def _get_system_prompt(self) -> str:
        """Override system prompt to include meta-orchestration capabilities"""
        base_prompt = super()._get_system_prompt()
        
        meta_orchestration_prompt = """

ENHANCED META-ORCHESTRATION CAPABILITIES:

1. INTELLIGENT TASK ROUTING:
   - Route tasks to appropriate specialized agents based on domain expertise
   - Implement domain-specific routing rules
   - Optimize routing based on agent performance

2. CROSS-AGENT VALIDATION:
   - Validate results across agents for consistency
   - Implement validation strategies for different data types
   - Resolve conflicts between agent outputs

3. MULTI-AGENT PROJECT MANAGEMENT:
   - Coordinate complex projects requiring multiple agents
   - Manage dependencies between agent tasks
   - Track progress across multiple workstreams

4. RESOURCE CONFLICT RESOLUTION:
   - Identify and resolve conflicts when agents compete for resources
   - Prioritize tasks based on business impact
   - Implement fair resource allocation strategies

5. WORKFLOW OPTIMIZATION:
   - Identify bottlenecks in multi-agent workflows
   - Optimize performance through process improvements
   - Implement workflow templates for common scenarios

6. KNOWLEDGE COORDINATION:
   - Ensure knowledge sharing across the agent ecosystem
   - Facilitate collaborative learning
   - Maintain consistent documentation standards

You are the central orchestrator for the entire agent ecosystem, responsible for ensuring efficient collaboration and optimal performance across all specialized agents."""
        
        return base_prompt + meta_orchestration_prompt
    
    async def route_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to appropriate specialized agents based on domain expertise
        
        Args:
            task_data: Dictionary containing task information
                - task_type: Type of task
                - content: Task content
                - priority: Task priority
                - metadata: Additional metadata
                
        Returns:
            Dictionary containing routing results
        """
        logger.info(f"Routing task: {task_data.get('task_type', 'unknown')}")
        
        # Use task router to determine appropriate agents
        agents = await self.task_router.route_task(task_data)
        
        # Get task dependencies
        dependencies = await self.task_router.get_task_dependencies(task_data)
        
        # Create task assignments
        task_assignments = []
        for agent_name in agents:
            assignment = {
                "agent": agent_name,
                "task_id": f"{agent_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task_data": task_data,
                "dependencies": dependencies,
                "assigned_at": datetime.now().isoformat(),
                "status": "pending"
            }
            task_assignments.append(assignment)
        
        # Store routing decision in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="task_routing",
                content={
                    "task_data": task_data,
                    "assigned_agents": agents,
                    "dependencies": dependencies,
                    "assignments": task_assignments
                },
                is_shared=True,
                confidence=0.9
            )
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("task_routed", {
                "task_type": task_data.get("task_type", "unknown"),
                "assigned_agents": agents,
                "assignments": task_assignments
            })
        
        return {
            "assigned_agents": agents,
            "task_assignments": task_assignments,
            "dependencies": dependencies
        }
    
    async def validate_cross_agent_results(self, 
                                         results: Dict[str, Any],
                                         agents_involved: List[str]) -> Dict[str, Any]:
        """
        Validate results across multiple agents for consistency
        
        Args:
            results: Dictionary mapping agent names to their results
            agents_involved: List of agent names involved in the task
                
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating results across agents: {agents_involved}")
        
        # Use cross-agent validator to validate results
        validation_result = await self.cross_agent_validator.validate(results, agents_involved)
        
        # Store validation result in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="cross_agent_validation",
                content=validation_result,
                is_shared=True,
                confidence=validation_result.get("confidence", 0.5)
            )
        
        # Handle conflicts if any
        conflicts = validation_result.get("conflicts", [])
        if conflicts:
            logger.warning(f"Found {len(conflicts)} conflicts in cross-agent validation")
            
            # Resolve conflicts
            for conflict in conflicts:
                conflict_type = conflict.get("type", "unknown")
                resolution_strategy = self.cross_agent_validator.conflict_resolution_strategies.get(conflict_type)
                
                if resolution_strategy:
                    resolution = await resolution_strategy(conflict)
                    conflict["resolution"] = resolution
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("results_validated", {
                "is_valid": validation_result.get("is_valid", False),
                "confidence": validation_result.get("confidence", 0),
                "conflict_count": len(conflicts)
            })
        
        return validation_result
    
    async def manage_multi_agent_project(self,
                                       project_id: str,
                                       project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage a complex project involving multiple agents
        
        Args:
            project_id: Project identifier
            project_data: Dictionary containing project information
                - name: Project name
                - description: Project description
                - tasks: List of tasks
                - timeline: Project timeline
                - agents: List of agents involved
                
        Returns:
            Dictionary containing project management results
        """
        logger.info(f"Managing multi-agent project: {project_id}")
        
        project_name = project_data.get("name", f"Project {project_id}")
        tasks = project_data.get("tasks", [])
        agents_involved = project_data.get("agents", [])
        
        # Create project structure
        project = {
            "id": project_id,
            "name": project_name,
            "description": project_data.get("description", ""),
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "agents_involved": agents_involved,
            "task_assignments": {},
            "dependencies": {},
            "progress": 0,
            "timeline": project_data.get("timeline", {})
        }
        
        # Route tasks to appropriate agents
        for task in tasks:
            task_id = task.get("id", f"task_{len(project['task_assignments']) + 1}")
            
            # Route task
            routing_result = await self.route_task({
                "task_type": task.get("type", "unknown"),
                "content": task.get("description", ""),
                "priority": task.get("priority", "normal"),
                "metadata": {"project_id": project_id}
            })
            
            # Store task assignment
            project["task_assignments"][task_id] = {
                "task": task,
                "assigned_agents": routing_result["assigned_agents"],
                "status": "pending",
                "dependencies": task.get("dependencies", [])
            }
            
            # Update dependencies
            for dep_id in task.get("dependencies", []):
                if dep_id not in project["dependencies"]:
                    project["dependencies"][dep_id] = []
                project["dependencies"][dep_id].append(task_id)
        
        # Store project in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="multi_agent_project",
                content=project,
                is_shared=True,
                confidence=0.9,
                metadata={"project_id": project_id}
            )
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("project_created", {
                "project_id": project_id,
                "project_name": project_name,
                "agents_involved": agents_involved,
                "task_count": len(tasks)
            })
        
        return project
    
    async def resolve_resource_conflict(self,
                                      conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts when agents compete for resources
        
        Args:
            conflict_data: Dictionary containing conflict information
                - agents: List of agents involved in conflict
                - resource: Resource being contested
                - priority: Priority of each agent's task
                
        Returns:
            Dictionary containing conflict resolution results
        """
        logger.info(f"Resolving resource conflict: {conflict_data.get('resource', 'unknown')}")
        
        agents = conflict_data.get("agents", [])
        resource = conflict_data.get("resource", "unknown")
        priorities = conflict_data.get("priority", {})
        
        # Default resolution strategy: prioritize by task priority
        resolution = {
            "resource": resource,
            "agents_involved": agents,
            "resolution_strategy": "priority_based",
            "allocation": {}
        }
        
        # Sort agents by priority
        sorted_agents = sorted(agents, key=lambda a: priorities.get(a, 0), reverse=True)
        
        # Allocate resource based on priority
        for i, agent in enumerate(sorted_agents):
            if i == 0:
                # Highest priority agent gets the resource
                resolution["allocation"][agent] = {
                    "access": "granted",
                    "share": 1.0,
                    "reason": "highest_priority"
                }
            else:
                # Other agents have to wait
                resolution["allocation"][agent] = {
                    "access": "deferred",
                    "share": 0.0,
                    "reason": "lower_priority"
                }
        
        # Store resolution in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="resource_conflict_resolution",
                content=resolution,
                is_shared=True,
                confidence=0.9
            )
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("resource_conflict_resolved", {
                "resource": resource,
                "winner": sorted_agents[0] if sorted_agents else None,
                "resolution_strategy": "priority_based"
            })
        
        return resolution
    
    async def optimize_workflow_performance(self,
                                         workflow_id: str,
                                         performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify bottlenecks and optimize workflow performance
        
        Args:
            workflow_id: Workflow identifier
            performance_data: Dictionary containing performance metrics
                
        Returns:
            Dictionary containing optimization results
        """
        logger.info(f"Optimizing workflow performance: {workflow_id}")
        
        # Extract performance metrics
        task_durations = performance_data.get("task_durations", {})
        agent_performance = performance_data.get("agent_performance", {})
        bottlenecks = []
        
        # Identify bottlenecks (tasks taking longer than average)
        if task_durations:
            avg_duration = sum(task_durations.values()) / len(task_durations)
            for task_id, duration in task_durations.items():
                if duration > avg_duration * 1.5:  # 50% longer than average
                    bottlenecks.append({
                        "task_id": task_id,
                        "duration": duration,
                        "avg_duration": avg_duration,
                        "ratio": duration / avg_duration
                    })
        
        # Generate optimization recommendations
        recommendations = []
        
        # Recommend task reassignment for bottlenecks
        for bottleneck in bottlenecks:
            task_id = bottleneck["task_id"]
            current_agent = performance_data.get("task_assignments", {}).get(task_id)
            
            if current_agent:
                # Find better performing agents for this task type
                task_type = performance_data.get("task_types", {}).get(task_id)
                better_agents = []
                
                for agent, perf in agent_performance.items():
                    if agent != current_agent and task_type in perf.get("specializations", []):
                        if perf.get("avg_duration", {}).get(task_type, float('inf')) < bottleneck["duration"]:
                            better_agents.append(agent)
                
                if better_agents:
                    recommendations.append({
                        "type": "task_reassignment",
                        "task_id": task_id,
                        "current_agent": current_agent,
                        "recommended_agents": better_agents,
                        "expected_improvement": "reduced_duration"
                    })
        
        # Recommend parallel execution for independent tasks
        dependencies = performance_data.get("dependencies", {})
        independent_tasks = []
        
        for task_id in task_durations:
            if task_id not in dependencies and not any(task_id in deps for deps in dependencies.values()):
                independent_tasks.append(task_id)
        
        if len(independent_tasks) > 1:
            recommendations.append({
                "type": "parallel_execution",
                "tasks": independent_tasks,
                "expected_improvement": "reduced_total_duration"
            })
        
        # Create optimization plan
        optimization_plan = {
            "workflow_id": workflow_id,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "performance_metrics": {
                "avg_task_duration": sum(task_durations.values()) / len(task_durations) if task_durations else 0,
                "total_duration": sum(task_durations.values()) if task_durations else 0,
                "bottleneck_count": len(bottlenecks)
            }
        }
        
        # Store optimization plan in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="workflow_optimization",
                content=optimization_plan,
                is_shared=True,
                confidence=0.8,
                metadata={"workflow_id": workflow_id}
            )
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("workflow_optimized", {
                "workflow_id": workflow_id,
                "bottleneck_count": len(bottlenecks),
                "recommendation_count": len(recommendations)
            })
        
        # Update task router with performance data
        await self.task_router.optimize_routing(agent_performance)
        
        return optimization_plan
    
    async def coordinate_learning(self,
                                learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure knowledge is shared across the agent ecosystem
        
        Args:
            learning_data: Dictionary containing learning information
                - source_agent: Agent that learned something
                - knowledge: Knowledge to be shared
                - relevance: Dictionary mapping agent names to relevance scores
                
        Returns:
            Dictionary containing coordination results
        """
        logger.info(f"Coordinating learning from {learning_data.get('source_agent', 'unknown')}")
        
        source_agent = learning_data.get("source_agent", "unknown")
        knowledge = learning_data.get("knowledge", {})
        relevance = learning_data.get("relevance", {})
        
        # Determine which agents should receive this knowledge
        target_agents = []
        for agent, score in relevance.items():
            if score >= 0.5:  # Only share with agents where relevance is at least 50%
                target_agents.append(agent)
        
        # Create knowledge sharing plan
        sharing_plan = {
            "source_agent": source_agent,
            "knowledge_type": knowledge.get("type", "general"),
            "target_agents": target_agents,
            "sharing_method": "memory_integration",
            "timestamp": datetime.now().isoformat()
        }
        
        # Share knowledge with target agents
        shared_with = []
        for agent in target_agents:
            # Store in agent's memory
            if self.memory_manager:
                await self.memory_manager.store_agent_memory(
                    agent_name=agent,
                    memory_type="shared_knowledge",
                    content={
                        "source_agent": source_agent,
                        "knowledge": knowledge,
                        "relevance": relevance.get(agent, 0)
                    },
                    is_shared=True,
                    confidence=relevance.get(agent, 0.5)
                )
                shared_with.append(agent)
        
        # Update sharing plan with results
        sharing_plan["shared_with"] = shared_with
        
        # Store sharing plan in memory
        if self.memory_manager:
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="knowledge_coordination",
                content=sharing_plan,
                is_shared=True,
                confidence=0.9
            )
        
        # Emit event if event bus is available
        if self.event_bus:
            await self.event_bus.emit("knowledge_shared", {
                "source_agent": source_agent,
                "target_agents": shared_with,
                "knowledge_type": knowledge.get("type", "general")
            })
        
        return sharing_plan