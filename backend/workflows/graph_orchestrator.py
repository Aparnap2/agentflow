"""
LangGraph-based workflow orchestrator for multi-agent coordination
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated, Callable, Union, Literal
from datetime import datetime
import operator
import asyncio
import json

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from loguru import logger
from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from events.event_bus import event_bus
from agents.graph_agent import GraphAgent

class WorkflowState(TypedDict):
    """Workflow state for multi-agent orchestration"""
    messages: Annotated[List[AnyMessage], add_messages]
    project_vision: str
    shared_context: Dict[str, Any]
    agent_outputs: Dict[str, Dict]
    workflow_phase: str
    current_agent: str
    iteration_count: int
    confidence_scores: Dict[str, float]
    requires_approval: bool
    errors: Annotated[List[Dict[str, Any]], operator.add]
    execution_path: Annotated[List[str], operator.add]

class GraphOrchestrator:
    """LangGraph-based workflow orchestrator for multi-agent coordination"""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        approval_manager: ApprovalManager,
        agents: Dict[str, GraphAgent]
    ):
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.agents = agents
        
        # Create the workflow graph
        self.workflow = self._build_workflow_graph()
        logger.info(f"Initialized GraphOrchestrator with {len(agents)} agents")
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the workflow orchestration graph"""
        # Create the graph with our state schema
        builder = StateGraph(WorkflowState)
        
        # Add core nodes
        builder.add_node("supervisor", self._supervisor_node)
        builder.add_node("error_handler", self._error_handler_node)
        builder.add_node("quality_check", self._quality_check_node)
        
        # Add agent nodes
        for agent_name in self.agents:
            builder.add_node(agent_name, self._create_agent_node(agent_name))
        
        # Add end node
        builder.add_node("end", self._end_node)
        
        # Define the workflow
        builder.set_entry_point("supervisor")
        
        # Connect supervisor to all agents and error handler
        for agent_name in self.agents:
            builder.add_conditional_edges(
                "supervisor",
                lambda state, agent=agent_name: state["current_agent"] == agent,
                {True: agent, False: None}
            )
        
        builder.add_conditional_edges(
            "supervisor",
            lambda state: state["current_agent"] == "error_handler",
            {True: "error_handler", False: None}
        )
        
        builder.add_conditional_edges(
            "supervisor",
            lambda state: state["current_agent"] == "end",
            {True: "end", False: None}
        )
        
        # Connect all agents back to supervisor
        for agent_name in self.agents:
            builder.add_edge(agent_name, "quality_check")
        
        # Connect quality check to supervisor or end
        builder.add_conditional_edges(
            "quality_check",
            lambda state: state["quality_decision"] == "continue",
            {True: "supervisor", False: "end"}
        )
        
        # Connect error handler back to supervisor
        builder.add_edge("error_handler", "supervisor")
        
        # Connect end to END
        builder.add_edge("end", END)
        
        return builder.compile(checkpointer=MemorySaver())
    
    async def _supervisor_node(self, state: WorkflowState) -> WorkflowState:
        """Supervisor node for intelligent routing"""
        # Initialize state fields if not present
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        if "errors" not in state:
            state["errors"] = []
        if "execution_path" not in state:
            state["execution_path"] = []
            
        completed = set(state.get("agent_outputs", {}).keys())
        iteration = state.get("iteration_count", 0)
        errors = state.get("errors", [])
        
        # Check for errors that need handling
        if errors:
            state["current_agent"] = "error_handler"
            logger.info(f"Supervisor detected {len(errors)} errors, routing to error handler")
            state["execution_path"].append("error_handler")
            return state
        
        # Determine next agent based on dependencies and completion
        next_agent = None
        
        # Define agent execution order with dependencies
        if "cofounder" not in completed:
            next_agent = "cofounder"
        elif "manager" not in completed and "cofounder" in completed:
            next_agent = "manager"
        elif "manager" in completed:
            # Prioritize agents based on dependencies
            specialists = ["product", "finance", "marketing", "legal"]
            pending = [s for s in specialists if s not in completed]
            
            if pending:
                # Optimize execution order based on dependencies
                if "product" in pending and all(a not in completed for a in ["finance", "marketing"]):
                    next_agent = "product"
                elif "finance" in pending and "product" in completed:
                    next_agent = "finance"
                elif "marketing" in pending and "product" in completed:
                    next_agent = "marketing"
                else:
                    next_agent = pending[0]
            else:
                next_agent = "end"
        
        # Update state with next agent
        state["current_agent"] = next_agent
        state["iteration_count"] = iteration + 1
        
        # Track execution path
        if next_agent != "end":
            state["execution_path"].append(next_agent)
        
        # Add routing message
        state["messages"].append(AIMessage(content=f"Routing to {next_agent}"))
        
        # Broadcast update
        await event_bus.broadcast_update("supervisor", {
            "type": "routing", 
            "data": {
                "next_agent": next_agent,
                "iteration": iteration + 1,
                "completed_agents": list(completed),
                "execution_path": state["execution_path"]
            }
        })
        
        return state
    
    async def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors in the workflow"""
        errors = state.get("errors", [])
        
        if not errors:
            logger.warning("Error handler called but no errors found")
            return state
        
        # Process each error
        for error in errors:
            logger.info(f"Processing error: {error}")
            
            # Add error handling logic here
            # For now, just log the error
            
            # Mark error as handled
            error["handled"] = True
            error["handled_at"] = datetime.now().isoformat()
        
        # Clear errors after handling
        state["errors"] = []
        
        # Add message about error handling
        state["messages"].append(AIMessage(content="Errors have been handled"))
        
        return state
    
    async def _quality_check_node(self, state: WorkflowState) -> WorkflowState:
        """Quality check with confidence scoring and inconsistency detection"""
        confidence_scores = state.get("confidence_scores", {})
        agent_outputs = state.get("agent_outputs", {})
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.7
        
        # Check for inconsistencies between agents
        inconsistencies = []
        if "product" in agent_outputs and "marketing" in agent_outputs:
            product_data = agent_outputs["product"].get("output", {})
            marketing_data = agent_outputs["marketing"].get("output", {})
            
            # Check for product-marketing alignment
            if product_data.get("target_audience") and marketing_data.get("target_audience"):
                if product_data["target_audience"] != marketing_data["target_audience"]:
                    inconsistencies.append({
                        "type": "target_audience_mismatch",
                        "agents": ["product", "marketing"],
                        "severity": "medium"
                    })
        
        # Add inconsistencies as errors if found
        if inconsistencies:
            for inconsistency in inconsistencies:
                state["errors"].append({
                    "agent": inconsistency["agents"][0],
                    "error": f"Inconsistency: {inconsistency['type']}",
                    "timestamp": datetime.now().isoformat(),
                    "inconsistency": inconsistency
                })
            # Continue to error handler
            state["quality_decision"] = "continue"
            return state
        
        # Make quality decision based on confidence and completeness
        iteration = state.get("iteration_count", 0)
        completed_agents = len(agent_outputs)
        
        if avg_confidence >= 0.8 and completed_agents >= 4:
            # High confidence and all agents completed
            state["quality_decision"] = "end"
        elif avg_confidence < 0.6 and iteration < 5:
            # Low confidence, try more iterations
            state["quality_decision"] = "continue"
        elif iteration < 3:
            # Still early in the process
            state["quality_decision"] = "continue"
        else:
            # Default to end after sufficient iterations
            state["quality_decision"] = "end"
        
        # Add quality check message
        state["messages"].append(AIMessage(
            content=f"Quality check: confidence={avg_confidence:.2f}, decision={state['quality_decision']}"
        ))
        
        return state
    
    def _create_agent_node(self, agent_name: str) -> Callable:
        """Create a node function for an agent"""
        async def agent_node(state: WorkflowState) -> WorkflowState:
            agent = self.agents.get(agent_name)
            if not agent:
                logger.error(f"Agent {agent_name} not found")
                state["errors"].append({
                    "agent": agent_name,
                    "error": f"Agent {agent_name} not found",
                    "timestamp": datetime.now().isoformat()
                })
                return state
            
            # Prepare task for agent
            task = {
                "id": f"task_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": agent_name,
                "vision": state.get("project_vision", ""),
                "context": state.get("shared_context", {})
            }
            
            # Execute agent
            logger.info(f"Executing agent: {agent_name}")
            result = await agent.execute(task)
            
            # Update state with agent output
            state["agent_outputs"][agent_name] = result
            state["confidence_scores"][agent_name] = result.get("confidence", 0.7)
            
            # Check if approval is required
            if result.get("requires_approval", False):
                state["requires_approval"] = True
            
            # Add message about agent completion
            state["messages"].append(AIMessage(content=f"Agent {agent_name} completed task"))
            
            # Broadcast update
            await event_bus.broadcast_update(agent_name, {
                "type": "completion",
                "data": {
                    "agent": agent_name,
                    "status": result.get("status", "completed"),
                    "confidence": result.get("confidence", 0.7)
                }
            })
            
            return state
        
        return agent_node
    
    async def _end_node(self, state: WorkflowState) -> WorkflowState:
        """End node to finalize workflow"""
        # Compile final results
        final_results = {
            "agents_completed": list(state.get("agent_outputs", {}).keys()),
            "average_confidence": sum(state.get("confidence_scores", {}).values()) / len(state.get("confidence_scores", {})) if state.get("confidence_scores") else 0,
            "iterations": state.get("iteration_count", 0),
            "execution_path": state.get("execution_path", []),
            "completed_at": datetime.now().isoformat()
        }
        
        # Add final message
        state["messages"].append(AIMessage(content=f"Workflow completed with {len(final_results['agents_completed'])} agents"))
        
        # Store final results in memory
        await self.memory_manager.store_global_context("workflow_results", final_results)
        
        # Broadcast completion
        await event_bus.broadcast_update("workflow", {
            "type": "completion",
            "data": final_results
        })
        
        return state
    
    async def execute_workflow(self, initial_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute workflow with streaming and checkpointing"""
        try:
            # Initialize state with proper defaults
            state = WorkflowState(
                messages=[],
                project_vision=initial_state.get("project_vision", ""),
                shared_context=initial_state.get("shared_context", {}),
                agent_outputs={},
                workflow_phase="execution",
                current_agent="",
                iteration_count=0,
                confidence_scores={},
                requires_approval=False,
                errors=[],
                execution_path=[]
            )
            
            # Set up configuration with thread_id and recursion limit
            thread_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            config = config or {}
            if "configurable" not in config:
                config["configurable"] = {}
            config["configurable"]["thread_id"] = thread_id
            
            # Set recursion limit to prevent infinite loops
            if "recursion_limit" not in config:
                config["recursion_limit"] = 30  # Higher limit for complex workflows
            
            # Track execution start for analytics
            start_time = datetime.now()
            
            # Stream execution for real-time updates with progress tracking
            final_state = None
            execution_steps = 0
            
            try:
                async for chunk in self.workflow.astream(state, config=config):
                    final_state = chunk
                    execution_steps += 1
                    
                    # Broadcast progress update every 5 steps
                    if execution_steps % 5 == 0:
                        await event_bus.broadcast_update("workflow_progress", {
                            "type": "progress_update",
                            "data": {
                                "steps": execution_steps,
                                "current_agent": final_state.get("current_agent", ""),
                                "completed_agents": list(final_state.get("agent_outputs", {}).keys())
                            }
                        })
                
                # Track successful execution
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "status": "completed",
                    "agent_outputs": final_state.get("agent_outputs", {}),
                    "iterations": final_state.get("iteration_count", 0),
                    "thread_id": thread_id,
                    "execution_path": final_state.get("execution_path", []),
                    "errors_handled": len(final_state.get("errors", [])),
                    "execution_time": execution_time
                }
                
            except Exception as e:
                logger.error(f"Error during workflow execution: {e}")
                raise
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "thread_id": config.get("configurable", {}).get("thread_id", "unknown")
            }