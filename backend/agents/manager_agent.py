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