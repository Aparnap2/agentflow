from typing import Dict, List, Any, Optional
import uuid
import json
from datetime import datetime
from enum import Enum
from loguru import logger
import redis
import os

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EDITED = "edited"

class ApprovalManager:
    """Manages human-in-the-loop approvals as specified in PRD"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.pending_approvals = {}
        
    async def create_approval_request(self, agent_name: str, action_type: str, 
                                    content: Dict[str, Any], reason: str) -> str:
        """Create new approval request"""
        approval_id = str(uuid.uuid4())
        
        approval_data = {
            "id": approval_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "content": content,
            "reason": reason,
            "status": ApprovalStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": None
        }
        
        # Store in Redis for real-time access
        self.redis_client.setex(
            f"approval:{approval_id}",
            3600,  # 1 hour TTL
            json.dumps(approval_data)
        )
        
        # Add to pending list
        self.redis_client.lpush("pending_approvals", approval_id)
        
        logger.info(f"Created approval request {approval_id} for {agent_name}")
        return approval_id
    
    async def handle_response(self, approval_id: str, action: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Handle approval response from user"""
        approval_data = self.redis_client.get(f"approval:{approval_id}")
        if not approval_data:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval = json.loads(approval_data)
        approval["status"] = action
        approval["feedback"] = feedback
        approval["updated_at"] = datetime.now().isoformat()
        
        # Update in Redis
        self.redis_client.setex(
            f"approval:{approval_id}",
            3600,
            json.dumps(approval)
        )
        
        # Remove from pending list
        self.redis_client.lrem("pending_approvals", 0, approval_id)
        
        # Process the response
        result = await self._process_approval_response(approval, action, feedback)
        
        logger.info(f"Processed approval {approval_id} with action: {action}")
        return result
    
    async def _process_approval_response(self, approval: Dict[str, Any], 
                                       action: str, feedback: Optional[str]) -> Dict[str, Any]:
        """Process the approval response and take appropriate action"""
        agent_name = approval["agent_name"]
        content = approval["content"]
        
        if action == "approve":
            # Store approved content in shared memory
            from memory.graph_memory import GraphMemory
            memory = GraphMemory()
            await memory.write_shared_memory(
                agent_name=agent_name,
                memory_type=f"{agent_name.lower()}_approved",
                content=content,
                confidence=1.0
            )
            return {"status": "approved", "content": content}
        
        elif action == "deny":
            logger.warning(f"Approval {approval['id']} denied: {feedback}")
            return {"status": "denied", "reason": feedback}
        
        elif action == "edit":
            # Return content for editing
            return {"status": "edit_requested", "content": content, "feedback": feedback}
        
        elif action == "retry":
            # Signal agent to retry
            return {"status": "retry_requested", "feedback": feedback}
        
        else:
            raise ValueError(f"Unknown approval action: {action}")
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        pending_ids = self.redis_client.lrange("pending_approvals", 0, -1)
        approvals = []
        
        for approval_id in pending_ids:
            approval_data = self.redis_client.get(f"approval:{approval_id.decode()}")
            if approval_data:
                approvals.append(json.loads(approval_data))
        
        return approvals
    
    async def get_approval_history(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get approval history, optionally filtered by agent"""
        # In a real implementation, this would query a persistent store
        # For now, return empty list as Redis data is temporary
        return []
    
    def check_approval_required(self, agent_name: str, action_type: str) -> bool:
        """Check if approval is required for this agent/action combination"""
        # Load approval configuration
        approval_config = self._load_approval_config()
        
        agent_config = approval_config.get(f"{agent_name.lower()}_agent", {})
        return agent_config.get(action_type, "auto") == "manual"
    
    def _load_approval_config(self) -> Dict[str, Any]:
        """Load approval configuration from file or environment"""
        # Default configuration matching PRD example
        default_config = {
            "finance_agent": {
                "api_calls": "manual",
                "memory_write": "manual"
            },
            "marketing_agent": {
                "api_calls": "auto",
                "memory_write": "auto"
            },
            "product_agent": {
                "api_calls": "auto",
                "memory_write": "manual"
            },
            "legal_agent": {
                "api_calls": "manual",
                "memory_write": "manual"
            },
            "cofounder_agent": {
                "api_calls": "auto",
                "memory_write": "auto"
            },
            "manager_agent": {
                "api_calls": "auto",
                "memory_write": "auto"
            }
        }
        
        # Try to load from file
        config_path = "/home/aparna/Desktop/agentflow/data/approval_config.yml"
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        return default_config