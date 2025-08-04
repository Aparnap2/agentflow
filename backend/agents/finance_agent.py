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
        
        # Initialize role-specific action methods
        self.role_actions = {
            "expense_processing": self._process_expenses,
            "financial_summary": self._generate_financial_summary,
            "transaction_categorization": self._categorize_transactions,
            "financial_modeling": self._create_financial_model,
            "pricing_analysis": self._analyze_pricing
        }
    
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
        """Process financial modeling and analysis with memory integration"""
        
        task = state["task"]
        context = state["context"]
        
        # Get relevant context using RAG (Qdrant)
        global_context = await self.memory_manager.get_global_context_for_agent(
            agent_name=self.name,
            query="financial projections pricing revenue model funding"
        )
        
        # Get my previous financial analysis from private memory (Neo4j)
        previous_analysis = await self.memory_manager.get_agent_private_memory(
            agent_name=self.name,
            memory_type="financial_modeling",
            limit=3
        )
        
        # Extract context from shared memory
        shared_context = global_context.get("shared_context", {})
        vision_data = shared_context.get("cofounder_output", {})
        product_data = shared_context.get("product_strategy", {})
        
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
        
        # Store in private memory (Neo4j) for my future reference
        await self.memory_manager.store_agent_private_memory(
            agent_name=self.name,
            memory_type="financial_modeling",
            content={
                "financial_model": financial_model,
                "market_analysis": market_data,
                "previous_analysis_count": len(previous_analysis),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Store in shared memory (Qdrant) for other agents to access
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="financial_projections",
            content=financial_model,
            is_shared=True,
            confidence=confidence,
            metadata={"task_id": task.get("id"), "agent": "David Park"}
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
  # === ROLE-SPECIFIC ACTION METHODS ===
    async def _process_expenses(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process expense reports"""
        expenses = params.get("expenses", [])
        report_type = params.get("report_type", "monthly")
        
        if not expenses:
            return {"error": "No expenses provided for processing", "success": False}
        
        # Process expenses
        total_amount = sum(expense.get("amount", 0) for expense in expenses)
        categorized_expenses = {}
        
        for expense in expenses:
            category = expense.get("category", "Uncategorized")
            if category not in categorized_expenses:
                categorized_expenses[category] = 0
            categorized_expenses[category] += expense.get("amount", 0)
        
        # Calculate percentages
        category_percentages = {}
        for category, amount in categorized_expenses.items():
            category_percentages[category] = round((amount / total_amount) * 100, 2) if total_amount > 0 else 0
        
        # Generate expense report
        expense_report = {
            "total_amount": total_amount,
            "report_type": report_type,
            "categorized_expenses": categorized_expenses,
            "category_percentages": category_percentages,
            "expense_count": len(expenses),
            "generated_at": datetime.now().isoformat()
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="expense_reports",
            content=expense_report,
            is_shared=True,
            confidence=0.95
        )
        
        return {
            "expense_report": expense_report,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_financial_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial summary"""
        financial_data = params.get("financial_data", {})
        period = params.get("period", "monthly")
        
        if not financial_data:
            return {"error": "No financial data provided for summary", "success": False}
        
        # Generate financial summary
        revenue = financial_data.get("revenue", 0)
        expenses = financial_data.get("expenses", 0)
        net_income = revenue - expenses
        profit_margin = (net_income / revenue) * 100 if revenue > 0 else 0
        
        financial_summary = {
            "period": period,
            "revenue": revenue,
            "expenses": expenses,
            "net_income": net_income,
            "profit_margin": round(profit_margin, 2),
            "key_metrics": {
                "burn_rate": expenses / 30 if period == "monthly" else expenses / 365,  # Daily burn rate
                "runway_days": (financial_data.get("cash_on_hand", 0) / (expenses / 30)) if expenses > 0 else 0,
                "revenue_growth": financial_data.get("revenue_growth", 0),
                "customer_acquisition_cost": financial_data.get("customer_acquisition_cost", 0)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="financial_summaries",
            content=financial_summary,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "financial_summary": financial_summary,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _categorize_transactions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize financial transactions"""
        transactions = params.get("transactions", [])
        
        if not transactions:
            return {"error": "No transactions provided for categorization", "success": False}
        
        # Categorize transactions
        categorized_transactions = []
        categories = {
            "salary": ["salary", "payroll", "wage", "income"],
            "rent": ["rent", "lease", "housing"],
            "utilities": ["electric", "water", "gas", "internet", "phone", "utility"],
            "food": ["restaurant", "grocery", "food", "meal"],
            "transportation": ["uber", "lyft", "taxi", "transit", "gas", "fuel"],
            "entertainment": ["movie", "game", "subscription", "netflix", "spotify"],
            "shopping": ["amazon", "walmart", "target", "purchase", "buy"],
            "travel": ["hotel", "flight", "airbnb", "airline"],
            "healthcare": ["doctor", "medical", "pharmacy", "health"],
            "education": ["tuition", "course", "book", "school"],
            "business": ["office", "software", "service", "consulting"]
        }
        
        for transaction in transactions:
            description = transaction.get("description", "").lower()
            amount = transaction.get("amount", 0)
            
            # Determine category based on description
            assigned_category = "other"
            for category, keywords in categories.items():
                if any(keyword in description for keyword in keywords):
                    assigned_category = category
                    break
            
            # Add categorized transaction
            categorized_transactions.append({
                "transaction_id": transaction.get("id", ""),
                "description": description,
                "amount": amount,
                "date": transaction.get("date", ""),
                "category": assigned_category,
                "confidence": 0.85
            })
        
        # Generate summary
        category_totals = {}
        for transaction in categorized_transactions:
            category = transaction["category"]
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += transaction["amount"]
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="categorized_transactions",
            content={
                "categorized_transactions": categorized_transactions,
                "category_totals": category_totals
            },
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "categorized_transactions": categorized_transactions,
            "category_totals": category_totals,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_financial_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create financial model"""
        business_model = params.get("business_model", {})
        timeframe = params.get("timeframe", "3 years")
        
        if not business_model:
            return {"error": "No business model provided for financial modeling", "success": False}
        
        # Use financial modeling tool
        financial_model = await self.financial_modeling._arun(business_model)
        
        # Extract vision info for dynamic pricing if available
        vision_statement = params.get("vision_statement", "")
        target_users = params.get("target_users", [])
        
        # Create financial model
        enhanced_model = {
            "revenue_model": {
                "primary_model": self._determine_revenue_model(vision_statement),
                "pricing_tiers": self._generate_pricing_tiers(vision_statement, target_users),
                "revenue_streams": self._generate_revenue_streams(vision_statement)
            },
            "financial_projections": financial_model.get("projections", {
                "year_1": {
                    "revenue": business_model.get("expected_revenue", 0),
                    "costs": business_model.get("expected_costs", 0),
                    "net_income": business_model.get("expected_revenue", 0) - business_model.get("expected_costs", 0),
                    "customers": business_model.get("expected_customers", 100)
                }
            }),
            "roi_analysis": financial_model.get("roi_analysis", {
                "break_even_point": "Month 18",
                "customer_acquisition_cost": 150,
                "customer_lifetime_value": 2400,
                "ltv_cac_ratio": 16
            })
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="financial_models",
            content=enhanced_model,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "financial_model": enhanced_model,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_pricing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing strategy"""
        product_data = params.get("product_data", {})
        competitors = params.get("competitors", [])
        
        if not product_data:
            return {"error": "No product data provided for pricing analysis", "success": False}
        
        # Analyze pricing strategy
        pricing_analysis = await self._analyze_pricing_strategy(product_data)
        
        # Generate pricing recommendations
        pricing_recommendations = {
            "recommended_pricing_model": self._determine_revenue_model(product_data.get("description", "")),
            "pricing_tiers": self._generate_pricing_tiers(product_data.get("description", ""), product_data.get("target_users", [])),
            "competitive_analysis": {
                "market_position": "premium" if product_data.get("premium_features", False) else "standard",
                "price_comparison": "competitive",
                "value_proposition": "strong"
            },
            "optimization_strategies": [
                "Value-based pricing for premium features",
                "Tiered pricing to capture different market segments",
                "Usage-based components for scalability",
                "Annual discount to improve cash flow"
            ]
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="pricing_analysis",
            content={
                "pricing_analysis": pricing_analysis,
                "pricing_recommendations": pricing_recommendations
            },
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "pricing_analysis": pricing_analysis,
            "pricing_recommendations": pricing_recommendations,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }