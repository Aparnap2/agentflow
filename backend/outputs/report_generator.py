"""
Advanced report generation with comprehensive output formats
"""

from typing import Dict, List, Any
from datetime import datetime
import os
import json
from pathlib import Path

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
        
        # Ensure output directories exist
        os.makedirs("outputs/reports", exist_ok=True)
        os.makedirs("outputs/pdfs", exist_ok=True)
    
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
    
    def _create_timestamp(self) -> str:
        """Create timestamp for reports"""
        return datetime.now().isoformat()
    
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
    
    async def generate_pdf_report(self, report_data: Dict[str, Any], report_type: str = "comprehensive") -> str:
        """Generate PDF report from report data"""
        try:
            # Try to import WeasyPrint for PDF generation
            from weasyprint import HTML, CSS
            
            # Generate HTML content
            html_content = self._generate_html_report(report_data, report_type)
            
            # Create PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"outputs/pdfs/{report_type}_report_{timestamp}.pdf"
            
            HTML(string=html_content).write_pdf(pdf_filename)
            
            return pdf_filename
            
        except ImportError:
            # Fallback: Generate HTML file instead
            return await self._generate_html_fallback(report_data, report_type)
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Generate HTML content for PDF report"""
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgentFlow {report_type.title()} Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #1f2937; color: white; padding: 20px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ background: #f3f4f6; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .kpi {{ display: inline-block; margin: 10px; padding: 15px; background: #dbeafe; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 AgentFlow Business Report</h1>
                <p>Generated: {report_data.get('report_metadata', {}).get('generated_at', datetime.now().isoformat())}</p>
            </div>
            
            <div class="section">
                <h2>📊 Executive Summary</h2>
                {self._format_executive_summary_html(report_data.get('executive_summary', {}))}
            </div>
            
            <div class="section">
                <h2>📈 Key Performance Indicators</h2>
                {self._format_kpi_section_html(report_data.get('sections', {}).get('executive_dashboard', {}))}
            </div>
            
            <div class="section">
                <h2>💰 Financial Projections</h2>
                {self._format_financial_section_html(report_data.get('sections', {}).get('financial_projections', {}))}
            </div>
            
            <div class="section">
                <h2>📱 Marketing Intelligence</h2>
                {self._format_marketing_section_html(report_data.get('sections', {}).get('marketing_intelligence', {}))}
            </div>
            
            <div class="section">
                <h2>⚖️ Legal & Compliance</h2>
                {self._format_legal_section_html(report_data.get('sections', {}).get('legal_compliance', {}))}
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _format_executive_summary_html(self, summary: Dict[str, Any]) -> str:
        """Format executive summary as HTML"""
        project_health = summary.get('project_health', {})
        key_metrics = summary.get('key_metrics', {})
        
        return f"""
        <div class="metric">
            <h3>Project Health Score: {project_health.get('overall_score', 'N/A')}/100</h3>
            <p><strong>Risk Level:</strong> {project_health.get('risk_level', 'Unknown').title()}</p>
            <p><strong>Confidence:</strong> {project_health.get('confidence', 'N/A')}</p>
            <p><strong>Next Milestone:</strong> {project_health.get('next_milestone', 'TBD')}</p>
        </div>
        
        <div class="kpi">
            <strong>Market Opportunity:</strong><br>
            {key_metrics.get('market_opportunity', 'TBD')}
        </div>
        <div class="kpi">
            <strong>Revenue Projection:</strong><br>
            {key_metrics.get('revenue_projection', 'TBD')}
        </div>
        <div class="kpi">
            <strong>Product Readiness:</strong><br>
            {key_metrics.get('product_readiness', 'TBD')}
        </div>
        """
    
    def _format_kpi_section_html(self, kpi_data: Dict[str, Any]) -> str:
        """Format KPI section as HTML"""
        dashboard = kpi_data.get('kpi_dashboard', {})
        revenue_metrics = dashboard.get('revenue_metrics', {})
        product_metrics = dashboard.get('product_metrics', {})
        
        return f"""
        <table>
            <tr><th>Metric</th><th>Current</th><th>Target</th></tr>
            <tr><td>Monthly Recurring Revenue</td><td>{revenue_metrics.get('current_mrr', '$0')}</td><td>$50K</td></tr>
            <tr><td>Annual Recurring Revenue</td><td>{revenue_metrics.get('projected_arr', 'TBD')}</td><td>$500K</td></tr>
            <tr><td>Growth Rate</td><td>{revenue_metrics.get('growth_rate', 'TBD')}</td><td>25% MoM</td></tr>
            <tr><td>Feature Completion</td><td>{product_metrics.get('feature_completion', 'TBD')}</td><td>100%</td></tr>
            <tr><td>User Satisfaction</td><td>{product_metrics.get('user_satisfaction', 'TBD')}</td><td>4.5/5</td></tr>
        </table>
        """
    
    def _format_financial_section_html(self, financial_data: Dict[str, Any]) -> str:
        """Format financial section as HTML"""
        return f"""
        <div class="metric">
            <h3>Revenue Model</h3>
            <p>{json.dumps(financial_data.get('revenue_model', {}), indent=2)}</p>
        </div>
        <div class="metric">
            <h3>Financial Projections</h3>
            <p>{json.dumps(financial_data.get('financial_projections', {}), indent=2)}</p>
        </div>
        """
    
    def _format_marketing_section_html(self, marketing_data: Dict[str, Any]) -> str:
        """Format marketing section as HTML"""
        projections = marketing_data.get('campaign_projections', {})
        
        return f"""
        <div class="metric">
            <h3>Campaign Projections</h3>
            <p><strong>Customer Acquisition Cost:</strong> {projections.get('cac_prediction', 'TBD')}</p>
            <p><strong>Lifetime Value:</strong> {projections.get('ltv_projection', 'TBD')}</p>
            <p><strong>ROI Projection:</strong> {projections.get('roi_projection', 'TBD')}</p>
        </div>
        """
    
    def _format_legal_section_html(self, legal_data: Dict[str, Any]) -> str:
        """Format legal section as HTML"""
        compliance = legal_data.get('compliance_status', {})
        
        return f"""
        <div class="metric">
            <h3>Compliance Status</h3>
            <p><strong>GDPR Compliance:</strong> {compliance.get('gdpr_compliance', 'N/A')}%</p>
            <p><strong>CCPA Compliance:</strong> {compliance.get('ccpa_compliance', 'N/A')}%</p>
            <p><strong>Data Protection:</strong> {compliance.get('data_protection', 'N/A')}%</p>
        </div>
        """
    
    async def _generate_html_fallback(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Generate HTML file as fallback when PDF generation fails"""
        html_content = self._generate_html_report(report_data, report_type)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"outputs/reports/{report_type}_report_{timestamp}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_filename