"""
Core LangGraph implementation with optimized performance and caching
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import operator
import json
import asyncio
from functools import lru_cache

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

from loguru import logger
from services.llm_service import llm_service, LLMProvider

# Global context cache with TTL
class ContextCache:
    """Cache for global context with TTL"""
    _cache = {}
    _last_updated = {}
    _ttl = 300  # 5 minutes default TTL
    
    @classmethod
    async def get(cls, key: str, fetch_func):
        """Get from cache or fetch and cache"""
        now = datetime.now().timestamp()
        
        # Return from cache if valid
        if key in cls._cache and now - cls._last_updated.get(key, 0) < cls._ttl:
            logger.debug(f"Cache hit for {key}")
            return cls._cache[key]
        
        # Fetch and cache
        logger.debug(f"Cache miss for {key}, fetching...")
        result = await fetch_func()
        cls._cache[key] = result
        cls._last_updated[key] = now
        return result
    
    @classmethod
    def invalidate(cls, key: str = None):
        """Invalidate cache for key or all"""
        if key:
            if key in cls._cache:
                del cls._cache[key]
                del cls._last_updated[key]
        else:
            cls._cache.clear()
            cls._last_updated.clear()

# Optimized state schema
class AgentState(TypedDict):
    """Optimized state schema for LangGraph agents"""
    messages: Annotated[List[AnyMessage], add_messages]
    task: Dict[str, Any]
    context: Dict[str, Any]
    execution_path: Annotated[List[str], operator.add]
    iteration: int
    confidence: float

# Efficient LLM calling with caching for similar prompts
@lru_cache(maxsize=100)
async def _cached_llm_call(system_prompt: str, user_prompt: str, agent_name: str, temperature: float):
    """Cached LLM call for repeated similar prompts"""
    try:
        response = await llm_service.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            agent_name=agent_name,
            temperature=temperature,
            preferred_provider=LLMProvider.OPENROUTER
        )
        return response.content, response.confidence
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"Error: {str(e)}", 0.0

class GraphAgent:
    """Efficient LangGraph agent with caching"""
    
    def __init__(self, name, role, memory_manager, approval_manager, personality=None):
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.personality = personality or {}
        self.temperature = personality.get("temperature", 0.7)
        
        # Lazy initialization of workflow
        self.workflow = None
        
        # Initialize cache
        self._private_memory_cache = {}
        self._last_memory_fetch = 0
        self._memory_ttl = 60  # 1 minute TTL for private memory
    
    def _build_workflow(self):
        """Build efficient workflow graph"""
        builder = StateGraph(AgentState)
        
        # Add minimal set of nodes
        builder.add_node("analyze", self._analyze_node)
        builder.add_node("execute", self._execute_node)
        builder.add_node("synthesize", self._synthesize_node)
        
        # Simple linear flow
        builder.set_entry_point("analyze")
        builder.add_edge("analyze", "execute")
        builder.add_edge("execute", "synthesize")
        builder.add_edge("synthesize", END)
        
        return builder.compile()
    
    def _get_system_prompt(self):
        """Get system prompt"""
        return f"""You are {self.name}, a {self.role} agent.
Your expertise: {', '.join(self.personality.get('expertise', []))}
Provide structured, actionable outputs."""
    
    async def _get_cached_context(self):
        """Get cached global context"""
        return await ContextCache.get(
            f"global_context_{self.name}",
            lambda: self.memory_manager.get_global_context_for_agent(self.name, "")
        )
    
    async def _get_cached_private_memory(self):
        """Get cached private memory"""
        now = datetime.now().timestamp()
        if now - self._last_memory_fetch > self._memory_ttl:
            self._private_memory_cache = await self.memory_manager.get_agent_private_memory(self.name, limit=5)
            self._last_memory_fetch = now
        return self._private_memory_cache
    
    async def _analyze_node(self, state):
        """Analyze task with cached context"""
        task = state["task"]
        
        # Get cached context
        context = await self._get_cached_context()
        private_memory = await self._get_cached_private_memory()
        
        # Create minimal prompt
        prompt = f"""Analyze this task: {json.dumps(task)}
Use your expertise as {self.role} to identify key insights."""
        
        # Call LLM with caching
        content, confidence = await _cached_llm_call(
            self._get_system_prompt(), 
            prompt,
            self.name,
            self.temperature
        )
        
        # Parse response
        try:
            analysis = json.loads(content)
        except:
            analysis = {"insights": content}
        
        # Update state
        state["analysis"] = analysis
        state["context"] = context
        state["private_memory"] = private_memory
        state["execution_path"].append("analyze")
        
        return state
    
    async def _execute_node(self, state):
        """Execute task based on analysis"""
        analysis = state["analysis"]
        
        # Create execution prompt
        prompt = f"""Based on analysis: {json.dumps(analysis)}
Create an execution plan with specific actions."""
        
        # Call LLM
        content, confidence = await _cached_llm_call(
            self._get_system_prompt(),
            prompt,
            self.name,
            self.temperature
        )
        
        # Parse response
        try:
            execution = json.loads(content)
        except:
            execution = {"plan": content}
        
        # Update state
        state["execution"] = execution
        state["execution_path"].append("execute")
        
        return state
    
    async def _synthesize_node(self, state):
        """Synthesize final output"""
        analysis = state["analysis"]
        execution = state["execution"]
        
        # Create synthesis prompt
        prompt = f"""Synthesize final output based on:
