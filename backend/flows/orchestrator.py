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
from memory.memory_manager import MemoryManager
from memory.graph_memory import GraphMemory
from approvals.approval_manager import ApprovalManager

class AgentOrchestrator:
    """Orchestrates agent execution following the PRD DAG workflow"""
    
    def __init__(self):
        # Initialize shared systems
        self.memory_manager = MemoryManager()
        self.graph_memory = GraphMemory()
        self.approval_manager = ApprovalManager()
        
        # Initialize agents with shared systems
        self.agents = {
            "Cofounder": CofounderAgent(self.memory_manager, self.approval_manager),
            "Manager": ManagerAgent(self.memory_manager, self.approval_manager),
            "Product": ProductAgent(self.memory_manager, self.approval_manager),
            "Finance": FinanceAgent(self.memory_manager, self.approval_manager),
            "Marketing": MarketingAgent(self.memory_manager, self.approval_manager),
            "Legal": LegalAgent(self.memory_manager, self.approval_manager)
        }
        
        # Add new specialized agents
        try:
            from agents.sales_agent import SalesAgent
            from agents.operations_agent import OperationsAgent
            self.agents["Sales"] = SalesAgent(self.memory_manager, self.approval_manager)
            self.agents["Operations"] = OperationsAgent(self.memory_manager, self.approval_manager)
        except ImportError:
            pass  # New agents not available yet
        self.execution_timeline = []
        self.current_project_id = None
        self.conversations = {}
        
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
        for agent_name in ["Product", "Finance", "Marketing", "Legal", "Sales", "Operations"]:
            if agent_name in agent_assignments and agent_name in self.agents:
                task = {
                    "id": f"task_{agent_name.lower()}_{project_id}",
                    "project_id": project_id,
                    "assignment": agent_assignments[agent_name],
                    "manager_context": manager_result
                }
                specialist_tasks.append((agent_name, task))
        
        # Execute in parallel
        results = {}
        if specialist_tasks:
            parallel_executions = [
                self.agents[agent_name].execute(task) 
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
                    
                    # Store in graph memory
                    await self.graph_memory.store_agent_relationship(
                        agent_name=agent_name,
                        task_id=specialist_tasks[i][1]["id"],
                        output_data=result
                    )
        
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
        
        # Initialize conversation
        self.conversations[conversation_id] = {
            "messages": [{"role": "user", "content": message}],
            "agent": "Cofounder",
            "status": "active",
            "vision_ready": False
        }
        
        # Get Cofounder response
        response = await self.agents["Cofounder"].chat(message, conversation_id)
        
        self.conversations[conversation_id]["messages"].append({
            "role": "assistant", 
            "content": response["message"]
        })
        
        return {
            "conversation_id": conversation_id,
            "response": response["message"],
            "ready_for_approval": response.get("vision_complete", False)
        }
    
    async def continue_conversation(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Continue conversation with agent"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conv = self.conversations[conversation_id]
        conv["messages"].append({"role": "user", "content": message})
        
        # Get agent response with conversation context
        response = await self.agents[conv["agent"]].chat(message, conversation_id, conv["messages"])
        
        conv["messages"].append({"role": "assistant", "content": response["message"]})
        conv["vision_ready"] = response.get("vision_complete", False)
        
        return {
            "response": response["message"],
            "ready_for_approval": conv["vision_ready"]
        }
    
    async def approve_and_distribute(self, conversation_id: str) -> Dict[str, Any]:
        """Approve conversation and distribute tasks to sub-agents"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conv = self.conversations[conversation_id]
        if not conv["vision_ready"]:
            raise ValueError("Vision not ready for approval")
        
        # Extract vision from conversation
        vision_summary = await self.agents["Cofounder"].extract_vision(conv["messages"])
        
        # Create project and get Manager to distribute tasks
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_project_id = project_id
        
        # Manager creates task distribution
        manager_result = await self.agents["Manager"].create_task_distribution(vision_summary, project_id)
        
        # Mark conversation as approved
        conv["status"] = "approved"
        conv["project_id"] = project_id
        
        return {
            "project_id": project_id,
            "tasks": manager_result["tasks"],
            "agents_assigned": list(manager_result["tasks"].keys())
        }
    
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
    
    def close(self):
        """Close all connections"""
        self.memory_manager.close()
        self.graph_memory.close()