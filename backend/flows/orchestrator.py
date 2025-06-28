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
from approvals.approval_manager import ApprovalManager

class AgentOrchestrator:
    """Orchestrates agent execution following the PRD DAG workflow"""
    
    def __init__(self):
        # Initialize shared systems
        self.memory_manager = MemoryManager()
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
        self.execution_timeline = []
        self.current_project_id = None
        
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
        for agent_name in ["Product", "Finance", "Marketing", "Legal"]:
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
    
    def close(self):
        """Close all connections"""
        self.memory_manager.close()