from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
import json
from datetime import datetime

class ManagerAgent(LangGraphAgent):
    """🧭 Manager Agent - Breaks vision into workstreams + assigns agents"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "organized and tactical",
            "focus": "project coordination and task assignment",
            "expertise": ["project management", "workflow design", "resource allocation", "timeline planning"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.4,
            "confidence_threshold": 0.8,
            "description": "Breaks down vision into workstreams and assigns tasks to specialist agents"
        }
        super().__init__("Manager", "Project Management", memory_manager, approval_manager, personality)
    
    def _get_system_prompt(self) -> str:
        return """You are the Manager agent in a virtual AI startup team. Your role is to:

1. Break down the vision into actionable workstreams
2. Assign tasks to specialist agents (Product, Finance, Marketing, Legal)
3. Create project roadmap and timeline
4. Coordinate agent dependencies and workflows

You are organized and tactical. Focus on clear task definition, realistic timelines, and efficient resource allocation.

Available specialist agents:
- Product: MVP definition, features, user personas
- Finance: Budget planning, ROI analysis, pricing strategy  
- Marketing: Content strategy, SEO, outreach planning
- Legal: Terms of service, privacy policy, compliance

Structure your output as:
- Project Roadmap (phases and milestones)
- Agent Assignments (specific tasks per agent)
- Dependencies (what each agent needs from others)
- Timeline (estimated completion dates)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute manager-specific actions"""
        task = state["task"]
        context = state["context"]
        
        # Get vision from context
        vision_data = context.get("cofounder_output", {})
        if not vision_data:
            raise ValueError("No vision found in shared context")
        
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
                "Product": {
                    "type": "product_planning",
                    "primary_tasks": [
                        "Define MVP features based on vision",
                        "Create detailed user personas",
                        "Design user experience flow"
                    ],
                    "dependencies": ["Vision from Cofounder"],
                    "deliverables": ["product.json", "personas.json", "ux_flow.json"]
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
        
        # Check if all required agents are assigned
        required_agents = ["Product", "Finance", "Marketing", "Legal"]
        assigned_agents = list(outputs.get("agent_assignments", {}).keys())
        missing_agents = set(required_agents) - set(assigned_agents)
        if missing_agents:
            base_confidence -= 0.1 * len(missing_agents)
        
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