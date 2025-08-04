import json
import re
from typing import Dict, Any
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from utils.agent_logger import AgentLogger
from datetime import datetime
from loguru import logger

class CofounderAgent(LangGraphAgent):
    """🧠 Cofounder Agent - Captures vision, goals, target users"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.6,
            "expertise": ["strategy", "market analysis", "vision setting"]
        }
        super().__init__("Cofounder", "Vision & Strategy", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
        self.agent_logger = AgentLogger("Cofounder")
        
        # Initialize role-specific action methods
        self.role_actions = {
            "vision_setting": self._vision_setting,
            "goal_definition": self._goal_definition,
            "market_analysis": self._market_analysis,
            "strategic_planning": self._strategic_planning,
            "kpi_establishment": self._kpi_establishment
        }
    
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
        """Cofounder-specific analysis with dynamic thinking"""
        self.agent_logger.log_node_start("execute_actions", state)
        
        task = state["task"]
        context = state["context"]
        
        # Check for coordination mode
        coordination_mode = task.get("coordination_mode", False)
        peer_context = task.get("peer_context", {})
        
        if coordination_mode:
            logger.info(f"🤝 [{self.name}] Running in coordination mode with peer context: {list(peer_context.keys())}")
        
        # Get memory and context with logging
        logger.info(f"🔍 [{self.name}] Retrieving private memory...")
        private_memory = await self.memory_manager.get_agent_private_memory(self.name, limit=3)
        self.agent_logger.log_memory_access("private_memory", "read", len(private_memory))
        
        logger.info(f"🌐 [{self.name}] Retrieving global context...")
        global_context = await self.memory_manager.get_global_context_for_agent(
            self.name, "vision strategy market opportunity"
        )
        self.agent_logger.log_memory_access("global_context", "read", len(str(global_context)))
        
        # Enhanced prompt with coordination context
        coordination_context = f"\nPeer agent insights: {peer_context}" if coordination_mode else ""
        
        analysis_prompt = f"""
        I'm Alex Chen, a visionary cofounder. I need to analyze this startup idea:
        
        Task: {task}
        Context: {context}
        My previous insights: {private_memory}
        Market intelligence: {global_context}{coordination_context}
        
        Let me think deeply about:
        1. What's the core problem being solved?
        2. Who are the real target users?
        3. What's the market opportunity size?
        4. What makes this unique?
        5. What are the key success factors?
        
        I should provide strategic insights, not generic advice.
        Return JSON with: vision_statement, target_users, market_opportunity, strategic_priorities, competitive_advantage
        """
        
        logger.info(f"🤖 [{self.name}] Starting LLM analysis...")
        self.agent_logger.log_llm_call(len(analysis_prompt), 0, self.model)
        
        analysis = await self._think(analysis_prompt)
        
        logger.info(f"📝 [{self.name}] Analysis complete: {len(str(analysis))} chars")
        self.agent_logger.log_llm_call(len(analysis_prompt), len(str(analysis)), self.model)
        
        state["analysis"] = analysis
        self.agent_logger.log_node_complete("execute_actions", analysis)
        
        return state
    
    async def _synthesize_node(self, state) -> Dict[str, Any]:
        """Synthesize vision analysis into actionable strategy"""
        analysis = state["analysis"]
        
        synthesis_prompt = f"""
        Based on my vision analysis: {analysis}
        
        As Alex Chen, I need to synthesize this into a clear strategic direction:
        
        1. Craft a compelling vision statement
        2. Define specific user personas with pain points
        3. Size the market opportunity
        4. Identify 3-5 strategic priorities
        5. Articulate our competitive advantage
        
        Make it specific, actionable, and inspiring - not generic startup advice.
        Return structured recommendations.
        """
        
        synthesis = await self._think(synthesis_prompt)
        state["recommendations"] = synthesis.get("recommendations", [])
        return state
    
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
        """Chat interface for conversational vision refinement with memory"""
        try:
            logger.info(f"💬 [{self.name}] Starting chat - Message: {message[:50]}...")
            self.agent_logger.log_node_start("chat", {"message": message, "context_length": len(context or [])})
            
            context = context or []
            conversation_length = len(context)
            
            # Store user message in private memory
            logger.info(f"💾 [{self.name}] Storing user message in private memory...")
            await self.memory_manager.store_agent_private_memory(
                agent_name=self.name,
                memory_type="conversation",
                content={
                    "user_message": message,
                    "conversation_id": conversation_id,
                    "message_count": conversation_length + 1,
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.agent_logger.log_memory_access("private_memory", "write", 1)
            
            # Get relevant global context using RAG with caching
            logger.info(f"🔍 [{self.name}] Retrieving global context via RAG...")
            cache_key = f"global_context_{self.name}_{hash(message[:50])}"
            global_context = await self.memory_manager.get_with_cache(
                cache_key,
                lambda: self.memory_manager.get_global_context_for_agent(self.name, message)
            )
            self.agent_logger.log_memory_access("global_context_rag", "read", len(str(global_context)))
            
            # Generic completion logic - provide output after sufficient exchanges
            should_complete = conversation_length >= 2 or any(phrase in message.lower() for phrase in [
                'generate', 'create', 'start', 'provide', 'give me', 'show me', 'help me',
                'no more details', 'thats enough', 'proceed', 'continue'
            ])
            
            if should_complete:
                chat_prompt = f"""Based on our conversation, provide a comprehensive response as {self.name}:
                
