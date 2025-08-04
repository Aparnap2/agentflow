"""
LangGraph-powered agent implementation with efficient state management
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated, Callable, Union, Literal
from datetime import datetime
import operator
import asyncio
import json

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

from loguru import logger
from memory.memory_manager import MemoryManager
from approvals.approval_manager import ApprovalManager
from tools.tool_registry import ToolRegistry
from services.llm_service import llm_service, LLMProvider

class AgentState(TypedDict):
    """Core agent state with efficient message handling"""
    messages: Annotated[List[AnyMessage], add_messages]
    task: Dict[str, Any]
    context: Dict[str, Any]
    analysis: Dict[str, Any]
    tools_output: Dict[str, Any]
    confidence: float
    requires_approval: bool
    iteration: int
    errors: Annotated[List[Dict[str, Any]], operator.add]
    execution_path: Annotated[List[str], operator.add]

class GraphAgent:
    """LangGraph-powered agent with efficient state management"""
    
    def __init__(
        self, 
        name: str, 
        role: str, 
        memory_manager: MemoryManager,
        approval_manager: ApprovalManager,
        personality: Dict[str, Any] = None
    ):
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.personality = personality or {}
        
        # LLM configuration
        self.model = personality.get("model", "deepseek/deepseek-chat:free")
        self.temperature = personality.get("temperature", 0.7)
        
        # Tool configuration
        self.tool_registry = ToolRegistry(name)
        
        # Create the agent's internal workflow
        self.workflow = self._build_agent_workflow()
        logger.info(f"Initialized GraphAgent: {name}")
    
    def _build_agent_workflow(self) -> StateGraph:
        """Build the agent's internal workflow graph"""
        # Create the graph with our state schema
        builder = StateGraph(AgentState)
        
        # Add core nodes
        builder.add_node("analyze", self._analyze_node)
        builder.add_node("plan", self._plan_node)
        builder.add_node("execute_tools", self._execute_tools_node)
        builder.add_node("synthesize", self._synthesize_node)
        builder.add_node("validate", self._validate_node)
        
        # Define the workflow
        builder.set_entry_point("analyze")
        builder.add_edge("analyze", "plan")
        builder.add_edge("plan", "execute_tools")
        builder.add_edge("execute_tools", "synthesize")
        builder.add_edge("synthesize", "validate")
        
        # Add conditional edge from validate
        builder.add_conditional_edges(
            "validate",
            self._should_continue,
            {
                "continue": "analyze",
                "complete": END
            }
        )
        
        return builder.compile()
    
    async def _analyze_node(self, state: AgentState) -> AgentState:
        """Analyze the task and context"""
        task = state["task"]
        context = state["context"]
        
        # Get relevant memory
        private_memory = await self.memory_manager.get_agent_private_memory(self.name, limit=3)
        global_context = await self.memory_manager.get_global_context_for_agent(
            self.name, 
            query=f"{task.get('type', '')} {self.role}"
        )
        
        # Create analysis prompt
        analysis_prompt = f"""
        As {self.name}, analyze this task:
        
        Task: {json.dumps(task)}
        Context: {json.dumps(context)}
        Previous work: {json.dumps(private_memory)}
        Global context: {json.dumps(global_context)}
        
        Think step by step about:
        1. What is the core objective?
        2. What information do I need?
        3. What tools might help me?
        4. What unique insights can I provide?
        
        Provide structured analysis.
        """
        
        # Call LLM
        response = await llm_service.generate_response(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_prompt}
            ],
            agent_name=self.name,
            temperature=self.temperature,
            preferred_provider=LLMProvider.OPENROUTER
        )
        
        # Parse response
        try:
            analysis = json.loads(response.content)
        except:
            analysis = {"insights": response.content, "confidence": 0.7}
        
        # Update state
        state["analysis"] = analysis
        state["messages"].append(AIMessage(content=f"{self.name} analyzed the task"))
        state["execution_path"].append("analyze")
        
        return state
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Plan the approach and tool usage"""
        task = state["task"]
        analysis = state["analysis"]
        
        # Get available tools
        available_tools = self.tool_registry.get_tools()
        tool_names = [tool.name for tool in available_tools]
        
        # Create planning prompt
        planning_prompt = f"""
        Based on my analysis: {json.dumps(analysis)}
        
        I have these tools available: {tool_names}
        
        Create a plan to complete this task:
        1. What specific steps should I take?
        2. Which tools should I use and why?
        3. What information do I need to gather?
        
        Provide a structured plan with clear steps.
        """
        
        # Call LLM
        response = await llm_service.generate_response(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": planning_prompt}
            ],
            agent_name=self.name,
            temperature=self.temperature,
            preferred_provider=LLMProvider.OPENROUTER
        )
        
        # Parse response
        try:
            plan = json.loads(response.content)
        except:
            plan = {"steps": response.content.split("\n"), "tools": tool_names[:2]}
        
        # Update state
        state["plan"] = plan
        state["messages"].append(AIMessage(content=f"{self.name} created a plan"))
        state["execution_path"].append("plan")
        
        return state
    
    async def _execute_tools_node(self, state: AgentState) -> AgentState:
        """Execute selected tools"""
        plan = state.get("plan", {})
        selected_tools = plan.get("tools", [])
        
        # Initialize tools output
        tools_output = {}
        
        # Execute each selected tool
        for tool_name in selected_tools:
            try:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    # Extract parameters from plan
                    params = self._extract_tool_params(plan, tool_name)
                    
                    # Execute tool
                    result = await tool._arun(**params)
                    tools_output[tool_name] = result
                    
                    # Log success
                    logger.info(f"Tool {tool_name} executed successfully")
                else:
                    logger.warning(f"Tool {tool_name} not found")
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tools_output[tool_name] = {"error": str(e)}
                state["errors"].append({"tool": tool_name, "error": str(e)})
        
        # Update state
        state["tools_output"] = tools_output
        state["messages"].append(AIMessage(content=f"{self.name} executed tools: {', '.join(tools_output.keys())}"))
        state["execution_path"].append("execute_tools")
        
        return state
    
    async def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize insights from analysis and tool outputs"""
        analysis = state["analysis"]
        tools_output = state["tools_output"]
        
        # Create synthesis prompt
        synthesis_prompt = f"""
        Based on my analysis: {json.dumps(analysis)}
        And tool outputs: {json.dumps(tools_output)}
        
        Synthesize the key insights and create recommendations:
        1. What are the most important findings?
        2. What specific recommendations can I make?
        3. What are the next steps?
        
        Provide structured insights and actionable recommendations.
        """
        
        # Call LLM
        response = await llm_service.generate_response(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": synthesis_prompt}
            ],
            agent_name=self.name,
            temperature=self.temperature,
            preferred_provider=LLMProvider.OPENROUTER
        )
        
        # Parse response
        try:
            synthesis = json.loads(response.content)
        except:
            synthesis = {"insights": response.content, "recommendations": []}
        
        # Update state
        state["synthesis"] = synthesis
        state["messages"].append(AIMessage(content=f"{self.name} synthesized insights"))
        state["execution_path"].append("synthesize")
        
        return state
    
    async def _validate_node(self, state: AgentState) -> AgentState:
        """Validate the quality of the results"""
        synthesis = state.get("synthesis", {})
        iteration = state.get("iteration", 0)
        
        # Create validation prompt
        validation_prompt = f"""
        Review my work:
        Synthesis: {json.dumps(synthesis)}
        Iteration: {iteration}
        
        Evaluate the quality (1-10) and assess:
        1. Is the analysis thorough and insightful?
        2. Are the recommendations specific and actionable?
        3. Is anything missing or unclear?
        4. Should I continue iterating or is this complete?
        
        Provide a confidence score and completion assessment.
        """
        
        # Call LLM
        response = await llm_service.generate_response(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": validation_prompt}
            ],
            agent_name=self.name,
            temperature=self.temperature,
            preferred_provider=LLMProvider.OPENROUTER
        )
        
        # Parse response
        try:
            validation = json.loads(response.content)
        except:
            validation = {"confidence": 0.7, "complete": iteration >= 2}
        
        # Update state
        state["confidence"] = validation.get("confidence", 0.7)
        state["requires_approval"] = state["confidence"] < 0.6
        state["iteration"] = iteration + 1
        state["messages"].append(AIMessage(content=f"{self.name} validated results with confidence {state['confidence']}"))
        state["execution_path"].append("validate")
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if the agent should continue iterating"""
        iteration = state.get("iteration", 0)
        confidence = state.get("confidence", 0)
        
        # Continue if confidence is low and we haven't exceeded max iterations
        if confidence < 0.7 and iteration < 3:
            return "continue"
        return "complete"
    
    def _get_system_prompt(self) -> str:
        """Get the agent's system prompt"""
        return f"""You are {self.name}, a {self.role} agent.

Your personality traits:
- Tone: {self.personality.get('tone', 'professional')}
- Focus: {self.personality.get('focus', 'task completion')}
- Expertise: {', '.join(self.personality.get('expertise', []))}

Your role is to {self.personality.get('description', 'complete assigned tasks effectively')}.

Always provide structured, actionable outputs that other agents can build upon.
Be thorough but concise. If you're uncertain, indicate your confidence level.
"""
    
    def _extract_tool_params(self, plan: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """Extract parameters for a tool from the plan"""
        # Default implementation - override in subclasses for specific parameter extraction
        return {}
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent workflow"""
        try:
            # Get context
            context = await self.memory_manager.get_shared_context()
            
            # Initialize state
            initial_state = AgentState(
                messages=[HumanMessage(content=f"Task: {json.dumps(task)}")],
                task=task,
                context=context,
                analysis={},
                tools_output={},
                confidence=0.0,
                requires_approval=False,
                iteration=0,
                errors=[],
                execution_path=[]
            )
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Store results in memory
            await self._store_results(task, final_state)
            
            # Prepare result
            result = {
                "status": "completed",
                "output": final_state.get("synthesis", {}),
                "confidence": final_state.get("confidence", 0.0),
                "requires_approval": final_state.get("requires_approval", False),
                "agent": self.name,
                "execution_path": final_state.get("execution_path", []),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    async def _store_results(self, task: Dict[str, Any], final_state: AgentState):
        """Store results in memory systems"""
        # Store in private memory
        await self.memory_manager.store_agent_private_memory(
            agent_name=self.name,
            memory_type="task_result",
            content={
                "task": task,
                "synthesis": final_state.get("synthesis", {}),
                "confidence": final_state.get("confidence", 0.0),
                "execution_path": final_state.get("execution_path", []),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Store in shared memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type=f"{self.name.lower()}_output",
            content=final_state.get("synthesis", {}),
            is_shared=True,
            confidence=final_state.get("confidence", 0.0)
        )