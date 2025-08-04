"""
Report Generator - Creates comprehensive reports from agent outputs
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
import weasyprint
import markdown

from services.template_manager import template_manager
from .enhanced_output_manager import output_manager

class ReportGenerator:
    """Creates comprehensive reports from agent outputs"""
    
    def __init__(self):
        self.report_dir = Path("data/reports")
        self.report_dir.mkdir(exist_ok=True, parents=True)
        
        # Report templates
        self.report_templates = {
            "executive": self._generate_executive_report,
            "marketing": self._generate_marketing_report,
            "financial": self._generate_financial_report,
            "research": self._generate_research_report,
            "comprehensive": self._generate_comprehensive_report
        }
    
    async def generate_report(self, report_type: str, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report based on type"""
        if report_type not in self.report_templates:
            raise ValueError(f"Unknown report type: {report_type}")
            
        generator_func = self.report_templates[report_type]
        report = await generator_func(outputs)
        
        # Save report
        report_id = f"{report_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report_path = self.report_dir / f"{report_id}.json"
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Generated {report_type} report: {report_path}")
        
        return {
            "id": report_id,
            "type": report_type,
            "path": str(report_path),
            "data": report
        }
    
    async def generate_pdf_report(self, report_data: Dict[str, Any], report_type: str) -> Path:
        """Generate PDF report from data"""
        # Determine template
        template_name = f"reports/{report_type}.j2"
        
        # Render template
        try:
            rendered = template_manager.render_file_template(template_name, report_data)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            # Fallback to basic HTML
            rendered = self._generate_fallback_html(report_data, report_type)
        
        # Generate PDF
        report_id = f"{report_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        pdf_path = self.report_dir / f"{report_id}.pdf"
        
        try:
            # Convert HTML to PDF
            weasyprint.HTML(string=rendered).write_pdf(pdf_path)
            
            logger.info(f"Generated PDF report: {pdf_path}")
            
            return pdf_path
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise
    
    def _generate_fallback_html(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Generate fallback HTML for a report"""
        # Convert report data to HTML
        html_parts = ["<html><head>"]
        html_parts.append(f"<title>{report_type.title()} Report</title>")
        html_parts.append("""
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .section { margin-bottom: 30px; }
        </style>
        """)
        html_parts.append("</head><body>")
        
        # Add title
        html_parts.append(f"<h1>{report_type.title()} Report</h1>")
        html_parts.append(f"<p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        # Add sections
        for key, value in report_data.items():
            if key in ["id", "type", "generated_at"]:
                continue
                
            html_parts.append(f"<div class='section'>")
            html_parts.append(f"<h2>{key.replace('_', ' ').title()}</h2>")
            
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    html_parts.append(f"<h3>{subkey.replace('_', ' ').title()}</h3>")
                    html_parts.append(self._value_to_html(subvalue))
            else:
                html_parts.append(self._value_to_html(value))
                
            html_parts.append("</div>")
        
        html_parts.append("</body></html>")
        return "".join(html_parts)
    
    def _value_to_html(self, value: Any) -> str:
        """Convert a value to HTML"""
        if isinstance(value, str):
            # Try to convert markdown to HTML
            try:
                return markdown.markdown(value)
            except:
                return f"<p>{value}</p>"
        elif isinstance(value, list):
            if not value:
                return "<p>No items</p>"
                
            if isinstance(value[0], dict):
                # Table
                html = "<table>"
                
                # Headers
                html += "<tr>"
                for key in value[0].keys():
                    html += f"<th>{key.replace('_', ' ').title()}</th>"
                html += "</tr>"
                
                # Rows
                for item in value:
                    html += "<tr>"
                    for key, val in item.items():
                        html += f"<td>{val}</td>"
                    html += "</tr>"
                
                html += "</table>"
                return html
            else:
                # List
                html = "<ul>"
                for item in value:
                    html += f"<li>{item}</li>"
                html += "</ul>"
                return html
        elif isinstance(value, dict):
            # Definition list
            html = "<dl>"
            for key, val in value.items():
                html += f"<dt>{key.replace('_', ' ').title()}</dt>"
                html += f"<dd>{val}</dd>"
            html += "</dl>"
            return html
        else:
            return f"<p>{value}</p>"
    
    async def _generate_executive_report(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary report"""
        report = {
            "title": "Executive Summary Report",
            "generated_at": datetime.now().isoformat(),
            "summary": "This report provides a high-level overview of key business insights and recommendations.",
            "key_metrics": {},
            "strategic_insights": [],
            "recommendations": [],
            "next_steps": []
        }
        
        # Extract data from outputs
        for output_id, output_data in outputs.items():
            if isinstance(output_data, dict):
                # Extract key metrics
                if "metrics" in output_data:
                    report["key_metrics"].update(output_data["metrics"])
                
                # Extract insights
                if "insights" in output_data:
                    if isinstance(output_data["insights"], list):
                        report["strategic_insights"].extend(output_data["insights"])
                    elif isinstance(output_data["insights"], str):
                        report["strategic_insights"].append(output_data["insights"])
                
                # Extract recommendations
                if "recommendations" in output_data:
                    if isinstance(output_data["recommendations"], list):
                        report["recommendations"].extend(output_data["recommendations"])
                    elif isinstance(output_data["recommendations"], str):
                        report["recommendations"].append(output_data["recommendations"])
                
                # Extract next steps
                if "next_steps" in output_data:
                    if isinstance(output_data["next_steps"], list):
                        report["next_steps"].extend(output_data["next_steps"])
                    elif isinstance(output_data["next_steps"], str):
                        report["next_steps"].append(output_data["next_steps"])
        
        # Deduplicate lists
        report["strategic_insights"] = list(set(report["strategic_insights"]))
        report["recommendations"] = list(set(report["recommendations"]))
        report["next_steps"] = list(set(report["next_steps"]))
        
        return report
    
    async def _generate_marketing_report(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate marketing report"""
        report = {
            "title": "Marketing Strategy Report",
            "generated_at": datetime.now().isoformat(),
            "summary": "This report provides a comprehensive marketing strategy and content plan.",
            "target_audience": {},
            "content_strategy": {},
            "channel_recommendations": [],
            "content_calendar": [],
            "performance_metrics": {}
        }
        
        # Extract data from outputs
        for output_id, output_data in outputs.items():
            if isinstance(output_data, dict):
                # Extract target audience
                if "target_audience" in output_data:
                    report["target_audience"] = output_data["target_audience"]
                
                # Extract content strategy
                if "content_strategy" in output_data:
                    report["content_strategy"] = output_data["content_strategy"]
                
                # Extract channel recommendations
                if "channel_recommendations" in output_data:
                    if isinstance(output_data["channel_recommendations"], list):
                        report["channel_recommendations"].extend(output_data["channel_recommendations"])
                    elif isinstance(output_data["channel_recommendations"], dict):
                        for channel, recommendation in output_data["channel_recommendations"].items():
                            report["channel_recommendations"].append({
                                "channel": channel,
                                "recommendation": recommendation
                            })
                
                # Extract content calendar
                if "content_calendar" in output_data:
                    if isinstance(output_data["content_calendar"], list):
                        report["content_calendar"].extend(output_data["content_calendar"])
                
                # Extract performance metrics
                if "performance_metrics" in output_data:
                    report["performance_metrics"].update(output_data["performance_metrics"])
        
        return report
    
    async def _generate_financial_report(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial report"""
        report = {
            "title": "Financial Analysis Report",
            "generated_at": datetime.now().isoformat(),
            "summary": "This report provides a comprehensive financial analysis and projections.",
            "financial_summary": {},
            "revenue_projections": {},
            "expense_analysis": {},
            "roi_analysis": {},
            "recommendations": []
        }
        
        # Extract data from outputs
        for output_id, output_data in outputs.items():
            if isinstance(output_data, dict):
                # Extract financial summary
                if "financial_summary" in output_data:
                    report["financial_summary"] = output_data["financial_summary"]
                
                # Extract revenue projections
                if "revenue_projections" in output_data:
                    report["revenue_projections"] = output_data["revenue_projections"]
                
                # Extract expense analysis
                if "expense_analysis" in output_data:
                    report["expense_analysis"] = output_data["expense_analysis"]
                
                # Extract ROI analysis
                if "roi_analysis" in output_data:
                    report["roi_analysis"] = output_data["roi_analysis"]
                
                # Extract recommendations
                if "recommendations" in output_data:
                    if isinstance(output_data["recommendations"], list):
                        report["recommendations"].extend(output_data["recommendations"])
                    elif isinstance(output_data["recommendations"], str):
                        report["recommendations"].append(output_data["recommendations"])
        
        # Deduplicate recommendations
        report["recommendations"] = list(set(report["recommendations"]))
        
        return report
    
    async def _generate_research_report(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research report"""
        report = {
            "title": "Market Research Report",
            "generated_at": datetime.now().isoformat(),
            "summary": "This report provides comprehensive market research and competitive analysis.",
            "market_overview": "",
            "target_audience": {},
            "competitor_analysis": [],
            "swot_analysis": {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": []
            },
            "trends": [],
            "recommendations": []
        }
        
        # Extract data from outputs
        for output_id, output_data in outputs.items():
            if isinstance(output_data, dict):
                # Extract market overview
                if "market_overview" in output_data:
                    report["market_overview"] = output_data["market_overview"]
                
                # Extract target audience
                if "target_audience" in output_data:
                    report["target_audience"] = output_data["target_audience"]
                
                # Extract competitor analysis
                if "competitor_analysis" in output_data:
                    if isinstance(output_data["competitor_analysis"], list):
                        report["competitor_analysis"].extend(output_data["competitor_analysis"])
                
                # Extract SWOT analysis
                if "swot_analysis" in output_data:
                    swot = output_data["swot_analysis"]
                    if isinstance(swot, dict):
                        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
                            if key in swot and isinstance(swot[key], list):
                                report["swot_analysis"][key].extend(swot[key])
                
                # Extract trends
                if "trends" in output_data:
                    if isinstance(output_data["trends"], list):
                        report["trends"].extend(output_data["trends"])
                
                # Extract recommendations
                if "recommendations" in output_data:
                    if isinstance(output_data["recommendations"], list):
                        report["recommendations"].extend(output_data["recommendations"])
                    elif isinstance(output_data["recommendations"], str):
                        report["recommendations"].append(output_data["recommendations"])
        
        # Deduplicate lists
        report["trends"] = list(set(report["trends"]))
        report["recommendations"] = list(set(report["recommendations"]))
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            report["swot_analysis"][key] = list(set(report["swot_analysis"][key]))
        
        return report
    
    async def _generate_comprehensive_report(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report combining all report types"""
        # Generate individual reports
        executive_report = await self._generate_executive_report(outputs)
        marketing_report = await self._generate_marketing_report(outputs)
        financial_report = await self._generate_financial_report(outputs)
        research_report = await self._generate_research_report(outputs)
        
        # Combine into comprehensive report
        report = {
            "title": "Comprehensive Business Report",
            "generated_at": datetime.now().isoformat(),
            "summary": "This report provides a comprehensive analysis of all business aspects.",
            "executive_summary": executive_report,
            "market_research": research_report,
            "marketing_strategy": marketing_report,
            "financial_analysis": financial_report
        }
        
        return report
    
    def _create_timestamp(self) -> str:
        """Create a formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports"""
        reports = []
        
        # Find all report files
        report_files = list(self.report_dir.glob("*.json"))
        
        for report_path in report_files:
            try:
                # Load report
                with open(report_path, "r") as f:
                    report_data = json.load(f)
                
                # Extract report info
                report_id = report_path.stem
                report_type = report_id.split("_")[0]
                
                reports.append({
                    "id": report_id,
                    "type": report_type,
                    "title": report_data.get("title", report_type.title()),
                    "generated_at": report_data.get("generated_at", ""),
                    "path": str(report_path),
                    "has_pdf": (self.report_dir / f"{report_id}.pdf").exists()
                })
            except Exception as e:
                logger.error(f"Failed to process report file {report_path}: {e}")
        
        # Sort by generation date (newest first)
        reports.sort(key=lambda x: x["generated_at"], reverse=True)
        
        return reports
    
    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get a report by ID"""
        report_path = self.report_dir / f"{report_id}.json"
        
        if not report_path.exists():
            raise ValueError(f"Report not found: {report_id}")
            
        # Load report
        with open(report_path, "r") as f:
            report_data = json.load(f)
            
        # Check if PDF exists
        pdf_path = self.report_dir / f"{report_id}.pdf"
        has_pdf = pdf_path.exists()
        
        return {
            "id": report_id,
            "data": report_data,
            "has_pdf": has_pdf,
            "pdf_path": str(pdf_path) if has_pdf else None
        }
    
    async def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        report_path = self.report_dir / f"{report_id}.json"
        
        if not report_path.exists():
            return False
            
        # Delete JSON file
        report_path.unlink()
        
        # Delete PDF if exists
        pdf_path = self.report_dir / f"{report_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
            
        logger.info(f"Deleted report: {report_id}")
        return True

# Global instance
report_generator = ReportGenerator()