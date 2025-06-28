import uuid
from typing import Dict, Any, List, Optional
from loguru import logger

# Singleton pattern to share state across the application
_instance = None

class ApprovalManager:
    def __new__(cls):
        global _instance
        if _instance is None:
            _instance = super(ApprovalManager, cls).__new__(cls)
            # Initialize in-memory storage for pending requests
            _instance.pending_requests: Dict[str, Dict[str, Any]] = {}
            logger.info("Initialized ApprovalManager singleton")
        return _instance

    async def create_approval_request(self, agent_name: str, action_type: str, content: Any, reason: str) -> str:
        """Creates and stores a new approval request."""
        request_id = str(uuid.uuid4())
        self.pending_requests[request_id] = {
            "id": request_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "content": content,
            "reason": reason,
            "status": "pending"
        }
        logger.info(f"Created approval request {request_id} for {agent_name}")
        return request_id

    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Gets all requests with 'pending' status."""
        return [req for req in self.pending_requests.values() if req["status"] == "pending"]

    async def handle_response(self, request_id: str, action: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Updates the status of an approval request based on user response."""
        if request_id not in self.pending_requests:
            logger.error(f"Approval request {request_id} not found.")
            raise ValueError(f"Approval request {request_id} not found.")
        
        request = self.pending_requests[request_id]
        request["status"] = action
        request["feedback"] = feedback
        
        logger.info(f"Handled response for approval {request_id} with action: {action}")
        return request