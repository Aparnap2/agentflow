"""
Slack API Client for Notifications
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from .base_integration import BaseIntegration, IntegrationConfig
from loguru import logger


class SlackMessage(BaseModel):
    """Slack message data model"""
    channel: str
    text: str
    blocks: Optional[List[Dict]] = None
    thread_ts: Optional[str] = None


class SlackNotification(BaseModel):
    """Slack notification data model"""
    agent_name: str
    event_type: str
    message: str
    priority: str = "normal"  # low, normal, high, urgent


class SlackClient(BaseIntegration):
    """Slack API client for agent notifications"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.bot_token = config.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Slack API"""
        try:
            result = await self.make_request("GET", "/auth.test")
            logger.info("Slack authentication successful")
            return True
        except Exception as e:
            logger.error(f"Slack authentication failed: {e}")
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """Check Slack API connectivity"""
        try:
            await self.make_request("GET", "/auth.test")
            return {"status": "healthy", "service": "slack"}
        except Exception as e:
            return {"status": "unhealthy", "service": "slack", "error": str(e)}
            
    async def send_message(self, message: SlackMessage) -> Dict[str, Any]:
        """Send message to Slack channel"""
        message_data = {
            "channel": message.channel,
            "text": message.text,
            "blocks": message.blocks,
            "thread_ts": message.thread_ts
        }
        
        result = await self.make_request("POST", "/chat.postMessage", message_data)
        logger.info(f"Slack message sent to {message.channel}")
        return result
        
    async def send_agent_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Send agent status notification"""
        priority_emoji = {
            "low": "🔵",
            "normal": "🟡", 
            "high": "🟠",
            "urgent": "🔴"
        }
        
        message = SlackMessage(
            channel="#agent-updates",
            text=f"{priority_emoji.get(notification.priority, '🟡')} **{notification.agent_name}** - {notification.event_type}\n{notification.message}"
        )
        
        return await self.send_message(message)
        
    async def send_workflow_update(self, workflow_id: str, status: str, details: str) -> Dict[str, Any]:
        """Send workflow status update"""
        message = SlackMessage(
            channel="#workflow-updates",
            text=f"🔄 **Workflow {workflow_id}** - Status: {status}\n{details}"
        )
        
        return await self.send_message(message)
        
    async def send_approval_request(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send approval request with interactive buttons"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔔 **Approval Required**\nAgent: {approval_data.get('agent_name')}\nAction: {approval_data.get('action_description')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": f"approve_{approval_data.get('approval_id')}"
                    },
                    {
                        "type": "button", 
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": f"reject_{approval_data.get('approval_id')}"
                    }
                ]
            }
        ]
        
        message = SlackMessage(
            channel="#approvals",
            text="Approval Required",
            blocks=blocks
        )
        
        return await self.send_message(message)
        
    async def create_project_channel(self, project_id: str, team_members: List[str]) -> Dict[str, Any]:
        """Create dedicated Slack channel for project"""
        channel_data = {
            "name": f"project-{project_id}",
            "is_private": False
        }
        
        result = await self.make_request("POST", "/conversations.create", channel_data)
        
        # Invite team members
        if result.get("ok") and team_members:
            channel_id = result.get("channel", {}).get("id")
            invite_data = {
                "channel": channel_id,
                "users": ",".join(team_members)
            }
            await self.make_request("POST", "/conversations.invite", invite_data)
            
        logger.info(f"Project channel created: {project_id}")
        return result