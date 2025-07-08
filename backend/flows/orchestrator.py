from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime
import os
from loguru import logger

from agents.cofounder_agent import CofounderAgent
from agents.manager_agent import ManagerAgent
from agents.product_agent import ProductAgent
from agents.finance_agent import FinanceAgent
from agents.marketing_agent import MarketingAgent
from agents.legal_agent import LegalAgent
from agents.closer_agent import CloserAgent
from agents.assistant_agent import AssistantAgent
from agents.workflow_agent import WorkflowAgent
from agents.amplifier_agent import AmplifierAgent
from agents.money_agent import MoneyAgent
from memory.memory_manager import MemoryManager
from memory.graph_memory import GraphMemory
from approvals.approval_manager import ApprovalManager
from memory.state_manager import StateManager
from coordination.auto_coordinator import AutoCoordinator

class AgentOrchestrator:
    """Orchestrates agent execution following the PRD DAG workflow"""
    
    def __init__(self):
        # Initialize shared systems
        self.memory_manager = MemoryManager()
        self.graph_memory = GraphMemory()
        self.approval_manager = ApprovalManager()
        self.state_manager = StateManager()
        
        # Initialize agents with shared systems
        self.agents = {
            "Cofounder": CofounderAgent(self.memory_manager, self.approval_manager),
            "Manager": ManagerAgent(self.memory_manager, self.approval_manager),
            "Product": ProductAgent(self.memory_manager, self.approval_manager),
            "Finance": FinanceAgent(self.memory_manager, self.approval_manager),
            "Marketing": MarketingAgent(self.memory_manager, self.approval_manager),
            "Legal": LegalAgent(self.memory_manager, self.approval_manager)
        }
        
        # Add specialized agents based on real-world AI agent types
        self.agents["Closer"] = CloserAgent(self.memory_manager, self.approval_manager)
        self.agents["Assistant"] = AssistantAgent(self.memory_manager, self.approval_manager)
        self.agents["Workflow"] = WorkflowAgent(self.memory_manager, self.approval_manager)
        self.agents["Amplifier"] = AmplifierAgent(self.memory_manager, self.approval_manager)
        self.agents["Money"] = MoneyAgent(self.memory_manager, self.approval_manager)
        
        # Add legacy agents if available
        try:
            from agents.sales_agent import SalesAgent
            from agents.operations_agent import OperationsAgent
            self.agents["Sales"] = SalesAgent(self.memory_manager, self.approval_manager)
            self.agents["Operations"] = OperationsAgent(self.memory_manager, self.approval_manager)
        except ImportError:
            pass
        self.execution_timeline = []
        self.current_project_id = None
        self.conversations = {}  # Add conversations attribute
        self.auto_coordinator = AutoCoordinator(self.agents, self.memory_manager)
        
    async def start_project(self, vision: str, user_name: str = "User", approval_mode: str = "manual") -> Dict[str, Any]:
        """Start new project following PRD execution flow"""
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_project_id = project_id
        
        logger.info(f"Starting project {project_id} with vision: {vision[:100]}...")
        
        try:
            # Step 1: Cofounder captures vision
            cofounder_task = {
                "id": f"task_cofounder_{project_id}",
                "vision": vision,
                "user_name": user_name,
                "project_id": project_id
            }
            
            cofounder_result = await self.agents["Cofounder"].execute(cofounder_task)
            self._log_execution("Cofounder", cofounder_result)
            
            if "error" in cofounder_result:
                raise Exception(f"Cofounder failed: {cofounder_result['error']}")
            
            # Step 2: Manager creates roadmap
            manager_task = {
                "id": f"task_manager_{project_id}",
                "project_id": project_id,
                "vision_context": cofounder_result
            }
            
            manager_result = await self.agents["Manager"].execute(manager_task)
            self._log_execution("Manager", manager_result)
            
            if "error" in manager_result:
                raise Exception(f"Manager failed: {manager_result['error']}")
            
            # Step 3: Execute specialist agents in parallel
            specialist_results = await self._execute_specialists(project_id, manager_result)
            
            # Step 4: Generate final outputs
            await self._generate_outputs(project_id, {
                "cofounder": cofounder_result,
                "manager": manager_result,
                **specialist_results
            })
            
            return {
                "project_id": project_id,
                "status": "completed",
                "agents_executed": len(specialist_results) + 2,
                "timeline": self.execution_timeline
            }
            
        except Exception as e:
            logger.error(f"Project {project_id} failed: {e}")
            return {
                "project_id": project_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_specialists(self, project_id: str, manager_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specialist agents in parallel as per PRD"""
        
        agent_assignments = manager_result.get("output", {}).get("agent_assignments", {})
        specialist_tasks = []
        
        # Create tasks for available specialist agents
        available_agents = ["Product", "Finance", "Marketing", "Legal"]
        if "Sales" in self.agents:
            available_agents.append("Sales")
        if "Operations" in self.agents:
            available_agents.append("Operations")
            
        for agent_name in available_agents:
            if agent_name in agent_assignments and agent_name in self.agents:
                task = {
                    "id": f"task_{agent_name.lower()}_{project_id}",
                    "project_id": project_id,
                    "assignment": agent_assignments[agent_name],
                    "manager_context": manager_result
                }
                specialist_tasks.append((agent_name, task))
        
        # Execute in parallel with timeout
        results = {}
        if specialist_tasks:
            # Create tasks with timeout to prevent hanging
            parallel_executions = [
                asyncio.wait_for(self.agents[agent_name].execute(task), timeout=60.0)
                for agent_name, task in specialist_tasks
            ]
            
            specialist_results = await asyncio.gather(*parallel_executions, return_exceptions=True)
            
            for i, (agent_name, _) in enumerate(specialist_tasks):
                result = specialist_results[i]
                if isinstance(result, Exception):
                    logger.error(f"{agent_name} failed: {result}")
                    results[agent_name.lower()] = {"error": str(result), "agent": agent_name}
                else:
                    results[agent_name.lower()] = result
                    self._log_execution(agent_name, result)
                    
                    # Store in graph memory if available
                    try:
                        await self.graph_memory.store_agent_relationship(
                            agent_name=agent_name,
                            task_id=specialist_tasks[i][1]["id"],
                            output_data=result
                        )
                    except Exception as e:
                        logger.warning(f"Graph memory storage failed: {e}")
        
        return results
    
    async def _generate_outputs(self, project_id: str, all_results: Dict[str, Any]):
        """Generate final output files using memory manager"""
        
        # Use memory manager to export all outputs
        exported_files = await self.memory_manager.export_all_outputs()
        
        # Log the export
        logger.info(f"Generated {len(exported_files)} output files for project {project_id}")
        
        # Store project completion in memory
        await self.memory_manager.store_agent_memory(
            agent_name="Orchestrator",
            memory_type="project_completion",
            content={
                "project_id": project_id,
                "agents_executed": list(all_results.keys()),
                "exported_files": exported_files,
                "completion_time": datetime.now().isoformat()
            },
            is_shared=True,
            confidence=1.0
        )
    
    def _log_execution(self, agent_name: str, result: Dict[str, Any]):
        """Log agent execution to timeline"""
        timeline_entry = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "status": "completed" if "output" in result else "failed",
            "confidence": result.get("confidence", 0.0),
            "summary": result.get("summary", ""),
            "error": result.get("error")
        }
        self.execution_timeline.append(timeline_entry)
    
    async def get_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        for name, agent in self.agents.items():
            status[name] = agent.get_status()
        return status
    
    async def get_outputs(self) -> Dict[str, Any]:
        """Get all generated outputs in frontend-expected format"""
        try:
            # Get shared context which contains agent outputs
            shared_context = await self.memory_manager.get_shared_context()
            
            # Format outputs for frontend - prioritize data directory files
            formatted_outputs = {}
            
            # Check for exported files in data directory (primary source)
            data_dir = "data"
            if os.path.exists(data_dir):
                for filename in os.listdir(data_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(data_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                file_data = json.load(f)
                                
                                # Extract the actual output data
                                if "outputs" in file_data:
                                    # Get the first output key (e.g., "cofounder_output")
                                    output_key = list(file_data["outputs"].keys())[0]
                                    output_content = file_data["outputs"][output_key]
                                    
                                    formatted_outputs[filename] = {
                                        "agent": file_data.get("agent", "Unknown"),
                                        "data": output_content.get("content", {}),
                                        "confidence": output_content.get("confidence", 0.8),
                                        "timestamp": output_content.get("timestamp", file_data.get("exported_at", datetime.now().isoformat()))
                                    }
                                else:
                                    # Fallback for direct format
                                    formatted_outputs[filename] = {
                                        "agent": file_data.get("agent", "Unknown"),
                                        "data": file_data,
                                        "confidence": file_data.get("confidence", 0.8),
                                        "timestamp": file_data.get("timestamp", datetime.now().isoformat())
                                    }
                        except Exception as e:
                            logger.error(f"Failed to read {filename}: {e}")
            
            return formatted_outputs
            
        except Exception as e:
            logger.error(f"Failed to get outputs: {e}")
            return {"error": str(e)}
    
    async def get_timeline(self) -> List[Dict[str, Any]]:
        """Get execution timeline"""
        return self.execution_timeline
    
    async def start_conversation(self, message: str) -> Dict[str, Any]:
        """Start conversation with Cofounder agent"""
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize conversation state
        conversation_state = {
            "messages": [{"role": "user", "content": message}],
            "agent": "Cofounder",
            "status": "active",
            "vision_ready": False
        }
        await self.state_manager.persist_conversation(conversation_id, conversation_state)
        
        # Get Cofounder response
        try:
            response = await self.agents["Cofounder"].chat(message, conversation_id)
            logger.info(f"Raw agent response: {response}")
            
            # Force string conversion for any response
            if isinstance(response, dict):
                if "message" in response:
                    response_text = str(response["message"])
                    # Mark as complete if response contains structured plan OR user has provided comprehensive details
                    has_structured_plan = (
                        "phase" in response_text.lower() and 
                        "task" in response_text.lower() and
                        "agent" in response_text.lower()
                    )
                    
                    # Check if user has provided enough details (multiple exchanges)
                    conversation_length = len(conversation_state.get("messages", []))
                    has_sufficient_detail = (
                        conversation_length >= 6 and  # At least 3 exchanges
                        any(keyword in str(conversation_state.get("messages", [])).lower() 
                            for keyword in ["target", "user", "problem", "solution", "market"])
                    )
                    
                    vision_complete = has_structured_plan or (has_sufficient_detail and len(response_text) > 300)
                else:
                    response_text = "I've analyzed your idea! Here's what I found:\n\n" + json.dumps(response, indent=2)
                    vision_complete = False
            else:
                response_text = str(response)
                vision_complete = False
            
            # Store conversation state
            conversation_state["messages"].append({"role": "assistant", "content": response_text})
            await self.state_manager.persist_conversation(conversation_id, conversation_state)
            
            # Also store in memory for continue_conversation
            self.conversations[conversation_id] = conversation_state
            
            return {
                "conversation_id": conversation_id,
                "response": response_text,
                "ready_for_approval": vision_complete
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "conversation_id": conversation_id,
                "response": "Hello! I'm your AI Cofounder. I'd love to learn about your startup idea. Can you tell me what problem you're trying to solve?",
                "ready_for_approval": False
            }
    
    def _format_to_markdown(self, data: dict) -> str:
        """Convert structured data to markdown format"""
        if not isinstance(data, dict):
            return str(data)
        
        md = "## 🚀 Vision Analysis\n\n"
        
        if "Vision Statement" in data:
            md += f"### Vision Statement\n{data['Vision Statement']}\n\n"
        
        if "Target User Personas" in data:
            md += "### 👥 Target Users\n"
            for persona in data["Target User Personas"]:
                md += f"- **{persona.get('Persona', 'User')}**: {persona.get('Description', '')}\n"
            md += "\n"
        
        if "Market Opportunity" in data:
            market = data["Market Opportunity"]
            md += "### 📊 Market Opportunity\n"
            md += f"- **Market Size**: {market.get('Market Size', 'TBD')}\n"
            md += f"- **Competition**: {market.get('Competition', 'TBD')}\n\n"
        
        if "Success Metrics and KPIs" in data:
            md += "### 📈 Success Metrics\n"
            for metric in data["Success Metrics and KPIs"]:
                md += f"- **{metric.get('Metric', 'Metric')}**: {metric.get('Target', '')}\n"
            md += "\n"
        
        if "Strategic Priorities" in data:
            md += "### 🎯 Strategic Priorities\n"
            for priority in data["Strategic Priorities"]:
                md += f"- **{priority.get('Priority', 'Priority')}**: {priority.get('Description', '')}\n"
            md += "\n"
        
        md += "---\n\n*This analysis was generated based on your input. Would you like to proceed with task distribution to the specialist agents?*"
        
        return md
    
    async def continue_conversation(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Continue conversation with agent"""
        try:
            logger.info(f"=== CONTINUE CONVERSATION ===")
            logger.info(f"Conversation ID: {conversation_id}")
            logger.info(f"Available conversations: {list(self.conversations.keys())}")
            
            if conversation_id not in self.conversations:
                conversation_state = await self.state_manager.retrieve_conversation(conversation_id)
                if conversation_state:
                    self.conversations[conversation_id] = conversation_state
                else:
                    logger.warning(f"No conversation state found for {conversation_id}")
                    return {
                        "response": "I apologize, but I couldn't find our conversation. Please start a new conversation.",
                        "ready_for_approval": False
                    }
            
            conv = self.conversations[conversation_id]
            conv["messages"].append({"role": "user", "content": message})
            
            # Get agent response with conversation context
            response = await self.agents[conv["agent"]].chat(message, conversation_id, conv["messages"])
            logger.info(f"Agent response in continue: {response}")
            
            # Extract message properly
            if isinstance(response, dict) and "message" in response:
                response_text = str(response["message"])
                # Mark as complete if response contains structured plan OR sufficient conversation
                has_structured_plan = (
                    "phase" in response_text.lower() and 
                    "task" in response_text.lower() and
                    "agent" in response_text.lower()
                )
                
                conversation_length = len(conv.get("messages", []))
                has_sufficient_detail = (
                    conversation_length >= 6 and
                    any(keyword in str(conv.get("messages", [])).lower() 
                        for keyword in ["target", "user", "problem", "solution", "market"])
                )
                
                vision_complete = has_structured_plan or (has_sufficient_detail and len(response_text) > 300)
            else:
                response_text = str(response)
                vision_complete = False
            
            conv["messages"].append({"role": "assistant", "content": response_text})
            conv["vision_ready"] = vision_complete
            
            return {
                "response": response_text,
                "ready_for_approval": vision_complete
            }
        except Exception as e:
            logger.error(f"Continue conversation failed: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "ready_for_approval": False
            }
    
    async def auto_execute_from_vision(self, vision: str) -> Dict[str, Any]:
        """Auto-execute project with agent coordination"""
        try:
            execution_id = await self.auto_coordinator.auto_execute_project(vision)
            return {
                "status": "started",
                "execution_id": execution_id,
                "message": "Auto-execution started with agent coordination"
            }
        except Exception as e:
            logger.error(f"Auto-execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_auto_execution_status(self) -> Dict[str, Any]:
        """Get auto-execution status"""
        return self.auto_coordinator.get_execution_status()
    
    async def approve_and_distribute(self, conversation_id: str) -> Dict[str, Any]:
        """Approve conversation and distribute tasks to sub-agents"""
        try:
            logger.info(f"=== APPROVE AND DISTRIBUTE ===")
            logger.info(f"Conversation ID: {conversation_id}")
            logger.info(f"Available conversations: {list(self.conversations.keys())}")
            
            if conversation_id not in self.conversations:
                conversation_state = await self.state_manager.retrieve_conversation(conversation_id)
                if conversation_state:
                    self.conversations[conversation_id] = conversation_state
                else:
                    # Create a simple task distribution without conversation
                    project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.current_project_id = project_id
                
                # Simple task distribution
                tasks = {
                    "Product": {
                        "id": f"task_product_{project_id}",
                        "type": "product_analysis",
                        "description": "Analyze product requirements and create user personas",
                        "inputs": {"vision": "User startup idea"}
                    },
                    "Finance": {
                        "id": f"task_finance_{project_id}",
                        "type": "financial_modeling",
                        "description": "Create financial projections and funding requirements",
                        "inputs": {"vision": "User startup idea"}
                    },
                    "Marketing": {
                        "id": f"task_marketing_{project_id}",
                        "type": "marketing_strategy",
                        "description": "Develop marketing strategy and content plan",
                        "inputs": {"vision": "User startup idea"}
                    },
                    "Legal": {
                        "id": f"task_legal_{project_id}",
                        "type": "legal_compliance",
                        "description": "Review legal requirements and compliance needs",
                        "inputs": {"vision": "User startup idea"}
                    }
                }
                
                return {
                    "project_id": project_id,
                    "tasks": tasks,
                    "agents_assigned": list(tasks.keys())
                }
            
            conv = self.conversations[conversation_id]
            logger.info(f"Conversation status: {conv.get('status', 'unknown')}")
            
            # Skip vision ready check for now
            # if not conv.get("vision_ready", False):
            #     logger.warning("Vision not ready, proceeding anyway")
            
            # Create project and simple task distribution
            project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_project_id = project_id
            
            # Simple task distribution without complex manager logic
            tasks = {
                "Product": {
                    "id": f"task_product_{project_id}",
                    "type": "product_analysis",
                    "description": "Analyze product requirements and create user personas",
                    "inputs": {"conversation": conv["messages"]}
                },
                "Finance": {
                    "id": f"task_finance_{project_id}",
                    "type": "financial_modeling",
                    "description": "Create financial projections and funding requirements",
                    "inputs": {"conversation": conv["messages"]}
                },
                "Marketing": {
                    "id": f"task_marketing_{project_id}",
                    "type": "marketing_strategy",
                    "description": "Develop marketing strategy and content plan",
                    "inputs": {"conversation": conv["messages"]}
                },
                "Legal": {
                    "id": f"task_legal_{project_id}",
                    "type": "legal_compliance",
                    "description": "Review legal requirements and compliance needs",
                    "inputs": {"conversation": conv["messages"]}
                }
            }
            
            # Mark conversation as approved
            conv["status"] = "approved"
            conv["project_id"] = project_id
            
            # Extract vision from conversation for auto-execution
            vision_text = " ".join([msg.get("content", "") for msg in conv["messages"] if msg.get("role") == "user"])
            
            # Start ACTUAL auto-coordination (this is the key fix!)
            logger.info(f"🚀 Starting REAL agent coordination for vision: {vision_text[:100]}...")
            
            # This will make agents actually talk to each other
            coordination_result = await self.auto_coordinator.auto_execute_project(vision_text)
            
            logger.info(f"✅ Agent coordination completed: {coordination_result}")
            
            return {
                "project_id": project_id,
                "tasks": tasks,
                "agents_assigned": list(tasks.keys()),
                "coordination_started": True,
                "execution_id": coordination_result
            }
            
        except Exception as e:
            logger.error(f"Approve and distribute failed: {e}")
            raise
    
    async def execute_single_agent(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent with given task"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        
        # Create execution task
        execution_task = {
            "id": task["id"],
            "type": task["type"],
            "inputs": task["inputs"],
            "project_id": task.get("project_id")
        }
        
        # Execute agent
        result = await agent.execute(execution_task)
        self._log_execution(agent_name, result)
        
        return result
    
    async def update_agent_configs(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent configurations"""
        for agent_name, config in configs.items():
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                if hasattr(agent, 'update_config'):
                    agent.update_config(config)
        return configs
    
    async def get_agent_configs(self) -> Dict[str, Any]:
        """Get current agent configurations"""
        configs = {}
        for name, agent in self.agents.items():
            if hasattr(agent, 'get_config'):
                configs[name] = agent.get_config()
            else:
                configs[name] = {
                    "approvalMode": "manual",
                    "priority": "medium",
                    "temperature": getattr(agent.personality, 'temperature', 0.7),
                    "enabled": True
                }
        return configs
    
    async def handle_conversation(self, message: str, history: List[Dict[str, str]] = None, agent: str = None) -> Dict[str, Any]:
        """Handle conversation with agents"""
        try:
            # Determine which agent should handle the message
            handling_agent = agent or self._get_best_agent_for_message(message)
            
            # Create conversation context
            context = {
                "history": history or [],
                "current_time": datetime.now().isoformat(),
                "shared_context": await self.memory_manager.get_shared_context()
            }
            
            # Create task for the agent
            task = {
                "id": f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": "conversation",
                "message": message,
                "context": context
            }
            
            # Get agent response
            agent_instance = self.agents.get(handling_agent)
            if not agent_instance:
                raise ValueError(f"Agent {handling_agent} not found")
            
            response = await agent_instance._execute_actions({
                "task": task,
                "context": context
            })
            
            # Store conversation in memory
            await self.memory_manager.store_agent_memory(
                agent_name=handling_agent,
                memory_type="conversation",
                content={
                    "message": message,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                },
                is_shared=True
            )
            
            return {
                "response": response,
                "agent": handling_agent,
                "confidence": 0.8,  # TODO: Implement proper confidence scoring
                "conversation_id": task["id"]
            }
            
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}")
            raise
    
    def _get_best_agent_for_message(self, message: str) -> str:
        """Determine best agent to handle the message based on content"""
        # Simple keyword-based routing for now
        message = message.lower()
        
        if any(word in message for word in ["finance", "money", "cost", "price", "revenue"]):
            return "Finance"
        elif any(word in message for word in ["market", "competitor", "customer", "user"]):
            return "Marketing"
        elif any(word in message for word in ["product", "feature", "design", "technical"]):
            return "Product"
        elif any(word in message for word in ["legal", "compliance", "regulation", "risk"]):
            return "Legal"
        elif any(word in message for word in ["sale", "pipeline", "deal", "client"]):
            return "Sales"
        else:
            return "Cofounder"  # Default agent
    
    def close(self):
        """Close all connections"""
        if self.memory_manager:
            self.memory_manager.close()
        if hasattr(self, 'state_manager') and self.state_manager:
            self.state_manager.close()
