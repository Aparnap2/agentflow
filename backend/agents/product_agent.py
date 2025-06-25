from typing import Dict, Any
from agents.base_agent import BaseAgent
import json
from datetime import datetime

class ProductAgent(BaseAgent):
    """🎯 Product Agent - Defines MVP, features, personas"""
    
    def __init__(self):
        personality = {
            "tone": "analytical",
            "depth": "detailed",
            "confidence_threshold": 0.75,
            "retry_limit": 3
        }
        super().__init__("Product", "Product Management", personality)
    
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
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process product definition and persona creation"""
        
        # Get context from vision and manager assignments
        vision_context = await self.get_context("cofounder_output")
        manager_context = await self.get_context("manager_output")
        
        if not vision_context:
            return {
                "error": "No vision context available",
                "confidence": 0.0,
                "agent": self.name
            }
        
        vision_data = vision_context[0]["content"]
        
        # Use RAG search for additional context
        rag_tool = self.tools.get_tool("rag_search")
        persona_tool = self.tools.get_tool("persona_create")
        
        # Search for relevant product insights
        market_insights = await self.search_knowledge("product market fit user needs")
        
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
        
        # Store in vector memory for cross-agent access
        product_text = f"MVP: {json.dumps(product_definition['mvp_definition'])} Personas: {json.dumps(product_definition['user_personas'])}"
        await self.vector_memory.store_document(
            text=product_text,
            metadata={"type": "product_definition", "timestamp": result["timestamp"]},
            agent=self.name
        )
        
        return result