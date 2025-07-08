from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from datetime import datetime
from loguru import logger

class AmplifierAgent(LangGraphAgent):
    """📢 Amplifier Agent - Content Analysis, Brand Voice, Content Creation"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.7,
            "expertise": ["content analysis", "brand voice", "content creation", "audience engagement"]
        }
        super().__init__("Amplifier", "Content & Brand", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
    
    def _get_system_prompt(self) -> str:
        return """You are the Amplifier Agent - a content and brand specialist. Your role is to:

1. CONTENT ANALYSIS: Analyze performance to identify what works
2. CONTENT CHECKER: Ensure brand voice and tone consistency  
3. CONTENT CREATION: Support creation of videos, reels, newsletters, tweets
4. AUDIENCE INSIGHTS: Understand what resonates with target audience

You are creative and data-driven. Focus on amplifying brand reach and engagement.

Structure your output as:
- Content Performance Analysis (metrics, insights, recommendations)
- Brand Voice Guidelines (tone, style, messaging)
- Content Strategy (formats, topics, distribution)
- Audience Engagement (resonance factors, optimization)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute content amplification and brand optimization"""
        task = state["task"]
        context = state["context"]
        
        task_type = task.get("type", "content_strategy")
        
        if task_type == "content_analysis":
            return await self._analyze_content_performance(task, context)
        elif task_type == "brand_voice_check":
            return await self._check_brand_voice(task, context)
        elif task_type == "content_creation":
            return await self._support_content_creation(task, context)
        else:
            return await self._develop_content_strategy(task, context)
    
    async def _analyze_content_performance(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content performance and identify patterns"""
        content_data = task.get("content_data", {})
        
        analysis_prompt = f"""
        Analyze this content performance data:
        
        Content Data: {content_data}
        Context: {context}
        
        Provide comprehensive analysis:
        1. Performance Metrics (engagement, reach, conversions)
        2. Top Performing Content (what works and why)
        3. Underperforming Content (what doesn't work)
        4. Audience Insights (demographics, preferences, behavior)
        5. Content Format Analysis (videos vs posts vs stories)
        6. Timing Optimization (best posting times/days)
        7. Improvement Recommendations (actionable next steps)
        """
        
        analysis = await self._think(analysis_prompt)
        return {"content_analysis": analysis, "task_type": "content_analysis"}
    
    async def _check_brand_voice(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check content for brand voice consistency"""
        content_to_check = task.get("content", "")
        brand_guidelines = task.get("brand_guidelines", {})
        
        voice_check_prompt = f"""
        Check this content against brand voice guidelines:
        
        Content: {content_to_check}
        Brand Guidelines: {brand_guidelines}
        Context: {context}
        
        Evaluate:
        1. Tone Consistency (matches brand personality)
        2. Voice Alignment (consistent with brand voice)
        3. Messaging Coherence (aligns with brand values)
        4. Style Guidelines (formatting, language, structure)
        5. Audience Appropriateness (suitable for target audience)
        6. Brand Differentiation (unique brand positioning)
        7. Improvement Suggestions (specific edits needed)
        """
        
        voice_check = await self._think(voice_check_prompt)
        return {"brand_voice_check": voice_check, "task_type": "brand_voice_check"}
    
    async def _support_content_creation(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Support content creation across formats"""
        content_request = task.get("content_request", {})
        content_format = task.get("format", "general")
        
        creation_prompt = f"""
        Support creation of {content_format} content:
        
        Request: {content_request}
        Format: {content_format}
        Context: {context}
        
        Provide:
        1. Content Outline (structure, key points, flow)
        2. Hook/Opening (attention-grabbing start)
        3. Key Messages (main points to communicate)
        4. Call-to-Action (desired audience response)
        5. Visual Suggestions (images, graphics, video elements)
        6. Distribution Strategy (platforms, timing, hashtags)
        7. Engagement Optimization (audience interaction tactics)
        """
        
        creation_support = await self._think(creation_prompt)
        return {"content_creation": creation_support, "task_type": "content_creation"}
    
    async def _develop_content_strategy(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Develop comprehensive content strategy"""
        strategy_requirements = task.get("strategy_requirements", {})
        
        strategy_prompt = f"""
        Develop comprehensive content strategy:
        
        Requirements: {strategy_requirements}
        Context: {context}
        
        Create strategy covering:
        1. Content Pillars (main themes and topics)
        2. Content Calendar (posting schedule and frequency)
        3. Format Mix (videos, posts, stories, newsletters)
        4. Platform Strategy (platform-specific approaches)
        5. Audience Segmentation (different content for different segments)
        6. Brand Storytelling (narrative and messaging framework)
        7. Performance Tracking (KPIs and measurement plan)
        8. Content Repurposing (maximize content value)
        """
        
        strategy = await self._think(strategy_prompt)
        return {"content_strategy": strategy, "task_type": "content_strategy"}
    
    async def _research_trending_content(self, topic: str) -> Dict[str, Any]:
        """Research trending content in specific topic area"""
        try:
            search_query = f"{topic} trending content viral posts social media"
            research = await self.web_search._arun(search_query)
            
            return {
                "trending_topics": research.get("summary", "No trending data found"),
                "viral_content_patterns": "Analyze successful content formats",
                "audience_preferences": "Current audience engagement trends",
                "platform_insights": research.get("results", [])[:5]
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual trend research required"}