User's request: {message}
Conversation context: {prev_conversations if 'prev_conversations' in locals() else []}
Global context: {global_context.get('shared_context', {})}
                
As {self.name} with expertise in {', '.join(self.personality.get('expertise', []))}, provide:
1. A clear summary of what we've discussed
2. Specific recommendations based on my expertise
3. Actionable next steps
4. Any deliverables the user requested

Be helpful and complete the conversation with valuable output.
                """
                vision_complete = True
            else:
                # Get previous conversation context from private memory with caching
                logger.info(f"📚 [{self.name}] Retrieving conversation history...")
                cache_key = f"conversation_history_{self.name}_{conversation_id}"
                prev_conversations = await self.memory_manager.get_with_cache(
                    cache_key,
                    lambda: self.memory_manager.get_agent_private_memory(self.name, "conversation", 5)
                )
                self.agent_logger.log_memory_access("conversation_history", "read", len(prev_conversations))
                
                # Ask strategic questions based on what's missing
                missing_info = []
                conversation_text = str(prev_conversations).lower()
                
                if 'target' not in conversation_text and 'user' not in conversation_text:
                    missing_info.append('target users')
                if 'market' not in conversation_text and 'competition' not in conversation_text:
                    missing_info.append('market size and competition')
                if 'revenue' not in conversation_text and 'money' not in conversation_text:
                    missing_info.append('business model and revenue')
                if 'problem' not in conversation_text and 'pain' not in conversation_text:
                    missing_info.append('specific problem being solved')
                
                focus_areas = missing_info[:2] if missing_info else ['market validation', 'competitive advantage']
                
                # Generic questioning logic
                if conversation_length == 0:
                    chat_prompt = f"""You are {self.name}, a {self.role} specialist.
                    
User's message: {message}
                    
Ask 1-2 relevant questions based on your expertise in {', '.join(self.personality.get('expertise', []))} to better understand their needs.
                    """
                else:
                    chat_prompt = f"""You are {self.name}. Continue this conversation:
                    
User's message: {message}
Previous context: {prev_conversations}
                    
