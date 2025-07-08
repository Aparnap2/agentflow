from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from datetime import datetime
from loguru import logger

class WorkflowAgent(LangGraphAgent):
    """⚙️ Workflow Agent - System Creation, Process Documentation, Customer Support"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.2,
            "expertise": ["process documentation", "workflow automation", "customer support", "system creation"]
        }
        super().__init__("Workflow", "Process & Systems", memory_manager, approval_manager, personality)
    
    def _get_system_prompt(self) -> str:
        return """You are the Workflow Agent - a process optimization specialist. Your role is to:

1. SYSTEM CREATOR: Document processes and create SOPs/checklists
2. OFFICE MANAGER: Handle purchasing, scheduling, policy management
3. CUSTOMER SUPPORT: Manage support requests and identify upsell opportunities
4. PROCESS AUTOMATION: Streamline workflows and eliminate inefficiencies

You are systematic and detail-oriented. Focus on scalable processes and automation.

Structure your output as:
- Process Documentation (SOPs, checklists, workflows)
- System Recommendations (tools, automation opportunities)
- Support Strategy (customer service optimization)
- Workflow Improvements (efficiency gains)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute workflow optimization and system creation"""
        task = state["task"]
        context = state["context"]
        
        task_type = task.get("type", "process_optimization")
        
        if task_type == "sop_creation":
            return await self._create_sop(task, context)
        elif task_type == "customer_support":
            return await self._handle_customer_support(task, context)
        elif task_type == "office_management":
            return await self._handle_office_management(task, context)
        else:
            return await self._optimize_workflow(task, context)
    
    async def _create_sop(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Standard Operating Procedures"""
        process_description = task.get("process_description", "")
        
        sop_prompt = f"""
        Create a comprehensive SOP for this process:
        
        Process: {process_description}
        Context: {context}
        
        Create:
        1. Process Overview (purpose, scope, stakeholders)
        2. Step-by-Step Procedure (detailed instructions)
        3. Checklist Format (actionable items)
        4. Quality Controls (verification points)
        5. Troubleshooting Guide (common issues)
        6. Tools & Resources (required systems/tools)
        7. Success Metrics (how to measure effectiveness)
        
        Make it actionable for team members to follow.
        """
        
        sop = await self._think(sop_prompt)
        return {"sop_documentation": sop, "task_type": "sop_creation"}
    
    async def _handle_customer_support(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer support optimization"""
        support_data = task.get("support_data", {})
        
        support_prompt = f"""
        Optimize customer support based on this data:
        
        Support Data: {support_data}
        Context: {context}
        
        Analyze and provide:
        1. Support Ticket Analysis (common issues, resolution times)
        2. Knowledge Base Gaps (missing documentation)
        3. Upsell Opportunities (customer expansion potential)
        4. Process Improvements (efficiency gains)
        5. Customer Satisfaction Enhancement (experience improvements)
        6. Automation Opportunities (repetitive task elimination)
        """
        
        support_optimization = await self._think(support_prompt)
        return {"support_optimization": support_optimization, "task_type": "customer_support"}
    
    async def _handle_office_management(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle office management tasks"""
        management_request = task.get("management_request", {})
        
        management_prompt = f"""
        Handle this office management request:
        
        Request: {management_request}
        Context: {context}
        
        Provide:
        1. Purchasing Recommendations (vendors, pricing, specifications)
        2. Scheduling Coordination (appointments, services, maintenance)
        3. Policy Information (company policies, procedures, guidelines)
        4. Resource Management (supplies, equipment, facilities)
        5. Vendor Coordination (service providers, contractors)
        """
        
        management = await self._think(management_prompt)
        return {"office_management": management, "task_type": "office_management"}
    
    async def _optimize_workflow(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize general workflows"""
        workflow_data = task.get("workflow_data", {})
        
        optimization_prompt = f"""
        Optimize this workflow for efficiency:
        
        Workflow: {workflow_data}
        Context: {context}
        
        Analyze and recommend:
        1. Bottleneck Identification (process slowdowns)
        2. Automation Opportunities (repetitive tasks)
        3. Tool Integration (system connections)
        4. Resource Optimization (time, people, tools)
        5. Quality Improvements (error reduction)
        6. Scalability Enhancements (growth preparation)
        7. Cost Reduction (efficiency savings)
        """
        
        optimization = await self._think(optimization_prompt)
        return {"workflow_optimization": optimization, "task_type": "process_optimization"}