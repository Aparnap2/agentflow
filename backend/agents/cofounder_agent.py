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
        
        # Use LLM to process the vision
        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": vision_prompt}
            ]
            response = await self._call_llm(messages)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to structured analysis
            response = {"choices": [{"message": {"content": self._create_fallback_analysis(vision_input)}}]}
        
        try:
            # Try to extract JSON from the response
            response_content = response["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                vision_analysis = json.loads(json_match.group())
            else:
                # Fallback: create structured output from text
                vision_analysis = self._parse_vision_from_text(response_content, vision_input)
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.error(f"JSON parsing failed: {e}")
            # Fallback parsing
            vision_analysis = self._parse_vision_from_text(str(response_content), vision_input)
        
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
            market_data = await self.web_search._arun(f"{search_query} market trends nowadays")
            
            return {
                "current_trends": market_data.get("summary", "Market research in progress"),
            "search_results": market_data.get("count", 0),
            "last_updated": datetime.now().isoformat()
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
    
    async def chat(self, message: str, conversation_id: str, context: list = None) -> Dict[str, Any]:
        """Chat interface for conversational vision refinement"""
        try:
            context = context or []
            
            chat_prompt = f"""You are having a conversation to understand their startup vision.
            
User's message: {message}
            
Your goal: Ask clarifying questions about vision, users, market, problems.
When you have enough info, end with: "VISION_COMPLETE"
            """
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": chat_prompt}
            ]
            response = await self._call_llm(messages)
            
            response_content = response["choices"][0]["message"]["content"]
            vision_complete = "VISION_COMPLETE" in response_content
            clean_response = response_content.replace("VISION_COMPLETE", "").strip()
            
            return {
                "message": clean_response,
                "vision_complete": vision_complete
            }
        except Exception as e:
            logger.error(f"=== COFOUNDER CHAT ERROR ===")
            logger.error(f"Chat failed: {e}")
            logger.error(f"Exception type: {type(e)}")
            
            # Check if it's an API key issue
            if "API key" in str(e) or "Authorization" in str(e):
                logger.error("API key not configured properly")
                response_text = "I need to be configured with an API key to provide intelligent responses. For now, I can help you structure your startup idea. What problem are you trying to solve?"
            else:
                # Simple conversational responses based on input
                if "hi" in message.lower() or "hello" in message.lower():
                    response_text = "Hello! I'm your AI Cofounder. I'd love to learn about your startup idea. What problem are you trying to solve?"
                else:
                    response_text = "That's interesting! Can you tell me more about who your target users would be and what specific pain points you're addressing?"
            
            fallback = {
                "message": response_text,
                "vision_complete": False
            }
            logger.info(f"Returning fallback: {fallback}")
            return fallback
    
    def _create_fallback_analysis(self, vision_input: str) -> str:
        """Create fallback analysis when LLM fails"""
        return json.dumps({
            "vision_statement": vision_input,
            "target_users": ["Early adopters", "Tech-savvy professionals"],
            "market_opportunity": {
                "size": "Market analysis in progress",
                "competition": "Competitive landscape to be researched"
            },
            "success_metrics": ["User acquisition", "Revenue growth", "Market penetration"],
            "strategic_priorities": ["Product development", "Market validation", "User acquisition"],
            "competitive_advantage": "Unique value proposition to be defined"
        })
    
    async def extract_vision(self, messages: list) -> Dict[str, Any]:
        """Extract structured vision from conversation"""
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        extract_prompt = f"""Extract vision from: {conversation_text}
        
Return JSON with: vision_statement, target_users, problem_solving, key_features"""
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": extract_prompt}
        ]
        response = await self._call_llm(messages)
        
        try:
            response_content = response["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "vision_statement": "Vision from conversation",
            "target_users": ["Users discussed"],
            "problem_solving": "Problems identified",
            "key_features": ["Features mentioned"]
        }