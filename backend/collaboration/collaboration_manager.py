"""
CollaborationManager - Enhanced agent collaboration with dynamic messaging
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from loguru import logger

from memory.memory_manager import MemoryManager
from memory.state_manager import StateManager

class CollaborationManager:
    """Manages dynamic collaboration between agents with messaging and context sharing"""
    
    def __init__(self, memory_manager: MemoryManager, state_manager: StateManager):
        """Initialize collaboration manager
        
        Args:
            memory_manager: Memory manager for storing and retrieving agent memory
            state_manager: State manager for persisting collaboration state
        """
        self.memory_manager = memory_manager
        self.state_manager = state_manager
        self.active_collaborations = {}
        self.message_handlers = {}
        
    async def register_agent(self, agent_name: str, message_handler: Callable):
        """Register an agent for collaboration
        
        Args:
            agent_name: Name of the agent being registered
            message_handler: Callback function to handle incoming messages
        """
        self.message_handlers[agent_name] = message_handler
        logger.info(f"Registered agent {agent_name} for collaboration")
        
    async def send_message(
        self, 
        from_agent: str, 
        to_agent: str, 
        message_type: str, 
        content: Dict[str, Any],
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message from one agent to another
        
        Args:
            from_agent: Name of the sending agent
            to_agent: Name of the receiving agent
            message_type: Type of message (request, response, notification)
            content: Message content
            workflow_id: Optional workflow identifier
            
        Returns:
            Dict[str, Any]: Status and message information
        """
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{from_agent}_{to_agent}"
        
        message = {
            "id": message_id,
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "status": "sent"
        }
        
        # Store message in memory for both agents
        await self.memory_manager.store_agent_memory(
            agent_name=from_agent,
            memory_type="sent_message",
            content=message,
            is_shared=True
        )
        
        await self.memory_manager.store_agent_memory(
            agent_name=to_agent,
            memory_type="received_message",
            content=message,
            is_shared=True
        )
        
        # Check if recipient agent has a message handler
        if to_agent in self.message_handlers:
            # Start background task to handle message
            asyncio.create_task(self._deliver_message(to_agent, message))
        else:
            logger.warning(f"No message handler registered for agent {to_agent}")
            message["status"] = "pending_delivery"
            
        # For workflow messages, store in collaboration state
        if workflow_id:
            collab_key = f"workflow_{workflow_id}"
            collab_state = await self.state_manager.retrieve_agent_state(
                "collaboration", collab_key
            ) or {"messages": []}
            
            collab_state["messages"].append(message)
            
            await self.state_manager.persist_agent_state(
                "collaboration", collab_key, collab_state
            )
            
        return {
            "message_id": message_id,
            "status": message["status"],
            "timestamp": message["timestamp"]
        }
    
    async def _deliver_message(self, to_agent: str, message: Dict[str, Any]):
        """Internal method to deliver message to agent
        
        Args:
            to_agent: Recipient agent name
            message: Full message object
        """
        try:
            handler = self.message_handlers.get(to_agent)
            if handler:
                # Call the agent's message handler with the message
                response = await handler(message)
                
                # Update message status
                message["status"] = "delivered"
                message["delivered_at"] = datetime.now().isoformat()
                
                # If the handler returned a response, send it back
                if response:
                    await self.send_message(
                        from_agent=to_agent,
                        to_agent=message["from"],
                        message_type="response",
                        content=response,
                        workflow_id=message.get("workflow_id")
                    )
            else:
                logger.warning(f"Message handler for {to_agent} no longer available")
                message["status"] = "failed"
                
        except Exception as e:
            logger.error(f"Failed to deliver message to {to_agent}: {e}")
            message["status"] = "failed"
            message["error"] = str(e)
    
    async def request_data(
        self, 
        from_agent: str, 
        to_agent: str, 
        data_type: str, 
        parameters: Dict[str, Any],
        workflow_id: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """Request data from another agent with synchronous wait for response
        
        Args:
            from_agent: Requesting agent name
            to_agent: Agent to request data from
            data_type: Type of data being requested
            parameters: Request parameters
            workflow_id: Optional workflow identifier
            timeout: Maximum time to wait for response in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Requested data or None if request failed
        """
        # Create a future to wait for the response
        response_future = asyncio.Future()
        
        # Create a unique request ID
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{from_agent}_{to_agent}"
        
        # Store the future in active collaborations
        self.active_collaborations[request_id] = response_future
        
        # Send the request message
        message_result = await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="data_request",
            content={
                "request_id": request_id,
                "data_type": data_type,
                "parameters": parameters
            },
            workflow_id=workflow_id
        )
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} timed out after {timeout} seconds")
            return None
        finally:
            # Remove the request from active collaborations
            if request_id in self.active_collaborations:
                del self.active_collaborations[request_id]
    
    async def provide_response(
        self,
        from_agent: str,
        request_id: str,
        data: Dict[str, Any],
        workflow_id: Optional[str] = None
    ) -> bool:
        """Provide response data for a request
        
        Args:
            from_agent: Responding agent name
            request_id: Original request ID
            data: Response data
            workflow_id: Optional workflow identifier
            
        Returns:
            bool: True if response was successfully delivered
        """
        # Check if the request is still active
        if request_id not in self.active_collaborations:
            logger.warning(f"Request {request_id} no longer active, response discarded")
            return False
            
        # Get the response future
        response_future = self.active_collaborations[request_id]
        
        # Resolve the future with the data
        response_future.set_result(data)
        
        # Also send a message to maintain the conversation record
        to_agent = request_id.split("_")[3]  # Extract recipient from request ID
        
        await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="data_response",
            content={
                "request_id": request_id,
                "data": data
            },
            workflow_id=workflow_id
        )
        
        return True
    
    async def broadcast_notification(
        self,
        from_agent: str,
        notification_type: str,
        content: Dict[str, Any],
        target_agents: Optional[List[str]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Broadcast a notification to multiple agents
        
        Args:
            from_agent: Notifying agent name
            notification_type: Type of notification
            content: Notification content
            target_agents: Optional list of target agents (if None, sent to all)
            workflow_id: Optional workflow identifier
            
        Returns:
            Dict[str, Any]: Status and message information
        """
        notification_id = f"notify_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{from_agent}"
        
        # If no target agents specified, send to all registered agents
        if target_agents is None:
            target_agents = list(self.message_handlers.keys())
            # Remove the sending agent from targets
            if from_agent in target_agents:
                target_agents.remove(from_agent)
        
        # Send to each target agent
        sent_count = 0
        results = []
        
        for agent in target_agents:
            try:
                result = await self.send_message(
                    from_agent=from_agent,
                    to_agent=agent,
                    message_type=f"notification_{notification_type}",
                    content={
                        "notification_id": notification_id,
                        "data": content
                    },
                    workflow_id=workflow_id
                )
                results.append(result)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to notify {agent}: {e}")
                results.append({
                    "agent": agent,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "notification_id": notification_id,
            "sent_count": sent_count,
            "total_targets": len(target_agents),
            "results": results
        }
    
    async def get_collaboration_history(
        self,
        workflow_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get collaboration message history
        
        Args:
            workflow_id: Optional workflow to filter by
            agent_name: Optional agent to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: List of messages in the collaboration history
        """
        messages = []
        
        if workflow_id:
            # Get workflow-specific messages
            collab_state = await self.state_manager.retrieve_agent_state(
                "collaboration", f"workflow_{workflow_id}"
            )
            
            if collab_state and "messages" in collab_state:
                messages = collab_state["messages"]
        else:
            # Get messages from memory
            query_type = None
            if agent_name:
                # Get messages sent or received by this agent
                sent = await self.memory_manager.query_agent_memory(
                    agent_name=agent_name,
                    memory_type="sent_message",
                    limit=limit
                )
                
                received = await self.memory_manager.query_agent_memory(
                    agent_name=agent_name,
                    memory_type="received_message",
                    limit=limit
                )
                
                # Combine and sort by timestamp
                messages = sent + received
            else:
                # Get all messages
                shared_context = await self.memory_manager.get_shared_context()
                for item in shared_context:
                    if item.get("type") in ["sent_message", "received_message"]:
                        messages.append(item.get("content", {}))
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit number of messages
        return messages[:limit]
    
    def close(self):
        """Clean up resources"""
        self.active_collaborations.clear()
        self.message_handlers.clear()
