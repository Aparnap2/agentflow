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
            
            # Get relevant global context using RAG
            logger.info(f"🔍 [{self.name}] Retrieving global context via RAG...")
            global_context = await self.memory_manager.get_global_context_for_agent(
                agent_name=self.name,
                query=message
            )
            self.agent_logger.log_memory_access("global_context_rag", "read", len(str(global_context)))
            
            # After 3+ exchanges with sufficient detail, provide final structured plan
            has_key_info = any(keyword in message.lower() for keyword in ['target', 'user', 'customer', 'market', 'problem', 'solution', 'revenue', 'business'])
            
            if conversation_length >= 3 and has_key_info:
                chat_prompt = f"""Based on our conversation and global context, provide a FINAL STRUCTURED PLAN:
                
User's latest: {message}
Global context: {global_context.get('shared_context', {})}
                
## 🚀 VISION SUMMARY
[Summarize their startup vision]

## 🎯 TARGET USERS  
[Define primary user segments]

## 📊 MARKET OPPORTUNITY
[Market size and competition]

## 🔄 EXECUTION PHASES

### Phase 1: Foundation (Weeks 1-2)
- Product Agent: Analyze user needs and MVP features
- Finance Agent: Create financial projections and funding strategy

### Phase 2: Development (Weeks 3-4)  
- Marketing Agent: Develop content strategy and campaigns
- Legal Agent: Handle compliance and legal requirements

## 📋 NEXT STEPS
Ready to distribute tasks to specialist agents.

**Vision is ready for approval!**
                """
                vision_complete = True
            else:
                # Get previous conversation context from private memory
                logger.info(f"📚 [{self.name}] Retrieving conversation history...")
                prev_conversations = await self.memory_manager.get_agent_private_memory(
                    agent_name=self.name,
                    memory_type="conversation",
                    limit=5
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
                
                chat_prompt = f"""You are Alex Chen, an experienced startup cofounder. Continue this strategic conversation:
                
User's message: {message}
Previous context: {prev_conversations}
                
Ask 2-3 SPECIFIC questions focusing on: {', '.join(focus_areas)}
                
Be direct and strategic. Examples:
- "Who exactly are your first 100 customers?"
- "What's your unfair advantage over [specific competitor]?"
- "How will you make money in month 1 vs year 1?"
- "What problem costs your users $X per month right now?"
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