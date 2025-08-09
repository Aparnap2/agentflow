"""
HITL-Enhanced LangGraph Orchestrator with Explicit Interrupts
Implements PRD-compliant Human-in-the-Loop patterns
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
    from langgraph.graph.message import add_messages
    from langchain_core.messages import AnyMessage
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangGraph not available: {e}. Using fallback implementation.")
    LANGGRAPH_AVAILABLE = False

from database.supabase_db import supabase_db

class HITLAgentFlowState(TypedDict):
    """Enhanced state with HITL checkpoints"""
    # Core workflow state
    messages: Annotated[List[AnyMessage], add_messages]
    project_vision: str
    shared_context: Dict[str, Any]
    agent_outputs: Dict[str, Dict]
    workflow_phase: str
    current_agent: str
    iteration_count: int
    confidence_scores: Dict[str, float]
    
    # HITL-specific state
    pending_approvals: Annotated[List[Dict[str, Any]], operator.add]
    approval_checkpoints: Dict[str, str]  # agent -> checkpoint_id
    human_feedback: Dict[str, Any]
    requires_approval: bool
    approval_timeout: Optional[str]
    
    # Execution tracking
    errors: Annotated[List[Dict[str, Any]], operator.add]
    correction_attempts: Dict[str, int]
    execution_path: Annotated[List[str], operator.add]
    
    # Workspace context
    workspace_id: str
    user_id: str

class HITLLangGraphOrchestrator:
    """LangGraph orchestrator with explicit HITL interrupts"""
    
    def __init__(self, agents: Dict[str, Any], workspace_id: str):
        self.agents = agents
        self.workspace_id = workspace_id
        self.memory = MemorySaver()
        self.workflow = self._create_hitl_workflow()
        
        # HITL configuration per agent
        self.hitl_config = {
            "Executive_Advisor": {
                "requires_approval": ["strategic_decisions", "budget_allocation"],
                "auto_approve_threshold": 0.9
            },
            "Chief_of_Staff": {
                "requires_approval": ["workflow_changes", "priority_updates"],
                "auto_approve_threshold": 0.8
            },
            "Marketing_Intelligence": {
                "requires_approval": ["instagram_posts", "dm_responses", "campaign_launches"],
                "auto_approve_threshold": 0.7
            },
            "Customer_Success": {
                "requires_approval": ["crm_stage_moves", "customer_communications"],
                "auto_approve_threshold": 0.8
            },
            "Financial_Operations": {
                "requires_approval": ["invoice_generation", "pricing_changes", "contracts"],
                "auto_approve_threshold": 0.9
            },
            "Business_Intelligence": {
                "requires_approval": ["market_reports", "competitor_analysis"],
                "auto_approve_threshold": 0.7
            }
        }
    
    def _create_hitl_workflow(self):
        """Create LangGraph workflow with HITL interrupt nodes"""
        workflow = StateGraph(HITLAgentFlowState)
        
        # Core agent nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("executive_advisor", self._executive_advisor_node)
        workflow.add_node("chief_of_staff", self._chief_of_staff_node)
        workflow.add_node("marketing_intelligence", self._marketing_intelligence_node)
        workflow.add_node("customer_success", self._customer_success_node)
        workflow.add_node("financial_operations", self._financial_operations_node)
        workflow.add_node("business_intelligence", self._business_intelligence_node)
        
        # HITL interrupt nodes - placed BEFORE side effects
        workflow.add_node("hitl_checkpoint", self._hitl_checkpoint_node)
        workflow.add_node("approval_gate", self._approval_gate_node)
        workflow.add_node("side_effects_executor", self._side_effects_executor_node)
        
        # Error handling
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Routing with HITL checkpoints
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next,
            {
                "executive_advisor": "executive_advisor",
                "chief_of_staff": "chief_of_staff", 
                "marketing_intelligence": "marketing_intelligence",
                "customer_success": "customer_success",
                "financial_operations": "financial_operations",
                "business_intelligence": "business_intelligence",
                "end": END
            }
        )
        
        # All agents go to HITL checkpoint BEFORE side effects
        for agent in ["executive_advisor", "chief_of_staff", "marketing_intelligence", 
                     "customer_success", "financial_operations", "business_intelligence"]:
            workflow.add_edge(agent, "hitl_checkpoint")
        
        # HITL checkpoint routes to approval gate or side effects
        workflow.add_conditional_edges(
            "hitl_checkpoint",
            self._hitl_routing,
            {
                "needs_approval": "approval_gate",
                "execute_directly": "side_effects_executor",
                "error": "error_handler"
            }
        )
        
        # Approval gate - INTERRUPT HERE for human input
        workflow.add_conditional_edges(
            "approval_gate",
            self._approval_routing,
            {
                "approved": "side_effects_executor",
                "rejected": "supervisor",
                "timeout": "error_handler"
            }
        )
        
        # Side effects executor back to supervisor
        workflow.add_edge("side_effects_executor", "supervisor")
        workflow.add_edge("error_handler", "supervisor")
        
        # Compile with checkpointer and interrupts
        return workflow.compile(
            checkpointer=self.memory,
            interrupt_before=["approval_gate"],  # Explicit interrupt for HITL
            interrupt_after=["side_effects_executor"]  # Checkpoint after side effects
        )
    
    async def _supervisor_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Enhanced supervisor with HITL awareness"""
        # Initialize HITL state if needed
        if "pending_approvals" not in state:
            state["pending_approvals"] = []
        if "approval_checkpoints" not in state:
            state["approval_checkpoints"] = {}
        if "human_feedback" not in state:
            state["human_feedback"] = {}
        
        completed = set(state.get("agent_outputs", {}).keys())
        
        # Route based on PRD agent priorities
        next_agent = None
        
        if "executive_advisor" not in completed:
            next_agent = "executive_advisor"  # Strategic decisions first
        elif "chief_of_staff" not in completed and "executive_advisor" in completed:
            next_agent = "chief_of_staff"  # Orchestration second
        elif "chief_of_staff" in completed:
            # Parallel execution of specialists
            specialists = ["marketing_intelligence", "customer_success", 
                         "financial_operations", "business_intelligence"]
            pending = [s for s in specialists if s not in completed]
            
            if pending:
                # Prioritize based on dependencies
                if "financial_operations" in pending:
                    next_agent = "financial_operations"  # Financial foundation
                elif "marketing_intelligence" in pending:
                    next_agent = "marketing_intelligence"  # Customer-facing
                elif "customer_success" in pending:
                    next_agent = "customer_success"  # Retention focus
                else:
                    next_agent = pending[0]
            else:
                next_agent = "end"
        
        state["current_agent"] = next_agent
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        if next_agent != "end":
            state["execution_path"].append(next_agent)
        
        # Add routing message
        state["messages"].append(AIMessage(content=f"HITL Supervisor routing to {next_agent}"))
        
        return state
    
    async def _hitl_checkpoint_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """HITL checkpoint - determine if approval needed"""
        current_agent = state.get("current_agent", "")
        agent_output = state.get("agent_outputs", {}).get(current_agent, {})
        confidence = state.get("confidence_scores", {}).get(current_agent, 0.7)
        
        # Check if this agent/action requires approval
        config = self.hitl_config.get(current_agent, {})
        requires_approval = False
        approval_reason = ""
        
        # Check confidence threshold
        if confidence < config.get("auto_approve_threshold", 0.8):
            requires_approval = True
            approval_reason = f"Low confidence ({confidence:.2f})"
        
        # Check for sensitive actions
        output_data = agent_output.get("output", {})
        if current_agent == "Marketing_Intelligence":
            if any(key in output_data for key in ["instagram_post", "dm_response", "campaign"]):
                requires_approval = True
                approval_reason = "Instagram/Marketing content requires approval"
        
        elif current_agent == "Financial_Operations":
            if any(key in output_data for key in ["invoice", "pricing", "contract", "budget"]):
                requires_approval = True
                approval_reason = "Financial decision requires approval"
        
        elif current_agent == "Customer_Success":
            if any(key in output_data for key in ["crm_update", "stage_move", "customer_email"]):
                requires_approval = True
                approval_reason = "CRM/Customer action requires approval"
        
        # Set approval requirement
        state["requires_approval"] = requires_approval
        
        if requires_approval:
            # Create approval request
            approval_request = {
                "agent_name": current_agent,
                "action_type": "agent_execution",
                "action_description": approval_reason,
                "payload": {
                    "agent_output": agent_output,
                    "confidence": confidence,
                    "context": state.get("shared_context", {})
                },
                "reasoning": approval_reason
            }
            
            # Store in database
            approval_record = await supabase_db.create_approval_request(
                state["workspace_id"], approval_request
            )
            
            state["pending_approvals"].append(approval_record)
            state["approval_checkpoints"][current_agent] = approval_record.get("id", "")
            
            logger.info(f"HITL checkpoint: {current_agent} requires approval - {approval_reason}")
        
        state["messages"].append(AIMessage(
            content=f"HITL checkpoint: {current_agent} - {'Requires approval' if requires_approval else 'Auto-approved'}"
        ))
        
        return state
    
    async def _approval_gate_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Approval gate - INTERRUPT point for human decision"""
        current_agent = state.get("current_agent", "")
        
        # This is where the workflow will interrupt and wait for human input
        # The human will provide approval through the API
        
        state["messages"].append(AIMessage(
            content=f"⏸️ WORKFLOW INTERRUPTED: Waiting for human approval for {current_agent}"
        ))
        
        # Send Slack notification for approval
        await self._send_slack_approval_notification(state)
        
        return state
    
    async def _side_effects_executor_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Execute side effects AFTER approval"""
        current_agent = state.get("current_agent", "")
        agent_output = state.get("agent_outputs", {}).get(current_agent, {})
        
        # Execute side effects based on agent type
        if current_agent == "Marketing_Intelligence":
            await self._execute_marketing_side_effects(state, agent_output)
        elif current_agent == "Financial_Operations":
            await self._execute_financial_side_effects(state, agent_output)
        elif current_agent == "Customer_Success":
            await self._execute_crm_side_effects(state, agent_output)
        
        # Log audit event
        await supabase_db.log_audit_event(
            workspace_id=state["workspace_id"],
            user_id=state["user_id"],
            agent=current_agent,
            action="side_effects_executed",
            details={"output": agent_output},
            sensitive=True
        )
        
        state["messages"].append(AIMessage(
            content=f"✅ Side effects executed for {current_agent}"
        ))
        
        return state
    
    def _hitl_routing(self, state: HITLAgentFlowState) -> str:
        """Route based on HITL requirements"""
        if state.get("requires_approval", False):
            return "needs_approval"
        return "execute_directly"
    
    def _approval_routing(self, state: HITLAgentFlowState) -> str:
        """Route based on approval status"""
        # This will be set by the resume_with_approval method
        approval_status = state.get("human_feedback", {}).get("approval_status")
        
        if approval_status == "approved":
            return "approved"
        elif approval_status == "rejected":
            return "rejected"
        else:
            return "timeout"
    
    def _route_next(self, state: HITLAgentFlowState) -> str:
        """Route to next agent"""
        return state.get("current_agent", "end")
    
    async def _send_slack_approval_notification(self, state: HITLAgentFlowState):
        """Send Slack notification for approval"""
        try:
            # Import here to avoid circular imports
            from integrations.slack_client import SlackClient, SlackMessage
            from integrations.base_integration import IntegrationConfig
            
            # Get Slack config (would be from workspace settings)
            slack_config = IntegrationConfig(
                api_key=os.getenv("SLACK_BOT_TOKEN", ""),
                base_url="https://slack.com/api"
            )
            
            if slack_config.api_key:
                slack_client = SlackClient(slack_config)
                
                current_agent = state.get("current_agent", "")
                approval_id = state.get("approval_checkpoints", {}).get(current_agent, "")
                
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🔔 **HITL Approval Required**\nAgent: {current_agent}\nWorkflow paused for human decision"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Approve"},
                                "style": "primary",
                                "action_id": f"hitl_approve_{approval_id}"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Reject"},
                                "style": "danger", 
                                "action_id": f"hitl_reject_{approval_id}"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Request Changes"},
                                "action_id": f"hitl_changes_{approval_id}"
                            }
                        ]
                    }
                ]
                
                message = SlackMessage(
                    channel="#hitl-approvals",
                    text="HITL Approval Required",
                    blocks=blocks
                )
                
                await slack_client.send_message(message)
                
        except Exception as e:
            logger.error(f"Failed to send Slack approval notification: {e}")
    
    async def resume_with_approval(self, thread_id: str, approval_status: str, 
                                 feedback: str = "") -> Dict[str, Any]:
        """Resume workflow after human approval"""
        try:
            # Get current state
            config = {"configurable": {"thread_id": thread_id}}
            
            # Update state with human feedback
            human_feedback = {
                "approval_status": approval_status,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            }
            
            # Resume workflow with updated state
            final_state = None
            async for chunk in self.workflow.astream(
                {"human_feedback": human_feedback}, 
                config=config
            ):
                final_state = chunk
            
            return {
                "status": "resumed",
                "approval_status": approval_status,
                "final_state": final_state
            }
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return {"status": "error", "error": str(e)}
    
    # Agent execution methods (mapped to existing agents)
    async def _executive_advisor_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Executive Advisor (maps to Cofounder agent)"""
        return await self._execute_mapped_agent("Cofounder", "executive_advisor", state)
    
    async def _chief_of_staff_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Chief of Staff (maps to Manager agent)"""
        return await self._execute_mapped_agent("Manager", "chief_of_staff", state)
    
    async def _marketing_intelligence_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Marketing Intelligence (maps to Marketing agent)"""
        return await self._execute_mapped_agent("Marketing", "marketing_intelligence", state)
    
    async def _customer_success_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Customer Success (maps to Sales agent)"""
        return await self._execute_mapped_agent("Sales", "customer_success", state)
    
    async def _financial_operations_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Financial Operations (maps to Finance agent)"""
        return await self._execute_mapped_agent("Finance", "financial_operations", state)
    
    async def _business_intelligence_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Business Intelligence (new agent or enhanced existing)"""
        return await self._execute_mapped_agent("Manager", "business_intelligence", state)
    
    async def _execute_mapped_agent(self, agent_name: str, state_key: str, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Execute existing agent mapped to PRD role"""
        agent = self.agents.get(agent_name)
        if agent:
            try:
                task = {
                    "id": f"{state_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "context": state.get("shared_context", {}),
                    "project_vision": state.get("project_vision", ""),
                    "previous_outputs": state.get("agent_outputs", {})
                }
                
                result = await asyncio.wait_for(agent.execute(task), timeout=60.0)
                
                state["agent_outputs"][state_key] = result
                state["confidence_scores"][state_key] = result.get("confidence", 0.7)
                state["shared_context"][f"{state_key}_output"] = result.get("output", {})
                
                # Broadcast completion
                await event_bus.broadcast_update(state_key, {"type": "completed", "data": result})
                
            except Exception as e:
                error_info = {
                    "agent": state_key,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                state["errors"].append(error_info)
                logger.error(f"Error in {state_key} execution: {e}")
        
        return state
    
    async def _error_handler_node(self, state: HITLAgentFlowState) -> HITLAgentFlowState:
        """Handle errors in HITL context"""
        errors = state.get("errors", [])
        if errors:
            latest_error = errors[-1]
            logger.error(f"HITL Error Handler: {latest_error}")
            
            # Send error notification
            await event_bus.broadcast_update("hitl_error", {
                "type": "error_in_hitl_workflow",
                "data": latest_error
            })
        
        return state
    
    async def _execute_marketing_side_effects(self, state: HITLAgentFlowState, agent_output: Dict[str, Any]):
        """Execute marketing side effects (Instagram posts, DMs)"""
        output_data = agent_output.get("output", {})
        
        if "instagram_post" in output_data:
            # Execute Instagram post
            logger.info("Executing Instagram post side effect")
            # Implementation would call Instagram API
        
        if "dm_response" in output_data:
            # Execute DM response with compliance check
            logger.info("Executing Instagram DM response side effect")
            # Implementation would call Instagram DM API with 24-hour rule check
    
    async def _execute_financial_side_effects(self, state: HITLAgentFlowState, agent_output: Dict[str, Any]):
        """Execute financial side effects (invoices, contracts)"""
        output_data = agent_output.get("output", {})
        
        if "invoice" in output_data:
            logger.info("Executing invoice generation side effect")
            # Implementation would generate and send invoice
    
    async def _execute_crm_side_effects(self, state: HITLAgentFlowState, agent_output: Dict[str, Any]):
        """Execute CRM side effects (HubSpot updates)"""
        output_data = agent_output.get("output", {})
        
        if "crm_update" in output_data:
            logger.info("Executing CRM update side effect")
            # Implementation would call HubSpot API