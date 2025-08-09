"""
Workflow Templates - Predefined workflow templates for common tasks
"""

from typing import Dict, Any, List

class WorkflowTemplates:
    """Predefined workflow templates for common tasks"""
    
    @staticmethod
    def get_content_workflow_template() -> Dict[str, Any]:
        """Get content workflow template"""
        return {
            "name": "Content Creation Workflow",
            "description": "Create and publish content across platforms",
            "type": "content_creation",
            "config": {
                "research_agent": "research",
                "content_agent": "content",
                "review_agent": "manager"
            },
            "steps": [
                {
                    "name": "research",
                    "agent": "research",
                    "description": "Research topic and gather information",
                    "inputs": ["topic", "keywords"],
                    "outputs": ["research_results"]
                },
                {
                    "name": "draft",
                    "agent": "content",
                    "description": "Create content draft",
                    "inputs": ["topic", "keywords", "research_results", "tone"],
                    "outputs": ["draft_content"]
                },
                {
                    "name": "review",
                    "agent": "manager",
                    "description": "Review content for quality",
                    "inputs": ["draft_content", "brand_guidelines"],
                    "outputs": ["reviewed_content", "needs_revision"]
                },
                {
                    "name": "publish",
                    "tool": "publisher",
                    "description": "Publish content to platforms",
                    "inputs": ["reviewed_content", "platforms"],
                    "outputs": ["publish_results"]
                }
            ]
        }
    
    @staticmethod
    def get_client_workflow_template() -> Dict[str, Any]:
        """Get client management workflow template"""
        return {
            "name": "Client Management Workflow",
            "description": "Manage client relationships from proposal to invoice",
            "type": "client_management",
            "config": {
                "client_agent": "client",
                "finance_agent": "finance",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "gather_requirements",
                    "agent": "client",
                    "description": "Gather client requirements",
                    "inputs": ["client_name", "project_type"],
                    "outputs": ["client_requirements"]
                },
                {
                    "name": "create_proposal",
                    "agent": "client",
                    "description": "Create client proposal",
                    "inputs": ["client_requirements", "pricing_guidelines"],
                    "outputs": ["proposal"]
                },
                {
                    "name": "review_proposal",
                    "agent": "manager",
                    "description": "Review proposal for quality and pricing",
                    "inputs": ["proposal", "company_guidelines"],
                    "outputs": ["reviewed_proposal", "needs_revision"]
                },
                {
                    "name": "create_invoice",
                    "agent": "finance",
                    "description": "Create invoice based on proposal",
                    "inputs": ["reviewed_proposal", "client_info"],
                    "outputs": ["invoice"]
                },
                {
                    "name": "send_documents",
                    "tool": "document_sender",
                    "description": "Send proposal and invoice to client",
                    "inputs": ["reviewed_proposal", "invoice", "client_email"],
                    "outputs": ["send_results"]
                }
            ]
        }
    
    @staticmethod
    def get_financial_workflow_template() -> Dict[str, Any]:
        """Get financial workflow template"""
        return {
            "name": "Financial Analysis Workflow",
            "description": "Analyze financial data and create reports",
            "type": "financial",
            "config": {
                "finance_agent": "finance",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "gather_data",
                    "agent": "finance",
                    "description": "Gather financial data",
                    "inputs": ["data_sources", "time_period"],
                    "outputs": ["financial_data"]
                },
                {
                    "name": "analyze_data",
                    "agent": "finance",
                    "description": "Analyze financial data",
                    "inputs": ["financial_data", "analysis_type"],
                    "outputs": ["analysis_results"]
                },
                {
                    "name": "create_report",
                    "agent": "finance",
                    "description": "Create financial report",
                    "inputs": ["analysis_results", "report_type"],
                    "outputs": ["financial_report"]
                },
                {
                    "name": "review_report",
                    "agent": "manager",
                    "description": "Review financial report",
                    "inputs": ["financial_report", "company_guidelines"],
                    "outputs": ["reviewed_report", "needs_revision"]
                },
                {
                    "name": "finalize_report",
                    "tool": "report_finalizer",
                    "description": "Finalize and format report",
                    "inputs": ["reviewed_report", "format"],
                    "outputs": ["final_report"]
                }
            ]
        }
    
    @staticmethod
    def get_research_workflow_template() -> Dict[str, Any]:
        """Get research workflow template"""
        return {
            "name": "Market Research Workflow",
            "description": "Research markets and create comprehensive reports",
            "type": "research",
            "config": {
                "research_agent": "research",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "define_scope",
                    "agent": "manager",
                    "description": "Define research scope and objectives",
                    "inputs": ["research_topic", "objectives"],
                    "outputs": ["research_scope"]
                },
                {
                    "name": "gather_data",
                    "agent": "research",
                    "description": "Gather market data from various sources",
                    "inputs": ["research_scope", "data_sources"],
                    "outputs": ["market_data"]
                },
                {
                    "name": "analyze_data",
                    "agent": "research",
                    "description": "Analyze market data",
                    "inputs": ["market_data", "analysis_framework"],
                    "outputs": ["analysis_results"]
                },
                {
                    "name": "create_report",
                    "agent": "research",
                    "description": "Create market research report",
                    "inputs": ["analysis_results", "report_template"],
                    "outputs": ["research_report"]
                },
                {
                    "name": "review_report",
                    "agent": "manager",
                    "description": "Review research report",
                    "inputs": ["research_report", "quality_guidelines"],
                    "outputs": ["reviewed_report", "needs_revision"]
                },
                {
                    "name": "finalize_report",
                    "tool": "report_finalizer",
                    "description": "Finalize and format report",
                    "inputs": ["reviewed_report", "format"],
                    "outputs": ["final_report"]
                }
            ]
        }
    
    @staticmethod
    def get_marketing_campaign_workflow_template() -> Dict[str, Any]:
        """Get marketing campaign workflow template with cross-agent collaboration"""
        return {
            "name": "Marketing Campaign Workflow",
            "description": "Create and execute marketing campaigns with legal compliance and financial tracking",
            "type": "marketing_campaign",
            "config": {
                "marketing_agent": "marketing",
                "legal_agent": "legal",
                "finance_agent": "finance",
                "strategy_agent": "strategy",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "campaign_strategy",
                    "agent": "strategy",
                    "description": "Develop campaign strategy aligned with business goals",
                    "inputs": ["campaign_objectives", "target_audience", "business_goals"],
                    "outputs": ["campaign_strategy"]
                },
                {
                    "name": "budget_allocation",
                    "agent": "finance",
                    "description": "Allocate budget for campaign components",
                    "inputs": ["campaign_strategy", "available_budget", "fiscal_constraints"],
                    "outputs": ["campaign_budget"]
                },
                {
                    "name": "content_creation",
                    "agent": "marketing",
                    "description": "Create campaign content and materials",
                    "inputs": ["campaign_strategy", "campaign_budget", "brand_guidelines"],
                    "outputs": ["campaign_content"]
                },
                {
                    "name": "legal_review",
                    "agent": "legal",
                    "description": "Review campaign for legal compliance",
                    "inputs": ["campaign_content", "regulatory_requirements"],
                    "outputs": ["legal_review", "compliance_issues"]
                },
                {
                    "name": "content_revision",
                    "agent": "marketing",
                    "description": "Revise content based on legal feedback",
                    "inputs": ["campaign_content", "legal_review", "compliance_issues"],
                    "outputs": ["revised_content"]
                },
                {
                    "name": "final_approval",
                    "agent": "manager",
                    "description": "Final review and approval of campaign",
                    "inputs": ["revised_content", "campaign_budget", "legal_review"],
                    "outputs": ["approved_campaign", "needs_revision"]
                },
                {
                    "name": "campaign_execution",
                    "agent": "marketing",
                    "description": "Execute approved marketing campaign",
                    "inputs": ["approved_campaign", "campaign_channels"],
                    "outputs": ["execution_results"]
                },
                {
                    "name": "performance_tracking",
                    "agent": "finance",
                    "description": "Track ROI and financial performance of campaign",
                    "inputs": ["execution_results", "campaign_budget", "performance_metrics"],
                    "outputs": ["financial_performance"]
                },
                {
                    "name": "campaign_analysis",
                    "collaborative_decision": {
                        "agents": ["marketing", "finance", "strategy"],
                        "description": "Analyze campaign results and determine next steps",
                        "inputs": ["execution_results", "financial_performance"],
                        "outputs": ["campaign_analysis", "recommendations"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_strategic_planning_workflow_template() -> Dict[str, Any]:
        """Get strategic planning workflow template with cross-functional collaboration"""
        return {
            "name": "Strategic Planning Workflow",
            "description": "Develop comprehensive strategic plans with cross-functional input",
            "type": "strategic_planning",
            "config": {
                "cofounder_agent": "cofounder",
                "strategy_agent": "strategy",
                "finance_agent": "finance",
                "marketing_agent": "marketing",
                "legal_agent": "legal",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "vision_setting",
                    "agent": "cofounder",
                    "description": "Define vision and high-level objectives",
                    "inputs": ["business_context", "market_trends", "organizational_goals"],
                    "outputs": ["vision_statement", "strategic_objectives"]
                },
                {
                    "name": "market_analysis",
                    "agent": "strategy",
                    "description": "Analyze market conditions and competitive landscape",
                    "inputs": ["vision_statement", "market_data", "competitor_information"],
                    "outputs": ["market_analysis", "opportunity_assessment"]
                },
                {
                    "name": "financial_projection",
                    "agent": "finance",
                    "description": "Create financial projections and resource requirements",
                    "inputs": ["strategic_objectives", "market_analysis", "historical_financials"],
                    "outputs": ["financial_projections", "resource_requirements"]
                },
                {
                    "name": "marketing_strategy",
                    "agent": "marketing",
                    "description": "Develop marketing strategy aligned with objectives",
                    "inputs": ["strategic_objectives", "market_analysis", "target_segments"],
                    "outputs": ["marketing_strategy", "brand_positioning"]
                },
                {
                    "name": "legal_assessment",
                    "agent": "legal",
                    "description": "Assess legal implications and regulatory requirements",
                    "inputs": ["strategic_objectives", "market_analysis", "operational_changes"],
                    "outputs": ["legal_assessment", "compliance_requirements"]
                },
                {
                    "name": "cross_functional_impact",
                    "collaborative_decision": {
                        "agents": ["strategy", "finance", "marketing", "legal"],
                        "description": "Analyze cross-functional impacts of strategic plan",
                        "inputs": ["strategic_objectives", "financial_projections", "marketing_strategy", "legal_assessment"],
                        "outputs": ["impact_analysis", "risk_assessment"]
                    }
                },
                {
                    "name": "implementation_planning",
                    "agent": "manager",
                    "description": "Develop implementation plan with milestones and responsibilities",
                    "inputs": ["strategic_objectives", "impact_analysis", "resource_requirements"],
                    "outputs": ["implementation_plan", "milestone_schedule"]
                },
                {
                    "name": "executive_review",
                    "agent": "cofounder",
                    "description": "Review and approve final strategic plan",
                    "inputs": ["implementation_plan", "impact_analysis", "risk_assessment"],
                    "outputs": ["approved_strategic_plan", "executive_feedback"]
                },
                {
                    "name": "communication_planning",
                    "agent": "marketing",
                    "description": "Develop communication plan for strategic initiatives",
                    "inputs": ["approved_strategic_plan", "stakeholder_analysis"],
                    "outputs": ["communication_plan", "stakeholder_messages"]
                }
            ]
        }
    
    @staticmethod
    def get_product_development_workflow_template() -> Dict[str, Any]:
        """Get product development workflow template with cross-agent collaboration"""
        return {
            "name": "Product Development Workflow",
            "description": "Develop new products with input from multiple specialized agents",
            "type": "product_development",
            "config": {
                "cofounder_agent": "cofounder",
                "strategy_agent": "strategy",
                "marketing_agent": "marketing",
                "finance_agent": "finance",
                "legal_agent": "legal",
                "manager_agent": "manager"
            },
            "steps": [
                {
                    "name": "market_opportunity",
                    "agent": "strategy",
                    "description": "Identify market opportunity and product concept",
                    "inputs": ["market_trends", "customer_needs", "competitive_landscape"],
                    "outputs": ["product_concept", "market_opportunity"]
                },
                {
                    "name": "concept_validation",
                    "collaborative_decision": {
                        "agents": ["marketing", "finance", "strategy"],
                        "description": "Validate product concept from multiple perspectives",
                        "inputs": ["product_concept", "market_opportunity"],
                        "outputs": ["concept_validation", "refinement_suggestions"]
                    }
                },
                {
                    "name": "financial_feasibility",
                    "agent": "finance",
                    "description": "Assess financial feasibility and ROI projections",
                    "inputs": ["product_concept", "development_costs", "market_opportunity"],
                    "outputs": ["financial_assessment", "roi_projection"]
                },
                {
                    "name": "legal_requirements",
                    "agent": "legal",
                    "description": "Identify legal requirements and IP considerations",
                    "inputs": ["product_concept", "regulatory_environment"],
                    "outputs": ["legal_requirements", "ip_strategy"]
                },
                {
                    "name": "marketing_plan",
                    "agent": "marketing",
                    "description": "Develop marketing plan for product launch",
                    "inputs": ["product_concept", "market_opportunity", "target_audience"],
                    "outputs": ["marketing_plan", "positioning_strategy"]
                },
                {
                    "name": "product_roadmap",
                    "agent": "manager",
                    "description": "Create product development roadmap and timeline",
                    "inputs": ["product_concept", "financial_assessment", "legal_requirements"],
                    "outputs": ["product_roadmap", "development_timeline"]
                },
                {
                    "name": "resource_allocation",
                    "agent": "finance",
                    "description": "Allocate resources for product development",
                    "inputs": ["product_roadmap", "financial_assessment", "development_timeline"],
                    "outputs": ["resource_allocation", "budget_approval"]
                },
                {
                    "name": "executive_approval",
                    "agent": "cofounder",
                    "description": "Review and approve product development plan",
                    "inputs": ["product_roadmap", "financial_assessment", "marketing_plan", "legal_requirements"],
                    "outputs": ["executive_approval", "strategic_guidance"]
                },
                {
                    "name": "launch_planning",
                    "collaborative_decision": {
                        "agents": ["marketing", "finance", "manager"],
                        "description": "Coordinate product launch activities across functions",
                        "inputs": ["product_roadmap", "marketing_plan", "resource_allocation"],
                        "outputs": ["launch_plan", "success_metrics"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_compliance_review_workflow_template() -> Dict[str, Any]:
        """Get compliance review workflow template with legal and finance collaboration"""
        return {
            "name": "Compliance Review Workflow",
            "description": "Review business operations for regulatory compliance with legal and finance collaboration",
            "type": "compliance_review",
            "config": {
                "legal_agent": "legal",
                "finance_agent": "finance",
                "manager_agent": "manager",
                "cofounder_agent": "cofounder"
            },
            "steps": [
                {
                    "name": "compliance_scope",
                    "agent": "manager",
                    "description": "Define scope of compliance review",
                    "inputs": ["business_operations", "regulatory_environment", "review_objectives"],
                    "outputs": ["compliance_scope", "priority_areas"]
                },
                {
                    "name": "legal_analysis",
                    "agent": "legal",
                    "description": "Analyze legal requirements and regulations",
                    "inputs": ["compliance_scope", "regulatory_documents", "industry_standards"],
                    "outputs": ["legal_analysis", "compliance_requirements"]
                },
                {
                    "name": "financial_controls",
                    "agent": "finance",
                    "description": "Review financial controls and reporting procedures",
                    "inputs": ["compliance_scope", "financial_processes", "reporting_requirements"],
                    "outputs": ["financial_controls_assessment", "reporting_gaps"]
                },
                {
                    "name": "gap_analysis",
                    "collaborative_decision": {
                        "agents": ["legal", "finance"],
                        "description": "Identify compliance gaps across legal and financial domains",
                        "inputs": ["legal_analysis", "financial_controls_assessment"],
                        "outputs": ["compliance_gaps", "risk_assessment"]
                    }
                },
                {
                    "name": "remediation_planning",
                    "agent": "manager",
                    "description": "Develop remediation plan for compliance gaps",
                    "inputs": ["compliance_gaps", "risk_assessment", "resource_constraints"],
                    "outputs": ["remediation_plan", "implementation_timeline"]
                },
                {
                    "name": "financial_impact",
                    "agent": "finance",
                    "description": "Assess financial impact of compliance remediation",
                    "inputs": ["remediation_plan", "current_financials"],
                    "outputs": ["financial_impact_assessment", "budget_requirements"]
                },
                {
                    "name": "executive_review",
                    "agent": "cofounder",
                    "description": "Review compliance findings and remediation plan",
                    "inputs": ["compliance_gaps", "remediation_plan", "financial_impact_assessment"],
                    "outputs": ["executive_approval", "strategic_priorities"]
                },
                {
                    "name": "implementation_oversight",
                    "agent": "manager",
                    "description": "Oversee implementation of compliance remediation",
                    "inputs": ["remediation_plan", "executive_approval", "implementation_timeline"],
                    "outputs": ["implementation_status", "progress_report"]
                },
                {
                    "name": "compliance_certification",
                    "collaborative_decision": {
                        "agents": ["legal", "finance", "manager"],
                        "description": "Certify compliance status after remediation",
                        "inputs": ["implementation_status", "compliance_requirements"],
                        "outputs": ["compliance_certification", "ongoing_monitoring_plan"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Any]]:
        """Get all workflow templates"""
        return {
            "content_creation": WorkflowTemplates.get_content_workflow_template(),
            "client_management": WorkflowTemplates.get_client_workflow_template(),
            "financial": WorkflowTemplates.get_financial_workflow_template(),
            "research": WorkflowTemplates.get_research_workflow_template(),
            "marketing_campaign": WorkflowTemplates.get_marketing_campaign_workflow_template(),
            "strategic_planning": WorkflowTemplates.get_strategic_planning_workflow_template(),
            "product_development": WorkflowTemplates.get_product_development_workflow_template(),
            "compliance_review": WorkflowTemplates.get_compliance_review_workflow_template()
        }
    
    @staticmethod
    def get_template_by_type(workflow_type: str) -> Dict[str, Any]:
        """Get workflow template by type"""
        templates = WorkflowTemplates.get_all_templates()
        if workflow_type not in templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        return templates[workflow_type]
    
    @staticmethod
    def get_cross_functional_templates() -> Dict[str, Dict[str, Any]]:
        """Get all cross-functional workflow templates that involve multiple agents"""
        return {
            "marketing_campaign": WorkflowTemplates.get_marketing_campaign_workflow_template(),
            "strategic_planning": WorkflowTemplates.get_strategic_planning_workflow_template(),
            "product_development": WorkflowTemplates.get_product_development_workflow_template(),
            "compliance_review": WorkflowTemplates.get_compliance_review_workflow_template()
        }
    
    @staticmethod
    def get_collaborative_decision_patterns() -> Dict[str, Dict[str, Any]]:
        """Get reusable collaborative decision patterns for multi-agent workflows"""
        return {
            "marketing_finance_alignment": {
                "agents": ["marketing", "finance"],
                "description": "Align marketing initiatives with financial constraints",
                "inputs": ["marketing_proposal", "budget_constraints"],
                "outputs": ["aligned_plan", "resource_allocation"]
            },
            "legal_compliance_review": {
                "agents": ["legal", "marketing", "finance"],
                "description": "Review initiatives for legal compliance",
                "inputs": ["proposed_action", "regulatory_requirements"],
                "outputs": ["compliance_assessment", "required_changes"]
            },
            "strategic_impact_analysis": {
                "agents": ["strategy", "finance", "marketing", "legal"],
                "description": "Analyze cross-functional impacts of strategic decisions",
                "inputs": ["strategic_decision", "current_state"],
                "outputs": ["impact_analysis", "risk_assessment"]
            },
            "executive_decision": {
                "agents": ["cofounder", "manager"],
                "description": "Make executive-level decisions with management input",
                "inputs": ["decision_context", "options", "recommendations"],
                "outputs": ["executive_decision", "implementation_guidance"]
            }
        }