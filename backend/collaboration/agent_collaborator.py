"""
Agent collaboration system using existing Qdrant global context
"""

from typing import Dict, List, Any
from datetime import datetime
from loguru import logger

class AgentCollaborator:
    """Manages cross-agent collaboration and data sharing"""
    
    def __init__(self, memory_manager, vector_memory):
        self.memory_manager = memory_manager
        self.vector_memory = vector_memory
        self.collaboration_patterns = {
            "marketing_finance": self._marketing_finance_collaboration,
            "product_marketing": self._product_marketing_collaboration,
            "sales_marketing": self._sales_marketing_collaboration
        }
    
    async def request_collaboration(self, requesting_agent: str, target_agent: str, 
                                 request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Request collaboration between agents"""
        
        collaboration_key = f"{requesting_agent.lower()}_{target_agent.lower()}"
        reverse_key = f"{target_agent.lower()}_{requesting_agent.lower()}"
        
        # Check if collaboration pattern exists
        if collaboration_key in self.collaboration_patterns:
            handler = self.collaboration_patterns[collaboration_key]
        elif reverse_key in self.collaboration_patterns:
            handler = self.collaboration_patterns[reverse_key]
        else:
            handler = self._generic_collaboration
        
        # Execute collaboration
        result = await handler(requesting_agent, target_agent, request_type, context)
        
        # Store collaboration in memory
        await self._store_collaboration(requesting_agent, target_agent, request_type, result)
        
        return result
    
    async def _marketing_finance_collaboration(self, requesting_agent: str, target_agent: str, 
                                            request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Marketing-Finance collaboration patterns"""
        
        if request_type == "customer_list_for_campaign":
            # Marketing requests customer list from Finance
            customer_data = await self._get_customer_data()
            return {
                "collaboration_type": "customer_list_for_campaign",
                "data": customer_data,
                "recommendations": [
                    "Target high-value customers first",
                    "Segment by payment history",
                    "Personalize messaging by customer tier"
                ],
                "success": True
            }
        
        elif request_type == "budget_approval":
            # Marketing requests budget approval from Finance
            budget_data = await self._get_budget_constraints()
            return {
                "collaboration_type": "budget_approval",
                "approved_budget": budget_data.get("marketing_budget", 10000),
                "constraints": budget_data.get("constraints", []),
                "recommendations": ["Focus on high-ROI channels", "Track spend carefully"],
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _product_marketing_collaboration(self, requesting_agent: str, target_agent: str,
                                            request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Product-Marketing collaboration patterns"""
        
        if request_type == "feature_launch_campaign":
            # Product informs Marketing about new features
            product_data = await self._get_product_features()
            return {
                "collaboration_type": "feature_launch_campaign",
                "features_to_promote": product_data.get("new_features", []),
                "target_personas": product_data.get("target_personas", []),
                "messaging_suggestions": [
                    "Highlight user benefits",
                    "Show before/after scenarios",
                    "Include customer testimonials"
                ],
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _sales_marketing_collaboration(self, requesting_agent: str, target_agent: str,
                                          request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sales-Marketing collaboration patterns"""
        
        if request_type == "qualified_leads":
            # Sales requests qualified leads from Marketing
            lead_data = await self._get_marketing_leads()
            return {
                "collaboration_type": "qualified_leads",
                "qualified_leads": lead_data.get("qualified_leads", []),
                "lead_scoring": lead_data.get("scoring_criteria", {}),
                "follow_up_recommendations": [
                    "Contact within 24 hours",
                    "Personalize outreach based on lead source",
                    "Use provided talking points"
                ],
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _generic_collaboration(self, requesting_agent: str, target_agent: str,
                                   request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic collaboration handler"""
        
        # Search for relevant data in vector memory
        search_query = f"{requesting_agent} {target_agent} {request_type}"
        search_results = await self.vector_memory.semantic_search(search_query, limit=3)
        
        return {
            "collaboration_type": "generic",
            "requesting_agent": requesting_agent,
            "target_agent": target_agent,
            "request_type": request_type,
            "available_data": search_results,
            "recommendations": ["Review available data", "Define specific requirements"],
            "success": True
        }
    
    async def _get_customer_data(self) -> Dict[str, Any]:
        """Get customer data from global context"""
        try:
            # Search for customer/finance data in vector memory
            results = await self.vector_memory.semantic_search("customers paying clients revenue", limit=5)
            
            # Mock customer data based on financial projections
            return {
                "total_customers": 150,
                "paying_customers": 120,
                "high_value_customers": [
                    {"id": "cust_001", "name": "Enterprise Corp", "value": "$2400/month"},
                    {"id": "cust_002", "name": "Growth Inc", "value": "$1200/month"},
                    {"id": "cust_003", "name": "Scale LLC", "value": "$800/month"}
                ],
                "customer_segments": ["Enterprise", "SMB", "Startup"],
                "source": "finance_agent_data"
            }
        except Exception as e:
            logger.error(f"Failed to get customer data: {e}")
            return {"error": str(e)}
    
    async def _get_budget_constraints(self) -> Dict[str, Any]:
        """Get budget data from finance agent"""
        try:
            return {
                "marketing_budget": 15000,
                "constraints": ["ROI > 3:1", "Track all spend", "Monthly reporting required"],
                "available_channels": ["Content", "Social", "Email", "Paid ads"],
                "source": "finance_agent_data"
            }
        except Exception as e:
            return {"marketing_budget": 10000, "constraints": []}
    
    async def _get_product_features(self) -> Dict[str, Any]:
        """Get product features from product agent"""
        try:
            return {
                "new_features": ["Advanced Analytics", "API Integration", "Mobile App"],
                "target_personas": ["Tech-savvy users", "Enterprise customers"],
                "release_timeline": "Q2 2024",
                "source": "product_agent_data"
            }
        except Exception as e:
            return {"new_features": [], "target_personas": []}
    
    async def _get_marketing_leads(self) -> Dict[str, Any]:
        """Get marketing leads data"""
        try:
            return {
                "qualified_leads": [
                    {"name": "TechStart Inc", "score": 85, "source": "content_marketing"},
                    {"name": "Growth Co", "score": 78, "source": "social_media"},
                    {"name": "Scale Up", "score": 72, "source": "email_campaign"}
                ],
                "scoring_criteria": {"engagement": 40, "fit": 35, "intent": 25},
                "source": "marketing_agent_data"
            }
        except Exception as e:
            return {"qualified_leads": []}
    
    async def _store_collaboration(self, requesting_agent: str, target_agent: str, 
                                 request_type: str, result: Dict[str, Any]):
        """Store collaboration result in memory"""
        try:
            collaboration_record = {
                "requesting_agent": requesting_agent,
                "target_agent": target_agent,
                "request_type": request_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in vector memory for future reference
            collaboration_text = f"Collaboration between {requesting_agent} and {target_agent} for {request_type}"
            await self.vector_memory.store_document(
                text=collaboration_text,
                metadata=collaboration_record,
                agent="collaboration_system"
            )
            
        except Exception as e:
            logger.error(f"Failed to store collaboration: {e}")
    
    async def get_collaboration_history(self, agent_name: str = None) -> List[Dict[str, Any]]:
        """Get collaboration history"""
        try:
            query = f"collaboration {agent_name}" if agent_name else "collaboration"
            results = await self.vector_memory.semantic_search(query, agent="collaboration_system", limit=10)
            return results
        except Exception as e:
            logger.error(f"Failed to get collaboration history: {e}")
            return []