Ask 1 final question to clarify their needs, then offer to provide specific recommendations based on your expertise.
                    """
                vision_complete = False
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": chat_prompt}
            ]
            
            logger.info(f"🤖 [{self.name}] Making LLM call...")
            self.agent_logger.log_llm_call(len(chat_prompt), 0, self.model)
            
            response = await self._call_llm(messages)
            
            response_content = response["choices"][0]["message"]["content"]
            
            # Store response in private memory
            logger.info(f"💾 [{self.name}] Storing response in private memory...")
            await self.memory_manager.store_agent_private_memory(
                agent_name=self.name,
                memory_type="conversation_response",
                content={
                    "response": response_content,
                    "conversation_id": conversation_id,
                    "vision_complete": vision_complete,
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.agent_logger.log_memory_access("conversation_response", "write", 1)
            
            logger.info(f"✅ [{self.name}] Chat complete - Vision complete: {vision_complete}")
            self.agent_logger.log_node_complete("chat", {"vision_complete": vision_complete, "response_length": len(response_content)})
            
            return {
                "message": response_content,
                "vision_complete": vision_complete,
                "execution_log": self.agent_logger.get_execution_log()[-5:]  # Last 5 log entries
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
    
    async def _vision_setting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Define project vision based on user input and market research"""
        vision_input = params.get("vision_input", "")
        if not vision_input:
            return {"error": "No vision input provided", "success": False}
        
        # Get market insights to inform vision
        market_insights = await self._get_market_insights(vision_input)
        
        vision_prompt = f"""
        As a strategic co-founder, I need to craft a compelling vision statement for this idea:
        
        User input: {vision_input}
        Market insights: {market_insights}
        
        Create a structured vision that includes:
        1. A clear, compelling vision statement (1-2 sentences)
        2. The core problem being solved
        3. The target audience and their pain points
        4. The unique value proposition
        5. The long-term impact
        
        Make it specific, inspiring, and aligned with market realities.
        """
        
        vision_result = await self._think(vision_prompt)
        
        # Store vision in memory for future reference
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="vision",
            content=vision_result,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "vision_statement": vision_result.get("vision_statement", ""),
            "core_problem": vision_result.get("core_problem", ""),
            "target_audience": vision_result.get("target_audience", []),
            "unique_value": vision_result.get("unique_value", ""),
            "long_term_impact": vision_result.get("long_term_impact", ""),
            "confidence": 0.9
        }
    
    async def _goal_definition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Define strategic goals for the project"""
        vision = params.get("vision", {})
        timeframe = params.get("timeframe", "12 months")
        
        if not vision:
            # Try to get vision from memory
            vision_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="vision",
                limit=1
            )
            if vision_memory:
                vision = vision_memory[0].get("content", {})
        
        if not vision:
            return {"error": "No vision available for goal definition", "success": False}
        
        goals_prompt = f"""
        Based on this vision:
        {json.dumps(vision, indent=2)}
        
        Define strategic goals for the next {timeframe} that are:
        1. Specific and measurable
        2. Aligned with the vision
        3. Realistic but ambitious
        4. Time-bound
        
        Include both business metrics and product milestones.
        Organize goals by timeframe (3 months, 6 months, 12 months).
        """
        
        goals_result = await self._think(goals_prompt)
        
        # Store goals in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="strategic_goals",
            content=goals_result,
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "short_term_goals": goals_result.get("3_month_goals", []),
            "mid_term_goals": goals_result.get("6_month_goals", []),
            "long_term_goals": goals_result.get("12_month_goals", []),
            "key_metrics": goals_result.get("key_metrics", []),
            "confidence": 0.85
        }
    
    async def _market_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market opportunity and competitive landscape"""
        industry = params.get("industry", "")
        target_audience = params.get("target_audience", [])
        
        if not industry and not target_audience:
            return {"error": "Insufficient information for market analysis", "success": False}
        
        # Use web search for market data
        search_terms = industry or " ".join(target_audience[:2])
        market_data = await self.web_search._arun(f"{search_terms} market size trends competition")
        
        analysis_prompt = f"""
        Analyze this market data:
        {market_data}
        
        Industry: {industry}
        Target audience: {target_audience}
        
        Provide a comprehensive market analysis including:
        1. Market size and growth rate
        2. Key competitors and their strengths/weaknesses
        3. Market trends and opportunities
        4. Potential challenges and threats
        5. Recommended positioning strategy
        
        Be specific and data-driven where possible.
        """
        
        analysis_result = await self._think(analysis_prompt)
        
        # Store analysis in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="market_analysis",
            content=analysis_result,
            is_shared=True,
            confidence=0.8
        )
        
        return {
            "market_size": analysis_result.get("market_size", ""),
            "growth_rate": analysis_result.get("growth_rate", ""),
            "competitors": analysis_result.get("competitors", []),
            "trends": analysis_result.get("trends", []),
            "challenges": analysis_result.get("challenges", []),
            "positioning": analysis_result.get("positioning", ""),
            "confidence": 0.8
        }
    
    async def _strategic_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategic plan based on vision and market analysis"""
        vision = params.get("vision", {})
        market_analysis = params.get("market_analysis", {})
        goals = params.get("goals", {})
        
        # Try to get missing data from memory
        if not vision:
            vision_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="vision",
                limit=1
            )
            if vision_memory:
                vision = vision_memory[0].get("content", {})
                
        if not market_analysis:
            market_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="market_analysis",
                limit=1
            )
            if market_memory:
                market_analysis = market_memory[0].get("content", {})
                
        if not goals:
            goals_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="strategic_goals",
                limit=1
            )
            if goals_memory:
                goals = goals_memory[0].get("content", {})
        
        if not vision or not market_analysis:
            return {"error": "Insufficient information for strategic planning", "success": False}
        
        planning_prompt = f"""
        Create a comprehensive strategic plan based on:
        
        Vision: {json.dumps(vision, indent=2)}
        Market Analysis: {json.dumps(market_analysis, indent=2)}
        Goals: {json.dumps(goals, indent=2)}
        
        Include:
        1. Strategic priorities (top 3-5)
        2. Key initiatives for each priority
        3. Resource requirements
        4. Critical success factors
        5. Risk mitigation strategies
        
        Make it actionable and specific.
        """
        
        plan_result = await self._think(planning_prompt)
        
        # Store plan in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="strategic_plan",
            content=plan_result,
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "strategic_priorities": plan_result.get("strategic_priorities", []),
            "key_initiatives": plan_result.get("key_initiatives", {}),
            "resource_requirements": plan_result.get("resource_requirements", {}),
            "success_factors": plan_result.get("success_factors", []),
            "risk_mitigation": plan_result.get("risk_mitigation", {}),
            "confidence": 0.85
        }
    
    async def _kpi_establishment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Establish key performance indicators for the project"""
        vision = params.get("vision", {})
        goals = params.get("goals", {})
        
        # Try to get missing data from memory
        if not vision:
            vision_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="vision",
                limit=1
            )
            if vision_memory:
                vision = vision_memory[0].get("content", {})
                
        if not goals:
            goals_memory = await self.memory_manager.get_agent_memory(
                agent_name=self.name,
                memory_type="strategic_goals",
                limit=1
            )
            if goals_memory:
                goals = goals_memory[0].get("content", {})
        
        if not vision:
            return {"error": "Insufficient information for KPI establishment", "success": False}
        
        kpi_prompt = f"""
        Based on this vision and goals:
        
        Vision: {json.dumps(vision, indent=2)}
        Goals: {json.dumps(goals, indent=2)}
        
        Establish key performance indicators (KPIs) that:
        1. Align with strategic objectives
        2. Are specific and measurable
        3. Cover different aspects of the business
        4. Include leading and lagging indicators
        
        Organize KPIs by category (e.g., user growth, revenue, product, marketing).
        For each KPI, include a definition, measurement method, and target.
        """
        
        kpi_result = await self._think(kpi_prompt)
        
        # Store KPIs in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="kpis",
            content=kpi_result,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "user_kpis": kpi_result.get("user_kpis", []),
            "revenue_kpis": kpi_result.get("revenue_kpis", []),
            "product_kpis": kpi_result.get("product_kpis", []),
            "marketing_kpis": kpi_result.get("marketing_kpis", []),
            "definitions": kpi_result.get("definitions", {}),
            "targets": kpi_result.get("targets", {}),
            "confidence": 0.9
        }
    
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