"""
Sales Agent - Advanced sales forecasting, pipeline analysis, and strategy
"""

from datetime import datetime
from typing import Dict, Any, List

from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import FinancialModelingTool, RiskAssessmentTool
class SalesAgent(LangGraphAgent):
    """Sales Agent responsible for revenue forecasting and sales strategy"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "results-driven and analytical",
            "focus": "revenue generation and customer acquisition",
            "expertise": ["sales forecasting", "pipeline management", "customer segmentation", "revenue optimization"],
            "model": "openai/gpt-3.5-turbo",
            "temperature": 0.4,
            "confidence_threshold": 0.75,
            "description": "Develops sales strategies, forecasts revenue, and optimizes customer acquisition"
        }
        
        super().__init__(
            name="Sales",
            role="Sales strategy and revenue optimization specialist",
            memory_manager=memory_manager,
            approval_manager=approval_manager,
            personality=personality
        )
        
        self.web_search = WebSearchTool()
        self.financial_tool = FinancialModelingTool()
        self.risk_tool = RiskAssessmentTool()
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute sales-specific analysis"""
        task = state["task"]
        context = state["context"]
        
        # Get market and product context
        vision_data = await self._get_context_data(context, "cofounder_output")
        product_data = await self._get_context_data(context, "product_output")
        finance_data = await self._get_context_data(context, "finance_output")
        
        # Perform sales analysis
        sales_forecast = await self._create_sales_forecast(vision_data, product_data, finance_data)
        customer_segments = await self._analyze_customer_segments(vision_data, product_data)
        sales_strategy = await self._develop_sales_strategy(vision_data, finance_data)
        
        # Get current market insights
        market_insights = await self._get_sales_market_insights(vision_data)
        
        return {
            "sales_forecast": sales_forecast,
            "customer_segments": customer_segments,
            "sales_strategy": sales_strategy,
            "market_insights": market_insights,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _create_sales_forecast(self, vision_data: Dict, product_data: Dict, finance_data: Dict) -> Dict[str, Any]:
        """Create detailed sales forecast"""
        
        # Extract pricing from finance data
        pricing_tiers = finance_data.get("revenue_model", {}).get("pricing_tiers", [])
        base_price = pricing_tiers[0].get("price", 50) if pricing_tiers else 50
        
        # Use financial modeling tool
        business_model = {
            "expected_revenue": base_price * 1000 * 12,  # Estimate based on pricing
            "expected_costs": base_price * 1000 * 12 * 0.7
        }
        
        financial_model = await self.financial_tool._arun(business_model)
        
        # Create sales-specific projections
        sales_projections = {
            "monthly_targets": {
                f"month_{i}": {
                    "new_customers": max(10, int(50 * (1 + i * 0.1))),
                    "revenue": max(1000, int(base_price * 50 * (1 + i * 0.1))),
                    "churn_rate": max(0.02, 0.05 - i * 0.002)
                }
                for i in range(1, 13)
            },
            "pipeline_analysis": {
                "total_leads": 500,
                "qualified_leads": 150,
                "opportunities": 75,
                "closed_won": 25,
                "conversion_rate": 0.05
            },
            "revenue_breakdown": {
                "new_business": 0.7,
                "expansion": 0.2,
                "renewal": 0.1
            }
        }
        
        return {
            **sales_projections,
            "financial_scenarios": financial_model.get("scenario_projections", {}),
            "confidence_level": 0.78
        }
    
    async def _analyze_customer_segments(self, vision_data: Dict, product_data: Dict) -> Dict[str, Any]:
        """Analyze and define customer segments"""
        
        # Extract user personas from product data
        user_personas = product_data.get("user_personas", [])
        
        segments = {}
        for i, persona in enumerate(user_personas[:3]):  # Limit to 3 segments
            segment_name = persona.get("name", f"Segment_{i+1}")
            segments[segment_name.lower().replace(" ", "_")] = {
                "description": persona.get("demographics", ""),
                "pain_points": persona.get("pain_points", []),
                "value_proposition": self._create_value_prop(persona),
                "sales_approach": self._define_sales_approach(persona),
                "estimated_size": self._estimate_segment_size(persona),
                "conversion_potential": self._estimate_conversion(persona)
            }
        
        return {
            "segments": segments,
            "primary_target": list(segments.keys())[0] if segments else "general_market",
            "segment_priorities": self._prioritize_segments(segments)
        }
    
    async def _develop_sales_strategy(self, vision_data: Dict, finance_data: Dict) -> Dict[str, Any]:
        """Develop comprehensive sales strategy"""
        
        pricing_tiers = finance_data.get("revenue_model", {}).get("pricing_tiers", [])
        
        return {
            "sales_channels": {
                "direct_sales": {
                    "percentage": 60,
                    "approach": "Inside sales team",
                    "target_segments": ["enterprise", "smb"],
                    "expected_conversion": 0.08
                },
                "partner_sales": {
                    "percentage": 25,
                    "approach": "Channel partnerships",
                    "target_segments": ["smb", "individual"],
                    "expected_conversion": 0.05
                },
                "self_service": {
                    "percentage": 15,
                    "approach": "Online signup",
                    "target_segments": ["individual", "small_teams"],
                    "expected_conversion": 0.02
                }
            },
            "sales_process": {
                "lead_qualification": "BANT criteria",
                "demo_to_close": "14 days average",
                "follow_up_sequence": "5 touchpoints over 30 days",
                "objection_handling": ["price", "features", "implementation"]
            },
            "pricing_strategy": {
                "model": "Tiered SaaS pricing",
                "tiers": len(pricing_tiers),
                "upsell_opportunities": ["premium_features", "additional_users", "integrations"],
                "discount_policy": "10% annual, 20% enterprise"
            },
            "sales_enablement": {
                "materials_needed": ["pitch_deck", "demo_script", "case_studies", "roi_calculator"],
                "training_topics": ["product_knowledge", "objection_handling", "demo_skills"],
                "tools_required": ["crm", "demo_environment", "proposal_generator"]
            }
        }
    
    async def _get_sales_market_insights(self, vision_data: Dict) -> Dict[str, Any]:
        """Get current sales and market insights"""
        try:
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"sales trends {vision_statement[:50]} B2B SaaS 2024"
            
            market_data = await self.web_search._arun(search_query)
            
            return {
                "current_sales_trends": market_data.get("summary", "Analysis in progress"),
                "market_sources": len(market_data.get("results", [])),
                "key_insights": [result.get("title", "") for result in market_data.get("results", [])[:3]],
                "last_updated": market_data.get("timestamp", "")
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual sales research required"}
    
    async def _get_context_data(self, context: Dict, key: str) -> Dict[str, Any]:
        """Helper to get context data with fallback"""
        if key in context:
            return context[key]
        
        # Try to get from shared context
        shared_context = await self.memory_manager.get_shared_context()
        return shared_context.get(key, [{}])[0].get("content", {}) if shared_context.get(key) else {}
    
    def _create_value_prop(self, persona: Dict) -> str:
        """Create value proposition for persona"""
        pain_points = persona.get("pain_points", [])
        if pain_points:
            return f"Solves {pain_points[0]} while providing {persona.get('goals', ['efficiency'])[0]}"
        return "Delivers value through innovative solution"
    
    def _define_sales_approach(self, persona: Dict) -> str:
        """Define sales approach for persona"""
        demographics = persona.get("demographics", "").lower()
        if "enterprise" in demographics or "large" in demographics:
            return "Enterprise sales with multiple stakeholders"
        elif "small business" in demographics or "smb" in demographics:
            return "Direct sales with decision maker"
        else:
            return "Product-led growth with self-service option"
    
    def _estimate_segment_size(self, persona: Dict) -> str:
        """Estimate market segment size"""
        demographics = persona.get("demographics", "").lower()
        if "enterprise" in demographics:
            return "Large enterprises: ~50K companies"
        elif "small business" in demographics:
            return "SMB market: ~500K companies"
        else:
            return "Individual users: ~5M potential users"
    
    def _estimate_conversion(self, persona: Dict) -> float:
        """Estimate conversion potential"""
        pain_points = len(persona.get("pain_points", []))
        goals = len(persona.get("goals", []))
        return min(0.15, (pain_points + goals) * 0.02 + 0.03)
    
    def _prioritize_segments(self, segments: Dict) -> List[str]:
        """Prioritize segments by conversion potential"""
        segment_scores = []
        for name, data in segments.items():
            score = data.get("conversion_potential", 0)
            segment_scores.append((name, score))
        
        segment_scores.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in segment_scores]