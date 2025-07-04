"""
LangGraph-based Agent Orchestration System
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, AIMessage
from communication.event_bus import event_bus
import operator

class AgentFlowState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    project_vision: str
    shared_context: Dict[str, Any]
    agent_outputs: Dict[str, Dict]
    workflow_phase: str
    current_agent: str
    iteration_count: int
    confidence_scores: Dict[str, float]
    requires_approval: bool

class LangGraphOrchestrator:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()
        
    def _create_workflow(self):
        """Create LangGraph workflow with cycles and checkpointing"""
        workflow = StateGraph(AgentFlowState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("cofounder", self._cofounder_node)
        workflow.add_node("manager", self._manager_node)
        workflow.add_node("product", self._product_node)
        workflow.add_node("finance", self._finance_node)
        workflow.add_node("marketing", self._marketing_node)
        workflow.add_node("legal", self._legal_node)
        workflow.add_node("quality_check", self._quality_check_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional routing with cycles
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next,
            {"cofounder": "cofounder", "manager": "manager", "product": "product", 
             "finance": "finance", "marketing": "marketing", "legal": "legal", "end": END}
        )
        
        # All agents go to quality check
        for agent in ["cofounder", "manager", "product", "finance", "marketing", "legal"]:
            workflow.add_edge(agent, "quality_check")
        
        # Quality check can cycle back or end
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_gate,
            {"continue": "supervisor", "end": END}
        )
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _supervisor_node(self, state: AgentFlowState) -> AgentFlowState:
        """Supervisor with intelligent routing"""
        completed = set(state.get("agent_outputs", {}).keys())
        iteration = state.get("iteration_count", 0)
        
        # Route based on dependencies and completion
        if "cofounder" not in completed:
            state["current_agent"] = "cofounder"
        elif "manager" not in completed and "cofounder" in completed:
            state["current_agent"] = "manager"
        elif "manager" in completed:
            specialists = {"product", "finance", "marketing", "legal"}
            pending = specialists - completed
            if pending:
                state["current_agent"] = next(iter(pending))
            else:
                state["current_agent"] = "end"
        
        state["iteration_count"] = iteration + 1
        state["messages"] = state.get("messages", []) + [AIMessage(content=f"Routing to {state['current_agent']}")]
        
        await event_bus.broadcast_update("supervisor", {
            "type": "routing", "data": {"next_agent": state["current_agent"]}
        })
        return state
    
    async def _cofounder_node(self, state: AgentFlowState) -> AgentFlowState:
        return await self._execute_specialist("Cofounder", "cofounder", state)
    
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
    
    def _route_next(self, state: AgentFlowState) -> str:
        """Route to next agent"""
        return state.get("current_agent", "end")
    
    async def _quality_check_node(self, state: AgentFlowState) -> AgentFlowState:
        """Quality check with confidence scoring"""
        confidence_scores = state.get("confidence_scores", {})
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.7
        
        # Check if we need more iterations or can end
        iteration = state.get("iteration_count", 0)
        completed_agents = len(state.get("agent_outputs", {}))
        
        if avg_confidence >= 0.7 and completed_agents >= 4:
            state["quality_decision"] = "end"
        elif iteration < 3:
            state["quality_decision"] = "continue"
        else:
            state["quality_decision"] = "end"
        
        return state
    
    def _quality_gate(self, state: AgentFlowState) -> str:
        """Quality gate routing"""
        return state.get("quality_decision", "end")
    
    async def _execute_specialist(self, agent_name: str, agent_key: str, state: AgentFlowState) -> AgentFlowState:
        """Execute specialist agent with state management"""
        agent = self.agents.get(agent_name)
        if agent:
            task = {"id": f"{agent_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "context": state.get("shared_context", {})}
            result = await agent.execute(task)
            
            state["agent_outputs"][agent_key] = result
            state["confidence_scores"][agent_key] = result.get("confidence", 0.7)
            state["shared_context"][f"{agent_key}_output"] = result.get("output", {})
            
            await event_bus.broadcast_update(agent_key, {"type": "completed", "data": result})
        return state
    
    async def execute_workflow(self, initial_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute workflow with streaming and checkpointing"""
        try:
            state = AgentFlowState(
                messages=[],
                project_vision=initial_state.get("project_vision", ""),
                shared_context=initial_state.get("shared_context", {}),
                agent_outputs={},
                workflow_phase="execution",
                current_agent="",
                iteration_count=0,
                confidence_scores={},
                requires_approval=False
            )
            
            config = config or {"configurable": {"thread_id": f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}
            
            # Stream execution for real-time updates
            final_state = None
            async for chunk in self.workflow.astream(state, config=config):
                final_state = chunk
            
            return {
                "status": "completed",
                "agent_outputs": final_state.get("agent_outputs", {}),
                "iterations": final_state.get("iteration_count", 0),
                "thread_id": config["configurable"]["thread_id"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def resume_from_checkpoint(self, thread_id: str) -> Dict[str, Any]:
        """Resume workflow from checkpoint"""
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = None
        async for chunk in self.workflow.astream(None, config=config):
            final_state = chunk
            
        return {"status": "resumed", "final_state": final_state}