"""
Operations Agent - Process optimization, quality assurance, and scalability planning
"""

from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import RiskAssessmentTool
from datetime import datetime
from typing import Dict, Any, List

class OperationsAgent(LangGraphAgent):
    """Operations Agent responsible for process optimization and scalability"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "systematic and efficiency-focused",
            "focus": "operational excellence and scalability",
            "expertise": ["process optimization", "quality assurance", "scalability planning", "performance monitoring"],
            "model": "openai/gpt-3.5-turbo",
            "temperature": 0.3,
            "confidence_threshold": 0.8,
            "description": "Optimizes operations, ensures quality, and plans for scalable growth"
        }
        
        super().__init__(
            name="Operations",
            role="Operations and process optimization specialist",
            memory_manager=memory_manager,
            approval_manager=approval_manager,
            personality=personality
        )
        
        self.web_search = WebSearchTool()
        self.risk_tool = RiskAssessmentTool()
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute operations-specific analysis"""
        task = state["task"]
        context = state["context"]
        
        # Get context from other agents
        vision_data = await self._get_context_data(context, "cofounder_output")
        product_data = await self._get_context_data(context, "product_output")
        finance_data = await self._get_context_data(context, "finance_output")
        
        # Perform operations analysis
        process_optimization = await self._analyze_processes(vision_data, product_data)
        quality_framework = await self._design_quality_framework(product_data)
        scalability_plan = await self._create_scalability_plan(vision_data, finance_data)
        operational_risks = await self._assess_operational_risks(vision_data)
        
        # Get current operational insights
        ops_insights = await self._get_operational_insights(vision_data)
        
        return {
            "process_optimization": process_optimization,
            "quality_framework": quality_framework,
            "scalability_plan": scalability_plan,
            "operational_risks": operational_risks,
            "operational_insights": ops_insights,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _analyze_processes(self, vision_data: Dict, product_data: Dict) -> Dict[str, Any]:
        """Analyze and optimize key business processes"""
        
        core_processes = {
            "customer_onboarding": {
                "current_state": "Manual process with email sequences",
                "optimization_opportunities": [
                    "Automate welcome email series",
                    "Create interactive onboarding checklist",
                    "Implement progress tracking"
                ],
                "expected_improvement": "50% reduction in time-to-value",
                "implementation_effort": "Medium",
                "priority": "High"
            },
            "customer_support": {
                "current_state": "Email-based support system",
                "optimization_opportunities": [
                    "Implement help desk ticketing system",
                    "Create knowledge base and FAQ",
                    "Add live chat functionality"
                ],
                "expected_improvement": "40% reduction in response time",
                "implementation_effort": "Medium",
                "priority": "High"
            },
            "product_development": {
                "current_state": "Ad-hoc development process",
                "optimization_opportunities": [
                    "Implement agile development methodology",
                    "Set up CI/CD pipeline",
                    "Establish code review process"
                ],
                "expected_improvement": "30% faster feature delivery",
                "implementation_effort": "High",
                "priority": "Medium"
            },
            "sales_process": {
                "current_state": "Manual lead qualification and follow-up",
                "optimization_opportunities": [
                    "Implement CRM system",
                    "Automate lead scoring",
                    "Create sales playbooks"
                ],
                "expected_improvement": "25% increase in conversion rate",
                "implementation_effort": "Medium",
                "priority": "High"
            }
        }
        
        return {
            "process_analysis": core_processes,
            "automation_roadmap": self._create_automation_roadmap(core_processes),
            "efficiency_metrics": {
                "current_efficiency_score": 65,
                "target_efficiency_score": 85,
                "improvement_timeline": "6 months"
            },
            "resource_requirements": {
                "tools_needed": ["CRM", "Help Desk", "CI/CD Platform", "Analytics"],
                "team_additions": ["Operations Manager", "QA Engineer"],
                "estimated_cost": "$15K setup + $5K monthly"
            }
        }
    
    async def _design_quality_framework(self, product_data: Dict) -> Dict[str, Any]:
        """Design comprehensive quality assurance framework"""
        
        mvp_features = product_data.get("mvp_definition", {}).get("core_features", [])
        
        return {
            "quality_standards": {
                "code_quality": {
                    "standards": ["Code review required", "80% test coverage", "No critical security issues"],
                    "tools": ["SonarQube", "ESLint", "Security scanner"],
                    "metrics": ["Cyclomatic complexity < 10", "Duplication < 3%"]
                },
                "product_quality": {
                    "standards": ["99.9% uptime", "< 2s page load time", "Zero data loss"],
                    "tools": ["Monitoring dashboard", "Performance testing", "Backup systems"],
                    "metrics": ["Error rate < 0.1%", "Customer satisfaction > 4.5/5"]
                },
                "process_quality": {
                    "standards": ["Documented procedures", "Regular audits", "Continuous improvement"],
                    "tools": ["Process documentation", "Audit checklists", "Feedback systems"],
                    "metrics": ["Process compliance > 95%", "Improvement suggestions implemented"]
                }
            },
            "testing_strategy": {
                "unit_testing": "Automated with 80% coverage",
                "integration_testing": "Automated for critical paths",
                "user_acceptance_testing": "Manual testing with real users",
                "performance_testing": "Load testing for expected traffic",
                "security_testing": "Regular penetration testing"
            },
            "quality_gates": {
                "development": ["Code review approval", "All tests passing", "Security scan clean"],
                "staging": ["Integration tests passing", "Performance benchmarks met"],
                "production": ["Monitoring alerts configured", "Rollback plan ready"]
            },
            "continuous_improvement": {
                "feedback_loops": ["Customer feedback", "Team retrospectives", "Metrics review"],
                "improvement_cycle": "Monthly quality reviews",
                "success_metrics": ["Defect reduction", "Customer satisfaction", "Team velocity"]
            }
        }
    
    async def _create_scalability_plan(self, vision_data: Dict, finance_data: Dict) -> Dict[str, Any]:
        """Create comprehensive scalability plan"""
        
        growth_projections = finance_data.get("financial_projections", {})
        
        return {
            "scaling_phases": {
                "phase_1_startup": {
                    "timeline": "Months 1-6",
                    "user_capacity": "0-1K users",
                    "team_size": "5-10 people",
                    "infrastructure": "Single server, basic monitoring",
                    "key_focus": "Product-market fit"
                },
                "phase_2_growth": {
                    "timeline": "Months 7-18",
                    "user_capacity": "1K-10K users",
                    "team_size": "10-25 people",
                    "infrastructure": "Load balancer, database scaling, CDN",
                    "key_focus": "Process optimization"
                },
                "phase_3_scale": {
                    "timeline": "Months 19-36",
                    "user_capacity": "10K-100K users",
                    "team_size": "25-50 people",
                    "infrastructure": "Microservices, auto-scaling, multi-region",
                    "key_focus": "Operational excellence"
                }
            },
            "infrastructure_scaling": {
                "current_architecture": "Monolithic application",
                "scaling_triggers": ["Response time > 2s", "CPU usage > 80%", "Error rate > 1%"],
                "scaling_actions": [
                    "Horizontal scaling with load balancers",
                    "Database read replicas",
                    "Caching layer implementation",
                    "CDN for static assets"
                ],
                "cost_projections": {
                    "current": "$500/month",
                    "phase_2": "$2K/month",
                    "phase_3": "$10K/month"
                }
            },
            "team_scaling": {
                "hiring_plan": {
                    "immediate": ["Senior Developer", "Customer Success Manager"],
                    "6_months": ["DevOps Engineer", "QA Engineer", "Product Manager"],
                    "12_months": ["Engineering Manager", "Data Analyst", "Security Engineer"]
                },
                "organizational_structure": {
                    "current": "Flat structure",
                    "phase_2": "Functional teams",
                    "phase_3": "Cross-functional squads"
                }
            },
            "process_scaling": {
                "automation_priorities": [
                    "Deployment automation",
                    "Testing automation",
                    "Monitoring and alerting",
                    "Customer onboarding"
                ],
                "governance_framework": {
                    "decision_making": "RACI matrix",
                    "communication": "Weekly all-hands, daily standups",
                    "documentation": "Centralized knowledge base"
                }
            }
        }
    
    async def _assess_operational_risks(self, vision_data: Dict) -> Dict[str, Any]:
        """Assess operational risks using risk assessment tool"""
        
        business_context = {
            "business_model": vision_data.get("vision_statement", ""),
            "stage": "startup",
            "team_size": "small"
        }
        
        risk_assessment = await self.risk_tool._arun(business_context)
        
        # Add operations-specific risks
        operational_risks = {
            "single_points_of_failure": [
                {"risk": "Key person dependency", "mitigation": "Cross-training and documentation"},
                {"risk": "Single server architecture", "mitigation": "Implement redundancy"},
                {"risk": "Manual processes", "mitigation": "Automation roadmap"}
            ],
            "capacity_risks": [
                {"risk": "Traffic spikes", "mitigation": "Auto-scaling configuration"},
                {"risk": "Data growth", "mitigation": "Database scaling plan"},
                {"risk": "Support volume", "mitigation": "Self-service options"}
            ],
            "quality_risks": [
                {"risk": "Lack of testing", "mitigation": "Automated testing suite"},
                {"risk": "No monitoring", "mitigation": "Comprehensive monitoring"},
                {"risk": "Security vulnerabilities", "mitigation": "Security audit and fixes"}
            ]
        }
        
        return {
            **risk_assessment,
            "operational_specific_risks": operational_risks,
            "risk_monitoring": {
                "key_metrics": ["System uptime", "Response time", "Error rate", "Customer satisfaction"],
                "alert_thresholds": ["Uptime < 99.5%", "Response time > 3s", "Error rate > 0.5%"],
                "review_frequency": "Weekly risk assessment meetings"
            }
        }
    
    async def _get_operational_insights(self, vision_data: Dict) -> Dict[str, Any]:
        """Get current operational insights from web search"""
        try:
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"operational excellence best practices {vision_statement[:50]} startup 2024"
            
            ops_data = await self.web_search._arun(search_query)
            
            return {
                "current_ops_trends": ops_data.get("summary", "Analysis in progress"),
                "best_practices": [result.get("title", "") for result in ops_data.get("results", [])[:3]],
                "industry_benchmarks": "Research in progress",
                "last_updated": ops_data.get("timestamp", "")
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual operations research required"}
    
    async def _get_context_data(self, context: Dict, key: str) -> Dict[str, Any]:
        """Helper to get context data with fallback"""
        if key in context:
            return context[key]
        
        shared_context = await self.memory_manager.get_shared_context()
        return shared_context.get(key, [{}])[0].get("content", {}) if shared_context.get(key) else {}
    
    def _create_automation_roadmap(self, processes: Dict) -> Dict[str, Any]:
        """Create automation implementation roadmap"""
        high_priority = [name for name, data in processes.items() if data["priority"] == "High"]
        medium_priority = [name for name, data in processes.items() if data["priority"] == "Medium"]
        
        return {
            "phase_1": {
                "timeline": "Months 1-3",
                "processes": high_priority[:2],
                "expected_roi": "200%"
            },
            "phase_2": {
                "timeline": "Months 4-6",
                "processes": high_priority[2:] + medium_priority[:1],
                "expected_roi": "150%"
            },
            "phase_3": {
                "timeline": "Months 7-12",
                "processes": medium_priority[1:],
                "expected_roi": "100%"
            }
        }