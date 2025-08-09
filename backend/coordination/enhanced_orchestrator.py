"""
Enhanced Orchestrator with Automatic Agent Coordination
Supports the new workflow: Chat -> Approval -> Auto-Execution -> Real-time Monitoring
"""
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass

from task_queue.enhanced_queue_manager import queue_manager, TaskPriority
from communication.event_bus import event_bus
from memory.memory_manager import MemoryManager
from agents.cofounder_agent import CofounderAgent
from agents.manager_agent import ManagerAgent
from agents.finance_agent import FinanceAgent
from agents.marketing_agent import MarketingAgent
from agents.legal_agent import LegalAgent
from agents.sales_agent import SalesAgent

@dataclass
class WorkflowSession:
    session_id: str
    conversation_id: str
    project_id: str
    user_id: str
    status: str
    vision: str
    approved_plan: Dict[str, Any]
    agent_tasks: Dict[str, str]  # agent_name -> task_id
    results: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
class EnhancedOrchestrator:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.active_sessions: Dict[str, WorkflowSession] = {}
        
        # Initialize agents
        self.agents = {
            "Cofounder": CofounderAgent(memory_manager, None),
            "Manager": ManagerAgent(memory_manager, None), 
            "Finance": FinanceAgent(memory_manager, None),
            "Marketing": MarketingAgent(memory_manager, None),
            "Legal": LegalAgent(memory_manager, None),
            "Sales": SalesAgent(memory_manager, None)
        }
        
        # Agent execution order and dependencies
        self.execution_graph = {
            "Cofounder": {"depends_on": [], "triggers": ["Manager"]},
            "Manager": {"depends_on": ["Cofounder"], "triggers": ["Finance", "Marketing", "Legal", "Sales"]},
            "Finance": {"depends_on": ["Manager"], "triggers": []},
            "Marketing": {"depends_on": ["Manager"], "triggers": []},
            "Legal": {"depends_on": ["Manager"], "triggers": []},
            "Sales": {"depends_on": ["Manager"], "triggers": []}
        }
        
        # Real-time monitoring
        self.monitoring_enabled = True
        self.live_logs: List[Dict] = []
        
    async def initialize(self):
        """Initialize the orchestrator and queue system with error handling"""
        try:
            # Connect to Redis with timeout protection
            try:
                await asyncio.wait_for(
                    queue_manager.connect(),
                    timeout=10.0  # 10 second timeout for connection
                )
            except asyncio.TimeoutError:
                logger.error("Redis connection timeout - system will operate with limited functionality")
            except Exception as e:
                logger.error(f"Redis connection error: {e} - system will operate with limited functionality")
            
            # Create queues for different types of work
            await queue_manager.create_queue("agent_tasks", {
                "max_concurrency": 2,  # Reduced concurrency
                "retry_delay": 3000,    # Increased retry delay
                "max_retries": 3       # Increased retries
            })
            
            await queue_manager.create_queue("coordination", {
                "max_concurrency": 1,
                "retry_delay": 2000,    # Increased retry delay
                "max_retries": 2        # Increased retries
            })
            
            await queue_manager.create_queue("notifications", {
                "max_concurrency": 5,   # Reduced concurrency
                "retry_delay": 1000,
                "max_retries": 2
            })
            
            # Start queue processors
            await queue_manager.process_queue("agent_tasks", self._process_agent_task)
            await queue_manager.process_queue("coordination", self._process_coordination_task)
            await queue_manager.process_queue("notifications", self._process_notification)
            
            # Subscribe to queue events for monitoring
            queue_manager.subscribe("task_processing", self._on_task_processing)
            queue_manager.subscribe("task_completed", self._on_task_completed)
            queue_manager.subscribe("task_failed", self._on_task_failed)
            
            logger.info("🚀 Enhanced Orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            # Continue with limited functionality
    
    async def start_chat_session(self, user_id: str, initial_message: str) -> Dict[str, Any]:
        """Start new chat session with cofounder agent and return initial AI response"""
        # Initialize queue system if not already initialized
        if not hasattr(queue_manager, 'redis') or queue_manager.redis is None:
            logger.info("Initializing queue system for the first time")
            await self.initialize()
            
        session_id = str(uuid.uuid4())
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🚀 Starting new chat session {session_id} for user {user_id}")
        
        # Create workflow session
        session = WorkflowSession(
            session_id=session_id,
            conversation_id=conversation_id,
            project_id="",
            user_id=user_id,
            status="chatting",
            vision="",
            approved_plan={},
            agent_tasks={},
            results={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        # Start conversation with Cofounder and get immediate response
        try:
            logger.info(f"💬 Getting initial response from Cofounder for session {session_id}")
            response = await self.agents["Cofounder"].chat(initial_message, conversation_id)
            
            # Log the interaction
            await self._log_interaction(session_id, "user", initial_message)
            await self._log_interaction(session_id, "assistant", response.get("message", ""))
            
            # Publish session started event
            await self._publish_session_event("session_started", {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "initial_message": initial_message[:100] + "..." if len(initial_message) > 100 else initial_message
            })
            
            logger.info(f"✅ Chat session {session_id} started successfully")
            
            return {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "response": response.get("message", ""),
                "ready_for_approval": response.get("vision_complete", False),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to start chat session: {e}")
            # Clean up failed session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            raise
    
    async def continue_chat_session(self, session_id: str, message: str) -> Dict[str, Any]:
        """Continue existing chat session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Continue conversation with Cofounder
            response = await self.agents["Cofounder"].chat(
                message, 
                session.conversation_id,
                context=[]  # You might want to retrieve context from memory
            )
            
            # Log the interaction
            await self._log_interaction(session_id, "user", message)
            await self._log_interaction(session_id, "assistant", response.get("message", ""))
            
            # Check if vision is ready for approval
            vision_ready = response.get("vision_complete", False)
            if vision_ready:
                session.status = "ready_for_approval"
                session.vision = message  # Store the final vision
                session.updated_at = datetime.now()
            
            return {
                "session_id": session_id,
                "response": response.get("message", ""),
                "ready_for_approval": vision_ready,
                "status": session.status
            }
            
        except Exception as e:
            logger.error(f"Failed to continue chat session: {e}")
            raise
    
    async def execute_role_action(self, agent_name: str, action: str, params: Dict[str, Any], 
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a role-specific action for an agent"""
        # Initialize queue system if not already initialized
        if not hasattr(queue_manager, 'redis') or queue_manager.redis is None:
            logger.info("Initializing queue system for role action execution")
            await self.initialize()
            
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
            
        # Create a correlation ID for tracking
        correlation_id = f"role_action_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🎯 Executing role action {action} for agent {agent_name}")
        
        try:
            # Queue the role-specific action
            task_id = await queue_manager.add_task(
                queue_name="agent_tasks",
                task_type=f"{agent_name.lower()}_{action}",
                payload={
                    "agent_name": agent_name,
                    "session_id": session_id,
                    "action": action,
                    "params": params
                },
                priority=TaskPriority.HIGH,
                agent_id=agent_name,
                correlation_id=correlation_id
            )
            
            # Wait for task completion
            await self._wait_for_task_completion(task_id)
            
            # Get task result
            task_result = await queue_manager.get_task_result(task_id)
            
            # Log completion
            if session_id:
                await self._log_interaction(
                    session_id=session_id,
                    role="system",
                    content=f"{agent_name} completed role action {action}"
                )
            
            return task_result
            
        except Exception as e:
            logger.error(f"Failed to execute role action {action} for {agent_name}: {e}")
            if session_id:
                await self._log_interaction(
                    session_id=session_id,
                    role="system",
                    content=f"❌ Failed to execute role action {action} for {agent_name}: {str(e)}"
                )
            raise
    
    async def approve_and_execute(self, session_id: str) -> Dict[str, Any]:
        """Approve vision and start automatic agent execution"""
        # Initialize queue system if not already initialized
        if not hasattr(queue_manager, 'redis') or queue_manager.redis is None:
            logger.info("Initializing queue system for execution")
            await self.initialize()
            
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if session.status != "ready_for_approval":
            raise ValueError("Session not ready for approval")
        
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session.project_id = project_id
        session.status = "executing"
        session.updated_at = datetime.now()
        
        logger.info(f"🎯 Starting automatic execution for project {project_id}")
        
        try:
            # Step 1: Execute Cofounder vision_setting role action
            cofounder_result = await self.execute_role_action(
                agent_name="Cofounder",
                action="vision_setting",
                params={
                    "vision_input": session.vision,
                    "project_id": project_id
                },
                session_id=session_id
            )
            
            # Store result in session
            session.results["Cofounder"] = cofounder_result
            
            # Step 2: Execute Manager workflow_design role action
            manager_result = await self.execute_role_action(
                agent_name="Manager",
                action="workflow_design",
                params={
                    "vision_data": cofounder_result,
                    "project_id": project_id
                },
                session_id=session_id
            )
            
            # Store result in session
            session.results["Manager"] = manager_result
            
            # Step 3: Execute Manager task_delegation role action
            delegation_result = await self.execute_role_action(
                agent_name="Manager",
                action="task_delegation",
                params={
                    "workflow": manager_result.get("workflow", {}),
                    "project_id": project_id,
                    "available_agents": ["Finance", "Marketing", "Legal", "Sales"]
                },
                session_id=session_id
            )
            
            # Step 4: Queue coordination task to orchestrate specialist agents
            coordination_task_id = await queue_manager.add_task(
                queue_name="coordination",
                task_type="orchestrate_execution",
                payload={
                    "session_id": session_id,
                    "project_id": project_id,
                    "agent_assignments": delegation_result.get("agent_assignments", {})
                },
                priority=TaskPriority.CRITICAL,
                correlation_id=project_id
            )
            
            # Publish execution start event
            await event_bus.broadcast_update("orchestrator", {
                "type": "execution_started",
                "data": {
                    "session_id": session_id,
                    "project_id": project_id,
                    "cofounder_result": cofounder_result,
                    "manager_result": manager_result,
                    "delegation_result": delegation_result
                }
            })
            
            return {
                "status": "execution_started",
                "session_id": session_id,
                "project_id": project_id,
                "message": "Agents are now working automatically using role-based capabilities. Monitor progress in real-time."
            }
            
        except Exception as e:
            logger.error(f"Failed to start execution: {e}")
            session.status = "error"
            raise
    
    async def _process_agent_task(self, task) -> Dict[str, Any]:
        """Process individual agent tasks with strict flow control"""
        payload = task.payload
        agent_name = payload.get("agent_name")
        session_id = payload.get("session_id")
        
        logger.info(f"🤖 Processing {agent_name} task for session {session_id}")
        
        # Check if this is a role-specific action
        role_action = payload.get("action")
        if role_action:
            logger.info(f"🔄 Processing role-specific action: {role_action} for {agent_name}")
            
            if agent_name not in self.agents:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            agent = self.agents[agent_name]
            
            # Execute role-specific action
            try:
                result = await agent.execute({
                    "id": task.id,
                    "action": role_action,
                    "params": payload.get("params", {})
                })
                
                # Log completion
                if session_id:
                    await self._log_interaction(session_id, "system", 
                        f"{agent_name} completed role action {role_action} with confidence {result.get('confidence', 0.8):.2f}")
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "action": role_action,
                    "result": result,
                    "confidence": result.get("confidence", 0.8)
                }
            except Exception as e:
                logger.error(f"Agent {agent_name} role action {role_action} failed: {e}")
                if session_id:
                    await self._log_interaction(session_id, "system", 
                        f"{agent_name} role action {role_action} failed: {str(e)}")
                raise
        
        # Standard task processing
        # ─────────────── STRICT GATING PROTECTION ─────────────────
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"❌ Skipping task {task.id} - Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        if session.status not in ["executing", "ready_for_approval"]:
            logger.warning(f"❌ Skipping task {task.id} - Session {session_id} status is {session.status}, not executing")
            return {"skipped": True, "reason": f"Session not in executing state: {session.status}"}
        
        # Special case: Allow Cofounder in ready_for_approval for final processing
        if session.status == "ready_for_approval" and agent_name != "Cofounder":
            logger.warning(f"❌ Skipping {agent_name} task - Session not yet approved for execution")
            return {"skipped": True, "reason": "Session not approved for specialist agent execution"}
        # ──────────────────────────────────────────────────────────
        
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.agents[agent_name]
        
        try:
            # Build execution context from session and shared memory
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get global context and peer results
            global_context = await self.memory_manager.get_shared_context()
            peer_context = {k: v for k, v in session.results.items() if k != agent_name}
            
            # Create agent task with coordination context
            agent_task = {
                "id": task.id,
                "vision": session.vision,
                "project_id": session.project_id,
                "coordination_mode": True,
                "peer_context": peer_context,
                "global_context": global_context
            }
            
            # Execute the agent
            result = await agent.execute(agent_task)
            
            # Store result in session and memory
            session.results[agent_name] = result
            session.updated_at = datetime.now()
            
            # Store in shared memory for other agents
            await self.memory_manager.store_agent_memory(
                agent_name=agent_name,
                memory_type="execution_result",
                content=result,
                is_shared=True,
                confidence=result.get("confidence", 0.8)
            )
            
            # Log completion
            await self._log_interaction(session_id, "system", 
                f"{agent_name} completed execution with confidence {result.get('confidence', 0.8):.2f}")
            
            return {
                "success": True,
                "agent": agent_name,
                "result": result,
                "confidence": result.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Agent {agent_name} execution failed: {e}")
            await self._log_interaction(session_id, "system", 
                f"{agent_name} execution failed: {str(e)}")
            raise
    
    async def _process_coordination_task(self, task) -> Dict[str, Any]:
        """Process coordination tasks that orchestrate agent execution"""
        payload = task.payload
        session_id = payload.get("session_id")
        project_id = payload.get("project_id")
        
        logger.info(f"🎯 Processing coordination for project {project_id}")
        
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            # Wait for dependencies (like Cofounder completion)
            depends_on = payload.get("depends_on", [])
            for dep_task_id in depends_on:
                await self._wait_for_task_completion(dep_task_id)
            
            # Get the Cofounder result to extract the plan
            cofounder_result = session.results.get("Cofounder", {})
            
            # Queue Manager task to create the execution plan
            manager_task_id = await queue_manager.add_task(
                queue_name="agent_tasks",
                task_type="create_execution_plan",
                payload={
                    "agent_name": "Manager",
                    "session_id": session_id,
                    "cofounder_result": cofounder_result
                },
                priority=TaskPriority.HIGH,
                agent_id="Manager",
                correlation_id=project_id
            )
            
            session.agent_tasks["Manager"] = manager_task_id
            
            # Wait for Manager to complete
            await self._wait_for_task_completion(manager_task_id)
            
            # Get Manager result
            manager_result = session.results.get("Manager", {})
            
            # Queue all specialist agents in parallel
            specialist_agents = ["Finance", "Marketing", "Legal", "Sales"]
            specialist_tasks = []
            
            for agent_name in specialist_agents:
                if agent_name in self.agents:
                    task_id = await queue_manager.add_task(
                        queue_name="agent_tasks",
                        task_type="specialist_execution",
                        payload={
                            "agent_name": agent_name,
                            "session_id": session_id,
                            "manager_plan": manager_result
                        },
                        priority=TaskPriority.NORMAL,
                        agent_id=agent_name,
                        correlation_id=project_id
                    )
                    
                    session.agent_tasks[agent_name] = task_id
                    specialist_tasks.append(task_id)
            
            # Wait for all specialists to complete
            await asyncio.gather(*[
                self._wait_for_task_completion(task_id) 
                for task_id in specialist_tasks
            ])
            
            # Mark session as completed
            session.status = "completed"
            session.updated_at = datetime.now()
            
            # Generate final notification
            await queue_manager.add_task(
                queue_name="notifications",
                task_type="execution_completed",
                payload={
                    "session_id": session_id,
                    "project_id": project_id,
                    "results_summary": self._generate_results_summary(session)
                },
                priority=TaskPriority.NORMAL,
                correlation_id=project_id
            )
            
            logger.info(f"✅ Coordination completed for project {project_id}")
            
            return {
                "success": True,
                "project_id": project_id,
                "agents_completed": len(session.results),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Coordination failed for project {project_id}: {e}")
            session.status = "failed"
            raise
    
    async def _process_notification(self, task) -> Dict[str, Any]:
        """Process notification tasks"""
        payload = task.payload
        notification_type = task.task_type
        
        logger.info(f"📢 Processing notification: {notification_type}")
        
        # Publish notification event
        await event_bus.broadcast_update("notifications", {
            "type": notification_type,
            "data": payload
        })
        
        return {"success": True, "type": notification_type}
    
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 300):
        """Wait for a specific task to complete with caching and improved error handling"""
        start_time = datetime.now()
        cache_key = f"task_status:{task_id}"
        redis_errors = 0  # Track consecutive Redis errors
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check cache first
            cached_status = queue_manager._cache_get(cache_key)
            if cached_status:
                if cached_status == "completed":
                    return True
                elif cached_status == "failed":
                    raise Exception(f"Task {task_id} failed")
            
            # If not in cache, check Redis with timeout protection
            try:
                if hasattr(queue_manager, 'redis') and queue_manager.redis:
                    task_data = await asyncio.wait_for(
                        queue_manager.redis.hget(f"task:{task_id}", "status"),
                        timeout=5.0  # 5 second timeout
                    )
                    
                    # Reset error counter on success
                    redis_errors = 0
                    
                    if task_data:
                        # Update cache
                        queue_manager._cache_set(cache_key, task_data)
                        
                        if task_data == "completed":
                            return True
                        elif task_data == "failed":
                            raise Exception(f"Task {task_id} failed")
                else:
                    # Redis not available, increment error counter
                    redis_errors += 1
                    logger.warning(f"Redis not available for task status check (attempt {redis_errors})")
                    
            except asyncio.TimeoutError:
                redis_errors += 1
                logger.warning(f"Redis timeout when checking task status (attempt {redis_errors})")
            except Exception as e:
                redis_errors += 1
                logger.warning(f"Error checking task status: {e} (attempt {redis_errors})")
            
            # If too many Redis errors, assume task is still running
            if redis_errors >= 5:
                logger.warning(f"Too many Redis errors, continuing to wait for task {task_id}")
                redis_errors = 0  # Reset counter to avoid log spam
            
            # Progressive backoff for polling
            elapsed_seconds = (datetime.now() - start_time).seconds
            if elapsed_seconds < 10:
                await asyncio.sleep(0.5)  # Poll frequently at first
            elif elapsed_seconds < 60:
                await asyncio.sleep(1)    # Then every second
            else:
                await asyncio.sleep(2)    # Then every 2 seconds
        
        raise TimeoutError(f"Task {task_id} timed out")
    
    async def _log_interaction(self, session_id: str, role: str, content: str):
        """Log interaction for real-time monitoring"""
        log_entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "type": "interaction"
        }
        
        self.live_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.live_logs) > 1000:
            self.live_logs = self.live_logs[-1000:]
        
        # Publish to real-time monitoring
        if self.monitoring_enabled:
            await event_bus.broadcast_update("live_logs", {
                "type": "new_log",
                "data": log_entry
            })
    
    def _generate_results_summary(self, session: WorkflowSession) -> Dict[str, Any]:
        """Generate summary of execution results"""
        return {
            "project_id": session.project_id,
            "vision": session.vision,
            "agents_executed": list(session.results.keys()),
            "overall_confidence": sum(
                result.get("confidence", 0.8) for result in session.results.values()
            ) / len(session.results) if session.results else 0.0,
            "execution_time": (session.updated_at - session.created_at).total_seconds(),
            "outputs_generated": len(session.results)
        }
    
    # Event handlers for real-time monitoring
    async def _on_task_processing(self, event):
        """Handle task processing events"""
        data = event["data"]
        await self._log_interaction(
            session_id=data.get("session_id", "unknown"),
            role="system",
            content=f"🔄 {data.get('agent_id', 'Agent')} started processing task {data.get('task_id', '')[:8]}..."
        )
    
    async def _on_task_completed(self, event):
        """Handle task completion events"""
        data = event["data"]
        await self._log_interaction(
            session_id=data.get("session_id", "unknown"),
            role="system", 
            content=f"✅ {data.get('agent_id', 'Agent')} completed task in {data.get('processing_time', 0):.2f}s"
        )
    
    async def _on_task_failed(self, event):
        """Handle task failure events"""
        data = event["data"]
        await self._log_interaction(
            session_id=data.get("session_id", "unknown"),
            role="system",
            content=f"❌ {data.get('agent_id', 'Agent')} task failed: {data.get('error', 'Unknown error')}"
        )
    
    # API methods for frontend
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a workflow session with Redis error handling"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Get queue statistics for session tasks with error handling
        task_stats = {}
        for agent_name, task_id in session.agent_tasks.items():
            try:
                if hasattr(queue_manager, 'redis') and queue_manager.redis:
                    # Try to get task status with timeout protection
                    try:
                        task_data = await asyncio.wait_for(
                            queue_manager.redis.hget(f"task:{task_id}", "status"),
                            timeout=3.0  # 3 second timeout
                        )
                        task_stats[agent_name] = task_data or "pending"
                    except (asyncio.TimeoutError, Exception) as e:
                        # Use cached status if available, otherwise mark as unknown
                        cached_status = queue_manager._cache_get(f"task_status:{task_id}")
                        task_stats[agent_name] = cached_status or "unknown"
                        logger.warning(f"Error getting task status for {agent_name}: {e}")
                else:
                    # Redis not available, use cached status or mark as unknown
                    cached_status = queue_manager._cache_get(f"task_status:{task_id}")
                    task_stats[agent_name] = cached_status or "unknown"
            except Exception as e:
                # Fallback for any other errors
                task_stats[agent_name] = "unknown"
                logger.error(f"Failed to get task status for {agent_name}: {e}")
        
        return {
            "session_id": session_id,
            "status": session.status,
            "project_id": session.project_id,
            "vision": session.vision,
            "agent_tasks": task_stats,
            "results_count": len(session.results),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
    
    async def get_live_logs(self, session_id: str = None) -> List[Dict]:
        """Get live execution logs"""
        if session_id:
            return [log for log in self.live_logs if log.get("session_id") == session_id]
        return self.live_logs[-50:]  # Return last 50 logs
    
    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get detailed results for a session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "project_id": session.project_id,
            "status": session.status,
            "results": session.results,
            "summary": self._generate_results_summary(session) if session.results else {}
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        queue_metrics = await queue_manager.get_system_metrics()
        
        return {
            "active_sessions": len([s for s in self.active_sessions.values() if s.status in ["chatting", "executing"]]),
            "total_sessions": len(self.active_sessions),
            "completed_sessions": len([s for s in self.active_sessions.values() if s.status == "completed"]),
            "queue_metrics": queue_metrics,
            "live_logs_count": len(self.live_logs)
        }
    
    async def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """Cancel an active session and cleanup resources"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        logger.info(f"🛑 Cancelling session {session_id}")
        
        # Mark session as cancelled
        session.status = "cancelled"
        session.updated_at = datetime.now()
        
        # Cancel any pending tasks
        cancelled_tasks = []
        for agent_name, task_id in session.agent_tasks.items():
            try:
                # Mark task as cancelled in Redis
                await queue_manager.redis.hset(f"task:{task_id}", "status", "cancelled")
                cancelled_tasks.append(task_id)
            except Exception as e:
                logger.error(f"Failed to cancel task {task_id}: {e}")
        
        # Publish cancellation event
        await self._publish_session_event("session_cancelled", {
            "session_id": session_id,
            "cancelled_tasks": cancelled_tasks
        })
        
        return {
            "status": "cancelled",
            "session_id": session_id,
            "cancelled_tasks": cancelled_tasks
        }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Cleanup sessions older than max_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = []
        
        for session_id, session in list(self.active_sessions.items()):
            if session.created_at < cutoff_time:
                old_sessions.append(session_id)
                del self.active_sessions[session_id]
        
        if old_sessions:
            logger.info(f"🧹 Cleaned up {len(old_sessions)} old sessions")
        
        return {"cleaned_sessions": old_sessions}
    
    async def _publish_session_event(self, event_type: str, data: Dict[str, Any]):
        """Publish session-level events"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use existing queue manager's event publishing
        await queue_manager._publish_event(event_type, data)

# Global enhanced orchestrator instance  
enhanced_orchestrator = None

async def get_enhanced_orchestrator(memory_manager: MemoryManager, connect_queue: bool = True) -> EnhancedOrchestrator:
    """Get or create the enhanced orchestrator instance"""
    global enhanced_orchestrator
    
    if enhanced_orchestrator is None:
        enhanced_orchestrator = EnhancedOrchestrator(memory_manager)
        if connect_queue:
            await enhanced_orchestrator.initialize()
    
    return enhanced_orchestrator
