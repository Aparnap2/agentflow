from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
import json
from datetime import datetime
from loguru import logger

class ManagerAgent(LangGraphAgent):
    """🧭 Enhanced Manager Agent - Project coordination + Product insights + Workflow optimization"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "organized and tactical",
            "focus": "project coordination, product strategy, and workflow optimization",
            "expertise": [
                "project management", "workflow design", "resource allocation", "timeline planning",
                "product strategy", "user experience", "process optimization", "operational efficiency",
                "mvp definition", "user personas", "process documentation", "workflow automation"
            ],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.4,
            "confidence_threshold": 0.8,
            "description": "Enhanced manager with product insights and workflow optimization capabilities"
        }
        super().__init__("Manager", "Project Management & Product Strategy", memory_manager, approval_manager, personality)
        
        # Initialize role-specific action methods
        self.role_actions = {
            "workflow_design": self._workflow_design,
            "task_delegation": self._task_delegation,
            "progress_monitoring": self._progress_monitoring,
            "performance_tracking": self._performance_tracking,
            "intervention": self._intervention
        }
    
    def _get_system_prompt(self) -> str:
        return """You are the Enhanced Manager agent in a virtual AI startup team. Your role includes:

1. PROJECT MANAGEMENT:
   - Break down vision into actionable workstreams
   - Assign tasks to specialist agents
   - Create project roadmap and timeline
   - Coordinate agent dependencies

2. PRODUCT STRATEGY (consolidated capabilities):
   - Define MVP features and requirements
   - Create detailed user personas
   - Design user experience flows
   - Validate product-market fit

3. WORKFLOW OPTIMIZATION (consolidated capabilities):
   - Document business processes
   - Optimize workflows for efficiency
   - Identify automation opportunities
   - Streamline operations

Available specialist agents:
- Finance: Budget planning, ROI analysis, pricing strategy  
- Marketing: Content strategy, SEO, outreach planning
- Legal: Terms of service, privacy policy, compliance
- Sales: Sales strategy, pipeline management
- Money: Financial operations, payment processing

