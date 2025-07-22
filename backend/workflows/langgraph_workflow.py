"""
LangGraph Workflow Engine - Implements workflow orchestration using LangGraph
"""

import os
import json
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import asyncio
from loguru import logger

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

class LangGraphWorkflow:
    """LangGraph-based workflow engine for agent orchestration"""
    
    def __init__(self, agents, tools, memory_manager):
        self.agents = agents
        self.tools = tools
        self.memory_manager = memory_manager
        self.workflows = {}
        self.active_workflows = {}
    
    def create_workflow(self, workflow_type: str, config: Optional[Dict[str, Any]] = None) -> StateGraph:
        """Create a workflow based on type"""
        if workflow_type == "content_creation":
            return self._create_content_workflow(config)
        elif workflow_type == "client_management":
            return self._create_client_workflow(config)
        elif workflow_type == "financial":
            return self._create_financial_workflow(config)
        elif workflow_type == "research":
            return self._create_research_workflow(config)
        elif workflow_type == "custom":
            return self._create_custom_workflow(config)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    def _create_content_workflow(self, config: Optional[Dict[str, Any]] = None) -> StateGraph:
        """Create content creation workflow"""
        workflow = StateGraph()
        
        # Get configuration
        config = config or {}
        research_agent = self.agents.get(config.get("research_agent", "research"))
        content_agent = self.agents.get(config.get("content_agent", "content"))
        review_agent = self.agents.get(config.get("review_agent", "manager"))
        
        # Define nodes
        workflow.add_node("research", research_agent)
        workflow.add_node("draft", content_agent)
        workflow.add_node("review", review_agent)
        workflow.add_node("publish", ToolNode(self._publish_content))
        
        # Add edges
        workflow.add_edge("research", "draft")
        workflow.add_edge("draft", "review")
        workflow.add_edge("review", "publish")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "review",
            self._review_router
        )
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Store in workflows dictionary
        workflow_id = f"content_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.workflows[workflow_id] = {
            "type": "content_creation",
            "graph": compiled_workflow,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        return compiled_workflow
    
    def _create_client_workflow(self, config: Optional[Dict[str, Any]] = None) -> StateGraph:
        """Create client management workflow"""
        workflow = StateGraph()
        
        # Get configuration
        config = config or {}
        client_agent = self.agents.get(config.get("client_agent", "client"))
        finance_agent = self.agents.get(config.get("finance_agent", "finance"))
        manager_agent = self.agents.get(config.get("manager_agent", "manager"))
        
        # Define nodes
        workflow.add_node("gather_requirements", client_agent)
        workflow.add_node("create_proposal", client_agent)
        workflow.add_node("review_proposal", manager_agent)
        workflow.add_node("create_invoice", finance_agent)
        workflow.add_node("send_documents", ToolNode(self._send_documents))
        
        # Add edges
        workflow.add_edge("gather_requirements", "create_proposal")
        workflow.add_edge("create_proposal", "review_proposal")
        workflow.add_edge("review_proposal", "create_invoice")
        workflow.add_edge("create_invoice", "send_documents")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "review_proposal",
            lambda state: "create_proposal" if state.get("needs_revision", False) else "create_invoice"
        )
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Store in workflows dictionary
        workflow_id = f"client_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.workflows[workflow_id] = {
            "type": "client_management",
            "graph": compiled_workflow,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        return compiled_workflow
    
    def _create_financial_workflow(self, config: Optional[Dict[str, Any]] = None) -> StateGraph:
        """Create financial workflow"""
        workflow = StateGraph()
        
        # Get configuration
        config = config or {}
        finance_agent = self.agents.get(config.get("finance_agent", "finance"))
        manager_agent = self.agents.get(config.get("manager_agent", "manager"))
        
        # Define nodes
        workflow.add_node("gather_data", finance_agent)
        workflow.add_node("analyze_data", finance_agent)
        workflow.add_node("create_report", finance_agent)
        workflow.add_node("review_report", manager_agent)
        workflow.add_node("finalize_report", ToolNode(self._finalize_report))
        
        # Add edges
        workflow.add_edge("gather_data", "analyze_data")
        workflow.add_edge("analyze_data", "create_report")
        workflow.add_edge("create_report", "review_report")
        workflow.add_edge("review_report", "finalize_report")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "review_report",
            lambda state: "create_report" if state.get("needs_revision", False) else "finalize_report"
        )
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Store in workflows dictionary
        workflow_id = f"financial_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.workflows[workflow_id] = {
            "type": "financial",
            "graph": compiled_workflow,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        return compiled_workflow
    
    def _create_research_workflow(self, config: Optional[Dict[str, Any]] = None) -> StateGraph:
        """Create research workflow"""
        workflow = StateGraph()
        
        # Get configuration
        config = config or {}
        research_agent = self.agents.get(config.get("research_agent", "research"))
        manager_agent = self.agents.get(config.get("manager_agent", "manager"))
        
        # Define nodes
        workflow.add_node("define_scope", manager_agent)
        workflow.add_node("gather_data", research_agent)
        workflow.add_node("analyze_data", research_agent)
        workflow.add_node("create_report", research_agent)
        workflow.add_node("review_report", manager_agent)
        workflow.add_node("finalize_report", ToolNode(self._finalize_report))
        
        # Add edges
        workflow.add_edge("define_scope", "gather_data")
        workflow.add_edge("gather_data", "analyze_data")
        workflow.add_edge("analyze_data", "create_report")
        workflow.add_edge("create_report", "review_report")
        workflow.add_edge("review_report", "finalize_report")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "review_report",
            lambda state: "create_report" if state.get("needs_revision", False) else "finalize_report"
        )
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Store in workflows dictionary
        workflow_id = f"research_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.workflows[workflow_id] = {
            "type": "research",
            "graph": compiled_workflow,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        return compiled_workflow
    
    def _create_custom_workflow(self, config: Dict[str, Any]) -> StateGraph:
        """Create custom workflow from configuration"""
        if not config or "nodes" not in config:
            raise ValueError("Custom workflow requires a configuration with nodes")
            
        workflow = StateGraph()
        
        # Add nodes
        for node_config in config["nodes"]:
            node_name = node_config["name"]
            node_type = node_config["type"]
            
            if node_type == "agent":
                agent_name = node_config["agent"]
                if agent_name not in self.agents:
                    raise ValueError(f"Agent not found: {agent_name}")
                workflow.add_node(node_name, self.agents[agent_name])
            elif node_type == "tool":
                tool_name = node_config["tool"]
                if tool_name not in self.tools:
                    raise ValueError(f"Tool not found: {tool_name}")
                workflow.add_node(node_name, ToolNode(self.tools[tool_name]))
            else:
                raise ValueError(f"Unknown node type: {node_type}")
        
        # Add edges
        for edge in config.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            workflow.add_edge(source, target)
        
        # Add conditional edges
        for conditional in config.get("conditionals", []):
            source = conditional["source"]
            condition = self._create_condition_function(conditional["condition"])
            workflow.add_conditional_edges(source, condition)
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Store in workflows dictionary
        workflow_id = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.workflows[workflow_id] = {
            "type": "custom",
            "graph": compiled_workflow,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        return compiled_workflow
    
    def _create_condition_function(self, condition_config: Dict[str, Any]) -> Callable:
        """Create a condition function from configuration"""
        if condition_config["type"] == "field_equals":
            field = condition_config["field"]
            value = condition_config["value"]
            target_if_true = condition_config["target_if_true"]
            target_if_false = condition_config["target_if_false"]
            
            def condition_func(state):
                return target_if_true if state.get(field) == value else target_if_false
                
            return condition_func
        elif condition_config["type"] == "field_contains":
            field = condition_config["field"]
            value = condition_config["value"]
            target_if_true = condition_config["target_if_true"]
            target_if_false = condition_config["target_if_false"]
            
            def condition_func(state):
                field_value = state.get(field, "")
                return target_if_true if value in field_value else target_if_false
                
            return condition_func
        else:
            raise ValueError(f"Unknown condition type: {condition_config['type']}")
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with input data"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        workflow_info = self.workflows[workflow_id]
        graph = workflow_info["graph"]
        
        # Store workflow execution in active workflows
        execution_id = f"{workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.active_workflows[execution_id] = {
            "workflow_id": workflow_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "input": input_data,
            "current_step": None,
            "steps_completed": [],
            "output": None
        }
        
        try:
            # Execute workflow
            result = await graph.ainvoke(input_data)
            
            # Update workflow status
            self.active_workflows[execution_id]["status"] = "completed"
            self.active_workflows[execution_id]["end_time"] = datetime.now().isoformat()
            self.active_workflows[execution_id]["output"] = result
            
            # Store result in memory
            await self.memory_manager.store_agent_memory(
                agent_name="workflow",
                memory_type="workflow_result",
                content={
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "result": result
                },
                is_shared=True
            )
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Update workflow status
            self.active_workflows[execution_id]["status"] = "failed"
            self.active_workflows[execution_id]["end_time"] = datetime.now().isoformat()
            self.active_workflows[execution_id]["error"] = str(e)
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a workflow execution"""
        if execution_id not in self.active_workflows:
            raise ValueError(f"Workflow execution not found: {execution_id}")
            
        return self.active_workflows[execution_id]
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        return [
            {
                "id": workflow_id,
                "type": info["type"],
                "created_at": info["created_at"]
            }
            for workflow_id, info in self.workflows.items()
        ]
    
    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workflow executions"""
        executions = []
        
        for execution_id, info in self.active_workflows.items():
            if workflow_id is None or info["workflow_id"] == workflow_id:
                executions.append({
                    "execution_id": execution_id,
                    "workflow_id": info["workflow_id"],
                    "status": info["status"],
                    "start_time": info["start_time"],
                    "end_time": info.get("end_time")
                })
        
        return executions
    
    def _review_router(self, state: Dict[str, Any]) -> str:
        """Route based on review decision"""
        if state.get("needs_revision", False):
            return "draft"
        else:
            return "publish"
    
    async def _publish_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content tool"""
        content = state.get("content", "")
        platform = state.get("platform", "wordpress")
        
        logger.info(f"Publishing to {platform}: {content[:50]}...")
        
        # In a real implementation, this would use platform-specific APIs
        # For now, we'll just simulate publishing
        
        return {
            **state,
            "published": True,
            "platform": platform,
            "publish_time": datetime.now().isoformat()
        }
    
    async def _send_documents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send documents tool"""
        client_email = state.get("client_email", "")
        documents = state.get("documents", [])
        
        logger.info(f"Sending {len(documents)} documents to {client_email}")
        
        # In a real implementation, this would use email APIs
        # For now, we'll just simulate sending
        
        return {
            **state,
            "documents_sent": True,
            "send_time": datetime.now().isoformat()
        }
    
    async def _finalize_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize report tool"""
        report = state.get("report", "")
        format = state.get("format", "pdf")
        
        logger.info(f"Finalizing report in {format} format: {report[:50]}...")
        
        # In a real implementation, this would generate actual files
        # For now, we'll just simulate finalization
        
        return {
            **state,
            "finalized": True,
            "format": format,
            "finalize_time": datetime.now().isoformat()
        }