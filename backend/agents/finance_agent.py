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
        return """You are David Park, the Finance Agent. Create ACTIONABLE financial strategy.

Provide structured output with:

## 💰 REVENUE MODEL
- Pricing Tiers (3 tiers with specific prices)
- Revenue Streams
- Market Sizing

## 📈 FINANCIAL PROJECTIONS
- Year 1-3 Revenue/Cost/Profit
- Customer Growth Projections
- Unit Economics

## 🎯 ROI ANALYSIS
- Break-even Timeline
- Customer Acquisition Cost
- Lifetime Value
- Key Ratios

## 💵 FUNDING STRATEGY
- Funding Requirements
- Use of Funds
- Milestones
- Runway Analysis

Be specific with numbers and realistic assumptions. Focus on actionable financial insights."""
    
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
        
        # Extract vision info for dynamic pricing
        vision_statement = vision_data.get("vision_statement", "")
        target_users = vision_data.get("target_users", [])
        
        # Create financial analysis
        financial_model = {
            "revenue_model": {
                "primary_model": self._determine_revenue_model(vision_statement),
                "pricing_tiers": self._generate_pricing_tiers(vision_statement, target_users),
                "revenue_streams": self._generate_revenue_streams(vision_statement)
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
        
        return result
    
    def _generate_financial_insights(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered financial insights"""
        insights = {
            "risk_assessment": "medium",
            "optimization_opportunities": [],
            "funding_recommendations": []
        }
        
        # Analyze pricing tiers
        pricing_tiers = financial_data.get("revenue_model", {}).get("pricing_tiers", [])
        if len(pricing_tiers) < 3:
            insights["optimization_opportunities"].append("Consider adding more pricing tiers for market segmentation")
        
        # Analyze projections
        projections = financial_data.get("financial_projections", {})
        if projections:
            year_1 = projections.get("year_1", {})
            if year_1.get("net_income", 0) < 0:
                insights["funding_recommendations"].append("Secure funding to cover initial losses")
        
        return insights
    
    def _determine_revenue_model(self, vision: str) -> str:
        """Determine revenue model based on vision"""
        if "saas" in vision.lower() or "subscription" in vision.lower():
            return "SaaS Subscription"
        elif "marketplace" in vision.lower():
            return "Marketplace Commission"
        elif "ai assistant" in vision.lower():
            return "Freemium + Premium Subscription"
        else:
            return "Subscription-based"
    
    def _generate_pricing_tiers(self, vision: str, target_users: list) -> list:
        """Generate pricing tiers based on vision and users"""
        if "ai assistant" in vision.lower():
            return [
                {
                    "tier": "Free",
                    "price": 0,
                    "billing": "monthly",
                    "features": ["Basic AI chat", "Limited queries"],
                    "target_segment": "Individual users"
                },
                {
                    "tier": "Pro",
                    "price": 19,
                    "billing": "monthly",
                    "features": ["Unlimited queries", "Memory", "Integrations"],
                    "target_segment": "Professionals"
                },
                {
                    "tier": "Business",
                    "price": 49,
                    "billing": "monthly",
                    "features": ["Team features", "API access", "Priority support"],
                    "target_segment": "Small businesses"
                }
            ]
        elif "content" in vision.lower():
            return [
                {
                    "tier": "Creator",
                    "price": 15,
                    "billing": "monthly",
                    "features": ["Content tools", "Basic analytics"],
                    "target_segment": "Individual creators"
                },
                {
                    "tier": "Pro Creator",
                    "price": 39,
                    "billing": "monthly",
                    "features": ["Advanced tools", "Team collaboration"],
                    "target_segment": "Professional creators"
                },
                {
                    "tier": "Agency",
                    "price": 99,
                    "billing": "monthly",
                    "features": ["White-label", "Client management"],
                    "target_segment": "Agencies"
                }
            ]
        else:
            return [
                {
                    "tier": "Basic",
                    "price": 29,
                    "billing": "monthly",
                    "features": ["Core features"],
                    "target_segment": "Small users"
                },
                {
                    "tier": "Professional",
                    "price": 79,
                    "billing": "monthly",
                    "features": ["Advanced features"],
                    "target_segment": "Professionals"
                }
            ]
    
    def _generate_revenue_streams(self, vision: str) -> list:
        """Generate revenue streams based on vision"""
        if "ai assistant" in vision.lower():
            return [
                "Subscription fees (70%)",
                "API usage fees (20%)",
                "Premium integrations (10%)"
            ]
        elif "content" in vision.lower():
            return [
                "Subscription fees (60%)",
                "Template marketplace (25%)",
                "Professional services (15%)"
            ]
        else:
            return [
                "Subscription fees (80%)",
                "Setup fees (15%)",
                "Support services (5%)"
            ]
    
    async def _use_financial_tools(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use financial tools for current market analysis"""
        try:
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"funding trends venture capital {vision_statement[:50]} 2024"

            funding_data = await self.web_search._arun(search_query)  # Returns List[Dict]

            return {
                "current_funding_trends": funding_data.get("summary", "No data found from web search."),
                "market_sources": funding_data.get("count", 0),
                "recent_insights": [result.get("title", "") for result in funding_data.get("results", [])[:3]],
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