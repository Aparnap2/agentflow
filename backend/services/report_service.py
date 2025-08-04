"""
Modular Report Service for Domain-Specific Outputs
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ReportService:
    def __init__(self, orchestrator, memory_manager):
        self.orchestrator = orchestrator
        self.memory = memory_manager
        self.domain_reports = {}
    
    async def generate_domain_reports(self) -> Dict[str, Any]:
        """Generate separate reports for each domain"""
        outputs = await self.orchestrator.get_outputs()
        
        domain_reports = {
            "marketing": await self._generate_marketing_report(outputs),
            "sales": await self._generate_sales_report(outputs),
            "finance": await self._generate_finance_report(outputs),
            "legal": await self._generate_legal_report(outputs),
            "product": await self._generate_product_report(outputs),
            "operations": await self._generate_operations_report(outputs)
        }
        
        # Add cross-references between reports
        domain_reports = self._add_cross_references(domain_reports)
        
        return domain_reports
    
    async def _generate_marketing_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate marketing-specific report"""
        marketing_data = self._extract_agent_data(outputs, "marketing")
        
        return {
            "title": "Marketing Strategy & Campaign Plan",
            "agent": "Emma Rodriguez",
            "sections": {
                "campaign_strategy": marketing_data.get("campaign_strategy", {}),
                "content_plan": marketing_data.get("content_plan", {}),
                "seo_strategy": marketing_data.get("seo_strategy", {}),
                "target_audience": marketing_data.get("target_audience", {})
            },
            "references": {
                "sales_data": "Referenced paying customers from Sales Report",
                "finance_budget": "Campaign budget from Finance Report"
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_sales_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate sales-specific report"""
        sales_data = self._extract_agent_data(outputs, "sales")
        
        return {
            "title": "Sales Strategy & Revenue Forecast",
            "agent": "Lisa Wang",
            "sections": {
                "sales_strategy": sales_data.get("sales_strategy", {}),
                "revenue_forecast": sales_data.get("revenue_forecast", {}),
                "customer_segments": sales_data.get("customer_segments", {}),
                "pipeline_analysis": sales_data.get("pipeline_analysis", {})
            },
            "shared_data": {
                "paying_customers": sales_data.get("paying_customers", []),
                "revenue_contributors": sales_data.get("top_customers", [])
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_finance_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate finance-specific report"""
        finance_data = self._extract_agent_data(outputs, "finance")
        
        return {
            "title": "Financial Planning & Projections",
            "agent": "David Park",
            "sections": {
                "financial_projections": finance_data.get("financial_projections", {}),
                "budget_allocation": finance_data.get("budget_allocation", {}),
                "roi_analysis": finance_data.get("roi_analysis", {}),
                "funding_requirements": finance_data.get("funding_requirements", {})
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_legal_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate legal-specific report"""
        legal_data = self._extract_agent_data(outputs, "legal")
        
        return {
            "title": "Legal Compliance & Risk Assessment",
            "agent": "Michael Thompson",
            "sections": {
                "compliance_checklist": legal_data.get("compliance_requirements", {}),
                "risk_assessment": legal_data.get("risk_assessment", {}),
                "legal_documents": legal_data.get("legal_documents", {}),
                "regulatory_requirements": legal_data.get("regulatory_requirements", {})
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_product_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate product-specific report"""
        product_data = self._extract_agent_data(outputs, "product")
        
        return {
            "title": "Product Strategy & Development Plan",
            "agent": "Jordan Martinez",
            "sections": {
                "product_strategy": product_data.get("product_strategy", {}),
                "user_personas": product_data.get("user_personas", {}),
                "feature_roadmap": product_data.get("feature_roadmap", {}),
                "mvp_definition": product_data.get("mvp_definition", {})
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_operations_report(self, outputs: Dict) -> Dict[str, Any]:
        """Generate operations-specific report"""
        operations_data = self._extract_agent_data(outputs, "operations")
        
        return {
            "title": "Operations Plan & Workflow Optimization",
            "agent": "Ryan Foster",
            "sections": {
                "operations_plan": operations_data.get("operations_plan", {}),
                "workflow_optimization": operations_data.get("workflow_optimization", {}),
                "resource_allocation": operations_data.get("resource_allocation", {}),
                "process_improvements": operations_data.get("process_improvements", {})
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _extract_agent_data(self, outputs: Dict, agent_type: str) -> Dict:
        """Extract data for specific agent type"""
        for filename, data in outputs.items():
            if data.get('agent', '').lower() == agent_type:
                return data.get('data', {})
        return {}
    
    def _add_cross_references(self, reports: Dict) -> Dict:
        """Add cross-references between reports"""
        # Marketing references Sales data
        if "paying_customers" in reports.get("sales", {}).get("shared_data", {}):
            reports["marketing"]["references"]["sales_customers"] = "Using paying customers from Sales Report"
        
        # Finance references all other reports for budget allocation
        reports["finance"]["references"] = {
            "marketing_budget": "Campaign budget allocation",
            "sales_forecast": "Revenue projections from Sales",
            "operations_costs": "Operational expenses from Operations"
        }
        
        return reports
    
    async def get_report(self, domain: str) -> Optional[Dict]:
        """Get specific domain report"""
        reports = await self.generate_domain_reports()
        return reports.get(domain)
    
    async def get_all_reports(self) -> Dict[str, Any]:
        """Get all domain reports"""
        return await self.generate_domain_reports()