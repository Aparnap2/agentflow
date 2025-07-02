"""
Enhanced LangGraphAgent with autonomy features
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import aiohttp
from loguru import logger
from langchain.tools import BaseTool as LCBaseTool
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from memory.memory_manager import MemoryManager
from memory.context_manager import ContextManager
from memory.state_manager import StateManager
from collaboration.collaboration_manager import CollaborationManager
from tools.tool_registry import ToolRegistry
from tools.dynamic_tool_selector import DynamicToolSelector
from approvals.approval_manager import ApprovalManager


class EnhancedAgentState(TypedDict):
    """Enhanced state structure for LangGraph agents"""
    messages: List[BaseMessage]
    task: Dict[str, Any]
    context: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    requires_approval: bool
    agent_name: str
    retry_count: int
    selected_tools: List[str]
    working_memory: Dict[str, Any]
    collaboration_requests: List[Dict[str, Any]]


class LangGraphAgentV2:
    """Enhanced LangGraph agent with autonomy features"""
    
    def __init__(
        self, 
        name: str, 
        role: str, 
        memory_manager: MemoryManager,
        approval_manager: ApprovalManager,
        personality: Dict[str, Any],
        state_manager: Optional[StateManager] = None,
        context_manager: Optional[ContextManager] = None,
        collaboration_manager: Optional[CollaborationManager] = None
    ):
        """Initialize the enhanced agent
        
        Args:
            name: Agent name
            role: Agent role description
            memory_manager: Memory manager for storing and retrieving agent memory
            approval_manager: Approval manager for handling approval workflows
            personality: Agent personality settings
            state_manager: Optional state manager for persisting state
            context_manager: Optional context manager for retrieving context
            collaboration_manager: Optional collaboration manager for inter-agent communication
        """
        self.name = name
        self.role = role
        self.memory_manager = memory_manager
        self.approval_manager = approval_manager
        self.personality = personality
        
        # Initialize optional components
        self.state_manager = state_manager
        self.context_manager = context_manager
        self.collaboration_manager = collaboration_manager
        
        # Initialize OpenRouter configuration
        self.model = personality.get("model", "deepseek/deepseek-chat:free")
        self.api_key = self._get_openrouter_key()
        self.temperature = personality.get("temperature", 0.7)
        self.max_tokens = personality.get("max_tokens", 2000)
        
        # Initialize tool components
        self.tool_registry = ToolRegistry(name)
        self.tool_selector = DynamicToolSelector(self.tool_registry)
        
        # Register collaboration handler if collaboration manager exists
        if self.collaboration_manager:
            asyncio.create_task(
                self.collaboration_manager.register_agent(
                    self.name, self._handle_collaboration_message
                )
            )
        
        logger.info(f"Initialized enhanced LangGraph agent: {name}")
    
    def _get_openrouter_key(self) -> str:
        """Get OpenRouter API key from environment"""
        import os
        return os.getenv("OPENROUTER_API_KEY", "")
    
    def _get_system_prompt(self) -> str:
        """Get agent's system prompt based on personality"""
        return f"""You are {self.name}, a {self.role} in a virtual AI office.

Your personality traits:
- Tone: {self.personality.get('tone', 'professional')}
- Focus: {self.personality.get('focus', 'task completion')}
- Expertise: {', '.join(self.personality.get('expertise', []))}

Your role is to {self.personality.get('description', 'complete assigned tasks effectively')}.

Always provide structured, actionable outputs that other agents can build upon.
Be thorough but concise. If you're uncertain, indicate your confidence level.

You have access to tools that you can use to help complete tasks.
Use tools when appropriate, but don't use tools for simple reasoning tasks.
"""
    
    async def _call_openrouter_with_tools(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[LCBaseTool]
    ) -> Dict[str, Any]:
        """Make a direct API call to OpenRouter with tools
        
        Args:
            messages: List of messages for the conversation
            tools: List of tools to make available
            
        Returns:
            Dict[str, Any]: OpenRouter API response
        """
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://agentflow.ai",
                    "X-Title": "AgentFlow"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "tools": [self._convert_tool_to_dict(tool) for tool in tools]
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {error_text}")
                return await response.json()
    
    def _convert_tool_to_dict(self, tool: LCBaseTool) -> Dict[str, Any]:
        """Convert a tool to OpenRouter-compatible format
        
        Args:
            tool: LangChain tool
            
        Returns:
            Dict[str, Any]: Tool in OpenRouter format
        """
        # Basic structure
        tool_dict = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description
            }
        }
        
        # Try to extract parameters from tool schema
        try:
            if hasattr(tool, "args_schema") and tool.args_schema:
                schema = tool.args_schema.schema()
                tool_dict["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for name, prop in schema.get("properties", {}).items():
                    tool_dict["function"]["parameters"]["properties"][name] = {
                        "type": prop.get("type", "string"),
                        "description": prop.get("description", "")
                    }
                    
                    # Add required parameters
                    if name in schema.get("required", []):
                        tool_dict["function"]["parameters"]["required"].append(name)
        except Exception as e:
            logger.warning(f"Failed to extract tool schema for {tool.name}: {e}")
        
        return tool_dict
    
    async def _handle_collaboration_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming collaboration message
        
        Args:
            message: Message from another agent
            
        Returns:
            Optional[Dict[str, Any]]: Optional response data
        """
        message_type = message.get("type", "")
        from_agent = message.get("from", "")
        content = message.get("content", {})
        
        logger.info(f"Received {message_type} from {from_agent}")
        
        # Handle different message types
        if message_type == "data_request":
            # Process request for data
            request_id = content.get("request_id", "")
            data_type = content.get("data_type", "")
            parameters = content.get("parameters", {})
            
            # Get requested data
            response_data = await self._process_data_request(data_type, parameters)
            
            # Provide response if collaboration manager exists
            if self.collaboration_manager:
                await self.collaboration_manager.provide_response(
                    from_agent=self.name,
                    request_id=request_id,
                    data=response_data,
                    workflow_id=message.get("workflow_id")
                )
            
            return response_data
            
        elif message_type.startswith("notification_"):
            # Process notification
            notification_type = message_type.replace("notification_", "")
            await self._process_notification(notification_type, content.get("data", {}), from_agent)
            return {"status": "received"}
        
        return None
    
    async def _process_data_request(
        self, 
        data_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a data request from another agent
        
        Args:
            data_type: Type of data requested
            parameters: Request parameters
            
        Returns:
            Dict[str, Any]: Response data
        """
        # Handle different data types
        if data_type == "agent_context":
            # Return agent context
            if self.context_manager:
                return await self.context_manager.get_working_memory(self.name)
            return {"status": "error", "message": "Context manager not available"}
            
        elif data_type == "memory_query":
            # Query agent memory
            query = parameters.get("query", "")
            memory_type = parameters.get("memory_type")
            limit = parameters.get("limit", 5)
            
            results = await self.memory_manager.query_agent_memory(
                agent_name=self.name,
                memory_type=memory_type,
                limit=limit
            )
            
            return {"results": results, "query": query}
            
        elif data_type == "specialized_knowledge":
            # Return specialized knowledge based on agent role
            return {
                "agent": self.name,
                "role": self.role,
                "expertise": self.personality.get("expertise", []),
                "data": {
                    "knowledge_areas": self.personality.get("knowledge_areas", []),
                    "capabilities": self.personality.get("capabilities", [])
                }
            }
        
        # Default response for unknown data types
        return {
            "status": "error", 
            "message": f"Unknown data type: {data_type}"
        }
    
    async def _process_notification(
        self, 
        notification_type: str, 
        data: Dict[str, Any],
        from_agent: str
    ):
        """Process a notification from another agent
        
        Args:
            notification_type: Type of notification
            data: Notification data
            from_agent: Agent that sent the notification
        """
        # Store notification in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type=f"notification_{notification_type}",
            content={
                "from": from_agent,
                "type": notification_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            },
            is_shared=False  # Private to this agent
        )
        
        # Handle different notification types
        if notification_type == "task_update":
            # Task status has been updated
            logger.info(f"Task update notification from {from_agent}: {data.get('status')}")
            
        elif notification_type == "knowledge_share":
            # Knowledge has been shared
            # Store in vector memory for future reference
            if hasattr(self.memory_manager, "vector_memory"):
                await self.memory_manager.vector_memory.store_document(
                    text=json.dumps(data),
                    metadata={
                        "type": "shared_knowledge",
                        "from_agent": from_agent,
                        "timestamp": datetime.now().isoformat()
                    },
                    agent=self.name
                )
    
    async def request_data_from_agent(
        self,
        to_agent: str,
        data_type: str,
        parameters: Dict[str, Any],
        workflow_id: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """Request data from another agent
        
        Args:
            to_agent: Agent to request data from
            data_type: Type of data being requested
            parameters: Request parameters
            workflow_id: Optional workflow identifier
            timeout: Maximum time to wait for response
            
        Returns:
            Optional[Dict[str, Any]]: Requested data or None if request failed
        """
        if not self.collaboration_manager:
            logger.warning(f"Cannot request data from {to_agent}: Collaboration manager not available")
            return None
            
        return await self.collaboration_manager.request_data(
            from_agent=self.name,
            to_agent=to_agent,
            data_type=data_type,
            parameters=parameters,
            workflow_id=workflow_id,
            timeout=timeout
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent workflow
        
        Args:
            task: Task to execute
            
        Returns:
            Dict[str, Any]: Execution results
        """
        try:
            # Enrich task with context if context manager exists
            enriched_task = task
            if self.context_manager:
                enriched_task = await self.context_manager.enrich_task_context(
                    task=task,
                    agent_name=self.name
                )
            
            # Select tools for task
            tools = await self.tool_selector.select_tools_for_task(
                task=enriched_task,
                context=enriched_task.get("context", {}),
                agent_name=self.name
            )
            
            # Get working memory if context manager exists
            working_memory = {}
            if self.context_manager:
                working_memory = await self.context_manager.get_working_memory(
                    agent_name=self.name,
                    current_task=enriched_task
                )
            
            # Create state
            state = {
                "task": enriched_task,
                "context": enriched_task.get("context", {}),
                "outputs": {},
                "working_memory": working_memory
            }
            
            # Convert state to messages format for OpenRouter
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": json.dumps({
                    "task": enriched_task,
                    "context": enriched_task.get("context", {}),
                    "working_memory": working_memory
                })}
            ]
            
            # Call OpenRouter API with tools
            response = await self._call_openrouter_with_tools(messages, tools)
            response_content = response["choices"][0]["message"]["content"]
            
            # Check for tool calls
            tool_calls = response["choices"][0]["message"].get("tool_calls", [])
            
            # If tool calls exist, execute them
            if tool_calls:
                tool_results = await self._execute_tool_calls(tool_calls, tools)
                
                # Add tool results to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # Add tool results to messages
                for tool_call_id, result in tool_results.items():
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result
                    })
                
                # Ask for final response with tool results
                messages.append({
                    "role": "user",
                    "content": "Please provide your final analysis and recommendations based on the task and tool results."
                })
                
                # Call OpenRouter API again
                response = await self._call_openrouter_with_tools(messages, [])
                response_content = response["choices"][0]["message"]["content"]
            
            # Try to parse JSON, fallback to structured text
            try:
                action_results = json.loads(response_content)
            except json.JSONDecodeError:
                # Create structured output from text response
                action_results = {
                    "analysis": response_content,
                    "agent": self.name,
                    "task_type": task.get("type", "general"),
                    "recommendations": ["Analysis completed"],
                    "confidence": 0.7
                }
            
            # Calculate confidence based on response
            confidence = float(response.get("choices", [{}])[0].get("finish_reason", "") == "stop") * 0.8
            
            # Store results in memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type=f"{self.name.lower()}_output",
                content=action_results,
                is_shared=True,
                confidence=confidence,
                metadata={"task_id": task.get("id")}
            )
            
            # Persist task state if state manager exists
            if self.state_manager and "id" in task:
                await self.state_manager.persist_agent_state(
                    agent_name=self.name,
                    state_key=f"task_{task['id']}",
                    state_data={
                        "task": task,
                        "result": action_results,
                        "confidence": confidence,
                        "completed_at": datetime.now().isoformat()
                    }
                )
            
            return {
                "status": "completed",
                "output": action_results,
                "confidence": confidence,
                "requires_approval": confidence < 0.6,
                "agent": self.name,
                "task_id": task.get("id"),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{self.name} execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "task_id": task.get("id")
            }
    
    async def _execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]], 
        tools: List[LCBaseTool]
    ) -> Dict[str, str]:
        """Execute tool calls
        
        Args:
            tool_calls: Tool calls from OpenRouter
            tools: Available tools
            
        Returns:
            Dict[str, str]: Tool results by tool_call_id
        """
        # Map tools by name for easy lookup
        tools_by_name = {tool.name: tool for tool in tools}
        
        # Execute each tool call
        results = {}
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id")
            function = tool_call.get("function", {})
            tool_name = function.get("name")
            
            # Parse arguments
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            
            # Execute tool if available
            if tool_name in tools_by_name:
                tool = tools_by_name[tool_name]
                try:
                    # Execute tool
                    result = await tool._arun(**arguments)
                    results[tool_call_id] = result
                except Exception as e:
                    results[tool_call_id] = f"Error executing tool: {str(e)}"
            else:
                results[tool_call_id] = f"Tool {tool_name} not available"
        
        return results
    
    async def chat(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Handle conversational interaction with the agent
        
        Args:
            message: User message
            conversation_id: Optional conversation identifier
            conversation_history: Optional conversation history
            
        Returns:
            Dict[str, Any]: Agent response
        """
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.name}"
                
            # Initialize or retrieve conversation state
            conversation_state = None
            if self.state_manager:
                conversation_state = await self.state_manager.retrieve_conversation(conversation_id)
                
            if not conversation_state:
                conversation_state = {
                    "messages": [],
                    "agent": self.name,
                    "status": "active",
                    "created_at": datetime.now().isoformat()
                }
                
            # Use provided history or state history
            if conversation_history:
                messages = conversation_history
            else:
                messages = conversation_state.get("messages", [])
                
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Select tools for conversation
            tools = await self.tool_selector.get_recommended_tools(
                query=message,
                agent_name=self.name,
                max_tools=3
            )
            
            # Prepare messages for OpenRouter
            openrouter_messages = [{"role": "system", "content": self._get_system_prompt()}]
            
            # Add conversation history
            for msg in messages:
                openrouter_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
                
            # Call OpenRouter API
            response = await self._call_openrouter_with_tools(openrouter_messages, tools)
            response_message = response["choices"][0]["message"]
            response_content = response_message["content"]
            
            # Check for tool calls
            tool_calls = response_message.get("tool_calls", [])
            
            # If tool calls exist, execute them
            if tool_calls:
                tool_results = await self._execute_tool_calls(tool_calls, tools)
                
                # Add tool calls to messages
                openrouter_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # Add tool results to messages
                for tool_call_id, result in tool_results.items():
                    openrouter_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result
                    })
                
                # Ask for final response with tool results
                openrouter_messages.append({
                    "role": "user",
                    "content": "Please provide your final response based on the tool results."
                })
                
                # Call OpenRouter API again
                response = await self._call_openrouter_with_tools(openrouter_messages, [])
                response_content = response["choices"][0]["message"]["content"]
                
            # Add assistant response to conversation
            messages.append({"role": "assistant", "content": response_content})
            
            # Update conversation state
            conversation_state["messages"] = messages
            conversation_state["last_updated"] = datetime.now().isoformat()
            
            # Persist conversation state
            if self.state_manager:
                await self.state_manager.persist_conversation(conversation_id, conversation_state)
            
            # Store in memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="conversation",
                content={
                    "conversation_id": conversation_id,
                    "user_message": message,
                    "response": response_content,
                    "timestamp": datetime.now().isoformat()
                },
                is_shared=True
            )
            
            return {
                "message": response_content,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            return {
                "message": f"I apologize, but I encountered an error: {str(e)}",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status
        
        Returns:
            Dict[str, Any]: Agent status information
        """
        return {
            "name": self.name,
            "role": self.role,
            "status": "ready",
            "current_task": None,
            "outputs_ready": False,
            "capabilities": self.personality.get("capabilities", []),
            "tools_available": len(self.tool_registry.get_tools())
        }
    
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration
        
        Args:
            config: New configuration settings
        """
        if 'temperature' in config:
            self.personality['temperature'] = config['temperature']
            self.temperature = config['temperature']
        if 'confidenceThreshold' in config:
            self.personality['confidence_threshold'] = config['confidenceThreshold']
        if 'model' in config:
            self.personality['model'] = config['model']
            self.model = config['model']
    
    def get_config(self) -> Dict[str, Any]:
        """Get current agent configuration
        
        Returns:
            Dict[str, Any]: Agent configuration
        """
        return {
            "approvalMode": "manual",
            "priority": "medium", 
            "temperature": self.personality.get('temperature', 0.7),
            "confidenceThreshold": self.personality.get('confidence_threshold', 0.8),
            "maxRetries": 3,
            "enabled": True,
            "model": self.model
        }
