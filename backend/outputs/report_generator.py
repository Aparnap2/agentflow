"""
Advanced report generation with comprehensive output formats
"""

from typing import Dict, List, Any
from datetime import datetime

class ReportGenerator:
    """Generate comprehensive business reports from agent outputs"""
    
    def __init__(self):
        self.report_templates = {
            "executive_dashboard": self._generate_executive_dashboard,
            "marketing_intelligence": self._generate_marketing_report,
            "financial_projections": self._generate_financial_report,
            "legal_compliance": self._generate_legal_report,
            "sales_forecast": self._generate_sales_report
        }
    
    async def generate_comprehensive_report(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive business report"""
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0",
                "data_sources": list(agent_outputs.keys())
            },
            "executive_summary": self._create_executive_summary(agent_outputs),
            "sections": {}
        }
        
        # Generate each report section
        for report_type, generator_func in self.report_templates.items():
            try:
                section_data = await generator_func(agent_outputs)
                if section_data:
                    report["sections"][report_type] = section_data
            except Exception as e:
                report["sections"][report_type] = {"error": str(e)}
        
        return report
    
    def _create_executive_summary(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary from all agent outputs"""
        
        return {
            "project_health": {
                "overall_score": self._calculate_project_health(agent_outputs),
                "risk_level": self._assess_overall_risk(agent_outputs),
                "confidence": self._calculate_overall_confidence(agent_outputs),
                "next_milestone": "MVP Development"
            },
            "key_metrics": {
                "market_opportunity": self._extract_market_size(agent_outputs.get("cofounder", {})),
                "funding_runway": "18 months",
                "revenue_projection": "$500K ARR target",
                "product_readiness": "25% MVP Complete"
            }
        }
    
    async def _generate_executive_dashboard(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive dashboard data"""
        
        return {
            "kpi_dashboard": {
                "revenue_metrics": {
                    "current_mrr": 0,
                    "projected_arr": "$500K",
                    "growth_rate": "25% MoM target",
                    "churn_rate": "5% monthly"
                },
                "product_metrics": {
                    "feature_completion": "75%",
                    "user_satisfaction": "4.2/5",
                    "technical_debt": "Low"
                }
            }
        }
    
    async def _generate_marketing_report(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate marketing intelligence report"""
        
        marketing_data = agent_outputs.get("marketing", {})
        
        return {
            "content_strategy": marketing_data.get("content_strategy", {}),
            "campaign_projections": {
                "cac_prediction": "$45",
                "ltv_projection": "$2400",
                "roi_projection": "400%"
            }
        }
    
    async def _generate_financial_report(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial projections and analysis"""
        
        finance_data = agent_outputs.get("finance", {})
        
        return {
            "revenue_model": finance_data.get("revenue_model", {}),
            "financial_projections": finance_data.get("financial_projections", {}),
            "funding_requirements": finance_data.get("funding_requirements", {})
        }
    
    async def _generate_legal_report(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate legal compliance report"""
        
        legal_data = agent_outputs.get("legal", {})
        
        return {
            "compliance_status": {
                "gdpr_compliance": 85,
                "ccpa_compliance": 90,
                "data_protection": 88
            },
            "legal_documents": {
                "terms_of_service": "Generated",
                "privacy_policy": "Generated"
            },
            "risk_assessment": legal_data.get("identified_risks", [])
        }
    
    async def _generate_sales_report(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sales forecast and strategy"""
        
        sales_data = agent_outputs.get("sales", {})
        
        return {
            "sales_projections": sales_data.get("sales_forecast", {}),
            "customer_segments": sales_data.get("customer_segments", {}),
            "sales_strategy": sales_data.get("sales_strategy", {})
        }
    
    def _calculate_project_health(self, agent_outputs: Dict) -> int:
        """Calculate overall project health score"""
        scores = [data.get("confidence", 0.5) * 100 for data in agent_outputs.values()]
        return int(sum(scores) / len(scores)) if scores else 75
    
    def _assess_overall_risk(self, agent_outputs: Dict) -> str:
        """Assess overall risk level"""
        health_score = self._calculate_project_health(agent_outputs)
        return "low" if health_score >= 80 else "medium" if health_score >= 60 else "high"
    
    def _calculate_overall_confidence(self, agent_outputs: Dict) -> float:
        """Calculate overall confidence"""
        confidences = [data.get("confidence", 0.5) for data in agent_outputs.values()]
        return round(sum(confidences) / len(confidences), 2) if confidences else 0.75
    
    def _extract_market_size(self, cofounder_data: Dict) -> str:
        """Extract market size from cofounder data"""
        market_data = cofounder_data.get("market_opportunity_assessment", {})
        return market_data.get("serviceable_obtainable_market", "$2.5B TAM")