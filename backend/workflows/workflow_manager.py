"""
Workflow Manager - Manages workflow creation, execution, and monitoring
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from .langgraph_workflow import LangGraphWorkflow
from .workflow_templates import WorkflowTemplates

class WorkflowManager:
    """Manages workflow creation, execution, and monitoring"""
    
    def __init__(self, agents, tools, memory_manager):
        self.agents = agents
        self.tools = tools
        self.memory_manager = memory_manager
        self.langgraph_workflow = LangGraphWorkflow(agents, tools, memory_manager)
        self.workflow_dir = Path("data/workflows")
        self.workflow_dir.mkdir(exist_ok=True, parents=True)
        
        # Load saved workflows
        self._load_saved_workflows()
    
    def _load_saved_workflows(self):
        """Load saved workflow configurations"""
        try:
            for file_path in self.workflow_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        workflow_config = json.load(f)
                    
                    # Create workflow from saved config
                    workflow_type = workflow_config.get("type")
                    if workflow_type:
                        self.langgraph_workflow.create_workflow(workflow_type, workflow_config.get("config"))
                        logger.info(f"Loaded workflow from {file_path}")
                except Exception as e:
                    logger.error(f"Failed to load workflow from {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load saved workflows: {e}")
    
    async def create_workflow(self, workflow_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new workflow"""
        try:
            # Create workflow
            workflow = self.langgraph_workflow.create_workflow(workflow_type, config)
            
            # Get workflow ID
            workflow_id = next(
                (wid for wid, info in self.langgraph_workflow.workflows.items() 
                 if info["graph"] == workflow),
                None
            )
            
            if not workflow_id:
                raise ValueError("Failed to create workflow")
            
            # Save workflow configuration
            workflow_info = self.langgraph_workflow.workflows[workflow_id]
            self._save_workflow_config(workflow_id, workflow_info)
            
            return {
                "workflow_id": workflow_id,
                "type": workflow_type,
                "created_at": workflow_info["created_at"]
            }
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    def _save_workflow_config(self, workflow_id: str, workflow_info: Dict[str, Any]):
        """Save workflow configuration to file"""
        try:
            config_path = self.workflow_dir / f"{workflow_id}.json"
            
            # Prepare config for saving (exclude graph object)
            save_config = {
                "workflow_id": workflow_id,
                "type": workflow_info["type"],
                "config": workflow_info["config"],
                "created_at": workflow_info["created_at"]
            }
            
            with open(config_path, 'w') as f:
                json.dump(save_config, f, indent=2)
                
            logger.info(f"Saved workflow configuration to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save workflow configuration: {e}")
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        try:
            result = await self.langgraph_workflow.execute_workflow(workflow_id, input_data)
            
            # Save execution result
            execution_id = result.get("execution_id")
            if execution_id:
                self._save_execution_result(execution_id, result)
            
            return result
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            raise
    
    def _save_execution_result(self, execution_id: str, result: Dict[str, Any]):
        """Save workflow execution result to file"""
        try:
            result_path = self.workflow_dir / f"execution_{execution_id}.json"
            
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
                
            logger.info(f"Saved execution result to {result_path}")
        except Exception as e:
            logger.error(f"Failed to save execution result: {e}")
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a workflow execution"""
        try:
            return await self.langgraph_workflow.get_workflow_status(execution_id)
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            
            # Try to load from file
            try:
                result_path = self.workflow_dir / f"execution_{execution_id}.json"
                if result_path.exists():
                    with open(result_path, 'r') as f:
                        return json.load(f)
            except Exception:
                pass
                
            raise
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        try:
            return await self.langgraph_workflow.list_workflows()
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise
    
    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workflow executions"""
        try:
            # Get active executions
            active_executions = await self.langgraph_workflow.list_executions(workflow_id)
            
            # Get saved executions from files
            saved_executions = []
            for file_path in self.workflow_dir.glob("execution_*.json"):
                try:
                    with open(file_path, 'r') as f:
                        execution_data = json.load(f)
                    
                    execution_id = file_path.stem.replace("execution_", "")
                    workflow_id_from_file = execution_id.split("_")[0]
                    
                    if workflow_id is None or workflow_id == workflow_id_from_file:
                        saved_executions.append({
                            "execution_id": execution_id,
                            "workflow_id": workflow_id_from_file,
                            "status": execution_data.get("status", "unknown"),
                            "start_time": execution_data.get("start_time", ""),
                            "end_time": execution_data.get("end_time", "")
                        })
                except Exception as e:
                    logger.error(f"Failed to load execution from {file_path}: {e}")
            
            # Combine active and saved executions
            all_executions = active_executions + [
                execution for execution in saved_executions
                if not any(active["execution_id"] == execution["execution_id"] for active in active_executions)
            ]
            
            # Sort by start time
            all_executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
            
            return all_executions
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            raise
    
    async def get_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all workflow templates"""
        return WorkflowTemplates.get_all_templates()
    
    async def create_workflow_from_template(self, template_type: str, config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a workflow from a template"""
        try:
            # Get template
            template = WorkflowTemplates.get_template_by_type(template_type)
            
            # Merge config overrides
            config = template.get("config", {})
            if config_overrides:
                config.update(config_overrides)
            
            # Create workflow
            return await self.create_workflow(template_type, config)
        except Exception as e:
            logger.error(f"Failed to create workflow from template: {e}")
            raise