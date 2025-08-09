"""
Task Processor - Handles processing of different task types
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from .queue_manager import queue_manager

class TaskProcessor:
    """Processes different types of tasks from the queue"""
    
    def __init__(self, memory_manager=None, agents=None, workflow_manager=None):
        self.memory_manager = memory_manager
        self.agents = agents or {}
        self.workflow_manager = workflow_manager
        self.registered_handlers = {}
    
    async def initialize(self):
        """Initialize task processor and register handlers"""
        # Register handlers for standard queues
        await self.register_handler("content_tasks", self.process_content_task)
        await self.register_handler("client_tasks", self.process_client_task)
        await self.register_handler("finance_tasks", self.process_finance_task)
        await self.register_handler("research_tasks", self.process_research_task)
        await self.register_handler("system_tasks", self.process_system_task)
        
        logger.info("Task processor initialized")
    
    async def register_handler(self, queue_name: str, handler_func, concurrency: int = 1) -> bool:
        """Register a handler for a queue"""
        self.registered_handlers[queue_name] = handler_func
        return await queue_manager.register_worker(queue_name, handler_func, concurrency)
    
    async def add_task(self, task_type: str, task_data: Dict[str, Any], 
                     priority: Optional[str] = None) -> Optional[str]:
        """Add a task to the appropriate queue"""
        # Determine queue based on task type
        queue_mapping = {
            "content_creation": "content_tasks",
            "blog_post": "content_tasks",
            "social_media": "content_tasks",
            "email_sequence": "content_tasks",
            
            "client_proposal": "client_tasks",
            "client_onboarding": "client_tasks",
            "client_followup": "client_tasks",
            
            "financial_report": "finance_tasks",
            "invoice": "finance_tasks",
            "expense_report": "finance_tasks",
            
            "market_research": "research_tasks",
            "competitor_analysis": "research_tasks",
            "trend_analysis": "research_tasks",
            
            "system_maintenance": "system_tasks",
            "memory_cleanup": "system_tasks",
            "workflow_execution": "system_tasks"
        }
        
        queue_name = queue_mapping.get(task_type, "system_tasks")
        
        # Set options based on priority
        options = None
        if priority == "high":
            options = {"priority": 1}
        elif priority == "low":
            options = {"priority": 3}
        
        # Add metadata
        task_data["_metadata"] = {
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
            "priority": priority or "normal"
        }
        
        # Add to queue
        return await queue_manager.add_job(queue_name, task_data, options=options)
    
    async def get_task_status(self, queue_name: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        return await queue_manager.get_job(queue_name, job_id)
    
    async def process_content_task(self, job):
        """Process content creation tasks"""
        data = job.data
        task_type = data.get("_metadata", {}).get("task_type", "unknown")
        
        logger.info(f"Processing content task: {task_type}")
        
        try:
            # Update progress
            await job.updateProgress(10)
            
            # Get appropriate agent
            agent_name = "content"
            if "agent" in data:
                agent_name = data["agent"]
                
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")
                
            agent = self.agents[agent_name]
            
            # Update progress
            await job.updateProgress(20)
            
            # Execute task based on type
            result = None
            if task_type == "blog_post":
                result = await agent.generate_blog_post(
                    topic=data.get("topic", ""),
                    keywords=data.get("keywords", []),
                    tone=data.get("tone", "professional")
                )
            elif task_type == "social_media":
                result = await agent.generate_social_media_campaign(
                    topic=data.get("topic", ""),
                    platforms=data.get("platforms", ["twitter", "linkedin"]),
                    post_count=data.get("post_count", 5)
                )
            elif task_type == "email_sequence":
                result = await agent.generate_email_sequence(
                    purpose=data.get("purpose", ""),
                    audience=data.get("audience", ""),
                    email_count=data.get("email_count", 3)
                )
            else:
                # Generic task execution
                result = await agent.execute_task(data)
            
            # Update progress
            await job.updateProgress(90)
            
            # Store result in memory
            if self.memory_manager:
                await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=task_type,
                    content=result,
                    is_shared=True
                )
            
            # Update progress
            await job.updateProgress(100)
            
            return {
                "status": "completed",
                "result": result,
                "task_type": task_type,
                "agent": agent_name
            }
        except Exception as e:
            logger.error(f"Content task processing failed: {e}")
            raise
    
    async def process_client_task(self, job):
        """Process client management tasks"""
        data = job.data
        task_type = data.get("_metadata", {}).get("task_type", "unknown")
        
        logger.info(f"Processing client task: {task_type}")
        
        try:
            # Update progress
            await job.updateProgress(10)
            
            # Get appropriate agent
            agent_name = "client"
            if "agent" in data:
                agent_name = data["agent"]
                
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")
                
            agent = self.agents[agent_name]
            
            # Update progress
            await job.updateProgress(20)
            
            # Execute task based on type
            result = None
            if task_type == "client_proposal":
                result = await agent.generate_client_proposal(
                    client_info=data.get("client_info", {}),
                    project_scope=data.get("project_scope", "")
                )
            elif task_type == "client_onboarding":
                result = await agent.generate_onboarding_sequence(
                    client_info=data.get("client_info", {}),
                    project_type=data.get("project_type", "")
                )
            elif task_type == "client_followup":
                result = await agent.generate_followup_emails(
                    client_info=data.get("client_info", {}),
                    project_status=data.get("project_status", ""),
                    email_count=data.get("email_count", 2)
                )
            else:
                # Generic task execution
                result = await agent.execute_task(data)
            
            # Update progress
            await job.updateProgress(90)
            
            # Store result in memory
            if self.memory_manager:
                await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=task_type,
                    content=result,
                    is_shared=True
                )
            
            # Update progress
            await job.updateProgress(100)
            
            return {
                "status": "completed",
                "result": result,
                "task_type": task_type,
                "agent": agent_name
            }
        except Exception as e:
            logger.error(f"Client task processing failed: {e}")
            raise
    
    async def process_finance_task(self, job):
        """Process financial tasks"""
        data = job.data
        task_type = data.get("_metadata", {}).get("task_type", "unknown")
        
        logger.info(f"Processing finance task: {task_type}")
        
        try:
            # Update progress
            await job.updateProgress(10)
            
            # Get appropriate agent
            agent_name = "finance"
            if "agent" in data:
                agent_name = data["agent"]
                
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")
                
            agent = self.agents[agent_name]
            
            # Update progress
            await job.updateProgress(20)
            
            # Execute task based on type
            result = None
            if task_type == "financial_report":
                result = await agent.generate_financial_report(
                    report_type=data.get("report_type", "monthly"),
                    time_period=data.get("time_period", "")
                )
            elif task_type == "invoice":
                result = await agent.generate_invoice(
                    client_id=data.get("client_id", ""),
                    project_id=data.get("project_id", ""),
                    items=data.get("items", [])
                )
            elif task_type == "expense_report":
                result = await agent.generate_expense_report(
                    expenses=data.get("expenses", []),
                    time_period=data.get("time_period", "")
                )
            else:
                # Generic task execution
                result = await agent.execute_task(data)
            
            # Update progress
            await job.updateProgress(90)
            
            # Store result in memory
            if self.memory_manager:
                await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=task_type,
                    content=result,
                    is_shared=True
                )
            
            # Update progress
            await job.updateProgress(100)
            
            return {
                "status": "completed",
                "result": result,
                "task_type": task_type,
                "agent": agent_name
            }
        except Exception as e:
            logger.error(f"Finance task processing failed: {e}")
            raise
    
    async def process_research_task(self, job):
        """Process research tasks"""
        data = job.data
        task_type = data.get("_metadata", {}).get("task_type", "unknown")
        
        logger.info(f"Processing research task: {task_type}")
        
        try:
            # Update progress
            await job.updateProgress(10)
            
            # Get appropriate agent
            agent_name = "research"
            if "agent" in data:
                agent_name = data["agent"]
                
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")
                
            agent = self.agents[agent_name]
            
            # Update progress
            await job.updateProgress(20)
            
            # Execute task based on type
            result = None
            if task_type == "market_research":
                result = await agent.generate_market_report(
                    industry=data.get("industry", ""),
                    target_audience=data.get("target_audience", "")
                )
            elif task_type == "competitor_analysis":
                result = await agent.analyze_competitors(
                    competitors=data.get("competitors", []),
                    metrics=data.get("metrics", [])
                )
            elif task_type == "trend_analysis":
                result = await agent.analyze_trends(
                    industry=data.get("industry", ""),
                    time_period=data.get("time_period", "")
                )
            else:
                # Generic task execution
                result = await agent.execute_task(data)
            
            # Update progress
            await job.updateProgress(90)
            
            # Store result in memory
            if self.memory_manager:
                await self.memory_manager.store_agent_memory(
                    agent_name=agent_name,
                    memory_type=task_type,
                    content=result,
                    is_shared=True
                )
            
            # Update progress
            await job.updateProgress(100)
            
            return {
                "status": "completed",
                "result": result,
                "task_type": task_type,
                "agent": agent_name
            }
        except Exception as e:
            logger.error(f"Research task processing failed: {e}")
            raise
    
    async def process_system_task(self, job):
        """Process system tasks"""
        data = job.data
        task_type = data.get("_metadata", {}).get("task_type", "unknown")
        
        logger.info(f"Processing system task: {task_type}")
        
        try:
            # Update progress
            await job.updateProgress(10)
            
            # Execute task based on type
            result = None
            if task_type == "memory_cleanup":
                if self.memory_manager:
                    days_old = data.get("days_old", 30)
                    await self.memory_manager.cleanup_old_memories(days_old)
                    result = {"status": "completed", "message": f"Cleaned up memories older than {days_old} days"}
            elif task_type == "workflow_execution":
                if self.workflow_manager:
                    workflow_id = data.get("workflow_id")
                    workflow_input = data.get("input", {})
                    
                    if not workflow_id:
                        raise ValueError("Workflow ID is required")
                        
                    result = await self.workflow_manager.execute_workflow(workflow_id, workflow_input)
            else:
                result = {"status": "unknown_task", "task_type": task_type}
            
            # Update progress
            await job.updateProgress(100)
            
            return {
                "status": "completed",
                "result": result,
                "task_type": task_type
            }
        except Exception as e:
            logger.error(f"System task processing failed: {e}")
            raise

# Global instance
task_processor = None