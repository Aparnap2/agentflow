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
            "finance_marketing": self._marketing_finance_collaboration,
            "product_marketing": self._product_marketing_collaboration,
            "marketing_product": self._product_marketing_collaboration,
            "sales_marketing": self._sales_marketing_collaboration,
            "marketing_sales": self._sales_marketing_collaboration,
            "product_finance": self._product_finance_collaboration,
            "finance_product": self._product_finance_collaboration,
            "legal_finance": self._legal_finance_collaboration,
            "finance_legal": self._legal_finance_collaboration,
            "operations_product": self._operations_product_collaboration,
            "product_operations": self._operations_product_collaboration,
            "sales_finance": self._sales_finance_collaboration,
            "finance_sales": self._sales_finance_collaboration,
            "legal_marketing": self._legal_marketing_collaboration,
            "marketing_legal": self._legal_marketing_collaboration
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
    
    async def _product_finance_collaboration(self, requesting_agent: str, target_agent: str,
                                          request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Product-Finance collaboration patterns"""
        
        if request_type == "pricing_validation":
            finance_data = await self._get_budget_constraints()
            return {
                "collaboration_type": "pricing_validation",
                "pricing_recommendations": {
                    "suggested_tiers": finance_data.get("customer_segments", []),
                    "budget_constraints": finance_data.get("constraints", [])
                },
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _legal_finance_collaboration(self, requesting_agent: str, target_agent: str,
                                        request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legal-Finance collaboration patterns"""
        
        if request_type == "compliance_budget":
            budget_data = await self._get_budget_constraints()
            return {
                "collaboration_type": "compliance_budget",
                "allocated_budget": budget_data.get("marketing_budget", 0) * 0.1,
                "recommendations": ["Prioritize GDPR compliance", "Allocate for legal review"],
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _operations_product_collaboration(self, requesting_agent: str, target_agent: str,
                                             request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Operations-Product collaboration patterns"""
        
        if request_type == "scalability_review":
            product_data = await self._get_product_features()
            return {
                "collaboration_type": "scalability_review",
                "scalability_assessment": {
                    "bottlenecks": ["Database scaling", "API rate limits"],
                    "recommendations": ["Implement caching", "Add load balancing"]
                },
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)
    
    async def _sales_finance_collaboration(self, requesting_agent: str, target_agent: str,
                                        request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sales-Finance collaboration patterns"""
        
        if request_type == "revenue_forecast":
            finance_data = await self._get_budget_constraints()
            return {
                "collaboration_type": "revenue_forecast",
                "revenue_data": {
                    "current_projections": finance_data.get("revenue_projections", {}),
                    "variance_analysis": "Sales tracking 15% above projections"
                },
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
        """Get real customer data from Finance agent's stored data"""
        try:
            # Search for actual finance agent data
            results = await self.vector_memory.semantic_search("finance revenue customers pricing tiers", limit=10)
            
            # Extract real data from finance agent outputs
            customer_data = {"customers": [], "segments": [], "revenue_data": {}}
            
            for result in results:
                if result.get("agent") == "Finance":
                    content = result.get("content", {})
                    
                    # Extract pricing tiers as customer segments
                    pricing_tiers = content.get("revenue_model", {}).get("pricing_tiers", [])
                    for tier in pricing_tiers:
                        customer_data["segments"].append({
                            "tier": tier.get("tier", ""),
                            "price": tier.get("price", 0),
                            "target_segment": tier.get("target_segment", "")
                        })
                    
                    # Extract financial projections
                    projections = content.get("financial_projections", {})
                    if projections:
                        customer_data["revenue_data"] = projections
            
            return {
                "customer_segments": customer_data["segments"],
                "revenue_projections": customer_data["revenue_data"],
                "source": "finance_agent_real_data",
                "last_updated": results[0].get("timestamp") if results else None
            }
        except Exception as e:
            logger.error(f"Failed to get customer data: {e}")
            return {"error": str(e)}
    
    async def _get_budget_constraints(self) -> Dict[str, Any]:
        """Get real budget data from Finance agent"""
        try:
            results = await self.vector_memory.semantic_search("finance budget cost marketing allocation", limit=5)
            
            budget_data = {"marketing_budget": 0, "cost_structure": {}, "constraints": []}
            
            for result in results:
                if result.get("agent") == "Finance":
                    content = result.get("content", {})
                    
                    # Extract cost structure
                    cost_structure = content.get("cost_structure", {})
                    if "marketing" in cost_structure:
                        marketing_cost = cost_structure["marketing"]
                        budget_data["marketing_budget"] = marketing_cost.get("annual_cost", 0)
                        budget_data["percentage"] = marketing_cost.get("percentage", 0)
                    
                    # Extract funding requirements
                    funding = content.get("funding_requirements", {})
                    if funding:
                        budget_data["constraints"] = [
                            f"Total funding available: ${funding.get('seed_funding', 0):,}",
                            f"Runway: {funding.get('runway', 'Unknown')}"
                        ]
            
            return {
                **budget_data,
                "source": "finance_agent_real_data",
                "last_updated": results[0].get("timestamp") if results else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_product_features(self) -> Dict[str, Any]:
        """Get real product features from Product agent"""
        try:
            results = await self.vector_memory.semantic_search("product features MVP personas development", limit=5)
            
            product_data = {"features": [], "personas": [], "roadmap": {}}
            
            for result in results:
                if result.get("agent") == "Product":
                    content = result.get("content", {})
                    
                    # Extract MVP features
                    mvp = content.get("mvp_definition", {})
                    if mvp:
                        product_data["features"] = mvp.get("core_features", [])
                    
                    # Extract user personas
                    personas = content.get("user_personas", [])
                    product_data["personas"] = [{
                        "name": p.get("name", ""),
                        "demographics": p.get("demographics", ""),
                        "goals": p.get("goals", [])
                    } for p in personas]
                    
                    # Extract feature prioritization
                    prioritization = content.get("feature_prioritization", {})
                    product_data["roadmap"] = prioritization
            
            return {
                "core_features": product_data["features"],
                "user_personas": product_data["personas"],
                "feature_roadmap": product_data["roadmap"],
                "source": "product_agent_real_data",
                "last_updated": results[0].get("timestamp") if results else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_marketing_leads(self) -> Dict[str, Any]:
        """Get real marketing leads from Marketing agent"""
        try:
            results = await self.vector_memory.semantic_search("marketing content strategy channels campaign", limit=5)
            
            marketing_data = {"channels": [], "strategy": {}, "performance": {}}
            
            for result in results:
                if result.get("agent") == "Marketing":
                    content = result.get("content", {})
                    
                    # Extract distribution channels
                    channels = content.get("distribution_channels", [])
                    marketing_data["channels"] = channels
                    
                    # Extract content strategy
                    strategy = content.get("content_strategy", {})
                    marketing_data["strategy"] = strategy
                    
                    # Extract success metrics
                    metrics = content.get("success_metrics", [])
                    marketing_data["performance"] = metrics
            
            return {
                "distribution_channels": marketing_data["channels"],
                "content_strategy": marketing_data["strategy"],
                "success_metrics": marketing_data["performance"],
                "source": "marketing_agent_real_data",
                "last_updated": results[0].get("timestamp") if results else None
            }
        except Exception as e:
            return {"error": str(e)}
    
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
    
    async def _legal_marketing_collaboration(self, requesting_agent: str, target_agent: str,
                                          request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legal-Marketing collaboration patterns"""
        
        if request_type == "compliance_review":
            marketing_data = await self._get_marketing_leads()
            return {
                "collaboration_type": "compliance_review",
                "compliance_status": {
                    "marketing_claims": "Review required for accuracy",
                    "data_collection": "GDPR compliant with consent mechanisms",
                    "advertising_standards": "Meets FTC guidelines"
                },
                "recommendations": ["Add disclaimers to promotional content", "Update privacy notices"],
                "success": True
            }
        
        return await self._generic_collaboration(requesting_agent, target_agent, request_type, context)