"""
LangGraph-based Agent Orchestration System
"""
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph
from communication.event_bus import event_bus

class AgentFlowState(TypedDict):
    project_vision: str
    shared_context: Dict[str, Any]
    agent_outputs: Dict[str, Dict]
    workflow_phase: str
    current_agent: str

class LangGraphOrchestrator:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.workflow = self._create_workflow()
        
    def _create_workflow(self):
        """Create LangGraph workflow with agent nodes"""
        workflow = StateGraph(AgentFlowState)
        
        # Add agent nodes
        workflow.add_node("cofounder", self._cofounder_node)
        workflow.add_node("manager", self._manager_node)
        workflow.add_node("product", self._product_node)
        workflow.add_node("finance", self._finance_node)
        workflow.add_node("marketing", self._marketing_node)
        workflow.add_node("legal", self._legal_node)
        workflow.add_node("supervisor", self._supervisor_node)
        
        # Define workflow
        workflow.set_entry_point("supervisor")
        workflow.add_edge("supervisor", "cofounder")
        workflow.add_edge("cofounder", "manager")
        workflow.add_edge("manager", "product")
        workflow.add_edge("manager", "finance")
        workflow.add_edge("manager", "marketing")
        workflow.add_edge("manager", "legal")
        workflow.add_edge(["product", "finance", "marketing", "legal"], "__end__")
        
        return workflow.compile()
    
    async def _supervisor_node(self, state: AgentFlowState) -> AgentFlowState:
        """Supervisor node that manages workflow"""
        await event_bus.broadcast_update("supervisor", {
            "type": "workflow_start",
            "data": {"phase": state.get("workflow_phase", "planning")},
            "message": "Starting agent workflow"
        })
        return state
    
    async def _cofounder_node(self, state: AgentFlowState) -> AgentFlowState:
        """Cofounder agent node"""
        agent = self.agents.get("Cofounder")
        if agent:
            task = {"id": f"cofounder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            result = await agent.execute(task)
            state["agent_outputs"]["cofounder"] = result
        return state
    
    async def _manager_node(self, state: AgentFlowState) -> AgentFlowState:
        """Manager agent node"""
        agent = self.agents.get("Manager")
        if agent:
            task = {"id": f"manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            result = await agent.execute(task)
            state["agent_outputs"]["manager"] = result
        return state
    
    async def _product_node(self, state: AgentFlowState) -> AgentFlowState:
        """Product agent node"""
        return await self._execute_specialist("Product", "product", state)
    
    async def _finance_node(self, state: AgentFlowState) -> AgentFlowState:
        """Finance agent node"""
        return await self._execute_specialist("Finance", "finance", state)
    
    async def _marketing_node(self, state: AgentFlowState) -> AgentFlowState:
        """Marketing agent node"""
        return await self._execute_specialist("Marketing", "marketing", state)
    
    async def _legal_node(self, state: AgentFlowState) -> AgentFlowState:
        """Legal agent node"""
        return await self._execute_specialist("Legal", "legal", state)
    
    async def _execute_specialist(self, agent_name: str, agent_key: str, state: AgentFlowState) -> AgentFlowState:
        """Execute specialist agent"""
        agent = self.agents.get(agent_name)
        if agent:
            task = {"id": f"{agent_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            result = await agent.execute(task)
            state["agent_outputs"][agent_key] = result
            
            await event_bus.broadcast_update(agent_key, {
                "type": "task_completed",
                "data": result,
                "message": f"{agent_name} completed"
            })
        return state
    
    async def execute_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete workflow"""
        try:
            state = {
                "project_vision": initial_state.get("project_vision", ""),
                "shared_context": initial_state.get("shared_context", {}),
                "agent_outputs": {},
                "workflow_phase": "execution",
                "current_agent": ""
            }
            
            result = await self.workflow.ainvoke(state)
            return {"status": "completed", "agent_outputs": result["agent_outputs"]}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}