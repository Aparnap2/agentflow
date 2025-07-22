"""
LangGraph-based Agent Orchestration System
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import asyncio
from datetime import datetime
from loguru import logger
from communication.event_bus import event_bus
import operator

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import BaseMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangGraph not available: {e}. Using fallback implementation.")
    LANGGRAPH_AVAILABLE = False
    
    # Fallback implementations
    class StateGraph:
        def __init__(self, state_schema):
            pass
        def add_node(self, name, func):
            pass
        def add_edge(self, from_node, to_node):
            pass
        def add_conditional_edges(self, from_node, condition, mapping):
            pass
        def set_entry_point(self, node):
            pass
        def compile(self, **kwargs):
            return self
    
    class MemorySaver:
        pass
    
    class BaseMessage:
        def __init__(self, content):
            self.content = content
    
    class AIMessage(BaseMessage):
        pass
    
    END = "__end__"

from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentFlowState(TypedDict):
    # Use proper message handling with add_messages reducer
    messages: Annotated[List[AnyMessage], add_messages]
    # Project context
    project_vision: str
    shared_context: Dict[str, Any]
    # Agent outputs with proper merging
    agent_outputs: Dict[str, Dict]
    # Workflow control
    workflow_phase: str
    current_agent: str
    iteration_count: int
    # Quality tracking
    confidence_scores: Dict[str, float]
    requires_approval: bool
    # Error handling and self-correction
    errors: Annotated[List[Dict[str, Any]], operator.add]
    correction_attempts: Dict[str, int]
    last_correction: Optional[str]
    # Execution tracking
    execution_path: Annotated[List[str], operator.add]

class LangGraphOrchestrator:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()
        
    def _create_workflow(self):
        """Create LangGraph workflow with cycles, self-correction, and checkpointing"""
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
        workflow.add_node("error_handler", self._error_handler_node)
        workflow.add_node("self_correction", self._self_correction_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional routing with cycles
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next,
            {"cofounder": "cofounder", "manager": "manager", "product": "product", 
             "finance": "finance", "marketing": "marketing", "legal": "legal", 
             "error_handler": "error_handler", "end": END}
        )
        
        # All agents can go to error handler on exception
        for agent in ["cofounder", "manager", "product", "finance", "marketing", "legal"]:
            # Normal flow to quality check
            workflow.add_edge(agent, "quality_check")
            
            # Add conditional edge for error handling
            workflow.add_conditional_edges(
                agent,
                self._check_for_errors,
                {"has_errors": "error_handler", "no_errors": "quality_check"}
            )
        
        # Error handler routes to self-correction
        workflow.add_edge("error_handler", "self_correction")
        
        # Self-correction routes back to supervisor
        workflow.add_edge("self_correction", "supervisor")
        
        # Quality check can cycle back or end
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_gate,
            {"continue": "supervisor", "end": END}
        )
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _supervisor_node(self, state: AgentFlowState) -> AgentFlowState:
        """Supervisor with intelligent routing, error detection, and conditional execution"""
        # Initialize state fields if not present
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        if "errors" not in state:
            state["errors"] = []
        if "correction_attempts" not in state:
            state["correction_attempts"] = {}
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
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
        
        # Route based on dependencies and completion with conditional logic
        if "cofounder" not in completed:
            next_agent = "cofounder"
        elif "manager" not in completed and "cofounder" in completed:
            next_agent = "manager"
        elif "manager" in completed:
            # Check if we need to optimize the execution order based on dependencies
            specialists = ["product", "finance", "marketing", "legal"]
            pending = [s for s in specialists if s not in completed]
            
            if pending:
                # Prioritize agents based on dependencies and confidence
                if "product" in pending and all(a not in completed for a in ["finance", "marketing"]):
                    # Product should go first as others depend on it
                    next_agent = "product"
                elif "finance" in pending and "product" in completed:
                    # Finance depends on product
                    next_agent = "finance"
                elif "marketing" in pending and "product" in completed:
                    # Marketing depends on product
                    next_agent = "marketing"
                else:
                    # Default to first pending agent
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
        from langchain_core.messages import AIMessage
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
        """Quality check with confidence scoring and self-correction triggers"""
        confidence_scores = state.get("confidence_scores", {})
        agent_outputs = state.get("agent_outputs", {})
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.7
        
        # Check if we need more iterations or can end
        iteration = state.get("iteration_count", 0)
        completed_agents = len(agent_outputs)
        
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
                    "agent": inconsistency["agents"][0],  # Use first agent as primary
                    "error": f"Inconsistency: {inconsistency['type']}",
                    "timestamp": datetime.now().isoformat(),
                    "inconsistency": inconsistency
                })
            # Continue to error handler
            state["quality_decision"] = "continue"
            return state
        
        # Make quality decision based on confidence and completeness
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
        from langchain_core.messages import AIMessage
        state["messages"].append(AIMessage(
            content=f"Quality check: confidence={avg_confidence:.2f}, decision={state['quality_decision']}"
        ))
        
        return state
    
    def _quality_gate(self, state: AgentFlowState) -> str:
        """Quality gate routing"""
        return state.get("quality_decision", "end")
    
    async def _execute_specialist(self, agent_name: str, agent_key: str, state: AgentFlowState) -> AgentFlowState:
        """Execute specialist agent with state management and error handling"""
        agent = self.agents.get(agent_name)
        if agent:
            try:
                # Initialize errors list if not present
                if "errors" not in state:
                    state["errors"] = []
                
                # Create task with context from previous agents
                task = {
                    "id": f"{agent_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                    "context": state.get("shared_context", {}),
                    "project_vision": state.get("project_vision", ""),
                    "previous_outputs": state.get("agent_outputs", {})
                }
                
                # Execute agent with timeout protection
                result = await asyncio.wait_for(
                    agent.execute(task),
                    timeout=60.0  # 60 second timeout
                )
                
                # Validate result structure
                if not isinstance(result, dict):
                    raise ValueError(f"Agent {agent_name} returned invalid result type: {type(result)}")
                
                # Check for required fields
                if "output" not in result:
                    raise ValueError(f"Agent {agent_name} result missing required 'output' field")
                
                # Store result in state
                state["agent_outputs"][agent_key] = result
                state["confidence_scores"][agent_key] = result.get("confidence", 0.7)
                state["shared_context"][f"{agent_key}_output"] = result.get("output", {})
                
                # Broadcast completion event
                await event_bus.broadcast_update(agent_key, {"type": "completed", "data": result})
                
            except Exception as e:
                # Capture error for self-correction
                error_info = {
                    "agent": agent_key,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "task_id": task["id"] if "task" in locals() else None
                }
                state["errors"].append(error_info)
                
                # Log error
                logger.error(f"Error in {agent_name} execution: {e}")
                
                # Broadcast error event
                await event_bus.broadcast_update(agent_key, {"type": "error", "data": error_info})
                
        return state
    
    async def execute_workflow(self, initial_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute workflow with streaming and checkpointing with enhanced error handling"""
        try:
            # Initialize state with proper defaults
            state = AgentFlowState(
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
                correction_attempts={},
                last_correction=None,
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
            from analytics.analytics_service import analytics_service
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
                await analytics_service.track_event(
                    event_name="workflow_execution",
                    properties={
                        "execution_time": execution_time,
                        "steps": execution_steps,
                        "agents_completed": len(final_state.get("agent_outputs", {})),
                        "errors_handled": len(final_state.get("errors", [])),
                        "success": True
                    }
                )
                
                return {
                    "status": "completed",
                    "agent_outputs": final_state.get("agent_outputs", {}),
                    "iterations": final_state.get("iteration_count", 0),
                    "thread_id": thread_id,
                    "execution_path": final_state.get("execution_path", []),
                    "errors_handled": len(final_state.get("errors", []))
                }
                
            except Exception as e:
                logger.error(f"Error during workflow execution: {e}")
                # Track workflow error
                await analytics_service.track_error(
                    error_type="workflow_execution_error",
                    recoverable=False
                )
                raise
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "thread_id": config.get("configurable", {}).get("thread_id", "unknown")
            }
    
    async def resume_from_checkpoint(self, thread_id: str) -> Dict[str, Any]:
        """Resume workflow from checkpoint"""
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = None
        async for chunk in self.workflow.astream(None, config=config):
            final_state = chunk
            
        return {"status": "resumed", "final_state": final_state}
    def _check_for_errors(self, state: AgentFlowState) -> str:
        """Check if the current execution has errors"""
        if state.get("errors", []):
            return "has_errors"
        return "no_errors"
    
    async def _error_handler_node(self, state: AgentFlowState) -> AgentFlowState:
        """Handle errors with intelligent diagnosis"""
        errors = state.get("errors", [])
        if not errors:
            return state
            
        # Process the most recent error
        latest_error = errors[-1]
        agent_name = latest_error.get("agent")
        error_msg = latest_error.get("error")
        
        logger.info(f"Error handler processing error in {agent_name}: {error_msg}")
        
        # Enhanced error categorization with role-specific handling
        error_type = self._categorize_error(error_msg)
        role_specific_handling = self._get_role_specific_error_handling(agent_name, error_msg)
            
        # Add enhanced error diagnosis to state
        latest_error["diagnosis"] = {
            "error_type": error_type,
            "severity": self._determine_error_severity(error_type, agent_name),
            "recoverable": self._is_error_recoverable(error_type, error_msg),
            "role_specific": role_specific_handling
        }
        
        # Track correction attempts
        if "correction_attempts" not in state:
            state["correction_attempts"] = {}
            
        if agent_name not in state["correction_attempts"]:
            state["correction_attempts"][agent_name] = 0
            
        state["correction_attempts"][agent_name] += 1
        
        # Add message about error
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Error detected in {agent_name}: {error_msg}. Attempting self-correction.")
        ]
        
        # Broadcast error handling event
        await event_bus.broadcast_update("error_handler", {
            "type": "error_diagnosed",
            "data": {
                "agent": agent_name,
                "error_type": error_type,
                "attempt": state["correction_attempts"][agent_name]
            }
        })
        
        return state
        
    async def _self_correction_node(self, state: AgentFlowState) -> AgentFlowState:
        """Attempt to self-correct errors"""
        if not state.get("errors", []):
            return state
            
        # Get the latest error
        latest_error = state["errors"][-1]
        agent_name = latest_error.get("agent")
        error_type = latest_error.get("diagnosis", {}).get("error_type", "unknown")
        attempt = state["correction_attempts"].get(agent_name, 0)
        
        # Check if we've tried too many times
        if attempt > 3:
            logger.warning(f"Too many correction attempts for {agent_name}, skipping agent")
            
            # Remove the agent from errors and mark as skipped
            state["errors"] = [e for e in state["errors"] if e.get("agent") != agent_name]
            state["agent_outputs"][agent_name] = {
                "status": "skipped",
                "error": latest_error.get("error"),
                "confidence": 0.0,
                "output": {"message": "Agent execution failed and was skipped after multiple attempts"}
            }
            
            # Add message about skipping
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"Skipping {agent_name} after {attempt} failed attempts.")
            ]
            
            return state
        
        # Get role-specific error handling strategy
        role_specific = latest_error.get("diagnosis", {}).get("role_specific", {})
        strategy = role_specific.get("strategy", "general")
        
        # Apply correction strategy based on role-specific handling
        logger.info(f"Applying {strategy} correction for {agent_name}")
        
        # Apply simplification if needed
        if role_specific.get("simplification", False):
            state["shared_context"][f"{agent_name}_simplified"] = True
            state["shared_context"][f"{agent_name}_simplification_strategy"] = strategy
            
        # Apply context enrichment if needed
        if role_specific.get("context_enrichment", False):
            # Add more context from other agents
            for other_agent, output in state.get("agent_outputs", {}).items():
                if other_agent != agent_name:
                    # Extract key information to help with context
                    if isinstance(output, dict) and "output" in output:
                        state["shared_context"][f"{other_agent}_context_for_{agent_name}"] = output["output"]
        
        # Apply different approach if needed
        if role_specific.get("retry_with_different_approach", False):
            state["shared_context"][f"{agent_name}_retry_approach"] = f"alternative_{attempt}"
            
        # Fallback to error type-based correction if no role-specific strategy
        if strategy == "general":
            if error_type == "timeout":
                # For timeouts, simplify the task
                logger.info(f"Applying timeout correction for {agent_name}")
                state["shared_context"][f"{agent_name}_simplified"] = True
                
            elif error_type == "key_error" or error_type == "value_error" or error_type == "json_error":
                # For data errors, provide more context
                logger.info(f"Applying data correction for {agent_name}")
                # Add more context from other agents
                for other_agent, output in state.get("agent_outputs", {}).items():
                    if other_agent != agent_name:
                        # Extract key information to help with context
                        if isinstance(output, dict) and "output" in output:
                            state["shared_context"][f"{other_agent}_context_for_{agent_name}"] = output["output"]
        
        # Remove this specific error so we can retry
        state["errors"] = [e for e in state["errors"] if e.get("agent") != agent_name]
        
        # Record the correction
        state["last_correction"] = agent_name
        
        # Add message about correction
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Applied self-correction for {agent_name} (attempt {attempt}). Retrying execution.")
        ]
        
        # Broadcast correction event
        await event_bus.broadcast_update("self_correction", {
            "type": "correction_applied",
            "data": {
                "agent": agent_name,
                "error_type": error_type,
                "attempt": attempt,
                "strategy": "simplification" if error_type == "timeout" else "context_enrichment"
            }
        })
        
        return state
        
    def _categorize_error(self, error_msg: str) -> str:
        """Categorize error based on error message with enhanced detection"""
        error_msg_lower = error_msg.lower()
        
        # Timeout errors
        if any(term in error_msg_lower for term in ["timeout", "timed out", "deadline exceeded"]):
            return "timeout"
        
        # Data structure errors
        if "key error" in error_msg_lower or "keyerror" in error_msg_lower:
            return "key_error"
        if "value error" in error_msg_lower or "valueerror" in error_msg_lower:
            return "value_error"
        if "type error" in error_msg_lower or "typeerror" in error_msg_lower:
            return "type_error"
        if "index" in error_msg_lower and "out of range" in error_msg_lower:
            return "index_error"
        
        # API and connection errors
        if any(term in error_msg_lower for term in ["api", "connection", "network", "http", "request"]):
            return "api_error"
        
        # Memory errors
        if "memory" in error_msg_lower:
            return "memory_error"
        
        # JSON parsing errors
        if "json" in error_msg_lower and any(term in error_msg_lower for term in ["parse", "decode", "invalid"]):
            return "json_error"
        
        # LLM-specific errors
        if any(term in error_msg_lower for term in ["token", "completion", "prompt", "llm"]):
            return "llm_error"
        
        # Default case
        return "general_error"
    
    def _determine_error_severity(self, error_type: str, agent_name: str) -> str:
        """Determine error severity based on error type and agent"""
        # Critical errors that block workflow
        if error_type in ["timeout", "api_error", "memory_error"]:
            return "high"
        
        # Errors that might be recoverable with context
        if error_type in ["key_error", "value_error", "json_error"]:
            return "medium"
        
        # Agent-specific severity adjustments
        if agent_name == "Cofounder" and error_type in ["llm_error"]:
            # Cofounder is critical for vision setting
            return "high"
        elif agent_name == "Manager" and error_type in ["type_error", "index_error"]:
            # Manager coordinates other agents, so structural errors are high severity
            return "high"
        
        # Default case
        return "medium"
    
    def _is_error_recoverable(self, error_type: str, error_msg: str) -> bool:
        """Determine if an error is potentially recoverable"""
        # Generally unrecoverable errors
        if "not implemented" in error_msg.lower():
            return False
        if "permission denied" in error_msg.lower():
            return False
        if "authentication failed" in error_msg.lower():
            return False
        
        # Potentially recoverable errors
        if error_type in ["timeout", "key_error", "value_error", "type_error", "index_error", "json_error"]:
            return True
        
        # Default to optimistic recovery attempt
        return True
    
    def _get_role_specific_error_handling(self, agent_name: str, error_msg: str) -> Dict[str, Any]:
        """Get role-specific error handling strategies"""
        error_handling = {
            "strategy": "general",
            "context_enrichment": False,
            "simplification": False,
            "retry_with_different_approach": False
        }
        
        # Cofounder agent error handling
        if agent_name == "Cofounder":
            if "vision" in error_msg.lower():
                error_handling["strategy"] = "vision_clarification"
                error_handling["context_enrichment"] = True
            elif "market" in error_msg.lower():
                error_handling["strategy"] = "market_research_fallback"
                error_handling["simplification"] = True
        
        # Manager agent error handling
        elif agent_name == "Manager":
            if "workflow" in error_msg.lower():
                error_handling["strategy"] = "workflow_simplification"
                error_handling["simplification"] = True
            elif "task" in error_msg.lower():
                error_handling["strategy"] = "task_restructuring"
                error_handling["retry_with_different_approach"] = True
        
        # Marketing agent error handling
        elif agent_name == "Marketing":
            if "content" in error_msg.lower():
                error_handling["strategy"] = "content_simplification"
                error_handling["simplification"] = True
            elif "seo" in error_msg.lower():
                error_handling["strategy"] = "seo_analysis_skip"
                error_handling["retry_with_different_approach"] = True
        
        # Finance agent error handling
        elif agent_name == "Finance":
            if "model" in error_msg.lower():
                error_handling["strategy"] = "financial_model_simplification"
                error_handling["simplification"] = True
            elif "calculation" in error_msg.lower():
                error_handling["strategy"] = "calculation_retry"
                error_handling["retry_with_different_approach"] = True
        
        # Legal agent error handling
        elif agent_name == "Legal":
            if "compliance" in error_msg.lower():
                error_handling["strategy"] = "compliance_check_simplification"
                error_handling["simplification"] = True
            elif "document" in error_msg.lower():
                error_handling["strategy"] = "document_generation_fallback"
                error_handling["retry_with_different_approach"] = True
        
        # Sales agent error handling
        elif agent_name == "Sales":
            if "forecast" in error_msg.lower():
                error_handling["strategy"] = "forecast_simplification"
                error_handling["simplification"] = True
            elif "pipeline" in error_msg.lower():
                error_handling["strategy"] = "pipeline_analysis_fallback"
                error_handling["retry_with_different_approach"] = True
        
        return error_handling