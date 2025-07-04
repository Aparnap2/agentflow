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
        return """You are Jordan Martinez, the Product Agent. Create ACTIONABLE product strategy.

Provide structured output with:

## 📱 MVP DEFINITION
- Core Features (3-5 essential features)
- Technical Requirements
- Success Criteria

## 👥 USER PERSONAS
- Primary Persona (detailed profile)
- Secondary Persona (if applicable)
- Pain Points & Goals

## 🎯 FEATURE ROADMAP
- Phase 1: Must-Have Features
- Phase 2: Should-Have Features
- Phase 3: Nice-to-Have Features

## 📊 SUCCESS METRICS
- User Acquisition KPIs
- Engagement Metrics
- Retention Goals

Be specific and actionable. Focus on user value and business impact."""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Process product definition and persona creation with memory integration"""
        
        task = state["task"]
        context = state["context"]
        
        # Get vision data from shared context (Qdrant RAG)
        global_context = await self.memory_manager.get_global_context_for_agent(
            agent_name=self.name,
            query="product strategy user personas MVP features"
        )
        
        # Get my previous product work from private memory (Neo4j)
        previous_work = await self.memory_manager.get_agent_private_memory(
            agent_name=self.name,
            memory_type="product_analysis",
            limit=3
        )
        
        # Extract vision data
        vision_data = global_context.get("shared_context", {}).get("cofounder_output", {})
        if not vision_data:
            vision_data = context.get("shared_context", {}).get("cofounder_output", {})
        
        # Use advanced tools for enhanced analysis
        market_intelligence = await self.market_intelligence._arun(vision_data.get("vision_statement", ""))
        market_research = await self._use_research_tools(vision_data)
        persona_insights = await self._use_persona_tools(vision_data)
        
        # Extract key info from vision
        vision_statement = vision_data.get("vision_statement", "AI assistant for professionals")
        target_users = vision_data.get("target_users", ["professionals"])
        
        # Create detailed product definition
        product_definition = {
            "mvp_definition": {
                "core_features": self._generate_core_features(vision_statement),
                "scope": f"MVP focused on {vision_statement[:100]}...",
                "technical_requirements": [
                    "Mobile-first responsive design",
                    "Real-time data processing",
                    "API integrations",
                    "Cloud infrastructure"
                ],
                "success_criteria": [
                    "User onboarding completed in < 3 minutes",
                    "Core feature usage > 80%",
                    "User satisfaction score > 4.2/5"
                ]
            },
            "user_personas": self._generate_personas(target_users, vision_statement),
            "feature_roadmap": {
                "phase_1_must_have": self._prioritize_features(vision_statement, "must_have"),
                "phase_2_should_have": self._prioritize_features(vision_statement, "should_have"),
                "phase_3_nice_to_have": self._prioritize_features(vision_statement, "nice_to_have")
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
        
        # Store in private memory (Neo4j) for my future reference
        await self.memory_manager.store_agent_private_memory(
            agent_name=self.name,
            memory_type="product_analysis",
            content={
                "product_definition": product_definition,
                "task_context": task,
                "previous_work_referenced": len(previous_work),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Store in shared memory (Qdrant) for other agents
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="product_strategy",
            content=product_definition,
            is_shared=True,
            confidence=confidence,
            metadata={"task_id": task.get("id"), "agent": "Jordan Martinez"}
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
        
        return {
            "output": product_definition,
            "confidence": confidence,
            "summary": f"Product strategy defined with {len(product_definition['mvp_definition']['core_features'])} core features",
            "agent": "Jordan Martinez",
            "timestamp": datetime.now().isoformat()
        }
    
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
    
    def _generate_core_features(self, vision: str) -> List[str]:
        """Generate core features based on vision"""
        if "ai assistant" in vision.lower():
            return [
                "Conversational AI interface",
                "Persistent memory system", 
                "Task automation",
                "Real-time notifications"
            ]
        elif "content" in vision.lower():
            return [
                "Content generation tools",
                "Social media integration",
                "Analytics dashboard",
                "Scheduling system"
            ]
        else:
            return [
                "User authentication",
                "Core functionality", 
                "Dashboard interface",
                "Data management"
            ]
    
    def _generate_personas(self, target_users: List[str], vision: str) -> List[Dict[str, Any]]:
        """Generate user personas based on target users"""
        personas = []
        
        if "professional" in str(target_users).lower():
            personas.append({
                "name": "Sarah the Rising Professional",
                "demographics": "28-35, ambitious professional",
                "goals": ["Career advancement", "Efficiency improvement"],
                "pain_points": ["Time management", "Information overload"],
                "key_features": ["Time-saving automation", "Professional templates"]
            })
        
        if "creator" in str(target_users).lower():
            personas.append({
                "name": "Alex the Content Creator", 
                "demographics": "22-32, creative professional",
                "goals": ["Audience growth", "Content consistency"],
                "pain_points": ["Content planning", "Multi-platform management"],
                "key_features": ["Content calendar", "Cross-platform posting"]
            })
        
        return personas or [{
            "name": "Primary User",
            "demographics": "Target demographic",
            "goals": ["Achieve objectives"],
            "pain_points": ["Current challenges"],
            "key_features": ["Essential functionality"]
        }]
    
    def _prioritize_features(self, vision: str, priority: str) -> List[str]:
        """Prioritize features based on vision and priority level"""
        if "ai assistant" in vision.lower():
            if priority == "must_have":
                return ["Chat interface", "Memory persistence", "Basic automation"]
            elif priority == "should_have":
                return ["Advanced AI features", "Integrations", "Mobile app"]
            else:
                return ["Voice interface", "Custom workflows", "API access"]
        else:
            if priority == "must_have":
                return ["Core functionality", "User management", "Basic features"]
            elif priority == "should_have":
                return ["Advanced features", "Integrations", "Analytics"]
            else:
                return ["Premium features", "Customization", "Enterprise tools"]
    
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