from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from datetime import datetime
from loguru import logger

class CloserAgent(LangGraphAgent):
    """🎯 Closer Agent - Lead Intelligence, Qualifying, Closing Support"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.4,
            "expertise": ["lead qualification", "sales intelligence", "closing support", "prospect research"]
        }
        super().__init__("Closer", "Sales Intelligence & Closing", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
    
    def _get_system_prompt(self) -> str:
        return """You are the Closer Agent - a sales intelligence specialist. Your role is to:

1. LEAD INTELLIGENCE: Research, qualify, and enrich lead data
2. CLOSING SUPPORT: Provide context and insights for sales conversations
3. QUALIFYING BOT: Ask strategic questions about needs, urgency, and budget
4. PROSPECT RESEARCH: Pull previous interactions and conversation history

You are results-driven and data-focused. Provide actionable sales intelligence.

Structure your output as:
- Lead Profile (company, role, pain points)
- Qualification Score (1-10 with reasoning)
- Closing Strategy (approach, objections, next steps)
- Research Insights (background, previous interactions)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute closer-specific lead intelligence and qualification"""
        task = state["task"]
        context = state["context"]
        
        # Get lead/prospect information
        lead_data = task.get("lead_data", {})
        conversation_history = task.get("conversation_history", [])
        
        # Lead Intelligence Analysis
        intelligence_prompt = f"""
        I'm analyzing this lead for sales intelligence:
        
        Lead Data: {lead_data}
        Conversation History: {conversation_history}
        Context: {context}
        
        Provide comprehensive lead intelligence:
        1. Lead Profile & Company Analysis
        2. Pain Points & Needs Assessment
        3. Budget & Decision-Making Authority
        4. Urgency & Timeline Analysis
        5. Competitive Landscape
        6. Closing Strategy Recommendations
        
        Return JSON with: lead_profile, qualification_score, pain_points, budget_analysis, closing_strategy
        """
        
        analysis = await self._think(intelligence_prompt)
        
        # Enhance with web research if company name available
        if lead_data.get("company"):
            research_data = await self._research_prospect(lead_data["company"])
            analysis["research_insights"] = research_data
        
        state["lead_intelligence"] = analysis
        return state
    
    async def _research_prospect(self, company_name: str) -> Dict[str, Any]:
        """Research prospect company for sales intelligence"""
        try:
            search_query = f"{company_name} company news funding recent developments"
            research = await self.web_search._arun(search_query)
            
            return {
                "company_news": research.get("summary", "No recent news found"),
                "funding_status": "Research funding and growth stage",
                "key_personnel": "Identify decision makers",
                "recent_developments": research.get("results", [])[:3],
                "competitive_intel": "Analyze competitive positioning"
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual research required"}
    
    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify lead using BANT framework"""
        qualification_prompt = f"""
        Qualify this lead using BANT framework:
        
        Lead: {lead_data}
        
        Analyze:
        - BUDGET: Do they have budget allocated?
        - AUTHORITY: Are they the decision maker?
        - NEED: Do they have a clear pain point?
        - TIMELINE: When do they need a solution?
        
        Score each area 1-10 and provide overall qualification score.
        """
        
        qualification = await self._think(qualification_prompt)
        return qualification
    
    async def generate_closing_strategy(self, lead_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized closing strategy"""
        strategy_prompt = f"""
        Create closing strategy for this qualified lead:
        
        Profile: {lead_profile}
        
        Provide:
        1. Approach Strategy (how to engage)
        2. Value Proposition (tailored to their needs)
        3. Objection Handling (likely objections and responses)
        4. Next Steps (specific actions)
        5. Follow-up Sequence (timing and touchpoints)
        """
        
        strategy = await self._think(strategy_prompt)
        return strategy