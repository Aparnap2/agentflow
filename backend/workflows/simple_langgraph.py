"""Simple LangGraph workflow implementation"""
from typing import Dict, Any, List
from dataclasses import dataclass
import asyncio
from datetime import datetime
from loguru import logger

@dataclass
class WorkflowState:
    """Simple workflow state"""
    project_vision: str = ""
    current_step: str = "start"
    agent_outputs: Dict[str, Any] = None
    completed_agents: List[str] = None
    
    def __post_init__(self):
        if self.agent_outputs is None:
            self.agent_outputs = {}
        if self.completed_agents is None:
            self.completed_agents = []

class SimpleLangGraph:
    """Minimal LangGraph-style workflow"""
    
    def __init__(self, agents: Dict[str, Any], memory_manager):
        self.agents = agents
        self.memory_manager = memory_manager
        self.workflow_steps = {
            "start": self._start_workflow,
            "manager_planning": self._manager_planning,
            "parallel_execution": self._parallel_execution,
            "results_aggregation": self._results_aggregation,
            "end": self._end_workflow
        }
    
    async def execute_workflow(self, vision: str) -> Dict[str, Any]:
        """Execute complete workflow"""
        state = WorkflowState(project_vision=vision)
        
        logger.info(f"🚀 Starting LangGraph workflow: {vision[:50]}...")
        
        while state.current_step != "end":
            step_func = self.workflow_steps.get(state.current_step)
            if not step_func:
                logger.error(f"Unknown workflow step: {state.current_step}")
                break
            
            logger.info(f"📋 Executing step: {state.current_step}")
            state = await step_func(state)
        
        return {
            "status": "completed",
            "agent_outputs": state.agent_outputs,
            "completed_agents": state.completed_agents,
            "workflow_id": f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    async def _start_workflow(self, state: WorkflowState) -> WorkflowState:
        """Initialize workflow"""
        await self.memory_manager.store_agent_memory(
            agent_name="Workflow",
            memory_type="workflow_start",
            content={"vision": state.project_vision, "timestamp": datetime.now().isoformat()},
            is_shared=True
        )
        state.current_step = "manager_planning"
        return state
    
    async def _manager_planning(self, state: WorkflowState) -> WorkflowState:
        """Manager creates execution plan"""
        if "Manager" not in self.agents:
            state.current_step = "parallel_execution"
            return state
        
        manager = self.agents["Manager"]
        task = {
            "id": f"manager_planning_{datetime.now().strftime('%H%M%S')}",
            "vision": state.project_vision,
            "mode": "workflow_planning"
        }
        
        try:
            result = await manager.execute(task)
            state.agent_outputs["Manager"] = result
            state.completed_agents.append("Manager")
            
            # Store in memory
            await self.memory_manager.store_agent_memory(
                agent_name="Manager",
                memory_type="workflow_planning",
                content=result,
                is_shared=True
            )
            
        except Exception as e:
            logger.error(f"Manager planning failed: {e}")
        
        state.current_step = "parallel_execution"
        return state
    
    async def _parallel_execution(self, state: WorkflowState) -> WorkflowState:
        """Execute specialist agents in parallel"""
        specialist_agents = ["Finance", "Marketing", "Legal", "Sales", "Money"]
        available_agents = [name for name in specialist_agents if name in self.agents]
        
        if not available_agents:
            state.current_step = "results_aggregation"
            return state
        
        # Execute agents in parallel
        tasks = []
        for agent_name in available_agents:
            if agent_name not in state.completed_agents:
                task = self._create_agent_task(agent_name, state)
                tasks.append((agent_name, task))
        
        if tasks:
            results = await asyncio.gather(
                *[self._execute_agent_task(agent_name, task) for agent_name, task in tasks],
                return_exceptions=True
            )
            
            for i, (agent_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"{agent_name} execution failed: {result}")
                    state.agent_outputs[agent_name] = {"error": str(result)}
                else:
                    state.agent_outputs[agent_name] = result
                    state.completed_agents.append(agent_name)
                    
                    # Store in memory
                    await self.memory_manager.store_agent_memory(
                        agent_name=agent_name,
                        memory_type="workflow_execution",
                        content=result,
                        is_shared=True
                    )
        
        state.current_step = "results_aggregation"
        return state
    
    async def _results_aggregation(self, state: WorkflowState) -> WorkflowState:
        """Aggregate and finalize results"""
        # Create summary of all outputs
        summary = {
            "total_agents_executed": len(state.completed_agents),
            "successful_executions": len([o for o in state.agent_outputs.values() if "error" not in o]),
            "execution_summary": {
                agent: {"status": "success" if "error" not in output else "failed"}
                for agent, output in state.agent_outputs.items()
            }
        }
        
        # Store final summary
        await self.memory_manager.store_agent_memory(
            agent_name="Workflow",
            memory_type="workflow_summary",
            content=summary,
            is_shared=True
        )
        
        state.current_step = "end"
        return state
    
    async def _end_workflow(self, state: WorkflowState) -> WorkflowState:
        """Complete workflow"""
        logger.info(f"✅ Workflow completed: {len(state.completed_agents)} agents executed")
        return state
    
    def _create_agent_task(self, agent_name: str, state: WorkflowState) -> Dict[str, Any]:
        """Create task for agent based on workflow context"""
        return {
            "id": f"{agent_name.lower()}_workflow_{datetime.now().strftime('%H%M%S')}",
            "vision": state.project_vision,
            "workflow_context": {
                "completed_agents": state.completed_agents,
                "available_outputs": list(state.agent_outputs.keys())
            },
            "mode": "workflow_execution"
        }
    
    async def _execute_agent_task(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent task with timeout"""
        agent = self.agents[agent_name]
        try:
            # Execute with timeout
            result = await asyncio.wait_for(agent.execute(task), timeout=60.0)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"{agent_name} execution timed out")
            return {"error": "execution_timeout", "agent": agent_name}
        except Exception as e:
            logger.error(f"{agent_name} execution failed: {e}")
            return {"error": str(e), "agent": agent_name}