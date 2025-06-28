from typing import Dict, Any
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
import json
import re
from datetime import datetime
from loguru import logger

class CofounderAgent(LangGraphAgent):
    """🧠 Cofounder Agent - Captures vision, goals, target users"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "conversational and strategic",
            "focus": "vision clarity and market opportunity",
            "expertise": ["strategy", "market analysis", "vision setting", "user research"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.6,
            "confidence_threshold": 0.7,
            "description": "Captures and refines project vision, identifies target users and market opportunities"
        }
        super().__init__("Cofounder", "Vision & Strategy", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
    
    def _get_system_prompt(self) -> str:
        return """You are the Cofounder agent in a virtual AI startup team. Your role is to:

1. Capture and refine the project vision
2. Identify target users and market opportunity  
3. Define high-level goals and success metrics
4. Provide strategic direction for the team

You have a conversational, strategic tone. Focus on the big picture while being practical about execution. Always consider market fit and user needs.

When processing a vision, structure your output as:
- Vision Statement (clear, compelling)
- Target Users (specific personas)
- Market Opportunity (size, competition)
- Success Metrics (measurable goals)
- Strategic Priorities (top 3-5 focus areas)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute cofounder-specific actions"""
        task = state["task"]
        vision_input = task.get("vision", "")
        user_name = task.get("user_name", "User")
        
        # Get current market insights
        market_research = await self._get_market_insights(vision_input)
        
        # Analyze and structure the vision using LLM
        vision_prompt = f"""
        User ({user_name}) has provided this vision:
        "{vision_input}"
        
        Please analyze and structure this vision. Provide a comprehensive analysis including:
        - A clear, compelling vision statement
        - Specific target user personas
        - Market opportunity assessment
        - Success metrics and KPIs
        - Strategic priorities
        - Competitive advantages
        
        Format your response as structured JSON.
        """
        
        # Use the LLM to process the vision
        from langchain_core.messages import HumanMessage
        response = await self.llm.ainvoke([HumanMessage(content=vision_prompt)])
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                vision_analysis = json.loads(json_match.group())
            else:
                # Fallback: create structured output from text
                vision_analysis = self._parse_vision_from_text(response.content, vision_input)
        except (json.JSONDecodeError, AttributeError):
            # Fallback parsing
            vision_analysis = self._parse_vision_from_text(response.content, vision_input)
        
        # Enhance with market research
        vision_analysis["market_research"] = market_research
        
        return vision_analysis
    
    def _parse_vision_from_text(self, text: str, original_vision: str) -> Dict[str, Any]:
        """Fallback method to parse vision from text response"""
        return {
            "vision_statement": original_vision,
            "target_users": ["Early adopters", "Tech-savvy users"],
            "market_opportunity": {
                "size": "To be determined",
                "competition": "Competitive landscape analysis needed"
            },
            "success_metrics": [
                "User acquisition",
                "User engagement",
                "Revenue growth"
            ],
            "strategic_priorities": [
                "Product development",
                "Market validation",
                "Team building"
            ],
            "competitive_advantage": "Unique value proposition to be defined",
            "raw_analysis": text
        }
    
    def _calculate_confidence(self, outputs: Dict[str, Any]) -> float:
        """Calculate confidence based on vision analysis completeness"""
        base_confidence = 0.8
        
        # Check for key components
        if not outputs.get("vision_statement"):
            base_confidence -= 0.3
        if not outputs.get("target_users"):
            base_confidence -= 0.2
        if not outputs.get("market_opportunity"):
            base_confidence -= 0.2
        if not outputs.get("success_metrics"):
            base_confidence -= 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    async def _get_market_insights(self, vision: str) -> Dict[str, Any]:
        """Get current market insights using web search"""
        try:
            # Extract key terms from vision
            search_query = self._extract_search_terms(vision)
            market_data = await self.web_search._arun(f"{search_query} market trends 2024")
            
            return {
                "current_trends": market_data.get("summary", "Market research in progress"),
                "search_results": len(market_data.get("results", [])),
                "last_updated": market_data.get("timestamp", "")
            }
        except Exception as e:
            logger.error(f"Market research failed: {e}")
            return {"error": str(e), "fallback": "Manual research recommended"}
    
    def _extract_search_terms(self, vision: str) -> str:
        """Extract key search terms from vision"""
        # Simple keyword extraction
        words = vision.lower().split()
        key_terms = [word for word in words if len(word) > 4 and word not in ['create', 'build', 'make', 'develop']]
        return ' '.join(key_terms[:3])