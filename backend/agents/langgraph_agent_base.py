"""
LangGraph-based Agent with Internal Node Structure
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

class AgentState(TypedDict):
    """Internal agent state"""
    messages: Annotated[List[BaseMessage], operator.add]
    task: Dict[str, Any]
    context: Dict[str, Any]
    analysis: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    needs_refinement: bool
    iteration: int

class LangGraphAgentBase:
    """Base agent with internal LangGraph workflow"""
    
    def __init__(self, name: str, role: str, memory_manager, approval_manager, personality: Dict[str, Any]):
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.personality = personality
        self.model = personality.get("model", "deepseek/deepseek-chat:free")
        self.temperature = personality.get("temperature", 0.7)
        
        # Create internal workflow
        self.workflow = self._create_internal_workflow()
    
    def _create_internal_workflow(self) -> StateGraph:
        """Create agent's internal thinking workflow"""
        workflow = StateGraph(AgentState)
        
        # Thinking nodes
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("synthesize", self._synthesize_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("refine", self._refine_node)
        
        # Workflow with cycles
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "synthesize")
        workflow.add_edge("synthesize", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_refine,
            {"refine": "refine", "complete": END}
        )
        workflow.add_edge("refine", "analyze")  # Cycle back
        
        return workflow.compile()
    
    async def _analyze_node(self, state: AgentState) -> AgentState:
        """Analyze task and context"""
        task = state["task"]
        context = state["context"]
        
        # Get relevant memory
        private_memory = await self.memory_manager.get_agent_private_memory(self.name, limit=3)
        global_context = await self.memory_manager.get_global_context_for_agent(
            self.name, 
            query=f"{task.get('type', '')} {self.role}"
        )
        
        # Let agent think about the analysis
        analysis_prompt = f"""
        As {self.name}, analyze this task:
        Task: {task}
        Context: {context}
        My previous work: {private_memory}
        Global insights: {global_context}
        
        Think step by step about:
        1. What specific insights can I provide?
        2. How does this relate to my expertise in {self.role}?
        3. What unique value can I add?
        
        Provide structured analysis.
        """
        
        analysis = await self._think(analysis_prompt)
        state["analysis"] = analysis
        state["messages"].append(AIMessage(content=f"{self.name} completed analysis"))
        
        return state
    
    async def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize insights into actionable recommendations"""
        analysis = state["analysis"]
        
        synthesis_prompt = f"""
        Based on my analysis: {analysis}
        
        As {self.name} specializing in {self.role}, synthesize this into:
        1. Key insights and findings
        2. Specific actionable recommendations
        3. Next steps and priorities
        4. Potential risks or considerations
        
        Be specific and actionable, not generic.
        """
        
        synthesis = await self._think(synthesis_prompt)
        state["recommendations"] = synthesis.get("recommendations", [])
        state["messages"].append(AIMessage(content=f"{self.name} synthesized insights"))
        
        return state
    
    async def _validate_node(self, state: AgentState) -> AgentState:
        """Validate quality and completeness"""
        analysis = state["analysis"]
        recommendations = state["recommendations"]
        
        validation_prompt = f"""
        Review my work:
        Analysis: {analysis}
        Recommendations: {recommendations}
        
        Rate quality (1-10) and assess:
        1. Are insights specific and valuable?
        2. Are recommendations actionable?
        3. Is anything missing or unclear?
        4. Should I refine further?
        
        Provide confidence score and refinement needs.
        """
        
        validation = await self._think(validation_prompt)
        state["confidence"] = validation.get("confidence", 0.7)
        state["needs_refinement"] = validation.get("needs_refinement", False)
        state["iteration"] = state.get("iteration", 0) + 1
        
        return state
    
    def _should_refine(self, state: AgentState) -> str:
        """Decide if refinement is needed"""
        if state["needs_refinement"] and state["iteration"] < 3:
            return "refine"
        return "complete"
    
    async def _refine_node(self, state: AgentState) -> AgentState:
        """Refine analysis based on validation"""
        analysis = state["analysis"]
        validation_feedback = state.get("validation_feedback", "")
        
        refinement_prompt = f"""
        My current analysis needs improvement: {analysis}
        Feedback: {validation_feedback}
        
        Refine and improve:
        1. Address identified gaps
        2. Make insights more specific
        3. Enhance actionability
        4. Add missing perspectives
        """
        
        refined_analysis = await self._think(refinement_prompt)
        state["analysis"].update(refined_analysis)
        state["messages"].append(AIMessage(content=f"{self.name} refined analysis"))
        
        return state
    
    async def _think(self, prompt: str) -> Dict[str, Any]:
        """Core thinking method using LLM"""
        try:
            import aiohttp
            import os
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return {"error": "No API key", "fallback": True}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"You are {self.name}, expert in {self.role}. Think deeply and provide structured insights."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.temperature
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Try to parse structured response
                        try:
                            import json
                            return json.loads(content)
                        except:
                            return {"insights": content, "confidence": 0.7}
                    else:
                        return {"error": "API call failed", "fallback": True}
        except Exception as e:
            return {"error": str(e), "fallback": True}
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's internal workflow with resilience"""
        try:
            # Get context with timeout protection
            try:
                context = await asyncio.wait_for(
                    self.memory_manager.get_shared_context(),
                    timeout=10.0  # 10 second timeout
                )
            except (asyncio.TimeoutError, Exception) as e:
                # Use empty context if shared context retrieval fails
                context = {}
                logger.warning(f"[{self.name}] Failed to get shared context: {e}, using empty context")
            
            # Initialize state
            initial_state = AgentState(
                messages=[HumanMessage(content=f"Task: {task}")],
                task=task,
                context=context,
                analysis={},
                recommendations=[],
                confidence=0.0,
                needs_refinement=False,
                iteration=0
            )
            
            # Execute internal workflow
            try:
                final_state = await asyncio.wait_for(
                    self.workflow.ainvoke(initial_state),
                    timeout=60.0  # 60 second timeout for workflow execution
                )
            except asyncio.TimeoutError:
                logger.error(f"[{self.name}] Workflow execution timed out")
                # Create fallback state with basic analysis
                final_state = {
                    "analysis": {"fallback": True, "message": "Workflow execution timed out"},
                    "recommendations": ["Consider retrying the operation"],
                    "confidence": 0.3,
                    "iteration": 1
                }
            except Exception as workflow_error:
                logger.error(f"[{self.name}] Workflow execution failed: {workflow_error}")
                # Create fallback state with error information
                final_state = {
                    "analysis": {"fallback": True, "error": str(workflow_error)},
                    "recommendations": ["Review error and retry"],
                    "confidence": 0.2,
                    "iteration": 1
                }
            
            # Store results in memory with error handling
            try:
                await self._store_results(task, final_state)
            except Exception as store_error:
                logger.error(f"[{self.name}] Failed to store results: {store_error}")
            
            return {
                "status": "completed",
                "output": {
                    "analysis": final_state["analysis"],
                    "recommendations": final_state.get("recommendations", []),
                    "agent": self.name,
                    "iterations": final_state.get("iteration", 1)
                },
                "confidence": final_state.get("confidence", 0.5),
                "agent": self.name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "fallback": True,
                "confidence": 0.1
            }
    
    async def _store_results(self, task: Dict[str, Any], final_state: Dict[str, Any]):
        """Store results in memory systems with error handling"""
        try:
            # Private memory
            await self.memory_manager.store_agent_private_memory(
                agent_name=self.name,
                memory_type="thinking_process",
                content={
                    "task": task,
                    "analysis": final_state.get("analysis", {}),
                    "iterations": final_state.get("iteration", 1),
                    "confidence": final_state.get("confidence", 0.5)
                }
            )
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to store private memory: {e}")
        
        try:
            # Shared memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_insights",
                content=final_state.get("analysis", {}),
                is_shared=True,
                confidence=final_state.get("confidence", 0.5)
            )
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to store shared memory: {e}")