Analysis: {json.dumps(analysis)}
Execution: {json.dumps(execution)}

Provide structured recommendations."""
        
        # Call LLM
        content, confidence = await _cached_llm_call(
            self._get_system_prompt(),
            prompt,
            self.name,
            self.temperature
        )
        
        # Parse response
        try:
            synthesis = json.loads(content)
        except:
            synthesis = {"recommendations": content}
        
        # Update state
        state["synthesis"] = synthesis
        state["confidence"] = confidence
        state["execution_path"].append("synthesize")
        
        return state
    
    async def execute(self, task):
        """Execute agent workflow"""
        try:
            # Initialize state
            state = AgentState(
                messages=[HumanMessage(content=f"Task: {json.dumps(task)}")],
                task=task,
                context={},
                execution_path=[],
                iteration=0,
                confidence=0.0
            )
            
            # Lazy initialize workflow if needed
            if self.workflow is None:
                self.workflow = self._build_workflow()
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(state)
            
            # Store result in memory (async)
            asyncio.create_task(self._store_result(task, final_state))
            
            return {
                "status": "completed",
                "output": final_state.get("synthesis", {}),
                "confidence": final_state.get("confidence", 0.7),
                "agent": self.name
            }
        except Exception as e:
            logger.error(f"{self.name} execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _store_result(self, task, final_state):
        """Store result in memory asynchronously"""
        try:
            # Store in private memory
            await self.memory_manager.store_agent_private_memory(
                agent_name=self.name,
                memory_type="task_result",
                content=final_state.get("synthesis", {})
            )
            
            # Store in shared memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_output",
                content=final_state.get("synthesis", {}),
                is_shared=True
            )
            
            # Invalidate cache
            ContextCache.invalidate(f"global_context_{self.name}")
        except Exception as e:
            logger.error(f"Failed to store result: {e}")

class GraphOrchestrator:
    """Efficient orchestrator with caching"""
    
    def __init__(self, memory_manager, approval_manager, agents):
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.agents = agents
        
        # Lazy initialization of workflow
        self.workflow = None
    
    def _build_workflow(self):
        """Build orchestrator workflow"""
        # Define workflow state
        class WorkflowState(TypedDict):
            messages: Annotated[List[AnyMessage], add_messages]
            project_vision: str
            shared_context: Dict[str, Any]
            agent_outputs: Dict[str, Dict]
            current_agent: str
            execution_path: Annotated[List[str], operator.add]
        
        # Create graph
        builder = StateGraph(WorkflowState)
        
        # Add nodes
        builder.add_node("supervisor", self._supervisor_node)
        
        # Add agent nodes
        for agent_name in self.agents:
            builder.add_node(agent_name, self._create_agent_node(agent_name))
        
        # Add end node
        builder.add_node("end", self._end_node)
        
        # Set entry point
        builder.set_entry_point("supervisor")
        
        # Connect supervisor to agents
        for agent_name in self.agents:
            builder.add_conditional_edges(
                "supervisor",
                lambda state, agent=agent_name: state["current_agent"] == agent,
                {True: agent_name, False: None}
            )
        
        # Connect supervisor to end
        builder.add_conditional_edges(
            "supervisor",
            lambda state: state["current_agent"] == "end",
            {True: "end", False: None}
        )
        
        # Connect agents back to supervisor
        for agent_name in self.agents:
            builder.add_edge(agent_name, "supervisor")
        
        # Connect end to END
        builder.add_edge("end", END)
        
        return builder.compile()
    
    async def _supervisor_node(self, state):
        """Supervisor node with efficient routing"""
        # Get completed agents
        completed = set(state.get("agent_outputs", {}).keys())
        
        # Determine next agent
        if "cofounder" not in completed:
            next_agent = "cofounder"
        elif "manager" not in completed and "cofounder" in completed:
            next_agent = "manager"
        elif "manager" in completed:
            specialists = ["product", "finance", "marketing", "legal"]
            pending = [s for s in specialists if s not in completed]
            next_agent = pending[0] if pending else "end"
        
        # Update state
        state["current_agent"] = next_agent
        state["execution_path"].append(next_agent)
        
        return state
    
    def _create_agent_node(self, agent_name):
        """Create agent node function"""
        async def agent_node(state):
            agent = self.agents.get(agent_name)
            
            # Prepare task
            task = {
                "type": agent_name,
                "vision": state.get("project_vision", ""),
                "context": state.get("shared_context", {})
            }
            
            # Execute agent
            result = await agent.execute(task)
            
            # Update state
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}
            state["agent_outputs"][agent_name] = result
            
            return state
        
        return agent_node
    
    async def _end_node(self, state):
        """End node"""
        # Add final message
        state["messages"].append(AIMessage(content="Workflow completed"))
        return state
    
    async def execute_workflow(self, initial_state, config=None):
        """Execute workflow with caching"""
        try:
            # Initialize state
            state = {
                "messages": [],
                "project_vision": initial_state.get("project_vision", ""),
                "shared_context": initial_state.get("shared_context", {}),
                "agent_outputs": {},
                "current_agent": "",
                "execution_path": []
            }
            
            # Lazy initialize workflow if needed
            if self.workflow is None:
                self.workflow = self._build_workflow()
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(state)
            
            return {
                "status": "completed",
                "agent_outputs": final_state.get("agent_outputs", {}),
                "execution_path": final_state.get("execution_path", [])
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {"status": "error", "error": str(e)}