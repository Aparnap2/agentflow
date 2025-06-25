from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime
from loguru import logger

from agents.cofounder_agent import CofounderAgent
from agents.manager_agent import ManagerAgent
from agents.product_agent import ProductAgent
from agents.finance_agent import FinanceAgent
# from agents.marketing_agent import MarketingAgent
# from agents.legal_agent import LegalAgent

class AgentOrchestrator:
    """Orchestrates agent execution following the PRD DAG workflow"""
    
    def __init__(self):
        self.agents = {
            "Cofounder": CofounderAgent(),
            "Manager": ManagerAgent(),
            "Product": ProductAgent(),
            "Finance": FinanceAgent(),
            # "Marketing": MarketingAgent(),
            # "Legal": LegalAgent()
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
        for agent_name in ["Product", "Finance"]:  # Add "Marketing", "Legal" when implemented
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
        """Generate final output files as specified in PRD deliverables"""
        
        outputs_dir = f"/home/aparna/Desktop/agentflow/data"
        
        # Generate individual agent outputs
        for agent_name, result in all_results.items():
            if "output" in result:
                output_file = f"{outputs_dir}/{agent_name}.json"
                with open(output_file, 'w') as f:
                    json.dump({
                        "agent": agent_name,
                        "project_id": project_id,
                        "timestamp": result.get("timestamp"),
                        "confidence": result.get("confidence"),
                        "data": result["output"]
                    }, f, indent=2)
        
        # Generate timeline
        timeline_file = f"{outputs_dir}/timeline.json"
        with open(timeline_file, 'w') as f:
            json.dump({
                "project_id": project_id,
                "execution_timeline": self.execution_timeline,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Generated outputs for project {project_id}")
    
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
        """Get all generated outputs"""
        outputs_dir = "/home/aparna/Desktop/agentflow/data"
        outputs = {}
        
        try:
            import os
            for filename in os.listdir(outputs_dir):
                if filename.endswith('.json'):
                    with open(f"{outputs_dir}/{filename}", 'r') as f:
                        outputs[filename] = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load outputs: {e}")
        
        return outputs
    
    async def get_timeline(self) -> List[Dict[str, Any]]:
        """Get execution timeline"""
        return self.execution_timeline