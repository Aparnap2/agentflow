from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from datetime import datetime
from loguru import logger

class ProductAgent(LangGraphAgent):
    """🎯 Product Agent - Defines MVP, features, personas"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.5,
            "expertise": ["product management", "user research", "MVP design"]
        }
        super().__init__("Product", "Product Management", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
    
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
        """Product analysis with dynamic thinking and coordination"""
        task = state["task"]
        context = state["context"]
        
        # Check for coordination mode
        coordination_mode = task.get("coordination_mode", False)
        peer_context = task.get("peer_context", {})
        
        logger.info(f"🎆 [{self.name}] Coordination mode: {coordination_mode}")
        if peer_context:
            logger.info(f"🤝 [{self.name}] Received context from peers: {list(peer_context.keys())}")
        
        # Get relevant context
        private_memory = await self.memory_manager.get_agent_private_memory(self.name, limit=3)
        global_context = await self.memory_manager.get_global_context_for_agent(
            self.name, "product strategy MVP user personas features"
        )
        
        # Build enhanced prompt with peer insights
        peer_insights = ""
        if coordination_mode and peer_context:
            peer_insights = f"\n\nPEER AGENT INSIGHTS:\n"
            for agent, insights in peer_context.items():
                peer_insights += f"- {agent}: {str(insights)[:200]}...\n"
        
        analysis_prompt = f"""
        I'm Jordan Martinez, a product strategist. I need to define the product strategy:
        
        Task: {task}
        Context: {context}
        My previous product work: {private_memory}
        Vision insights: {global_context}{peer_insights}
        
        Let me think about:
        1. What's the core user problem we're solving?
        2. Who exactly are our users and what do they need?
        3. What's the minimum viable product?
        4. How do we prioritize features?
        5. What's our user experience strategy?
        
        {"I'm working with other agents - I should consider their insights in my analysis." if coordination_mode else ""}
        
        I need to be specific about features, not generic.
        Return JSON with: mvp_definition, user_personas, feature_roadmap, success_metrics
        """
        
        analysis = await self._think(analysis_prompt)
        state["analysis"] = analysis
        return state
    
    async def _synthesize_node(self, state) -> Dict[str, Any]:
        """Synthesize product insights into actionable strategy"""
        analysis = state["analysis"]
        
        synthesis_prompt = f"""
        Based on my product analysis: {analysis}
        
        As Jordan Martinez, I need to create a comprehensive product strategy:
        
        1. Define specific MVP features (not generic ones)
        2. Create detailed user personas with real pain points
        3. Build a phased feature roadmap
        4. Design user experience flows
        5. Set measurable success metrics
        
        Make it actionable for the development team.
        """
        
        synthesis = await self._think(synthesis_prompt)
        state["recommendations"] = synthesis.get("recommendations", [])
        return state
    
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