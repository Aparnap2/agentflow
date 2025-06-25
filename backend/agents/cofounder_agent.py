from typing import Dict, Any
from agents.base_agent import BaseAgent
import json
from datetime import datetime

class CofounderAgent(BaseAgent):
    """🧠 Cofounder Agent - Captures vision, goals, target users"""
    
    def __init__(self):
        personality = {
            "tone": "conversational",
            "depth": "strategic",
            "confidence_threshold": 0.7,
            "retry_limit": 2
        }
        super().__init__("Cofounder", "Vision & Strategy", personality)
    
    def get_system_prompt(self) -> str:
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
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process vision capture and refinement"""
        vision_input = task.get("vision", "")
        user_name = task.get("user_name", "User")
        
        # Use LLM tool for reasoning
        llm_tool = self.tools.get_tool("llm_reasoning")
        
        prompt = f"""
        {self.get_system_prompt()}
        
        User ({user_name}) has provided this vision:
        "{vision_input}"
        
        Please analyze and structure this vision according to the format specified.
        Provide a confidence score (0-1) for how well-defined this vision is.
        """
        
        # Simulate LLM response (in real implementation, this would call OpenRouter)
        vision_analysis = {
            "vision_statement": f"Refined vision based on: {vision_input}",
            "target_users": [
                {"persona": "Early Adopters", "description": "Tech-savvy users seeking innovation"},
                {"persona": "SMB Owners", "description": "Small business owners needing efficiency"}
            ],
            "market_opportunity": {
                "size": "Large addressable market",
                "competition": "Moderate competition with differentiation opportunities",
                "timing": "Market ready for this solution"
            },
            "success_metrics": [
                "User acquisition rate",
                "Product-market fit indicators", 
                "Revenue milestones"
            ],
            "strategic_priorities": [
                "MVP development",
                "User validation",
                "Go-to-market strategy"
            ]
        }
        
        confidence = 0.85 if len(vision_input) > 50 else 0.6
        
        result = {
            "output": vision_analysis,
            "confidence": confidence,
            "summary": f"Captured and refined vision: {vision_analysis['vision_statement'][:100]}...",
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in vector memory for semantic search
        await self.vector_memory.store_document(
            text=f"Vision: {vision_analysis['vision_statement']} Target Users: {json.dumps(vision_analysis['target_users'])}",
            metadata={"type": "vision", "timestamp": result["timestamp"]},
            agent=self.name
        )
        
        return result