You are organized, tactical, and product-focused. Deliver comprehensive project plans with clear deliverables."""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute manager-specific actions"""
        task = state["task"]
        context = state["context"]
        
        # Handle auto-coordination mode
        if task.get("mode") == "auto_coordination":
            vision = task.get("vision", "")
            logger.info(f"Manager handling auto-coordination for vision: {vision[:50]}...")
            return self._create_auto_coordination_plan(vision)
        
        # Get vision from context or task
        vision_data = context.get("cofounder_output", {})
        if not vision_data and task.get("vision"):
            vision_data = {"vision_statement": task.get("vision", "AI productivity app")}
        elif not vision_data:
            # Create minimal vision data
            vision_data = {"vision_statement": "AI productivity application"}
        
        # Create comprehensive project breakdown
        project_plan = {
            "project_roadmap": {
                "phase_1": {
                    "name": "Foundation & Planning",
                    "duration": "2-3 weeks",
                    "deliverables": ["Product requirements", "Financial model", "Legal framework"]
                },
                "phase_2": {
                    "name": "Development & Content",
                    "duration": "4-6 weeks", 
                    "deliverables": ["MVP development", "Marketing content", "Launch preparation"]
                },
                "phase_3": {
                    "name": "Launch & Growth",
                    "duration": "Ongoing",
                    "deliverables": ["Product launch", "User acquisition", "Iteration"]
                }
            },
            "agent_assignments": {
                "Manager_Product": {
                    "type": "product_planning",
                    "primary_tasks": [
                        "Define MVP features based on vision",
                        "Create detailed user personas",
                        "Design user experience flow",
                        "Document product requirements"
                    ],
                    "dependencies": ["Vision from Cofounder"],
                    "deliverables": ["product.json", "personas.json", "ux_flow.json"],
                    "handled_by": "Manager (Product capabilities)"
                },
                "Finance": {
                    "type": "financial_planning",
                    "primary_tasks": [
                        "Create financial model and projections",
                        "Analyze pricing strategies",
                        "Calculate ROI scenarios"
                    ],
                    "dependencies": ["Product features", "Target market size"],
                    "deliverables": ["finance.json", "pricing_model.json"]
                },
                "Marketing": {
                    "type": "content_strategy",
                    "primary_tasks": [
                        "Develop content marketing strategy",
                        "Plan SEO and social media approach",
                        "Create launch campaign outline"
                    ],
                    "dependencies": ["Product positioning", "Target personas"],
                    "deliverables": ["marketing.json", "content_calendar.json"]
                },
                "Legal": {
                    "type": "compliance_check",
                    "primary_tasks": [
                        "Draft Terms of Service",
                        "Create Privacy Policy",
                        "Review compliance requirements"
                    ],
                    "dependencies": ["Business model", "Data handling approach"],
                    "deliverables": ["legal.json", "tos.md", "privacy.md"]
                }
            },
            "timeline": {
                "week_1": ["Product requirements", "Financial modeling starts"],
                "week_2": ["Legal framework", "Marketing strategy"],
                "week_3": ["Integration and review"],
                "week_4": ["Final deliverables and export"]
            },
            "coordination_plan": {
                "parallel_execution": ["Product", "Finance", "Marketing", "Legal"],
                "sync_points": [
                    "Week 1: Initial outputs review",
                    "Week 2: Cross-agent dependencies check",
                    "Week 3: Final integration"
                ]
            }
        }
        
        return project_plan
    
    def _calculate_confidence(self, outputs: Dict[str, Any]) -> float:
        """Calculate confidence based on plan completeness"""
        base_confidence = 0.9
        
        # Check for key components
        if not outputs.get("agent_assignments"):
            base_confidence -= 0.3
        if not outputs.get("project_roadmap"):
            base_confidence -= 0.2
        if not outputs.get("timeline"):
            base_confidence -= 0.1
        
        # Check if all required capabilities are assigned
        required_capabilities = ["Manager_Product", "Finance", "Marketing", "Legal"]
        assigned_capabilities = list(outputs.get("agent_assignments", {}).keys())
        missing_capabilities = set(required_capabilities) - set(assigned_capabilities)
        if missing_capabilities:
            base_confidence -= 0.1 * len(missing_capabilities)
        
        return max(0.1, min(1.0, base_confidence))
    
    async def assign_tasks_to_agents(self, agent_assignments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create task assignments for each agent"""
        tasks = []
        
        for agent_name, assignment in agent_assignments.items():
            task = {
                "id": f"task_{agent_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "agent": agent_name,
                "tasks": assignment["primary_tasks"],
                "dependencies": assignment["dependencies"],
                "deliverables": assignment["deliverables"],
                "assigned_by": self.name,
                "assigned_at": datetime.now().isoformat()
            }
            tasks.append(task)
        
        return tasks
    
    async def create_task_distribution(self, vision_summary: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Create task distribution for sub-agents"""
        tasks = {
            "Product": {
                "id": f"product_task_{project_id}",
                "type": "product_definition",
                "description": "Define MVP features and user personas",
                "inputs": vision_summary,
                "status": "pending_approval"
            },
            "Finance": {
                "id": f"finance_task_{project_id}",
                "type": "financial_modeling", 
                "description": "Create financial projections and pricing",
                "inputs": vision_summary,
                "status": "pending_approval"
            },
            "Marketing": {
                "id": f"marketing_task_{project_id}",
                "type": "marketing_strategy",
                "description": "Develop content and outreach strategy", 
                "inputs": vision_summary,
                "status": "pending_approval"
            },
            "Legal": {
                "id": f"legal_task_{project_id}",
                "type": "compliance_review",
                "description": "Draft legal documents and compliance check",
                "inputs": vision_summary,
                "status": "pending_approval"
            }
        }
        return {"tasks": tasks, "project_id": project_id}
    
    def _create_auto_coordination_plan(self, vision: str) -> Dict[str, Any]:
        """Create plan for auto-coordination mode"""
        logger.info(f"Creating auto-coordination plan for: {vision}")
        
        plan = {
            "project_roadmap": {
                "phase_1": {"name": "Foundation", "duration": "2 weeks"},
                "phase_2": {"name": "Development", "duration": "4 weeks"},
                "phase_3": {"name": "Launch", "duration": "Ongoing"}
            },
            "agent_assignments": {
                "Manager_Product": {"type": "product_planning", "primary_tasks": ["Define MVP", "Create personas"], "handled_by": "Manager"},
                "Finance": {"type": "financial_planning", "primary_tasks": ["Financial model", "Pricing"]},
                "Marketing": {"type": "content_strategy", "primary_tasks": ["Marketing strategy", "Content plan"]},
                "Legal": {"type": "compliance_check", "primary_tasks": ["Terms of service", "Privacy policy"]}
            },
            "vision": vision,
            "confidence": 0.8
        }
        
        logger.info(f"Auto-coordination plan created with {len(plan['agent_assignments'])} agent assignments")
        return plan
    
    # === PRODUCT CAPABILITIES (from Product Agent) ===
    async def define_mvp(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Define MVP features based on vision (consolidated from Product agent)"""
        mvp_prompt = f"""
        Define MVP features for this vision:
        
        Vision: {vision_data.get('vision_statement', '')}
        
        Provide:
        1. Core Features (3-5 essential features)
        2. Technical Requirements
        3. Success Criteria
        4. User Journey
        """
        
        mvp_definition = await self._think(mvp_prompt)
        return {"mvp_definition": mvp_definition, "confidence": 0.85}
    
    async def create_user_personas(self, target_users: List[str]) -> List[Dict[str, Any]]:
        """Create user personas (consolidated from Product agent)"""
        personas = []
        
        for user_type in target_users[:3]:  # Limit to 3 personas
            persona_prompt = f"""
            Create detailed user persona for: {user_type}
            
            Include:
            - Demographics
            - Goals and motivations
            - Pain points
            - User journey touchpoints
            - Feature priorities
            """
            
            persona = await self._think(persona_prompt)
            personas.append({"type": user_type, "details": persona})
        
        return personas
    
    # === ROLE-SPECIFIC ACTION METHODS ===
    async def _workflow_design(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Design workflow based on vision data"""
        vision_data = params.get("vision_data", {})
        project_id = params.get("project_id", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not vision_data:
            return {"error": "No vision data provided for workflow design", "success": False}
        
        workflow_prompt = f"""
        Design a comprehensive workflow for this project:
        
        Vision: {json.dumps(vision_data, indent=2)}
        
        Create a workflow that includes:
        1. Sequential phases with clear deliverables
        2. Task dependencies and relationships
        3. Agent assignments with responsibilities
        4. Timeline with milestones
        5. Coordination points for cross-agent collaboration
        
        Make it specific, actionable, and optimized for parallel execution where possible.
        """
        
        workflow_result = await self._think(workflow_prompt)
        
        # Store workflow in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="workflow_design",
            content=workflow_result,
            is_shared=True,
            confidence=0.9,
            metadata={"project_id": project_id}
        )
        
        return {
            "workflow": workflow_result,
            "project_id": project_id,
            "confidence": 0.9
        }
    
    async def _task_delegation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate tasks to appropriate agents"""
        workflow = params.get("workflow", {})
        available_agents = params.get("available_agents", ["Finance", "Marketing", "Legal", "Sales"])
        project_id = params.get("project_id", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not workflow:
            return {"error": "No workflow provided for task delegation", "success": False}
        
        # Create task assignments for each agent
        agent_assignments = {}
        
        for agent_name in available_agents:
            # Determine appropriate tasks based on agent type
            if agent_name == "Finance":
                primary_tasks = [
                    "Create financial model and projections",
                    "Analyze pricing strategies",
                    "Calculate ROI scenarios"
                ]
                dependencies = ["Product features", "Target market size"]
                deliverables = ["finance.json", "pricing_model.json"]
            elif agent_name == "Marketing":
                primary_tasks = [
                    "Develop content marketing strategy",
                    "Plan SEO and social media approach",
                    "Create launch campaign outline"
                ]
                dependencies = ["Product positioning", "Target personas"]
                deliverables = ["marketing.json", "content_calendar.json"]
            elif agent_name == "Legal":
                primary_tasks = [
                    "Draft Terms of Service",
                    "Create Privacy Policy",
                    "Review compliance requirements"
                ]
                dependencies = ["Business model", "Data handling approach"]
                deliverables = ["legal.json", "tos.md", "privacy.md"]
            elif agent_name == "Sales":
                primary_tasks = [
                    "Develop sales strategy",
                    "Create outreach templates",
                    "Design sales funnel"
                ]
                dependencies = ["Product features", "Target personas"]
                deliverables = ["sales.json", "outreach_templates.json"]
            else:
                # Generic tasks for unknown agent types
                primary_tasks = ["Analyze requirements", "Create implementation plan", "Deliver outputs"]
                dependencies = ["Project vision"]
                deliverables = [f"{agent_name.lower()}_output.json"]
            
            # Create assignment
            agent_assignments[agent_name] = {
                "type": f"{agent_name.lower()}_tasks",
                "primary_tasks": primary_tasks,
                "dependencies": dependencies,
                "deliverables": deliverables
            }
        
        # Create tasks in queue system
        tasks = []
        for agent_name, assignment in agent_assignments.items():
            task_id = f"task_{agent_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create task object
            task = {
                "id": task_id,
                "agent": agent_name,
                "tasks": assignment["primary_tasks"],
                "dependencies": assignment["dependencies"],
                "deliverables": assignment["deliverables"],
                "assigned_by": self.name,
                "assigned_at": datetime.now().isoformat(),
                "project_id": project_id,
                "status": "pending"
            }
            
            tasks.append(task)
        
        # Store task assignments in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="task_assignments",
            content={"agent_assignments": agent_assignments, "tasks": tasks},
            is_shared=True,
            confidence=0.9,
            metadata={"project_id": project_id}
        )
        
        return {
            "agent_assignments": agent_assignments,
            "tasks": tasks,
            "project_id": project_id,
            "confidence": 0.9
        }
    
    async def _progress_monitoring(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor progress of assigned tasks"""
        project_id = params.get("project_id")
        task_ids = params.get("task_ids", [])
        
        if not project_id and not task_ids:
            return {"error": "No project_id or task_ids provided for monitoring", "success": False}
        
        # Get task status from memory or queue system
        task_statuses = {}
        
        for task_id in task_ids:
            # In a real implementation, this would query the queue system
            # For now, we'll simulate with random statuses
            import random
            statuses = ["pending", "in_progress", "completed", "blocked"]
            task_statuses[task_id] = random.choice(statuses)
        
        # Calculate overall progress
        completed = sum(1 for status in task_statuses.values() if status == "completed")
        in_progress = sum(1 for status in task_statuses.values() if status == "in_progress")
        blocked = sum(1 for status in task_statuses.values() if status == "blocked")
        total = len(task_statuses)
        
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        # Identify bottlenecks
        bottlenecks = [task_id for task_id, status in task_statuses.items() if status == "blocked"]
        
        # Store monitoring results in memory
        monitoring_result = {
            "project_id": project_id,
            "task_statuses": task_statuses,
            "progress_percentage": progress_percentage,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked,
            "bottlenecks": bottlenecks,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="progress_monitoring",
            content=monitoring_result,
            is_shared=True,
            confidence=1.0,
            metadata={"project_id": project_id}
        )
        
        return monitoring_result
    
    async def _performance_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Track performance metrics for a project"""
        project_id = params.get("project_id")
        metrics = params.get("metrics", {})
        
        if not project_id:
            return {"error": "No project_id provided for performance tracking", "success": False}
        
        # If no metrics provided, generate some default ones
        if not metrics:
            metrics = {
                "time_efficiency": {
                    "target": 100,
                    "actual": 85,
                    "unit": "percentage"
                },
                "resource_utilization": {
                    "target": 90,
                    "actual": 75,
                    "unit": "percentage"
                },
                "output_quality": {
                    "target": 95,
                    "actual": 90,
                    "unit": "percentage"
                }
            }
        
        # Calculate performance scores
        performance_scores = {}
        for metric_name, metric_data in metrics.items():
            target = metric_data.get("target", 100)
            actual = metric_data.get("actual", 0)
            performance_scores[metric_name] = (actual / target * 100) if target > 0 else 0
        
        # Calculate overall performance score
        overall_score = sum(performance_scores.values()) / len(performance_scores) if performance_scores else 0
        
        # Generate recommendations based on performance
        recommendations = []
        for metric_name, score in performance_scores.items():
            if score < 70:
                recommendations.append(f"Critical improvement needed for {metric_name}")
            elif score < 90:
                recommendations.append(f"Moderate improvement needed for {metric_name}")
        
        # Store performance tracking results in memory
        performance_result = {
            "project_id": project_id,
            "metrics": metrics,
            "performance_scores": performance_scores,
            "overall_score": overall_score,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="performance_tracking",
            content=performance_result,
            is_shared=True,
            confidence=1.0,
            metadata={"project_id": project_id}
        )
        
        return performance_result
    
    async def _intervention(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle intervention for problematic tasks"""
        task_id = params.get("task_id")
        issue = params.get("issue", "")
        project_id = params.get("project_id")
        
        if not task_id:
            return {"error": "No task_id provided for intervention", "success": False}
        
        # Determine intervention type based on issue
        if "blocked" in issue.lower():
            intervention_type = "unblock_task"
        elif "quality" in issue.lower():
            intervention_type = "improve_quality"
        elif "deadline" in issue.lower():
            intervention_type = "extend_deadline"
        else:
            intervention_type = "general_assistance"
        
        # Generate intervention plan
        intervention_prompt = f"""
        Create an intervention plan for this issue:
        
        Task ID: {task_id}
        Issue: {issue}
        Intervention Type: {intervention_type}
        
        Provide:
        1. Root cause analysis
        2. Immediate actions
        3. Long-term solutions
        4. Resource requirements
        """
        
        intervention_plan = await self._think(intervention_prompt)
        
        # Store intervention in memory
        intervention_result = {
            "task_id": task_id,
            "project_id": project_id,
            "issue": issue,
            "intervention_type": intervention_type,
            "intervention_plan": intervention_plan,
            "status": "pending_implementation",
            "created_at": datetime.now().isoformat()
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="interventions",
            content=intervention_result,
            is_shared=True,
            confidence=0.9,
            metadata={"project_id": project_id, "task_id": task_id}
        )
        
        return intervention_result
    
    # === WORKFLOW CAPABILITIES (from Workflow Agent) ===
    async def create_process_documentation(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create process documentation (consolidated from Workflow agent)"""
        doc_prompt = f"""
        Create comprehensive process documentation:
        
        Process: {process_data.get('process_name', 'Business Process')}
        Context: {process_data.get('context', '')}
        
        Include:
        1. Process Overview
        2. Step-by-step workflow
        3. Roles and responsibilities
        4. Tools and resources needed
        5. Success metrics
        6. Optimization opportunities
        """
        
        documentation = await self._think(doc_prompt)
        return {"process_documentation": documentation, "confidence": 0.8}
    
    async def optimize_workflow(self, current_workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing workflow (consolidated from Workflow agent)"""
        optimization_prompt = f"""
        Analyze and optimize this workflow:
        
        Current Workflow: {current_workflow}
        
        Provide:
        1. Bottleneck analysis
        2. Efficiency improvements
        3. Automation opportunities
        4. Resource optimization
        5. Timeline improvements
        """
        
        optimization = await self._think(optimization_prompt)
        return {"workflow_optimization": optimization, "confidence": 0.8}