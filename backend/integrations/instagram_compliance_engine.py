"""
Instagram DM Compliance Engine
Implements 24-hour rule and human-agent tag compliance per PRD
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from database.supabase_db import supabase_db

class InstagramComplianceEngine:
    """Enforces Instagram DM compliance rules"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        
        # Compliance rules per PRD
        self.rules = {
            "response_window_hours": 24,  # 24-hour response window
            "human_agent_tag_days": 7,    # 7-day human-agent tag window
            "max_auto_responses": 3,      # Max auto responses per conversation
            "professional_account_only": True,  # Only professional accounts
            "no_broadcast_outside_window": True,  # No broadcasts outside window
            "no_promos_in_human_tag": True      # No promos during human-agent tag
        }
    
    async def check_dm_compliance(self, conversation_id: str, user_id: str, 
                                message_type: str = "response") -> Dict[str, Any]:
        """Check if DM action is compliant with Instagram rules"""
        
        # Get current compliance status
        compliance_record = await supabase_db.get_instagram_compliance_status(
            self.workspace_id, conversation_id
        )
        
        now = datetime.now()
        
        if not compliance_record:
            # First interaction - create compliance record
            compliance_record = await supabase_db.track_instagram_dm_compliance(
                self.workspace_id, conversation_id, user_id
            )
        
        # Parse timestamps
        response_window_expires = datetime.fromisoformat(
            compliance_record["response_window_expires_at"].replace("Z", "+00:00")
        )
        human_tag_expires = datetime.fromisoformat(
            compliance_record["human_agent_tag_expires_at"].replace("Z", "+00:00")
        )
        
        compliance_status = compliance_record["compliance_status"]
        auto_responses_sent = compliance_record.get("auto_responses_sent", 0)
        
        # Check compliance rules
        compliance_result = {
            "compliant": True,
            "action_allowed": True,
            "reason": "",
            "window_status": "active",
            "expires_at": response_window_expires.isoformat(),
            "human_tag_available": now < human_tag_expires,
            "auto_responses_remaining": max(0, self.rules["max_auto_responses"] - auto_responses_sent)
        }
        
        # Rule 1: 24-hour response window
        if now > response_window_expires:
            if compliance_status == "active":
                # Window expired, check if human-agent tag is available
                if now < human_tag_expires:
                    compliance_result.update({
                        "window_status": "expired_human_tag_available",
                        "action_allowed": message_type in ["human_agent_tag", "human_response"],
                        "reason": "24-hour window expired, human-agent tag available for 7 days"
                    })
                    
                    if message_type == "auto_response":
                        compliance_result.update({
                            "compliant": False,
                            "action_allowed": False,
                            "reason": "Auto-responses not allowed outside 24-hour window"
                        })
                else:
                    # Both windows expired
                    compliance_result.update({
                        "compliant": False,
                        "action_allowed": False,
                        "window_status": "expired",
                        "reason": "Both 24-hour and 7-day windows expired"
                    })
        
        # Rule 2: Max auto responses limit
        if (message_type == "auto_response" and 
            auto_responses_sent >= self.rules["max_auto_responses"]):
            compliance_result.update({
                "compliant": False,
                "action_allowed": False,
                "reason": f"Maximum auto responses ({self.rules['max_auto_responses']}) reached"
            })
        
        # Rule 3: No promotional content during human-agent tag
        if (compliance_status == "human_tagged" and 
            message_type == "promotional" and 
            self.rules["no_promos_in_human_tag"]):
            compliance_result.update({
                "compliant": False,
                "action_allowed": False,
                "reason": "Promotional content not allowed during human-agent tag period"
            })
        
        # Rule 4: No broadcasts outside window
        if (message_type == "broadcast" and 
            now > response_window_expires and
            self.rules["no_broadcast_outside_window"]):
            compliance_result.update({
                "compliant": False,
                "action_allowed": False,
                "reason": "Broadcast messages not allowed outside 24-hour window"
            })
        
        return compliance_result
    
    async def execute_compliant_dm_response(self, conversation_id: str, user_id: str, 
                                          message: str, message_type: str = "auto_response") -> Dict[str, Any]:
        """Execute DM response with compliance checking"""
        
        # Check compliance first
        compliance_check = await self.check_dm_compliance(conversation_id, user_id, message_type)
        
        if not compliance_check["action_allowed"]:
            logger.warning(f"DM response blocked: {compliance_check['reason']}")
            return {
                "success": False,
                "blocked": True,
                "reason": compliance_check["reason"],
                "compliance_status": compliance_check
            }
        
        try:
            # Import Instagram client
            from integrations.instagram_client import InstagramClient
            from integrations.base_integration import IntegrationConfig
            import os
            
            # Get Instagram config
            instagram_config = IntegrationConfig(
                api_key=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
                base_url="https://graph.facebook.com/v18.0"
            )
            
            if not instagram_config.api_key:
                return {
                    "success": False,
                    "error": "Instagram access token not configured"
                }
            
            # Send DM
            instagram_client = InstagramClient(instagram_config)
            result = await instagram_client.send_dm_response(conversation_id, message)
            
            if result.get("id"):  # Success
                # Update compliance tracking
                await self._update_compliance_after_response(
                    conversation_id, message_type, compliance_check
                )
                
                # Log audit event
                await supabase_db.log_audit_event(
                    workspace_id=self.workspace_id,
                    user_id="system",  # System-generated
                    agent="Marketing_Intelligence",
                    action="instagram_dm_sent",
                    details={
                        "conversation_id": conversation_id,
                        "message_type": message_type,
                        "compliance_status": compliance_check,
                        "message_length": len(message)
                    },
                    sensitive=True
                )
                
                return {
                    "success": True,
                    "message_id": result["id"],
                    "compliance_status": compliance_check,
                    "message_type": message_type
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send Instagram DM",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"Failed to send compliant DM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_compliance_after_response(self, conversation_id: str, 
                                              message_type: str, compliance_check: Dict[str, Any]):
        """Update compliance tracking after successful response"""
        
        # Get current record
        compliance_record = await supabase_db.get_instagram_compliance_status(
            self.workspace_id, conversation_id
        )
        
        if not compliance_record:
            return
        
        updates = {"updated_at": datetime.now().isoformat()}
        
        # Update auto response count
        if message_type == "auto_response":
            current_count = compliance_record.get("auto_responses_sent", 0)
            updates["auto_responses_sent"] = current_count + 1
        
        # Update status if using human-agent tag
        if message_type == "human_agent_tag":
            updates["compliance_status"] = "human_tagged"
        
        # Update the record (would need to implement update method in supabase_db)
        # For now, log the update
        logger.info(f"Compliance update for {conversation_id}: {updates}")
    
    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        try:
            # This would query the database for compliance metrics
            # For now, return mock data structure
            
            now = datetime.now()
            
            return {
                "workspace_id": self.workspace_id,
                "compliance_summary": {
                    "total_conversations": 0,  # Would query database
                    "active_windows": 0,
                    "expired_windows": 0,
                    "human_tagged_conversations": 0,
                    "blocked_responses": 0
                },
                "recent_activity": [],  # Would query recent DM activity
                "compliance_alerts": [],  # Active compliance issues
                "window_expiry_forecast": {
                    "expiring_in_1_hour": 0,
                    "expiring_in_6_hours": 0,
                    "expiring_in_24_hours": 0
                },
                "generated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate compliance dashboard: {e}")
            return {"error": str(e)}
    
    async def handle_new_user_message(self, conversation_id: str, user_id: str, 
                                    message: str) -> Dict[str, Any]:
        """Handle new incoming user message and reset compliance window"""
        
        # Reset compliance window for new user message
        compliance_record = await supabase_db.track_instagram_dm_compliance(
            self.workspace_id, conversation_id, user_id
        )
        
        # Analyze message for auto-response opportunity
        auto_response = await self._generate_compliant_auto_response(message)
        
        if auto_response:
            # Send compliant auto-response
            response_result = await self.execute_compliant_dm_response(
                conversation_id, user_id, auto_response, "auto_response"
            )
            
            return {
                "compliance_window_reset": True,
                "auto_response_sent": response_result.get("success", False),
                "auto_response": auto_response if response_result.get("success") else None,
                "compliance_record": compliance_record
            }
        
        return {
            "compliance_window_reset": True,
            "auto_response_sent": False,
            "compliance_record": compliance_record
        }
    
    async def _generate_compliant_auto_response(self, user_message: str) -> Optional[str]:
        """Generate compliant auto-response based on user message"""
        
        message_lower = user_message.lower()
        
        # Professional, compliant responses only
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            return "Hi! Thanks for reaching out. How can we help you today?"
        
        elif any(word in message_lower for word in ["product", "service", "info", "information"]):
            return "Thanks for your interest! I'd be happy to provide more information. What specific details would you like to know?"
        
        elif any(word in message_lower for word in ["help", "support", "question"]):
            return "I'm here to help! Could you please provide more details about what you need assistance with?"
        
        elif "?" in user_message:
            return "Thanks for your question! Our team will review this and get back to you with a detailed response."
        
        # No auto-response for unclear messages
        return None
    
    def get_compliance_rules(self) -> Dict[str, Any]:
        """Get current compliance rules configuration"""
        return {
            "rules": self.rules,
            "description": {
                "response_window_hours": "Professional accounts can respond to DMs within 24 hours",
                "human_agent_tag_days": "Human-agent tag extends window to 7 days where supported",
                "max_auto_responses": "Limit automated responses per conversation",
                "professional_account_only": "Only professional Instagram accounts supported",
                "no_broadcast_outside_window": "No broadcast messages outside response window",
                "no_promos_in_human_tag": "No promotional content during human-agent tag period"
            },
            "compliance_level": "strict",
            "last_updated": datetime.now().isoformat()
        }