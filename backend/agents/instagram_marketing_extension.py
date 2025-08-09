"""
Instagram Marketing Extension for Marketing Agent
"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

# Import integrations with fallback
try:
    from integrations.instagram_client import InstagramClient, InstagramPost
    from integrations.slack_client import SlackClient, SlackNotification
except ImportError:
    logger.warning("Instagram/Slack integrations not available")
    InstagramClient = None
    InstagramPost = None
    SlackClient = None
    SlackNotification = None


class InstagramMarketingMixin:
    """Mixin to add Instagram capabilities to Marketing Agent - Following PRD Architecture"""
    
    def init_instagram_integration(self, instagram_config=None, slack_config=None):
        """Initialize Instagram and Slack clients as per PRD specifications"""
        from integrations.base_integration import IntegrationConfig
        
        if instagram_config:
            config = IntegrationConfig(**instagram_config) if isinstance(instagram_config, dict) else instagram_config
            self.instagram_client = InstagramClient(config)
        else:
            self.instagram_client = None
            
        if slack_config:
            config = IntegrationConfig(**slack_config) if isinstance(slack_config, dict) else slack_config
            self.slack_client = SlackClient(config)
        else:
            self.slack_client = None
        
        # Initialize automation features as per PRD
        self.automation_features = {
            "instagram_posts": "scheduled_content_publishing",
            "dm_responses": "auto_reply_with_context",
            "story_management": "automated_story_posting",
            "hashtag_optimization": "ai_powered_hashtag_selection"
        }
    
    async def create_instagram_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create and schedule Instagram post with enhanced automation features"""
        if not self.instagram_client:
            return {"error": "Instagram client not initialized", "success": False}
            
        content = params.get("content", "")
        media_urls = params.get("media_urls", [])
        hashtags = params.get("hashtags", [])
        scheduled_time = params.get("scheduled_time")
        
        try:
            # AI-powered hashtag optimization if not provided
            if not hashtags and hasattr(self, '_optimize_hashtags'):
                hashtag_result = await self._optimize_hashtags({"content": content})
                if hashtag_result.get("success"):
                    hashtags = hashtag_result.get("optimized_hashtags", [])
            
            post = InstagramPost(
                content=content,
                media_urls=media_urls,
                hashtags=hashtags,
                scheduled_time=scheduled_time
            )
            
            # Use scheduled posting if time provided
            if scheduled_time:
                result = await self.instagram_client.schedule_post(post)
                post_status = "scheduled"
            else:
                result = await self.instagram_client.create_post(post)
                post_status = "published"
            
            # Store in memory with enhanced metadata
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="instagram_post",
                content={
                    "post_data": post.dict(), 
                    "result": result,
                    "status": post_status,
                    "automation_features_used": ["hashtag_optimization"] if not params.get("hashtags") else []
                },
                is_shared=True,
                confidence=0.9
            )
            
            # Send enhanced Slack notification
            if self.slack_client:
                notification = SlackNotification(
                    agent_name=self.name,
                    event_type="instagram_post_created",
                    message=f"📸 Instagram post {post_status}: {content[:50]}...\n🏷️ Hashtags: {', '.join(hashtags[:5])}",
                    priority="normal"
                )
                await self.slack_client.send_agent_notification(notification)
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "content": content,
                "status": post_status,
                "hashtags_used": hashtags,
                "automation_features": self.automation_features,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def handle_instagram_dms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Instagram DM automation with context-aware responses"""
        if not self.instagram_client:
            return {"error": "Instagram client not initialized", "success": False}
            
        try:
            conversations = await self.instagram_client.get_dm_conversations()
            responses_sent = 0
            conversation_insights = []
            
            for dm in conversations:
                # Enhanced auto-response logic with context
                response = None
                response_type = "none"
                
                message_lower = dm.message.lower()
                
                # Greeting responses
                if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
                    response = "Hi! Thanks for reaching out. How can we help you today? 😊"
                    response_type = "greeting"
                
                # Product inquiry responses
                elif any(word in message_lower for word in ["product", "service", "price", "cost"]):
                    response = "Thanks for your interest in our products! I'd love to help you find the perfect solution. What specific information are you looking for?"
                    response_type = "product_inquiry"
                
                # Support responses
                elif any(word in message_lower for word in ["help", "support", "problem", "issue"]):
                    response = "I'm here to help! Could you please describe the issue you're experiencing? Our team will get back to you shortly."
                    response_type = "support"
                
                # General inquiry
                elif "?" in dm.message:
                    response = "Thanks for your question! Our team will review this and get back to you with a detailed response soon. 🙏"
                    response_type = "inquiry"
                
                if response:
                    await self.instagram_client.send_dm_response(dm.conversation_id, response)
                    responses_sent += 1
                    
                    # Track conversation insights
                    conversation_insights.append({
                        "conversation_id": dm.conversation_id,
                        "original_message": dm.message[:100],
                        "response_type": response_type,
                        "auto_response": response
                    })
            
            # Store DM automation insights
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="instagram_dm_automation",
                content={
                    "conversations_processed": len(conversations),
                    "responses_sent": responses_sent,
                    "conversation_insights": conversation_insights,
                    "automation_effectiveness": responses_sent / len(conversations) if conversations else 0
                },
                is_shared=True,
                confidence=0.85
            )
            
            # Send Slack notification for DM activity
            if self.slack_client and responses_sent > 0:
                notification = SlackNotification(
                    agent_name=self.name,
                    event_type="instagram_dm_automation",
                    message=f"💬 Processed {len(conversations)} Instagram DMs, sent {responses_sent} auto-responses",
                    priority="low"
                )
                await self.slack_client.send_agent_notification(notification)
            
            return {
                "success": True,
                "conversations_processed": len(conversations),
                "responses_sent": responses_sent,
                "conversation_insights": conversation_insights,
                "automation_features": self.automation_features,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def send_slack_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send enhanced Slack notification with marketing context"""
        if not self.slack_client:
            return {"error": "Slack client not initialized", "success": False}
            
        event_type = params.get("event_type", "marketing_update")
        message = params.get("message", "Marketing agent update")
        priority = params.get("priority", "normal")
        channel = params.get("channel", "#marketing-updates")
        
        try:
            # Enhanced notification with marketing context
            enhanced_message = f"🎯 **Marketing Intelligence Update**\n{message}"
            
            # Add context based on event type
            if event_type == "campaign_performance":
                enhanced_message += "\n📊 Check analytics dashboard for detailed metrics"
            elif event_type == "content_published":
                enhanced_message += "\n🚀 Content is now live across channels"
            elif event_type == "automation_alert":
                enhanced_message += "\n🤖 Automated marketing process completed"
            
            notification = SlackNotification(
                agent_name=self.name,
                event_type=event_type,
                message=enhanced_message,
                priority=priority
            )
            
            result = await self.slack_client.send_agent_notification(notification)
            
            # Store notification history
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="slack_notifications",
                content={
                    "event_type": event_type,
                    "message": message,
                    "priority": priority,
                    "channel": channel,
                    "result": result
                },
                is_shared=False,
                confidence=1.0
            )
            
            return {
                "success": True,
                "notification_sent": True,
                "event_type": event_type,
                "priority": priority,
                "enhanced_message": enhanced_message,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}