from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import json
from datetime import datetime

class ManagerAgent(BaseAgent):
    """🧭 Manager Agent - Breaks vision into workstreams + assigns agents"""
    
    def __init__(self):
        personality = {
            "tone": "organized",
            "depth": "tactical", 
            "confidence_threshold": 0.8,
            "retry_limit": 3
        }
        super().__init__("Manager", "Project Management", personality)
    
    def get_system_prompt(self) -> str:
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
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process vision breakdown and agent assignment"""
        
        # Get vision from shared memory
        vision_context = await self.get_context("cofounder_output")
        if not vision_context:
            return {
                "error": "No vision found in shared memory",
                "confidence": 0.0,
                "agent": self.name
            }
        
        vision_data = vision_context[0]["content"]
        
        # Use workflow generation tool
        workflow_tool = self.tools.get_tool("workflow_generate")
        
        # Create project breakdown
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
                    "primary_tasks": [
                        "Define MVP features based on vision",
                        "Create detailed user personas",
                        "Design user experience flow"
                    ],
                    "dependencies": ["Vision from Cofounder"],
                    "deliverables": ["product.json", "personas.json", "ux_flow.json"]
                },
                "Finance": {
                    "primary_tasks": [
                        "Create financial model and projections",
                        "Analyze pricing strategies",
                        "Calculate ROI scenarios"
                    ],
                    "dependencies": ["Product features", "Target market size"],
                    "deliverables": ["finance.json", "pricing_model.json"]
                },
                "Marketing": {
                    "primary_tasks": [
                        "Develop content marketing strategy",
                        "Plan SEO and social media approach",
                        "Create launch campaign outline"
                    ],
                    "dependencies": ["Product positioning", "Target personas"],
                    "deliverables": ["marketing.json", "content_calendar.json"]
                },
                "Legal": {
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
            }
        }
        
        confidence = 0.9
        
        result = {
            "output": project_plan,
            "confidence": confidence,
            "summary": f"Created project roadmap with {len(project_plan['agent_assignments'])} agent assignments",
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "next_actions": list(project_plan["agent_assignments"].keys())
        }
        
        # Store detailed plan in vector memory
        plan_text = f"Project roadmap: {json.dumps(project_plan['project_roadmap'])} Agent assignments: {json.dumps(project_plan['agent_assignments'])}"
        await self.vector_memory.store_document(
            text=plan_text,
            metadata={"type": "project_plan", "timestamp": result["timestamp"]},
            agent=self.name
        )
        
        return result
    
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