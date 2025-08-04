"""
Sales Agent - Advanced sales forecasting, pipeline analysis, and strategy
"""

from datetime import datetime
from typing import Dict, Any, List

from agents.langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import FinancialModelingTool, RiskAssessmentTool
class SalesAgent(LangGraphAgent):
    """Enhanced Sales Agent - Revenue forecasting + Lead qualification + Deal closing"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "results-driven and analytical",
            "focus": "revenue generation, customer acquisition, and deal closing",
            "expertise": [
                "sales forecasting", "pipeline management", "customer segmentation", "revenue optimization",
                "lead qualification", "deal closing", "objection handling", "sales psychology"
            ],
            "model": "openai/gpt-3.5-turbo",
            "temperature": 0.4,
            "confidence_threshold": 0.75,
            "description": "Enhanced sales agent with lead qualification and deal closing capabilities"
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
        
        # Initialize role-specific action methods
        self.role_actions = {
            "lead_qualification": self._qualify_lead,
            "outreach_preparation": self._prepare_outreach,
            "meeting_scheduling": self._schedule_meeting,
            "sales_strategy": self._create_sales_strategy,
            "pipeline_management": self._manage_pipeline
        }
    
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
    
    # === CLOSER CAPABILITIES (consolidated from Closer Agent) ===
    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify leads using BANT criteria (consolidated from Closer agent)"""
        qualification_prompt = f"""
        Qualify this lead using BANT criteria:
        
        Lead Data: {lead_data}
        
        Analyze:
        1. Budget - Do they have budget allocated?
        2. Authority - Are they the decision maker?
        3. Need - Do they have a clear pain point?
        4. Timeline - When do they need a solution?
        
        Provide qualification score (1-10) and next steps.
        """
        
        qualification = await self._think(qualification_prompt)
        lead_score = self._calculate_lead_score(lead_data)
        
        return {
            "qualification_analysis": qualification,
            "lead_score": lead_score,
            "qualification_status": "qualified" if lead_score >= 7 else "needs_nurturing",
            "next_steps": self._get_next_steps(lead_score),
            "confidence": 0.85
        }
    
    async def create_closing_strategy(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create deal closing strategy (consolidated from Closer agent)"""
        return {
            "closing_techniques": {
                "assumptive_close": "When shall we schedule the implementation?",
                "alternative_close": "Would you prefer the monthly or annual plan?",
                "urgency_close": "This pricing is available until end of quarter",
                "summary_close": "Based on our discussion, this solves X, Y, Z"
            },
            "objection_handling": {
                "price_objection": {
                    "response": "Let's look at the ROI calculation together",
                    "supporting_materials": ["ROI calculator", "Case studies", "Cost comparison"]
                },
                "feature_objection": {
                    "response": "Let me show you how this feature works in practice",
                    "supporting_materials": ["Live demo", "Feature comparison", "Roadmap"]
                },
                "timing_objection": {
                    "response": "What would need to happen for this to be a priority?",
                    "supporting_materials": ["Implementation timeline", "Quick wins", "Pilot program"]
                }
            },
            "success_metrics": {
                "close_rate": "Target 25% of qualified opportunities",
                "sales_cycle": "Average 30-45 days for SMB, 60-90 for enterprise",
                "deal_size": "Average $5K SMB, $25K enterprise annually"
            }
        }
    
    def _calculate_lead_score(self, lead_data: Dict[str, Any]) -> int:
        """Calculate lead score based on qualification criteria"""
        score = 0
        
        if lead_data.get("budget_allocated") or lead_data.get("budget_range"):
            score += 3
        
        if lead_data.get("job_title", "").lower() in ["ceo", "cto", "vp", "director", "manager"]:
            score += 2
        
        if lead_data.get("pain_points") or lead_data.get("current_solution_issues"):
            score += 3
        
        if lead_data.get("timeline", "").lower() in ["immediate", "this quarter", "urgent"]:
            score += 2
        
        return min(10, score)
    
    def _get_next_steps(self, lead_score: int) -> List[str]:
        """Get next steps based on lead score"""
        if lead_score >= 8:
            return ["Schedule demo immediately", "Send proposal within 48 hours", "Involve decision makers"]
        elif lead_score >= 6:
            return ["Qualify further", "Schedule discovery call", "Send relevant case studies"]
        else:
            return ["Add to nurture campaign", "Send educational content", "Follow up in 30 days"]
            
    # === ROLE-SPECIFIC ACTION METHODS ===
    async def _qualify_lead(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify leads using BANT criteria"""
        lead_data = params.get("lead_data", {})
        
        if not lead_data:
            return {"error": "No lead data provided for qualification", "success": False}
        
        try:
            # Use existing qualify_lead method
            qualification_result = await self.qualify_lead(lead_data)
            
            # Store in memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="lead_qualifications",
                content=qualification_result,
                is_shared=True,
                confidence=qualification_result.get("confidence", 0.85)
            )
            
            return qualification_result
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _prepare_outreach(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare outreach messages for leads"""
        lead_data = params.get("lead_data", {})
        outreach_type = params.get("outreach_type", "email")
        
        if not lead_data:
            return {"error": "No lead data provided for outreach preparation", "success": False}
        
        # Prepare outreach messages based on type
        outreach_templates = {}
        
        if outreach_type == "email" or outreach_type == "all":
            outreach_templates["email"] = {
                "subject": f"Solving {lead_data.get('pain_point', 'your challenges')} with {lead_data.get('company_name', 'our solution')}",
                "greeting": f"Hi {lead_data.get('first_name', 'there')},",
                "intro": "I noticed your company is facing challenges with [pain point]. I thought you might be interested in how we've helped similar companies.",
                "value_prop": "Our solution helps [target persona] achieve [key benefit] by [unique approach].",
                "social_proof": "Companies like [reference customer] have seen [specific result] after implementing our solution.",
                "call_to_action": "Would you be open to a 15-minute call to discuss how we might help?",
                "signature": "Best regards,\n[Sales Rep Name]\n[Company Name]"
            }
        
        if outreach_type == "linkedin" or outreach_type == "all":
            outreach_templates["linkedin"] = {
                "connection_request": f"Hi {lead_data.get('first_name', 'there')}, I help companies like yours with {lead_data.get('pain_point', 'specific challenges')}. I'd love to connect!",
                "follow_up": "Thanks for connecting! I noticed your company is working on [relevant initiative]. I'd love to share how we've helped similar companies achieve [specific result]."
            }
        
        if outreach_type == "call_script" or outreach_type == "all":
            outreach_templates["call_script"] = {
                "introduction": f"Hi {lead_data.get('first_name', 'there')}, this is [Sales Rep] from [Company]. We help companies like yours with {lead_data.get('pain_point', 'specific challenges')}.",
                "reason_for_call": "I'm reaching out because we've helped several companies in your industry achieve [specific result].",
                "qualifying_questions": [
                    "What challenges are you currently facing with [relevant area]?",
                    "How are you currently addressing these challenges?",
                    "What would solving this problem mean for your business?",
                    "Who else is involved in making decisions about [relevant area]?",
                    "What's your timeline for implementing a solution?"
                ],
                "objection_handling": {
                    "not_interested": "I understand. May I ask what solution you're currently using for [pain point]?",
                    "too_expensive": "I appreciate that budget is a consideration. Many of our clients found that the ROI justified the investment within [timeframe].",
                    "bad_timing": "I understand timing is important. When would be a better time to revisit this conversation?"
                },
                "close": "Based on what you've shared, I think we could help. Would you be open to a more detailed demonstration of how our solution works?"
            }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="outreach_templates",
            content=outreach_templates,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "outreach_templates": outreach_templates,
            "lead_data": lead_data,
            "outreach_type": outreach_type,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _schedule_meeting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule meetings with leads"""
        lead_data = params.get("lead_data", {})
        meeting_type = params.get("meeting_type", "discovery")
        proposed_times = params.get("proposed_times", [])
        
        if not lead_data:
            return {"error": "No lead data provided for meeting scheduling", "success": False}
        
        # Create meeting details based on type
        meeting_details = {
            "lead_name": lead_data.get("first_name", "") + " " + lead_data.get("last_name", ""),
            "lead_company": lead_data.get("company_name", ""),
            "meeting_type": meeting_type,
            "duration": "30 minutes" if meeting_type == "discovery" else "60 minutes",
            "proposed_times": proposed_times or [
                "Tomorrow at 10:00 AM",
                "Tomorrow at 2:00 PM",
                "Day after tomorrow at 11:00 AM"
            ],
            "agenda": self._create_meeting_agenda(meeting_type),
            "preparation_checklist": self._create_preparation_checklist(meeting_type, lead_data),
            "follow_up_plan": self._create_follow_up_plan(meeting_type)
        }
        
        # Create calendar invite template
        calendar_invite = {
            "subject": f"{meeting_type.capitalize()} Call with {lead_data.get('company_name', 'Prospect')}",
            "location": "Zoom (link to be provided)",
            "description": f"""
Agenda:
{meeting_details['agenda']}

Preparation:
- Review company website and LinkedIn profile
- Review any previous interactions
- Prepare demo environment if needed

Looking forward to our conversation!
            """,
            "attendees": [
                lead_data.get("email", "prospect@example.com"),
                "sales@ourcompany.com"
            ]
        }
        
        meeting_details["calendar_invite"] = calendar_invite
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="scheduled_meetings",
            content=meeting_details,
            is_shared=True,
            confidence=0.95
        )
        
        return {
            "meeting_details": meeting_details,
            "lead_data": lead_data,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_sales_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales strategy"""
        vision_data = params.get("vision_data", {})
        finance_data = params.get("finance_data", {})
        
        # Use existing develop_sales_strategy method
        sales_strategy = await self._develop_sales_strategy(vision_data, finance_data)
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="sales_strategies",
            content=sales_strategy,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "sales_strategy": sales_strategy,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _manage_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage sales pipeline"""
        pipeline_data = params.get("pipeline_data", {})
        timeframe = params.get("timeframe", "monthly")
        
        if not pipeline_data:
            # Create default pipeline data
            pipeline_data = {
                "stages": {
                    "lead": {"count": 100, "conversion_rate": 0.5},
                    "qualified": {"count": 50, "conversion_rate": 0.4},
                    "proposal": {"count": 20, "conversion_rate": 0.5},
                    "negotiation": {"count": 10, "conversion_rate": 0.7},
                    "closed_won": {"count": 7, "conversion_rate": 1.0}
                },
                "total_value": 350000,
                "average_deal_size": 50000
            }
        
        # Calculate pipeline metrics
        pipeline_metrics = {
            "conversion_rates": {
                stage: data["conversion_rate"] 
                for stage, data in pipeline_data["stages"].items()
            },
            "stage_distribution": {
                stage: data["count"] / sum(s["count"] for s in pipeline_data["stages"].values())
                for stage, data in pipeline_data["stages"].items()
            },
            "expected_revenue": sum(
                data["count"] * data["conversion_rate"] * (pipeline_data["average_deal_size"] if "average_deal_size" in pipeline_data else 50000)
                for stage, data in pipeline_data["stages"].items()
                if stage != "closed_won"  # Don't double count closed deals
            ) + pipeline_data["stages"].get("closed_won", {}).get("count", 0) * (pipeline_data["average_deal_size"] if "average_deal_size" in pipeline_data else 50000),
            "pipeline_health": self._calculate_pipeline_health(pipeline_data),
            "risk_assessment": self._assess_pipeline_risks(pipeline_data)
        }
        
        # Generate recommendations
        recommendations = []
        
        # Check lead to qualified conversion
        lead_to_qualified = pipeline_data["stages"].get("lead", {}).get("conversion_rate", 0)
        if lead_to_qualified < 0.4:
            recommendations.append({
                "focus_area": "Lead Qualification",
                "issue": "Low lead-to-qualified conversion rate",
                "recommendation": "Improve lead qualification process and criteria",
                "expected_impact": "Increase qualified leads by 20%"
            })
        
        # Check proposal to negotiation conversion
        proposal_to_negotiation = pipeline_data["stages"].get("proposal", {}).get("conversion_rate", 0)
        if proposal_to_negotiation < 0.5:
            recommendations.append({
                "focus_area": "Proposal Quality",
                "issue": "Low proposal-to-negotiation conversion rate",
                "recommendation": "Enhance proposal templates and customize to specific client needs",
                "expected_impact": "Increase proposal conversion by 15%"
            })
        
        # Check pipeline distribution
        qualified_count = pipeline_data["stages"].get("qualified", {}).get("count", 0)
        proposal_count = pipeline_data["stages"].get("proposal", {}).get("count", 0)
        if qualified_count < proposal_count * 2:
            recommendations.append({
                "focus_area": "Pipeline Balance",
                "issue": "Insufficient qualified leads in pipeline",
                "recommendation": "Increase lead generation and qualification activities",
                "expected_impact": "Improve pipeline balance and future revenue"
            })
        
        pipeline_management = {
            "pipeline_data": pipeline_data,
            "pipeline_metrics": pipeline_metrics,
            "recommendations": recommendations,
            "action_plan": {
                "immediate_actions": [rec["recommendation"] for rec in recommendations],
                "monitoring_metrics": ["Conversion rates by stage", "Average sales cycle", "Win rate"],
                "review_frequency": "Weekly"
            },
            "timeframe": timeframe
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="pipeline_management",
            content=pipeline_management,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "pipeline_management": pipeline_management,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_meeting_agenda(self, meeting_type: str) -> List[str]:
        """Create meeting agenda based on meeting type"""
        if meeting_type == "discovery":
            return [
                "Introduction and rapport building (5 min)",
                "Overview of their business and challenges (10 min)",
                "Brief introduction to our solution (5 min)",
                "Exploration of specific pain points (5 min)",
                "Next steps and action items (5 min)"
            ]
        elif meeting_type == "demo":
            return [
                "Recap of previous conversation and goals (5 min)",
                "Overview of solution and key features (10 min)",
                "Demonstration of specific use cases (30 min)",
                "Questions and discussion (10 min)",
                "Next steps and timeline (5 min)"
            ]
        elif meeting_type == "proposal":
            return [
                "Recap of needs and solution fit (5 min)",
                "Presentation of proposal and pricing (15 min)",
                "Discussion of implementation timeline (10 min)",
                "Addressing questions and concerns (15 min)",
                "Agreement on next steps (15 min)"
            ]
        else:
            return [
                "Introduction and agenda setting (5 min)",
                "Discussion of key topics (15 min)",
                "Questions and answers (5 min)",
                "Next steps and action items (5 min)"
            ]
    
    def _create_preparation_checklist(self, meeting_type: str, lead_data: Dict[str, Any]) -> List[str]:
        """Create preparation checklist based on meeting type"""
        common_items = [
            f"Research {lead_data.get('company_name', 'the company')} website and LinkedIn",
            "Review previous interactions and notes",
            "Prepare relevant case studies and references"
        ]
        
        if meeting_type == "discovery":
            return common_items + [
                "Prepare discovery questions",
                "Research industry trends and challenges"
            ]
        elif meeting_type == "demo":
            return common_items + [
                "Prepare demo environment with relevant data",
                "Test all features to be demonstrated",
                "Prepare for common questions and objections"
            ]
        elif meeting_type == "proposal":
            return common_items + [
                "Finalize proposal document",
                "Prepare ROI calculations",
                "Prepare implementation timeline",
                "Anticipate negotiation points"
            ]
        else:
            return common_items
    
    def _create_follow_up_plan(self, meeting_type: str) -> Dict[str, Any]:
        """Create follow-up plan based on meeting type"""
        if meeting_type == "discovery":
            return {
                "same_day": "Send thank you email with summary of discussion",
                "next_day": "Connect on LinkedIn if not already connected",
                "within_week": "Send relevant case study or white paper",
                "next_steps": "Schedule demo if qualified"
            }
        elif meeting_type == "demo":
            return {
                "same_day": "Send thank you email with demo recording if available",
                "next_day": "Address any outstanding questions",
                "within_week": "Send proposal or schedule proposal meeting",
                "next_steps": "Move to proposal/negotiation stage"
            }
        elif meeting_type == "proposal":
            return {
                "same_day": "Send thank you email with final proposal document",
                "next_day": "Check in on decision timeline",
                "within_week": "Follow up on any open questions",
                "next_steps": "Secure verbal commitment or address objections"
            }
        else:
            return {
                "same_day": "Send thank you email with meeting summary",
                "within_week": "Follow up on action items",
                "next_steps": "Schedule next conversation"
            }
    
    def _calculate_pipeline_health(self, pipeline_data: Dict[str, Any]) -> str:
        """Calculate overall pipeline health"""
        # Check total pipeline value
        total_value = pipeline_data.get("total_value", 0)
        target_value = 500000  # Example target
        
        # Check stage distribution
        stages = pipeline_data.get("stages", {})
        lead_count = stages.get("lead", {}).get("count", 0)
        qualified_count = stages.get("qualified", {}).get("count", 0)
        proposal_count = stages.get("proposal", {}).get("count", 0)
        
        # Check conversion rates
        lead_conversion = stages.get("lead", {}).get("conversion_rate", 0)
        qualified_conversion = stages.get("qualified", {}).get("conversion_rate", 0)
        proposal_conversion = stages.get("proposal", {}).get("conversion_rate", 0)
        
        # Calculate health score
        value_score = min(1.0, total_value / target_value)
        
        distribution_score = 0.0
        if lead_count > 0 and qualified_count > 0 and proposal_count > 0:
            if lead_count > qualified_count > proposal_count:
                distribution_score = 1.0
            elif lead_count > qualified_count and qualified_count <= proposal_count:
                distribution_score = 0.7
            else:
                distribution_score = 0.4
        
        conversion_score = (lead_conversion + qualified_conversion + proposal_conversion) / 3
        
        overall_score = (value_score * 0.4) + (distribution_score * 0.3) + (conversion_score * 0.3)
        
        if overall_score >= 0.8:
            return "Excellent"
        elif overall_score >= 0.6:
            return "Good"
        elif overall_score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _assess_pipeline_risks(self, pipeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess risks in the sales pipeline"""
        risks = []
        
        # Check for large deal concentration
        if pipeline_data.get("average_deal_size", 0) > 100000:
            risks.append({
                "risk_type": "Deal Concentration",
                "description": "High average deal size may indicate over-reliance on few large deals",
                "severity": "Medium",
                "mitigation": "Diversify pipeline with more smaller deals"
            })
        
        # Check for stage imbalance
        stages = pipeline_data.get("stages", {})
        if stages.get("lead", {}).get("count", 0) < stages.get("qualified", {}).get("count", 0) * 2:
            risks.append({
                "risk_type": "Pipeline Imbalance",
                "description": "Insufficient leads at top of funnel",
                "severity": "High",
                "mitigation": "Increase lead generation activities"
            })
        
        # Check for conversion issues
        if stages.get("proposal", {}).get("conversion_rate", 0) < 0.3:
            risks.append({
                "risk_type": "Low Close Rate",
                "description": "Poor conversion from proposal to closed deal",
                "severity": "High",
                "mitigation": "Review proposal quality and closing techniques"
            })
        
        return risks