"""
PRD Agent Role Mapper
Maps existing agents to PRD-specified roles and enhances them with new capabilities
"""
from typing import Dict, Any, List, Optional
from loguru import logger

class PRDAgentMapper:
    """Maps existing agents to PRD roles and enhances capabilities"""
    
    def __init__(self):
        # PRD Role Mapping
        self.role_mapping = {
            # PRD Role -> Existing Agent
            "Executive_Advisor": {
                "existing_agent": "Cofounder",
                "description": "Strategic decisions, challenges/validates decisions, strategic memos",
                "enhancements": ["strategic_analysis", "decision_validation", "memo_generation"],
                "hitl_requirements": ["strategic_decisions", "budget_allocation", "major_pivots"]
            },
            "Chief_of_Staff": {
                "existing_agent": "Manager", 
                "description": "Orchestration, prioritization, routing, deadline mgmt, HITL gatekeeping",
                "enhancements": ["priority_management", "deadline_tracking", "hitl_coordination"],
                "hitl_requirements": ["workflow_changes", "priority_updates", "resource_allocation"]
            },
            "Marketing_Intelligence": {
                "existing_agent": "Marketing",
                "description": "Instagram content/scheduling, compliant DM replies, performance insights",
                "enhancements": ["instagram_automation", "dm_compliance", "performance_analytics"],
                "hitl_requirements": ["instagram_posts", "dm_responses", "campaign_launches", "content_publishing"]
            },
            "Customer_Success": {
                "existing_agent": "Sales",
                "description": "Health scoring, follow-ups, retention playbooks, CRM hygiene",
                "enhancements": ["health_scoring", "retention_automation", "crm_management"],
                "hitl_requirements": ["crm_stage_moves", "customer_communications", "retention_campaigns"]
            },
            "Financial_Operations": {
                "existing_agent": "Finance",
                "description": "Invoice/document drafts, reminders, cash-flow summaries, forecasting",
                "enhancements": ["invoice_automation", "cash_flow_analysis", "financial_forecasting"],
                "hitl_requirements": ["invoice_generation", "pricing_changes", "contracts", "financial_decisions"]
            },
            "Business_Intelligence": {
                "existing_agent": "Manager",  # Enhanced version
                "description": "Trend scans, competitor diffs, opportunity briefs, research synthesis",
                "enhancements": ["market_analysis", "competitor_tracking", "opportunity_identification"],
                "hitl_requirements": ["market_reports", "competitor_analysis", "strategic_recommendations"]
            }
        }
        
        # Enhanced capabilities per PRD
        self.enhanced_capabilities = {
            "instagram_automation": {
                "post_scheduling": "Automated Instagram post scheduling with optimal timing",
                "story_management": "Automated story posting and management",
                "hashtag_optimization": "AI-powered hashtag selection and optimization",
                "dm_compliance": "24-hour rule compliant DM automation"
            },
            "crm_management": {
                "health_scoring": "Automated lead health scoring based on HubSpot data",
                "pipeline_automation": "Automated pipeline stage transitions with HITL",
                "retention_playbooks": "Automated retention campaign execution",
                "crm_hygiene": "Automated data cleanup and enrichment"
            },
            "financial_forecasting": {
                "cash_flow_analysis": "Real-time cash flow monitoring and alerts",
                "invoice_automation": "Automated invoice generation and follow-up",
                "budget_tracking": "Automated budget variance analysis",
                "financial_reporting": "Automated financial report generation"
            },
            "strategic_analysis": {
                "decision_validation": "Multi-perspective decision analysis",
                "scenario_planning": "Automated scenario and risk analysis",
                "strategic_memos": "Executive-level strategic memo generation",
                "market_positioning": "Competitive positioning analysis"
            }
        }
    
    def get_agent_mapping(self, prd_role: str) -> Optional[Dict[str, Any]]:
        """Get mapping information for a PRD role"""
        return self.role_mapping.get(prd_role)
    
    def get_existing_agent_for_role(self, prd_role: str) -> Optional[str]:
        """Get existing agent name for PRD role"""
        mapping = self.role_mapping.get(prd_role)
        return mapping["existing_agent"] if mapping else None
    
    def get_role_enhancements(self, prd_role: str) -> List[str]:
        """Get required enhancements for PRD role"""
        mapping = self.role_mapping.get(prd_role)
        return mapping["enhancements"] if mapping else []
    
    def get_hitl_requirements(self, prd_role: str) -> List[str]:
        """Get HITL requirements for PRD role"""
        mapping = self.role_mapping.get(prd_role)
        return mapping["hitl_requirements"] if mapping else []
    
    def get_all_mappings(self) -> Dict[str, Any]:
        """Get all role mappings"""
        return self.role_mapping
    
    def get_enhancement_details(self, enhancement_key: str) -> Dict[str, str]:
        """Get details for a specific enhancement"""
        return self.enhanced_capabilities.get(enhancement_key, {})
    
    def generate_agent_enhancement_plan(self, prd_role: str) -> Dict[str, Any]:
        """Generate enhancement plan for a specific PRD role"""
        mapping = self.get_agent_mapping(prd_role)
        if not mapping:
            return {"error": f"No mapping found for role: {prd_role}"}
        
        enhancements = []
        for enhancement_key in mapping["enhancements"]:
            enhancement_details = self.get_enhancement_details(enhancement_key)
            enhancements.append({
                "key": enhancement_key,
                "capabilities": enhancement_details
            })
        
        return {
            "prd_role": prd_role,
            "existing_agent": mapping["existing_agent"],
            "description": mapping["description"],
            "enhancements_required": enhancements,
            "hitl_requirements": mapping["hitl_requirements"],
            "implementation_priority": self._get_implementation_priority(prd_role)
        }
    
    def _get_implementation_priority(self, prd_role: str) -> str:
        """Get implementation priority for role"""
        priority_map = {
            "Executive_Advisor": "high",      # Strategic foundation
            "Chief_of_Staff": "high",         # Orchestration critical
            "Marketing_Intelligence": "high", # Customer-facing
            "Customer_Success": "medium",     # Revenue impact
            "Financial_Operations": "medium", # Business operations
            "Business_Intelligence": "low"   # Supporting insights
        }
        return priority_map.get(prd_role, "medium")
    
    def validate_existing_agents(self, available_agents: List[str]) -> Dict[str, Any]:
        """Validate that required existing agents are available"""
        validation_results = {
            "valid": True,
            "missing_agents": [],
            "available_mappings": [],
            "unavailable_mappings": []
        }
        
        for prd_role, mapping in self.role_mapping.items():
            existing_agent = mapping["existing_agent"]
            if existing_agent in available_agents:
                validation_results["available_mappings"].append({
                    "prd_role": prd_role,
                    "existing_agent": existing_agent,
                    "status": "available"
                })
            else:
                validation_results["missing_agents"].append(existing_agent)
                validation_results["unavailable_mappings"].append({
                    "prd_role": prd_role,
                    "existing_agent": existing_agent,
                    "status": "missing"
                })
                validation_results["valid"] = False
        
        return validation_results
    
    def get_implementation_roadmap(self) -> Dict[str, Any]:
        """Get complete implementation roadmap for PRD compliance"""
        roadmap = {
            "phase_1_high_priority": [],
            "phase_2_medium_priority": [],
            "phase_3_low_priority": [],
            "total_enhancements": 0,
            "estimated_effort": {
                "high_priority": "2-3 weeks",
                "medium_priority": "1-2 weeks", 
                "low_priority": "1 week"
            }
        }
        
        for prd_role in self.role_mapping.keys():
            plan = self.generate_agent_enhancement_plan(prd_role)
            priority = plan["implementation_priority"]
            
            enhancement_item = {
                "prd_role": prd_role,
                "existing_agent": plan["existing_agent"],
                "enhancements_count": len(plan["enhancements_required"]),
                "hitl_requirements_count": len(plan["hitl_requirements"])
            }
            
            if priority == "high":
                roadmap["phase_1_high_priority"].append(enhancement_item)
            elif priority == "medium":
                roadmap["phase_2_medium_priority"].append(enhancement_item)
            else:
                roadmap["phase_3_low_priority"].append(enhancement_item)
            
            roadmap["total_enhancements"] += len(plan["enhancements_required"])
        
        return roadmap

# Global mapper instance
prd_agent_mapper = PRDAgentMapper()