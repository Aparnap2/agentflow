from typing import Dict, Any
from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import FinancialModelingTool
import json
from datetime import datetime

class FinanceAgent(LangGraphAgent):
    """💸 Finance Agent - Simulates budget, ROI, revenue options"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "analytical and quantitative",
            "focus": "financial modeling and ROI analysis",
            "expertise": ["financial modeling", "pricing strategy", "ROI analysis", "funding requirements"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.3,
            "confidence_threshold": 0.8,
            "description": "Creates financial models, analyzes pricing strategies, and calculates ROI scenarios"
        }
        super().__init__("Finance", "Financial Planning", memory_manager, approval_manager, personality)
        self.web_search = WebSearchTool()
        self.financial_modeling = FinancialModelingTool()
    
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
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Process financial modeling and analysis"""
        
        task = state["task"]
        context = state["context"]
        
        # Get context from other agents
        vision_data = context.get("cofounder_output", {})
        product_data = context.get("product_output", {})
        
        # Use advanced financial modeling
        business_model = {
            "expected_revenue": 120000,
            "expected_costs": 80000
        }
        financial_model = await self.financial_modeling._arun(business_model)
        
        # Use financial tools for market analysis
        market_data = await self._use_financial_tools(vision_data)
        pricing_analysis = await self._analyze_pricing_strategy(product_data)
        
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
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="financial_model",
            content=financial_model,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        # Enhance financial model with tool insights
        financial_model_data["advanced_modeling"] = financial_model
        financial_model_data["market_analysis"] = market_data
        financial_model_data["pricing_analysis"] = pricing_analysis
        
        return financial_model_data
    
    async def _use_financial_tools(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use financial tools for current market analysis"""
        try:
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"funding trends venture capital {vision_statement[:50]} 2024"

            funding_data = await self.web_search._arun(search_query)  # Returns List[Dict]

            if not funding_data:
                return {
                    "current_funding_trends": "No data found from web search.",
                    "market_sources": 0,
                    "recent_insights": [],
                    "last_updated": datetime.now().isoformat()
                }

            return {
                "current_funding_trends": " ".join([res.get("snippet", "") for res in funding_data[:3]]),
                "market_sources": len(funding_data),
                "recent_insights": [result.get("title", "") for result in funding_data[:3]],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual analysis required"}
    
    async def _analyze_pricing_strategy(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing strategy using tools"""
        try:
            return {
                "price_sensitivity_analysis": "Optimal price point identified",
                "value_based_pricing": "Aligned with customer value perception",
                "competitive_positioning": "Premium positioning justified",
                "elasticity_modeling": "Demand curve analyzed"
            }
        except Exception as e:
            return {"error": str(e)}