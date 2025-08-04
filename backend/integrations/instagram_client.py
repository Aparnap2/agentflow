"""
Instagram Business API Client
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from .base_integration import BaseIntegration, IntegrationConfig
from loguru import logger


class InstagramPost(BaseModel):
    """Instagram post data model"""
    content: str
    media_urls: List[str] = []
    hashtags: List[str] = []
    scheduled_time: Optional[datetime] = None


class InstagramDM(BaseModel):
    """Instagram DM data model"""
    conversation_id: str
    message: str
    sender_id: str
    timestamp: datetime


class InstagramClient(BaseIntegration):
    """Instagram Business API client for content and DM automation"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.account_id = None
        
    async def authenticate(self) -> bool:
        """Authenticate with Instagram Business API"""
        try:
            result = await self.make_request("GET", "/me", {"access_token": self.config.api_key})
            self.account_id = result.get("data", {}).get("id")
            logger.info("Instagram authentication successful")
            return True
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """Check Instagram API connectivity"""
        try:
            await self.make_request("GET", "/me")
            return {"status": "healthy", "service": "instagram"}
        except Exception as e:
            return {"status": "unhealthy", "service": "instagram", "error": str(e)}
            
    async def create_post(self, post: InstagramPost) -> Dict[str, Any]:
        """Create Instagram post"""
        post_data = {
            "message": post.content,
            "media_urls": post.media_urls,
            "hashtags": " ".join(f"#{tag}" for tag in post.hashtags)
        }
        
        result = await self.make_request("POST", f"/{self.account_id}/media", post_data)
        logger.info(f"Instagram post created: {result}")
        return result
        
    async def schedule_post(self, post: InstagramPost) -> Dict[str, Any]:
        """Schedule Instagram post for later"""
        post_data = {
            "message": post.content,
            "scheduled_publish_time": post.scheduled_time.timestamp() if post.scheduled_time else None
        }
        
        result = await self.make_request("POST", f"/{self.account_id}/media", post_data)
        logger.info(f"Instagram post scheduled: {result}")
        return result
        
    async def get_dm_conversations(self) -> List[InstagramDM]:
        """Get Instagram DM conversations"""
        result = await self.make_request("GET", f"/{self.account_id}/conversations")
        
        conversations = []
        for conv_data in result.get("data", []):
            dm = InstagramDM(
                conversation_id=conv_data.get("id"),
                message=conv_data.get("snippet", ""),
                sender_id=conv_data.get("participants", [{}])[0].get("id", ""),
                timestamp=datetime.now()
            )
            conversations.append(dm)
            
        return conversations
        
    async def send_dm_response(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Send automated DM response"""
        dm_data = {"message": message}
        result = await self.make_request("POST", f"/{conversation_id}/messages", dm_data)
        logger.info(f"Instagram DM sent to {conversation_id}")
        return result
        
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get Instagram post performance analytics"""
        result = await self.make_request("GET", f"/{post_id}/insights")
        return result.get("data", {})