from typing import Dict, Any
from agents.base_agent import BaseAgent
import json
from datetime import datetime

class FinanceAgent(BaseAgent):
    """💸 Finance Agent - Simulates budget, ROI, revenue options"""
    
    def __init__(self):
        personality = {
            "tone": "analytical",
            "depth": "quantitative",
            "confidence_threshold": 0.8,
            "retry_limit": 2
        }
        super().__init__("Finance", "Financial Planning", personality)
    
    def get_system_prompt(self) -> str:
        return """You are the Finance agent in a virtual AI startup team. Your role is to:

1. Create financial models and projections
2. Analyze pricing strategies and revenue models
3. Calculate ROI scenarios and break-even analysis
4. Assess funding requirements and cash flow

You are analytical and quantitative. Focus on realistic assumptions, multiple scenarios, and clear financial metrics.

Structure your output as:
- Financial Model (revenue, costs, projections)
- Pricing Strategy (models, tiers, competitive analysis)
- ROI Analysis (scenarios, break-even, sensitivity)
- Funding Requirements (startup costs, runway, milestones)"""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process financial modeling and analysis"""
        
        # Get context from other agents
        vision_context = await self.get_context("cofounder_output")
        product_context = await self.get_context("product_output")
        
        if not vision_context or not product_context:
            return {
                "error": "Missing required context from other agents",
                "confidence": 0.3,
                "agent": self.name
            }
        
        vision_data = vision_context[0]["content"]
        product_data = product_context[0]["content"]
        
        # Use finance API tool for market data
        finance_api_tool = self.tools.get_tool("api_finance_call")
        web_fetch_tool = self.tools.get_tool("web_fetch")
        
        # Create financial analysis
        financial_model = {
            "revenue_model": {
                "primary_model": "SaaS Subscription",
                "pricing_tiers": [
                    {
                        "tier": "Starter",
                        "price": 29,
                        "billing": "monthly",
                        "features": ["Basic features", "Email support"],
                        "target_segment": "Individual users"
                    },
                    {
                        "tier": "Professional", 
                        "price": 99,
                        "billing": "monthly",
                        "features": ["Advanced features", "Priority support", "Integrations"],
                        "target_segment": "Small businesses"
                    },
                    {
                        "tier": "Enterprise",
                        "price": 299,
                        "billing": "monthly", 
                        "features": ["All features", "Custom integrations", "Dedicated support"],
                        "target_segment": "Large organizations"
                    }
                ],
                "revenue_streams": [
                    "Subscription fees (80%)",
                    "Setup/onboarding fees (15%)",
                    "Professional services (5%)"
                ]
            },
            "financial_projections": {
                "year_1": {
                    "revenue": 120000,
                    "costs": 180000,
                    "net_income": -60000,
                    "customers": 150
                },
                "year_2": {
                    "revenue": 480000,
                    "costs": 320000,
                    "net_income": 160000,
                    "customers": 600
                },
                "year_3": {
                    "revenue": 1200000,
                    "costs": 720000,
                    "net_income": 480000,
                    "customers": 1500
                }
            },
            "cost_structure": {
                "development": {
                    "percentage": 40,
                    "annual_cost": 120000,
                    "description": "Engineering and product development"
                },
                "marketing": {
                    "percentage": 25,
                    "annual_cost": 75000,
                    "description": "Customer acquisition and marketing"
                },
                "operations": {
                    "percentage": 20,
                    "annual_cost": 60000,
                    "description": "Infrastructure and operations"
                },
                "sales": {
                    "percentage": 15,
                    "annual_cost": 45000,
                    "description": "Sales team and processes"
                }
            },
            "roi_analysis": {
                "break_even_point": "Month 18",
                "customer_acquisition_cost": 150,
                "customer_lifetime_value": 2400,
                "ltv_cac_ratio": 16,
                "payback_period": "6 months",
                "scenarios": {
                    "conservative": {"revenue_growth": "15% monthly", "churn_rate": "8%"},
                    "realistic": {"revenue_growth": "25% monthly", "churn_rate": "5%"},
                    "optimistic": {"revenue_growth": "40% monthly", "churn_rate": "3%"}
                }
            },
            "funding_requirements": {
                "seed_funding": 250000,
                "series_a": 1500000,
                "use_of_funds": {
                    "product_development": "40%",
                    "marketing_sales": "35%",
                    "operations": "15%",
                    "working_capital": "10%"
                },
                "runway": "18 months with seed funding",
                "milestones": [
                    "Product-market fit validation",
                    "100 paying customers",
                    "$50K MRR",
                    "Series A readiness"
                ]
            }
        }
        
        confidence = 0.82
        
        result = {
            "output": financial_model,
            "confidence": confidence,
            "summary": f"Created financial model with {len(financial_model['revenue_model']['pricing_tiers'])} pricing tiers and 3-year projections",
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store financial data for other agents
        finance_text = f"Pricing: {json.dumps(financial_model['revenue_model']['pricing_tiers'])} Projections: {json.dumps(financial_model['financial_projections'])}"
        await self.vector_memory.store_document(
            text=finance_text,
            metadata={"type": "financial_model", "timestamp": result["timestamp"]},
            agent=self.name
        )
        
        return result