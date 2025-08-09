"""
Instagram and Slack Integration API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from integrations.instagram_client import InstagramClient, InstagramPost
from integrations.slack_client import SlackClient, SlackMessage, SlackNotification
from integrations.base_integration import IntegrationConfig

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Request Models
class InstagramPostRequest(BaseModel):
    content: str
    media_urls: List[str] = []
    hashtags: List[str] = []
    schedule_time: Optional[datetime] = None

class SlackNotificationRequest(BaseModel):
    channel: str
    message: str
    agent_name: str
    event_type: str
    priority: str = "normal"

class IntegrationStatusResponse(BaseModel):
    service: str
    status: str
    last_check: datetime
    error: Optional[str] = None

# Global clients (would be initialized from config)
instagram_client = None
slack_client = None

@router.post("/instagram/post")
async def create_instagram_post(request: InstagramPostRequest):
    """Create Instagram post"""
    if not instagram_client:
        raise HTTPException(status_code=503, detail="Instagram client not configured")
    
    try:
        post = InstagramPost(
            content=request.content,
            media_urls=request.media_urls,
            hashtags=request.hashtags,
            scheduled_time=request.schedule_time
        )
        
        if request.schedule_time:
            result = await instagram_client.schedule_post(post)
        else:
            result = await instagram_client.create_post(post)
        
        return {
            "success": True,
            "post_id": result.get("id"),
            "status": "posted" if not request.schedule_time else "scheduled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instagram/dms")
async def get_instagram_dms():
    """Get Instagram DM conversations"""
    if not instagram_client:
        raise HTTPException(status_code=503, detail="Instagram client not configured")
    
    try:
        conversations = await instagram_client.get_dm_conversations()
        return {
            "success": True,
            "conversations": [dm.dict() for dm in conversations],
            "count": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instagram/dm/respond")
async def respond_to_instagram_dm(conversation_id: str, message: str):
    """Respond to Instagram DM"""
    if not instagram_client:
        raise HTTPException(status_code=503, detail="Instagram client not configured")
    
    try:
        result = await instagram_client.send_dm_response(conversation_id, message)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_sent": message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slack/notify")
async def send_slack_notification(request: SlackNotificationRequest):
    """Send Slack notification"""
    if not slack_client:
        raise HTTPException(status_code=503, detail="Slack client not configured")
    
    try:
        notification = SlackNotification(
            agent_name=request.agent_name,
            event_type=request.event_type,
            message=request.message,
            priority=request.priority
        )
        
        result = await slack_client.send_agent_notification(notification)
        
        return {
            "success": True,
            "notification_sent": True,
            "channel": request.channel,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slack/message")
async def send_slack_message(channel: str, text: str, blocks: Optional[List[Dict]] = None):
    """Send custom Slack message"""
    if not slack_client:
        raise HTTPException(status_code=503, detail="Slack client not configured")
    
    try:
        message = SlackMessage(
            channel=channel,
            text=text,
            blocks=blocks
        )
        
        result = await slack_client.send_message(message)
        
        return {
            "success": True,
            "message_sent": True,
            "channel": channel,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_integration_status():
    """Get status of all integrations"""
    status_checks = []
    
    # Check Instagram
    if instagram_client:
        try:
            instagram_health = await instagram_client.health_check()
            status_checks.append(IntegrationStatusResponse(
                service="instagram",
                status=instagram_health.get("status", "unknown"),
                last_check=datetime.now(),
                error=instagram_health.get("error")
            ))
        except Exception as e:
            status_checks.append(IntegrationStatusResponse(
                service="instagram",
                status="error",
                last_check=datetime.now(),
                error=str(e)
            ))
    else:
        status_checks.append(IntegrationStatusResponse(
            service="instagram",
            status="not_configured",
            last_check=datetime.now()
        ))
    
    # Check Slack
    if slack_client:
        try:
            slack_health = await slack_client.health_check()
            status_checks.append(IntegrationStatusResponse(
                service="slack",
                status=slack_health.get("status", "unknown"),
                last_check=datetime.now(),
                error=slack_health.get("error")
            ))
        except Exception as e:
            status_checks.append(IntegrationStatusResponse(
                service="slack",
                status="error",
                last_check=datetime.now(),
                error=str(e)
            ))
    else:
        status_checks.append(IntegrationStatusResponse(
            service="slack",
            status="not_configured",
            last_check=datetime.now()
        ))
    
    return {
        "integrations": [status.dict() for status in status_checks],
        "overall_status": "healthy" if all(s.status == "healthy" for s in status_checks) else "degraded"
    }

@router.post("/configure")
async def configure_integrations(instagram_config: Optional[Dict] = None, slack_config: Optional[Dict] = None):
    """Configure integration clients"""
    global instagram_client, slack_client
    
    results = {}
    
    if instagram_config:
        try:
            config = IntegrationConfig(**instagram_config)
            instagram_client = InstagramClient(config)
            auth_result = await instagram_client.authenticate()
            results["instagram"] = {"configured": True, "authenticated": auth_result}
        except Exception as e:
            results["instagram"] = {"configured": False, "error": str(e)}
    
    if slack_config:
        try:
            config = IntegrationConfig(**slack_config)
            slack_client = SlackClient(config)
            auth_result = await slack_client.authenticate()
            results["slack"] = {"configured": True, "authenticated": auth_result}
        except Exception as e:
            results["slack"] = {"configured": False, "error": str(e)}
    
    return {"configuration_results": results}