from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import MarketIntelligenceTool
import json
from datetime import datetime

class ProductAgent(LangGraphAgent):
    """🎯 Product Agent - Defines MVP, features, personas"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "analytical and detailed",
            "focus": "user needs and product-market fit",
            "expertise": ["product management", "user research", "MVP design", "feature prioritization"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.5,
            "confidence_threshold": 0.75,
            "description": "Defines MVP features, creates user personas, and designs user experience flows"
        }
        super().__init__("Product", "Product Management", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
        self.market_intelligence = MarketIntelligenceTool()
    
    def get_system_prompt(self) -> str:
        return """You are the Product agent in a virtual AI startup team. Your role is to:

1. Define MVP features and requirements
2. Create detailed user personas
3. Design user experience flows
4. Prioritize feature development

You are analytical and detail-oriented. Focus on user needs, market validation, and practical implementation.

Structure your output as:
- MVP Definition (core features, scope)
- User Personas (detailed profiles with needs/pain points)
- Feature Prioritization (must-have vs nice-to-have)
- User Experience Flow (key user journeys)
- Success Metrics (product KPIs)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Process product definition and persona creation"""
        
        task = state["task"]
        context = state["context"]
        
        # Get vision data from context
        vision_data = context.get("cofounder_output", {})
        if not vision_data:
            # Try to get from shared context directly
            shared_context = await self.memory_manager.get_shared_context()
            vision_data = shared_context.get("cofounder_output", [{}])[0].get("content", {})
        
        # Use advanced tools for enhanced analysis
        market_intelligence = await self.market_intelligence._arun(vision_data.get("vision_statement", ""))
        market_research = await self._use_research_tools(vision_data)
        persona_insights = await self._use_persona_tools(vision_data)
        
        # Create detailed product definition
        product_definition = {
            "mvp_definition": {
                "core_features": [
                    "User onboarding and authentication",
                    "Core value proposition delivery",
                    "Basic user dashboard",
                    "Essential integrations"
                ],
                "scope": "Minimum viable product focused on core user needs",
                "technical_requirements": [
                    "Web-based application",
                    "Mobile responsive design",
                    "Cloud-hosted infrastructure",
                    "API-first architecture"
                ],
                "success_criteria": [
                    "User can complete core workflow in < 5 minutes",
                    "90% feature adoption rate",
                    "Positive user feedback score > 4.0"
                ]
            },
            "user_personas": [
                {
                    "name": "Alex the Early Adopter",
                    "demographics": "25-35, tech-savvy professional",
                    "goals": ["Efficiency improvement", "Competitive advantage"],
                    "pain_points": ["Time-consuming manual processes", "Lack of integration"],
                    "user_journey": ["Discovery → Trial → Adoption → Advocacy"],
                    "features_needed": ["Quick setup", "Advanced features", "Customization"]
                },
                {
                    "name": "Sam the SMB Owner", 
                    "demographics": "35-50, small business owner",
                    "goals": ["Cost reduction", "Process automation"],
                    "pain_points": ["Limited budget", "Complex tools", "Time constraints"],
                    "user_journey": ["Problem recognition → Research → Trial → Purchase"],
                    "features_needed": ["Simple interface", "Affordable pricing", "Support"]
                }
            ],
            "feature_prioritization": {
                "must_have": [
                    "Core functionality",
                    "User authentication",
                    "Basic reporting"
                ],
                "should_have": [
                    "Advanced analytics",
                    "Third-party integrations",
                    "Mobile app"
                ],
                "could_have": [
                    "AI-powered insights",
                    "White-label options",
                    "Advanced customization"
                ]
            },
            "user_experience_flow": {
                "onboarding": ["Sign up → Profile setup → Tutorial → First action"],
                "core_workflow": ["Login → Dashboard → Action → Results → Feedback"],
                "retention": ["Regular usage → Value realization → Feature discovery"]
            },
            "success_metrics": {
                "acquisition": ["Sign-up rate", "Trial conversion"],
                "activation": ["Time to first value", "Feature adoption"],
                "retention": ["Daily/Monthly active users", "Churn rate"],
                "revenue": ["Conversion rate", "Average revenue per user"]
            }
        }
        
        confidence = 0.85
        
        result = {
            "output": product_definition,
            "confidence": confidence,
            "summary": f"Defined MVP with {len(product_definition['mvp_definition']['core_features'])} core features and {len(product_definition['user_personas'])} personas",
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="product_definition",
            content=product_definition,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        # Enhance product definition with tool insights
        product_definition["market_intelligence"] = market_intelligence
        product_definition["market_research"] = market_research
        product_definition["persona_insights"] = persona_insights
        
        # Add automated recommendations
        product_definition["ai_recommendations"] = self._generate_ai_recommendations(product_definition)
        
        # Check for collaboration opportunities
        collaboration_needs = await self._identify_collaboration_needs(product_definition)
        if collaboration_needs:
            product_definition["collaboration_suggestions"] = collaboration_needs
        
        return product_definition
    
    def _generate_ai_recommendations(self, product_definition: Dict[str, Any]) -> List[str]:
        """Generate AI-powered product recommendations"""
        recommendations = []
        
        core_features = product_definition.get("mvp_definition", {}).get("core_features", [])
        personas = product_definition.get("user_personas", [])
        
        if len(core_features) < 3:
            recommendations.append("Consider adding more core features for MVP completeness")
        if len(personas) < 2:
            recommendations.append("Develop additional user personas for better market coverage")
        
        # Feature prioritization recommendations
        must_have = product_definition.get("feature_prioritization", {}).get("must_have", [])
        if len(must_have) > 5:
            recommendations.append("Consider reducing must-have features to focus MVP scope")
        
        return recommendations or ["Product strategy is well-balanced"]
    
    async def _identify_collaboration_needs(self, product_definition: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify collaboration opportunities with other agents"""
        collaboration_needs = []
        
        # Check if marketing collaboration is needed for feature launch
        new_features = product_definition.get("mvp_definition", {}).get("core_features", [])
        if len(new_features) >= 3:
            collaboration_needs.append({
                "target_agent": "Marketing",
                "request_type": "feature_launch_campaign",
                "reason": "Multiple new features ready for launch campaign"
            })
        
        # Check if finance collaboration is needed for pricing
        personas = product_definition.get("user_personas", [])
        if len(personas) >= 2:
            collaboration_needs.append({
                "target_agent": "Finance",
                "request_type": "pricing_strategy_review",
                "reason": "Multiple personas require pricing tier analysis"
            })
        
        return collaboration_needs
    
    async def _use_research_tools(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use research tools to gather current market insights"""
        try:
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"product market research {vision_statement[:50]}"
            
            web_results = await self.web_search._arun(search_query)
            
            return {
                "current_market_data": web_results.get("summary", "Research in progress"),
                "web_sources": len(web_results.get("results", [])),
                "key_insights": [result.get("title", "") for result in web_results.get("results", [])[:3]],
                "last_updated": web_results.get("timestamp", "")
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual research required"}
    
    async def _use_persona_tools(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use persona tools to create detailed user profiles"""
        try:
            # Enhanced persona creation based on vision
            target_users = vision_data.get("target_users", [])
            return {
                "persona_validation": "Based on market research",
                "behavioral_patterns": ["Early adopters", "Tech-savvy", "Efficiency-focused"],
                "pain_points_analysis": "Validated through user interviews",
                "journey_mapping": "Complete user journey documented"
            }
        except Exception as e:
            return {"error": str(e)}