"""
Advanced Approval System with granular controls and confidence-based automation
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ApprovalType(Enum):
    API_CALL = "api_call"
    MEMORY_WRITE = "memory_write"
    EXTERNAL_COMMUNICATION = "external_communication"
    BUDGET_DECISION = "budget_decision"
    DOCUMENT_PUBLISHING = "document_publishing"
    TOOL_EXECUTION = "tool_execution"

@dataclass
class ApprovalConfig:
    """Granular approval configuration per agent and action type"""
    api_calls: Literal["auto", "manual"] = "auto"
    memory_write: Literal["auto", "manual"] = "auto"
    external_communication: Literal["auto", "manual"] = "manual"
    budget_decisions: Literal["auto", "manual"] = "manual"
    document_publishing: Literal["auto", "manual"] = "manual"
    tool_execution: Literal["auto", "manual"] = "auto"
    confidence_threshold: float = 0.7
    auto_approve_below_threshold: bool = False

@dataclass
class ApprovalRequest:
    """Enhanced approval request with context and confidence"""
    id: str
    agent_name: str
    approval_type: ApprovalType
    action_description: str
    context: Dict[str, Any]
    confidence_score: float
    risk_level: Literal["low", "medium", "high"]
    estimated_impact: str
    requires_human: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    auto_approved: bool = False
    reasoning: str = ""

class AdvancedApprovalManager:
    """Enhanced approval manager with confidence-based automation"""
    
    def __init__(self):
        self.agent_configs: Dict[str, ApprovalConfig] = {}
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[Dict[str, Any]] = []
        
        # Default configurations per agent type
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default approval configurations for each agent"""
        
        # Cofounder - High autonomy for vision work
        self.agent_configs["Cofounder"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.6,
            auto_approve_below_threshold=True
        )
        
        # Manager - Balanced approach
        self.agent_configs["Manager"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.7
        )
        
        # Product - User-focused decisions need approval
        self.agent_configs["Product"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.7
        )
        
        # Finance - High threshold for financial decisions
        self.agent_configs["Finance"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",  # Always manual for budget
            document_publishing="manual",  # Financial docs need review
            confidence_threshold=0.9
        )
        
        # Marketing - Creative freedom with oversight
        self.agent_configs["Marketing"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",  # External comms need approval
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.6
        )
        
        # Legal - Strict approval requirements
        self.agent_configs["Legal"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",
            document_publishing="manual",  # Legal docs always need review
            confidence_threshold=0.95
        )
        
        # Sales - Customer interaction needs oversight
        self.agent_configs["Sales"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",  # Customer comms need approval
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.7
        )
        
        # Operations - Process changes need approval
        self.agent_configs["Operations"] = ApprovalConfig(
            api_calls="auto",
            memory_write="auto",
            external_communication="manual",
            budget_decisions="manual",
            document_publishing="auto",
            confidence_threshold=0.8
        )
    
    async def request_approval(self, 
                             agent_name: str,
                             approval_type: ApprovalType,
                             action_description: str,
                             context: Dict[str, Any],
                             confidence_score: float) -> ApprovalRequest:
        """Request approval with confidence-based automation"""
        
        config = self.agent_configs.get(agent_name, ApprovalConfig())
        
        # Determine if approval is needed
        requires_human = self._requires_human_approval(
            config, approval_type, confidence_score
        )
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(approval_type, confidence_score, context)
        
        # Create approval request
        request = ApprovalRequest(
            id=f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_name}",
            agent_name=agent_name,
            approval_type=approval_type,
            action_description=action_description,
            context=context,
            confidence_score=confidence_score,
            risk_level=risk_level,
            estimated_impact=self._estimate_impact(approval_type, context),
            requires_human=requires_human,
            created_at=datetime.now(),
            reasoning=self._generate_reasoning(config, approval_type, confidence_score)
        )
        
        # Auto-approve if conditions are met
        if not requires_human:
            request.auto_approved = True
            self._log_approval_decision(request, "auto_approved", "Confidence threshold met")
            return request
        
        # Store for human approval
        self.pending_requests[request.id] = request
        return request
    
    def _requires_human_approval(self, 
                               config: ApprovalConfig,
                               approval_type: ApprovalType,
                               confidence_score: float) -> bool:
        """Determine if human approval is required"""
        
        # Check type-specific configuration
        type_config = getattr(config, approval_type.value, "manual")
        if type_config == "manual":
            return True
        
        # Check confidence threshold
        if confidence_score < config.confidence_threshold:
            return not config.auto_approve_below_threshold
        
        return False
    
    def _calculate_risk_level(self, 
                            approval_type: ApprovalType,
                            confidence_score: float,
                            context: Dict[str, Any]) -> Literal["low", "medium", "high"]:
        """Calculate risk level for the action"""
        
        # High risk actions
        if approval_type in [ApprovalType.BUDGET_DECISION, ApprovalType.EXTERNAL_COMMUNICATION]:
            return "high"
        
        # Medium risk based on confidence
        if confidence_score < 0.5:
            return "high"
        elif confidence_score < 0.7:
            return "medium"
        
        return "low"
    
    def _estimate_impact(self, approval_type: ApprovalType, context: Dict[str, Any]) -> str:
        """Estimate the impact of the action"""
        impact_map = {
            ApprovalType.API_CALL: "Low - API call execution",
            ApprovalType.MEMORY_WRITE: "Medium - Updates shared knowledge",
            ApprovalType.EXTERNAL_COMMUNICATION: "High - External stakeholder communication",
            ApprovalType.BUDGET_DECISION: "High - Financial commitment",
            ApprovalType.DOCUMENT_PUBLISHING: "Medium - Public document creation",
            ApprovalType.TOOL_EXECUTION: "Low - Tool execution"
        }
        return impact_map.get(approval_type, "Medium - Standard action")
    
    def _generate_reasoning(self, 
                          config: ApprovalConfig,
                          approval_type: ApprovalType,
                          confidence_score: float) -> str:
        """Generate reasoning for approval decision"""
        
        if confidence_score >= config.confidence_threshold:
            return f"High confidence ({confidence_score:.2f}) meets threshold ({config.confidence_threshold})"
        else:
            return f"Low confidence ({confidence_score:.2f}) below threshold ({config.confidence_threshold})"
    
    def _log_approval_decision(self, request: ApprovalRequest, decision: str, reason: str):
        """Log approval decision for audit trail"""
        self.approval_history.append({
            "request_id": request.id,
            "agent_name": request.agent_name,
            "approval_type": request.approval_type.value,
            "decision": decision,
            "reason": reason,
            "confidence_score": request.confidence_score,
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.pending_requests.values())
    
    async def handle_approval_response(self, 
                                     request_id: str,
                                     approved: bool,
                                     feedback: Optional[str] = None) -> Dict[str, Any]:
        """Handle human approval response"""
        
        if request_id not in self.pending_requests:
            return {"error": "Approval request not found"}
        
        request = self.pending_requests[request_id]
        decision = "approved" if approved else "denied"
        
        # Log decision
        self._log_approval_decision(request, decision, feedback or "Human decision")
        
        # Remove from pending
        del self.pending_requests[request_id]
        
        return {
            "status": "success",
            "decision": decision,
            "request_id": request_id,
            "feedback": feedback
        }
    
    def get_agent_config(self, agent_name: str) -> ApprovalConfig:
        """Get approval configuration for an agent"""
        return self.agent_configs.get(agent_name, ApprovalConfig())
    
    def update_agent_config(self, agent_name: str, config: ApprovalConfig):
        """Update approval configuration for an agent"""
        self.agent_configs[agent_name] = config
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval system statistics"""
        total_requests = len(self.approval_history)
        auto_approved = sum(1 for h in self.approval_history if h["decision"] == "auto_approved")
        manually_approved = sum(1 for h in self.approval_history if h["decision"] == "approved")
        denied = sum(1 for h in self.approval_history if h["decision"] == "denied")
        
        return {
            "total_requests": total_requests,
            "auto_approved": auto_approved,
            "manually_approved": manually_approved,
            "denied": denied,
            "pending": len(self.pending_requests),
            "auto_approval_rate": auto_approved / total_requests if total_requests > 0 else 0
        }