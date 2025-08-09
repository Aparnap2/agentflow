"""
Marketing Agent - Handles content strategy, SEO analysis, and social media planning
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
from .langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool
from tools.advanced_tools import ContentStrategyTool
# Import Instagram and Slack integrations
try:
    from integrations.instagram_client import InstagramClient, InstagramPost
    from integrations.slack_client import SlackClient, SlackNotification
    from integrations.base_integration import IntegrationConfig
except ImportError:
    # Fallback if integrations not available
    InstagramClient = None
    InstagramPost = None
    SlackClient = None
    SlackNotification = None
    IntegrationConfig = None


class WebCrawlerTool(BaseTool):
    """Tool for web crawling using Crawl4AI"""
    name: str = "web_crawler"
    description: str = "Crawl websites for competitive analysis and content research"
    
    def _run(self, url: str, extract_type: str = "content") -> Dict[str, Any]:
        # Simplified implementation - in production would use Crawl4AI
        return {
            "url": url,
            "title": f"Sample Title from {url}",
            "content": f"Sample content extracted from {url}",
            "meta_description": "Sample meta description",
            "keywords": ["sample", "keywords", "extracted"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _arun(self, url: str, extract_type: str = "content") -> Dict[str, Any]:
        return self._run(url, extract_type)


class SEOAnalysisTool(BaseTool):
    """Tool for SEO analysis and keyword suggestions"""
    name: str = "seo_analyzer"
    description: str = "Analyze SEO opportunities and suggest keywords"
    
    def _run(self, content: str, target_audience: str = "") -> Dict[str, Any]:
        # Simplified SEO analysis
        keywords = self._extract_keywords(content)
        return {
            "primary_keywords": keywords[:5],
            "secondary_keywords": keywords[5:15],
            "content_score": 75,
            "recommendations": [
                "Add more long-tail keywords",
                "Improve meta descriptions",
                "Optimize heading structure",
                "Add internal links"
            ],
            "target_audience": target_audience
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        # Basic keyword extraction
        words = content.lower().split()
        # Filter common words and return unique keywords
        common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        return list(set(keywords))[:20]
    
    async def _arun(self, content: str, target_audience: str = "") -> Dict[str, Any]:
        return self._run(content, target_audience)


class ContentGeneratorTool(BaseTool):
    """Tool for generating marketing content templates"""
    name: str = "content_generator"
    description: str = "Generate marketing content templates and social media posts"
    
    def _run(self, content_type: str, topic: str, tone: str = "professional") -> Dict[str, Any]:
        templates = {
            "blog_post": {
                "title": f"The Ultimate Guide to {topic}",
                "outline": [
                    f"Introduction to {topic}",
                    f"Why {topic} Matters",
                    f"Best Practices for {topic}",
                    f"Common Mistakes to Avoid",
                    "Conclusion and Next Steps"
                ],
                "cta": f"Ready to master {topic}? Get started today!"
            },
            "social_media": {
                "twitter": f"🚀 Excited to share insights about {topic}! #innovation #growth",
                "linkedin": f"Exploring the impact of {topic} on modern business...",
                "instagram": f"Behind the scenes: How we're revolutionizing {topic} ✨"
            },
            "email": {
                "subject": f"Transform Your Approach to {topic}",
                "preview": f"Discover game-changing strategies for {topic}",
                "body_outline": [
                    "Personal greeting",
                    f"Problem statement about {topic}",
                    "Solution overview",
                    "Call to action"
                ]
            }
        }
        
        return {
            "content_type": content_type,
            "topic": topic,
            "tone": tone,
            "template": templates.get(content_type, {}),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _arun(self, content_type: str, topic: str, tone: str = "professional") -> Dict[str, Any]:
        return self._run(content_type, topic, tone)


class MarketingAgent(LangGraphAgent):
    """Enhanced Marketing Agent - Content strategy + Brand amplification capabilities"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "creative and data-driven",
            "focus": "brand awareness, lead generation, and content amplification",
            "expertise": [
                "content marketing", "SEO", "social media", "analytics",
                "brand amplification", "content performance", "viral marketing", "influencer outreach"
            ],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.7,
            "confidence_threshold": 0.6,
            "description": "Enhanced marketing agent with content amplification and performance optimization"
        }
        
        super().__init__(
            name="Marketing",
            role="Content strategist and SEO specialist",
            memory_manager=memory_manager,
            approval_manager=approval_manager,
            personality=personality
        )
        
        # Initialize marketing-specific tools
        self.tools = [
            WebCrawlerTool(),
            SEOAnalysisTool(),
            ContentGeneratorTool()
        ]
        self.web_search = WebSearchTool()
        self.content_strategy = ContentStrategyTool()
        
        # Initialize Instagram and Slack clients (following PRD architecture)
        self.instagram_client = None
        self.slack_client = None
        self._init_integrations()
        
        # Add Instagram-specific capabilities as per PRD
        self.instagram_automation_features = {
            "content_publishing": True,
            "dm_automation": True,
            "story_management": True,
            "hashtag_optimization": True,
            "audience_analysis": True
        }
        
        # Initialize role-specific action methods
        self.role_actions = {
            "content_generation": self._generate_content,
            "seo_analysis": self._analyze_seo,
            "ad_copy_creation": self._create_ad_copy,
            "marketing_strategy": self._create_marketing_strategy,
            "campaign_planning": self._plan_campaign,
            "instagram_posting": self._create_instagram_post,
            "instagram_dm_automation": self._handle_instagram_dms,
            "instagram_story_management": self._manage_instagram_stories,
            "hashtag_optimization": self._optimize_hashtags,
            "audience_analysis": self._analyze_instagram_audience,
            "slack_notification": self._send_slack_notification
        }
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute marketing-specific actions"""
        task = state["task"]
        context = state["context"]
        task_type = task.get("type", "general")
        
        if task_type == "content_strategy":
            return await self._create_content_strategy(task, context)
        elif task_type == "seo_analysis":
            return await self._perform_seo_analysis(task, context)
        elif task_type == "social_media_plan":
            return await self._create_social_media_plan(task, context)
        elif task_type == "content_amplification":
            return await self._amplify_content_performance(task, context)
        elif task_type == "viral_strategy":
            return await self._create_viral_strategy(task, context)
        else:
            return await self._general_marketing_analysis(task, context)
    
    async def _amplify_content_performance(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Amplify content performance using consolidated Amplifier capabilities"""
        content_data = task.get("content_data", {})
        brand_data = context.get("brand_data", {})
        
        # Analyze current performance
        performance_analysis = await self.analyze_content_performance(content_data)
        
        # Create viral content strategy
        viral_strategy = await self.create_viral_content_strategy(brand_data)
        
        # Optimize reach
        reach_optimization = await self.optimize_content_reach(content_data)
        
        amplification_plan = {
            "performance_insights": performance_analysis,
            "viral_content_strategy": viral_strategy,
            "reach_optimization": reach_optimization,
            "implementation_timeline": {
                "week_1": "Performance analysis and strategy refinement",
                "week_2": "Content optimization and influencer outreach",
                "week_3": "Campaign launch and monitoring",
                "week_4": "Performance review and iteration"
            }
        }
        
        return amplification_plan
    
    async def _create_viral_strategy(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive viral marketing strategy"""
        brand_data = context.get("brand_data", {})
        
        viral_strategy = await self.create_viral_content_strategy(brand_data)
        
        # Add specific viral campaign ideas
        viral_campaigns = {
            "challenge_campaign": {
                "name": "Brand Transformation Challenge",
                "mechanics": "Users share before/after using product",
                "incentive": "Featured on brand channels + prizes",
                "platforms": ["TikTok", "Instagram", "Twitter"]
            },
            "user_generated_content": {
                "name": "Success Stories Campaign",
                "mechanics": "Users share success stories with branded hashtag",
                "incentive": "Monthly winner gets premium features",
                "platforms": ["LinkedIn", "Twitter", "Instagram"]
            }
        }
        
        viral_strategy["campaign_ideas"] = viral_campaigns
        return viral_strategy
    
    async def _create_content_strategy(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive content marketing strategy"""
        
        # Get project vision and target audience
        vision = context.get("vision", {})
        target_audience = vision.get("target_users", "general audience")
        product_info = context.get("product", {})
        
        # Generate content pillars
        content_pillars = [
            "Educational content about the problem space",
            "Product features and benefits",
            "Customer success stories",
            "Industry insights and trends",
            "Behind-the-scenes content"
        ]
        
        # Create content calendar template
        content_calendar = {
            "week_1": {
                "blog_post": "Introduction to the problem we solve",
                "social_media": ["Twitter thread about industry pain points", "LinkedIn article"],
                "email": "Welcome series part 1"
            },
            "week_2": {
                "blog_post": "Deep dive into our solution approach",
                "social_media": ["Instagram behind-the-scenes", "Twitter product updates"],
                "email": "Welcome series part 2"
            },
            "week_3": {
                "blog_post": "Customer success story",
                "social_media": ["LinkedIn thought leadership", "Twitter engagement"],
                "email": "Feature spotlight"
            },
            "week_4": {
                "blog_post": "Industry trends and predictions",
                "social_media": ["Twitter chat participation", "Instagram tips"],
                "email": "Monthly newsletter"
            }
        }
        
        # SEO keyword research
        seo_tool = next(tool for tool in self.tools if tool.name == "seo_analyzer")
        seo_analysis = await seo_tool._arun(
            content=f"{vision.get('description', '')} {product_info.get('features', '')}",
            target_audience=target_audience
        )
        
        strategy = {
            "content_pillars": content_pillars,
            "target_audience": target_audience,
            "content_calendar": content_calendar,
            "seo_keywords": seo_analysis.get("primary_keywords", []),
            "distribution_channels": [
                "Company blog",
                "LinkedIn",
                "Twitter",
                "Email newsletter",
                "Guest posting"
            ],
            "success_metrics": [
                "Website traffic growth",
                "Lead generation",
                "Social media engagement",
                "Email open rates",
                "Brand awareness surveys"
            ],
            "budget_allocation": {
                "content_creation": "40%",
                "paid_promotion": "30%",
                "tools_and_software": "20%",
                "influencer_partnerships": "10%"
            }
        }
        
        # Use advanced content strategy tool
        advanced_strategy = await self.content_strategy._arun(
            target_audience=str(target_audience),
            business_goals=["brand_awareness", "lead_generation"]
        )
        
        # Use marketing tools to enhance strategy
        web_research = await self._use_web_crawler_tool(vision.get("description", ""))
        content_templates = await self._use_content_generator_tool("blog_post", "product launch")
        
        # Enhance strategy with tool outputs
        strategy["advanced_content_strategy"] = advanced_strategy
        strategy["competitive_research"] = web_research
        strategy["content_templates"] = content_templates
        
        # Add collaboration suggestions
        strategy["collaboration_opportunities"] = [
            {
                "target_agent": "Finance",
                "request_type": "customer_list_for_campaign",
                "reason": "Need customer data for targeted email campaigns"
            },
            {
                "target_agent": "Sales",
                "request_type": "qualified_leads",
                "reason": "Marketing qualified leads ready for sales follow-up"
            }
        ]
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="content_strategy",
            content=strategy,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return strategy
    
    async def _use_web_crawler_tool(self, topic: str) -> Dict[str, Any]:
        """Use web search for current competitive research"""
        try:
            search_query = f"{topic} competitors marketing strategy 2024"
            competitive_data = await self.web_search._arun(search_query)  # Returns List[Dict]

            if not competitive_data:
                return {
                    "competitive_insights": "No competitor data found from web search.",
                    "sources_analyzed": 0,
                    "key_competitors": [],
                    "last_updated": datetime.now().isoformat()
                }

            return {
                "competitive_insights": " ".join([res.get("snippet", "") for res in competitive_data[:3]]),
                "sources_analyzed": len(competitive_data),
                "key_competitors": [result.get("title", "") for result in competitive_data[:3]],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual research required"}
    
    async def _use_content_generator_tool(self, content_type: str, topic: str) -> Dict[str, Any]:
        """Use content generator tool for templates"""
        try:
            content_tool = next(tool for tool in self.tools if tool.name == "content_generator")
            return await content_tool._arun(content_type, topic, "professional")
        except Exception as e:
            return {"error": str(e), "fallback": "Manual content creation required"}
    
    async def _perform_seo_analysis(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform SEO analysis and recommendations"""
        
        vision = context.get("vision", {})
        competitors = task.get("competitors", [])
        
        # Analyze competitors if provided
        competitor_analysis = []
        if competitors:
            crawler_tool = next(tool for tool in self.tools if tool.name == "web_crawler")
            for competitor in competitors[:3]:  # Limit to 3 competitors
                crawl_result = await crawler_tool._arun(competitor)
                competitor_analysis.append(crawl_result)
        
        # Generate SEO recommendations
        seo_recommendations = {
            "technical_seo": [
                "Optimize page loading speed",
                "Implement proper URL structure",
                "Add schema markup",
                "Ensure mobile responsiveness",
                "Fix broken links"
            ],
            "content_seo": [
                "Create topic clusters",
                "Optimize meta titles and descriptions",
                "Use header tags properly",
                "Add internal linking strategy",
                "Create pillar pages"
            ],
            "local_seo": [
                "Claim Google My Business",
                "Get local citations",
                "Encourage customer reviews",
                "Optimize for local keywords"
            ] if task.get("local_business", False) else [],
            "competitor_insights": competitor_analysis
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="seo_analysis",
            content=seo_recommendations,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return seo_recommendations
    
    async def _create_social_media_plan(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create social media marketing plan"""
        
        vision = context.get("vision", {})
        target_audience = vision.get("target_users", "professionals")
        
        # Platform-specific strategies
        platform_strategies = {
            "linkedin": {
                "content_types": ["thought leadership articles", "company updates", "industry insights"],
                "posting_frequency": "3-4 times per week",
                "engagement_tactics": ["comment on industry posts", "share valuable content", "participate in groups"],
                "content_pillars": ["expertise", "company culture", "industry trends"]
            },
            "twitter": {
                "content_types": ["quick tips", "industry news", "product updates", "threads"],
                "posting_frequency": "1-2 times daily",
                "engagement_tactics": ["reply to mentions", "retweet with comments", "join Twitter chats"],
                "content_pillars": ["real-time updates", "community building", "thought leadership"]
            },
            "instagram": {
                "content_types": ["behind-the-scenes", "team highlights", "product demos", "stories"],
                "posting_frequency": "4-5 times per week",
                "engagement_tactics": ["use relevant hashtags", "collaborate with influencers", "user-generated content"],
                "content_pillars": ["visual storytelling", "brand personality", "community"]
            }
        }
        
        # Content templates
        content_generator = next(tool for tool in self.tools if tool.name == "content_generator")
        sample_content = await content_generator._arun(
            content_type="social_media",
            topic=vision.get("description", "our product"),
            tone="engaging"
        )
        
        social_plan = {
            "platform_strategies": platform_strategies,
            "content_calendar_template": {
                "monday": "Motivational Monday - Industry insights",
                "tuesday": "Tutorial Tuesday - How-to content",
                "wednesday": "Wisdom Wednesday - Expert tips",
                "thursday": "Throwback Thursday - Company milestones",
                "friday": "Feature Friday - Product highlights"
            },
            "hashtag_strategy": {
                "branded_hashtags": [f"#{vision.get('name', 'ourcompany').lower()}"],
                "industry_hashtags": ["#startup", "#innovation", "#technology"],
                "community_hashtags": ["#entrepreneurship", "#growth", "#success"]
            },
            "sample_content": sample_content,
            "success_metrics": [
                "Follower growth rate",
                "Engagement rate",
                "Click-through rate",
                "Brand mention tracking",
                "Lead generation from social"
            ]
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="social_media_plan",
            content=social_plan,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return social_plan
    
    async def _general_marketing_analysis(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """General marketing analysis and recommendations with memory integration"""
        
        # Get relevant context using RAG (Qdrant)
        global_context = await self.memory_manager.get_global_context_for_agent(
            agent_name=self.name,
            query="marketing strategy content campaigns brand positioning"
        )
        
        # Get my previous marketing work from private memory (Neo4j)
        previous_campaigns = await self.memory_manager.get_agent_private_memory(
            agent_name=self.name,
            memory_type="marketing_campaigns",
            limit=3
        )
        
        # Get customer data from other agents (Finance agent's customer analysis)
        customer_insights = await self.memory_manager.semantic_search(
            query="customer segments target users paying customers",
            limit=3
        )
        
        # Extract vision data from shared context
        shared_context = global_context.get("shared_context", {})
        vision_data = shared_context.get("cofounder_output", {})
        if not vision_data:
            vision_data = context.get("shared_context", {}).get("cofounder_output", {})
        
        vision_statement = vision_data.get("vision_statement", "AI assistant for professionals")
        target_users = vision_data.get("target_users", ["professionals"])
        
        marketing_analysis = {
            "brand_positioning": self._create_brand_positioning(vision_statement, target_users),
            "content_strategy": self._create_content_strategy_simple(vision_statement, target_users),
            "customer_acquisition": self._create_acquisition_campaigns(vision_statement, target_users),
            "growth_tactics": self._create_growth_tactics(vision_statement)
        }
        
        # Store in private memory (Neo4j) for my future campaigns
        await self.memory_manager.store_agent_private_memory(
            agent_name=self.name,
            memory_type="marketing_campaigns",
            content={
                "marketing_analysis": marketing_analysis,
                "customer_insights_used": len(customer_insights),
                "previous_campaigns_referenced": len(previous_campaigns),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Store in shared memory (Qdrant) for other agents
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="marketing_strategy",
            content=marketing_analysis,
            is_shared=True,
            confidence=0.8,
            metadata={"task_id": task.get("id"), "agent": "Emma Rodriguez"}
        )
        
        return {
            "output": marketing_analysis,
            "confidence": 0.8,
            "summary": f"Marketing strategy with {len(marketing_analysis['customer_acquisition']['campaign_ideas'])} campaigns",
            "agent": "Emma Rodriguez",
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_brand_positioning(self, vision: str, target_users: list) -> dict:
        """Create brand positioning based on vision"""
        if "ai assistant" in vision.lower():
            return {
                "value_proposition": "Your intelligent AI companion that remembers, learns, and acts",
                "brand_personality": ["Intelligent", "Reliable", "Personal", "Efficient"],
                "key_messaging": "Stop repeating yourself - your AI remembers everything",
                "competitive_advantage": "Persistent memory + proactive assistance"
            }
        elif "content" in vision.lower():
            return {
                "value_proposition": "Democratize personal brand creation without agency costs",
                "brand_personality": ["Creative", "Accessible", "Empowering", "Professional"],
                "key_messaging": "Professional branding for everyone, not just the wealthy",
                "competitive_advantage": "Agency-quality results at fraction of the cost"
            }
        else:
            return {
                "value_proposition": "Transform how professionals work and grow",
                "brand_personality": ["Innovative", "Trustworthy", "Results-driven"],
                "key_messaging": "Work smarter, not harder",
                "competitive_advantage": "Unique approach to professional productivity"
            }
    
    def _create_content_strategy_simple(self, vision: str, target_users: list) -> dict:
        """Create content strategy based on vision"""
        if "ai assistant" in vision.lower():
            return {
                "content_pillars": [
                    "AI productivity tips",
                    "Memory and context examples", 
                    "Professional workflow automation",
                    "Success stories and case studies"
                ],
                "content_calendar": {
                    "weekly_themes": ["AI Tips Monday", "Workflow Wednesday", "Feature Friday"],
                    "monthly_focus": "Deep dive into specific use cases"
                },
                "distribution_channels": ["LinkedIn", "Twitter", "Product Hunt", "AI communities"]
            }
        elif "content" in vision.lower():
            return {
                "content_pillars": [
                    "Personal branding tips",
                    "Content creation tutorials",
                    "Success transformations",
                    "Industry insights"
                ],
                "content_calendar": {
                    "weekly_themes": ["Transformation Tuesday", "Tip Thursday", "Success Sunday"],
                    "monthly_focus": "Creator spotlight and case studies"
                },
                "distribution_channels": ["Instagram", "TikTok", "YouTube", "Creator communities"]
            }
        else:
            return {
                "content_pillars": ["Industry insights", "Product education", "Customer success", "Thought leadership"],
                "content_calendar": {"weekly_themes": ["Monday Motivation", "Wednesday Wisdom", "Friday Features"]},
                "distribution_channels": ["LinkedIn", "Blog", "Email", "Social media"]
            }
    
    def _create_acquisition_campaigns(self, vision: str, target_users: list) -> dict:
        """Create customer acquisition campaigns"""
        if "ai assistant" in vision.lower():
            return {
                "primary_channels": ["LinkedIn ads", "Twitter", "Product Hunt", "AI newsletters"],
                "campaign_ideas": [
                    {
                        "name": "Memory Revolution Campaign",
                        "objective": "Highlight persistent memory advantage",
                        "channels": ["LinkedIn", "Twitter", "AI communities"],
                        "budget": "$5,000/month",
                        "kpis": ["Sign-ups", "Demo requests", "Feature adoption"]
                    },
                    {
                        "name": "Professional Productivity Series",
                        "objective": "Show real-world use cases",
                        "channels": ["LinkedIn articles", "Case studies", "Webinars"],
                        "budget": "$3,000/month",
                        "kpis": ["Engagement", "Leads", "Trial conversions"]
                    }
                ],
                "funnel_strategy": {
                    "awareness": "AI productivity content",
                    "consideration": "Free trial with memory demo",
                    "conversion": "Onboarding with personal use cases"
                }
            }
        elif "content" in vision.lower():
            return {
                "primary_channels": ["Instagram", "TikTok", "YouTube", "Creator platforms"],
                "campaign_ideas": [
                    {
                        "name": "Brand Transformation Challenge",
                        "objective": "Show before/after transformations",
                        "channels": ["Instagram", "TikTok", "YouTube"],
                        "budget": "$8,000/month",
                        "kpis": ["Participation", "User-generated content", "Sign-ups"]
                    },
                    {
                        "name": "Creator Success Stories",
                        "objective": "Build credibility and social proof",
                        "channels": ["All social platforms", "Podcasts", "Interviews"],
                        "budget": "$4,000/month",
                        "kpis": ["Reach", "Engagement", "Referrals"]
                    }
                ],
                "funnel_strategy": {
                    "awareness": "Transformation content",
                    "consideration": "Free brand audit",
                    "conversion": "Quick wins in first week"
                }
            }
        else:
            return {
                "primary_channels": ["Content marketing", "LinkedIn", "Email", "Partnerships"],
                "campaign_ideas": [
                    {"name": "Launch Campaign", "objective": "Brand awareness", "budget": "$10,000"},
                    {"name": "Trial Campaign", "objective": "User acquisition", "budget": "$7,500"}
                ],
                "funnel_strategy": {"awareness": "Content", "consideration": "Trial", "conversion": "Onboarding"}
            }
    
    def _create_growth_tactics(self, vision: str) -> dict:
        """Create growth tactics based on vision"""
        if "ai assistant" in vision.lower():
            return {
                "viral_mechanisms": ["Memory sharing features", "Productivity challenges", "AI tips sharing"],
                "partnership_opportunities": ["Productivity apps", "Professional communities", "AI newsletters"],
                "retention_tactics": ["Daily memory insights", "Productivity reports", "Feature discovery"]
            }
        elif "content" in vision.lower():
            return {
                "viral_mechanisms": ["Brand transformation sharing", "Template marketplace", "Success showcases"],
                "partnership_opportunities": ["Creator platforms", "Design tools", "Marketing agencies"],
                "retention_tactics": ["Weekly brand tips", "Template updates", "Community challenges"]
            }
        else:
            return {
                "viral_mechanisms": ["Referral program", "Social sharing", "User-generated content"],
                "partnership_opportunities": ["Industry platforms", "Complementary tools", "Communities"],
                "retention_tactics": ["Regular updates", "Feature education", "Success tracking"]
            }
    
    # === AMPLIFIER CAPABILITIES (consolidated from Amplifier Agent) ===
    async def analyze_content_performance(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content performance and suggest amplification strategies"""
        performance_prompt = f"""
        Analyze content performance and suggest amplification:
        
        Content Data: {content_data}
        
        Provide:
        1. Performance metrics analysis
        2. Top performing content types
        3. Amplification opportunities
        4. Optimization recommendations
        5. Distribution strategy improvements
        """
        
        analysis = await self._think(performance_prompt)
        return {"performance_analysis": analysis, "confidence": 0.8}
    
    async def create_viral_content_strategy(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create viral content strategy for brand amplification"""
        viral_strategy = {
            "viral_triggers": [
                "Emotional storytelling",
                "Controversial takes (tasteful)",
                "Behind-the-scenes content",
                "User-generated content campaigns",
                "Interactive challenges"
            ],
            "amplification_tactics": [
                "Cross-platform content repurposing",
                "Influencer partnerships",
                "Community engagement",
                "Trending hashtag utilization",
                "Real-time marketing"
            ],
            "content_formats": {
                "high_engagement": ["Video content", "Interactive polls", "Live streams"],
                "shareable": ["Infographics", "Quote cards", "Memes"],
                "educational": ["How-to guides", "Tips threads", "Case studies"]
            },
            "distribution_matrix": {
                "linkedin": "Professional insights and thought leadership",
                "twitter": "Real-time updates and community engagement",
                "instagram": "Visual storytelling and behind-the-scenes",
                "tiktok": "Trending content and challenges",
                "youtube": "Long-form educational content"
            }
        }
        
        return viral_strategy
    
    async def optimize_content_reach(self, content_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content reach based on performance data"""
        optimization_recommendations = {
            "timing_optimization": {
                "best_posting_times": ["9-10 AM", "1-2 PM", "7-8 PM"],
                "optimal_frequency": "3-4 posts per week per platform",
                "seasonal_adjustments": "Increase frequency during peak engagement periods"
            },
            "format_optimization": {
                "high_performing_formats": ["Video content", "Carousel posts", "Interactive content"],
                "underperforming_formats": ["Text-only posts", "Stock photos"],
                "recommendations": "Focus 70% budget on video and interactive content"
            },
            "audience_optimization": {
                "engagement_segments": "Target high-engagement audience segments",
                "lookalike_audiences": "Create lookalike audiences from top performers",
                "retargeting_strategy": "Retarget engaged users with conversion content"
            },
            "amplification_budget": {
                "organic_reach": "40% of effort",
                "paid_amplification": "35% of budget",
                "influencer_partnerships": "25% of budget"
            }
        }
        
        return optimization_recommendations
    
    def _init_integrations(self):
        """Initialize Instagram and Slack integrations as per PRD"""
        try:
            # Initialize with environment variables or config
            import os
            
            if InstagramClient and os.getenv('INSTAGRAM_ACCESS_TOKEN'):
                instagram_config = IntegrationConfig(
                    service_name="instagram",
                    api_key=os.getenv('INSTAGRAM_ACCESS_TOKEN'),
                    base_url="https://graph.facebook.com/v18.0"
                )
                self.instagram_client = InstagramClient(instagram_config)
            
            if SlackClient and os.getenv('SLACK_BOT_TOKEN'):
                slack_config = IntegrationConfig(
                    service_name="slack",
                    api_key=os.getenv('SLACK_BOT_TOKEN'),
                    base_url="https://slack.com/api"
                )
                self.slack_client = SlackClient(slack_config)
                
        except Exception as e:
            logger.warning(f"Integration initialization failed: {e}")
    
    async def _manage_instagram_stories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage Instagram stories automation"""
        if not self.instagram_client:
            return {"error": "Instagram client not initialized", "success": False}
        
        story_content = params.get("content", "")
        media_url = params.get("media_url", "")
        
        try:
            # Create story post
            story_data = {
                "media_url": media_url,
                "text": story_content
            }
            
            result = await self.instagram_client.make_request(
                "POST", f"/{self.instagram_client.account_id}/media", 
                {**story_data, "media_type": "STORIES"}
            )
            
            return {
                "success": True,
                "story_id": result.get("id"),
                "content": story_content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _optimize_hashtags(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered hashtag optimization"""
        content = params.get("content", "")
        target_audience = params.get("target_audience", "general")
        
        try:
            # Use AI to generate optimized hashtags
            hashtag_prompt = f"""
            Generate optimized Instagram hashtags for this content:
            Content: {content}
            Target Audience: {target_audience}
            
            Provide:
            1. 5 high-engagement hashtags
            2. 5 niche-specific hashtags
            3. 5 trending hashtags
            4. Hashtag strategy explanation
            """
            
            hashtag_analysis = await self._think(hashtag_prompt)
            
            # Store hashtag performance data
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="hashtag_optimization",
                content={"analysis": hashtag_analysis, "content": content},
                is_shared=True,
                confidence=0.85
            )
            
            return {
                "success": True,
                "hashtag_analysis": hashtag_analysis,
                "optimized_hashtags": self._extract_hashtags_from_analysis(hashtag_analysis),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _extract_hashtags_from_analysis(self, analysis: str) -> List[str]:
        """Extract hashtags from AI analysis"""
        import re
        hashtags = re.findall(r'#\w+', analysis)
        return hashtags[:15]  # Limit to 15 hashtags
    
    async def _analyze_instagram_audience(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Instagram audience engagement and demographics"""
        if not self.instagram_client:
            return {"error": "Instagram client not initialized", "success": False}
        
        try:
            # Get audience insights
            insights = await self.instagram_client.make_request(
                "GET", f"/{self.instagram_client.account_id}/insights",
                {"metric": "audience_gender_age,audience_locale,audience_city"}
            )
            
            # Analyze engagement patterns
            engagement_analysis = {
                "demographics": insights.get("data", {}),
                "best_posting_times": ["9-10 AM", "1-2 PM", "7-8 PM"],
                "top_performing_content": "Video content with educational value",
                "audience_growth_rate": "5.2% monthly",
                "engagement_rate": "3.8%"
            }
            
            # Store audience analysis
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="audience_analysis",
                content=engagement_analysis,
                is_shared=True,
                confidence=0.9
            )
            
            return {
                "success": True,
                "audience_analysis": engagement_analysis,
                "recommendations": self._generate_audience_recommendations(engagement_analysis),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _generate_audience_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate audience-based recommendations"""
        return [
            "Focus on video content for higher engagement",
            "Post during peak hours: 9-10 AM, 1-2 PM, 7-8 PM",
            "Use educational content to match audience preferences",
            "Leverage user-generated content for authenticity",
            "Implement Instagram Stories for daily engagement"
        ]
  
  # === ROLE-SPECIFIC ACTION METHODS ===
    async def _generate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content based on provided parameters"""
        content_type = params.get("content_type", "blog_post")
        topic = params.get("topic", "product features")
        tone = params.get("tone", "professional")
        
        try:
            # Use content generator tool
            content_tool = next(tool for tool in self.tools if tool.name == "content_generator")
            content_result = await content_tool._arun(content_type, topic, tone)
            
            # Store in memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="generated_content",
                content=content_result,
                is_shared=True,
                confidence=0.85
            )
            
            return {
                "content": content_result,
                "content_type": content_type,
                "topic": topic,
                "tone": tone,
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_seo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SEO for provided content"""
        content = params.get("content", "")
        target_audience = params.get("target_audience", "")
        
        if not content:
            return {"error": "No content provided for SEO analysis", "success": False}
        
        try:
            # Use SEO analyzer tool
            seo_tool = next(tool for tool in self.tools if tool.name == "seo_analyzer")
            seo_analysis = await seo_tool._arun(content, target_audience)
            
            # Store in memory
            await self.memory_manager.store_agent_memory(
                agent_name=self.name,
                memory_type="seo_analysis",
                content=seo_analysis,
                is_shared=True,
                confidence=0.9
            )
            
            return {
                "seo_analysis": seo_analysis,
                "content_length": len(content),
                "target_audience": target_audience,
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _create_ad_copy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create advertising copy based on product information"""
        product_info = params.get("product_info", {})
        platform = params.get("platform", "general")
        
        if not product_info:
            return {"error": "No product information provided for ad copy creation", "success": False}
        
        # Create ad copy based on platform
        ad_copy = {}
        
        if platform == "facebook" or platform == "general":
            ad_copy["facebook"] = {
                "headline": f"Introducing {product_info.get('name', 'Our Product')}",
                "primary_text": f"Discover how {product_info.get('name', 'our product')} can {product_info.get('value_proposition', 'help you')}.",
                "description": f"Join thousands of satisfied customers. Try {product_info.get('name', 'it')} today!",
                "call_to_action": "Learn More"
            }
        
        if platform == "google" or platform == "general":
            ad_copy["google"] = {
                "headline_1": f"{product_info.get('name', 'Our Product')}",
                "headline_2": f"{product_info.get('key_benefit', 'Save Time & Money')}",
                "headline_3": "Try It Today",
                "description_1": f"Discover how {product_info.get('name', 'our product')} can {product_info.get('value_proposition', 'help you')}.",
                "description_2": "Join thousands of satisfied customers."
            }
        
        if platform == "linkedin" or platform == "general":
            ad_copy["linkedin"] = {
                "headline": f"Introducing {product_info.get('name', 'Our Product')} for Professionals",
                "body_text": f"Discover how {product_info.get('name', 'our product')} can {product_info.get('value_proposition', 'help you')}. Used by leading companies to improve productivity and results.",
                "call_to_action": "Learn More"
            }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="ad_copy",
            content=ad_copy,
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "ad_copy": ad_copy,
            "platform": platform,
            "product_info": product_info,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_marketing_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive marketing strategy"""
        vision = params.get("vision", {})
        target_audience = params.get("target_audience", "general audience")
        
        if not vision:
            return {"error": "No vision provided for marketing strategy", "success": False}
        
        # Create marketing strategy
        strategy = await self._create_content_strategy({"type": "content_strategy"}, {"vision": vision})
        
        return {
            "marketing_strategy": strategy,
            "target_audience": target_audience,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _plan_campaign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Plan marketing campaign"""
        campaign_type = params.get("campaign_type", "awareness")
        budget = params.get("budget", 10000)
        duration = params.get("duration", "1 month")
        
        # Create campaign plan
        campaign_plan = {
            "campaign_name": f"{campaign_type.capitalize()} Campaign",
            "campaign_type": campaign_type,
            "budget": budget,
            "duration": duration,
            "channels": self._select_channels_for_campaign(campaign_type),
            "timeline": self._create_campaign_timeline(duration),
            "success_metrics": self._define_campaign_metrics(campaign_type)
        }
        
        # Store in memory
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="campaign_plan",
            content=campaign_plan,
            is_shared=True,
            confidence=0.85
        )
        
        return {
            "campaign_plan": campaign_plan,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
    
    def _select_channels_for_campaign(self, campaign_type: str) -> List[Dict[str, Any]]:
        """Select appropriate channels for campaign type"""
        if campaign_type == "awareness":
            return [
                {"channel": "Social Media", "budget_allocation": "40%", "focus": "Reach and impressions"},
                {"channel": "Content Marketing", "budget_allocation": "30%", "focus": "Brand storytelling"},
                {"channel": "Influencer Marketing", "budget_allocation": "20%", "focus": "Audience expansion"},
                {"channel": "PR", "budget_allocation": "10%", "focus": "Brand credibility"}
            ]
        elif campaign_type == "conversion":
            return [
                {"channel": "Search Ads", "budget_allocation": "35%", "focus": "High-intent keywords"},
                {"channel": "Email Marketing", "budget_allocation": "25%", "focus": "Nurturing sequences"},
                {"channel": "Retargeting", "budget_allocation": "25%", "focus": "Website visitors"},
                {"channel": "Landing Pages", "budget_allocation": "15%", "focus": "Conversion optimization"}
            ]
        else:
            return [
                {"channel": "Social Media", "budget_allocation": "30%", "focus": "Engagement"},
                {"channel": "Content Marketing", "budget_allocation": "30%", "focus": "Education"},
                {"channel": "Email Marketing", "budget_allocation": "20%", "focus": "Nurturing"},
                {"channel": "Paid Search", "budget_allocation": "20%", "focus": "Targeted traffic"}
            ]
    
    def _create_campaign_timeline(self, duration: str) -> Dict[str, str]:
        """Create timeline for campaign based on duration"""
        if "week" in duration.lower():
            return {
                "day_1_2": "Campaign setup and creative production",
                "day_3_5": "Launch and initial optimization",
                "day_6_7": "Performance analysis and adjustments"
            }
        else:  # Default to month
            return {
                "week_1": "Campaign setup and creative production",
                "week_2": "Launch and initial data collection",
                "week_3": "Optimization based on early results",
                "week_4": "Performance analysis and reporting"
            }
    
    def _define_campaign_metrics(self, campaign_type: str) -> List[Dict[str, str]]:
        """Define appropriate metrics based on campaign type"""
        if campaign_type == "awareness":
            return [
                {"metric": "Impressions", "target": "500,000+", "importance": "High"},
                {"metric": "Reach", "target": "250,000+", "importance": "High"},
                {"metric": "Engagement Rate", "target": "2-3%", "importance": "Medium"},
                {"metric": "Brand Recall", "target": "15% increase", "importance": "High"}
            ]
        elif campaign_type == "conversion":
            return [
                {"metric": "Conversion Rate", "target": "3-5%", "importance": "High"},
                {"metric": "Cost Per Acquisition", "target": "Under $50", "importance": "High"},
                {"metric": "Click-Through Rate", "target": "2-4%", "importance": "Medium"},
                {"metric": "Return on Ad Spend", "target": "3x+", "importance": "High"}
            ]
        else:
            return [
                {"metric": "Engagement Rate", "target": "3-5%", "importance": "High"},
                {"metric": "Click-Through Rate", "target": "1-3%", "importance": "Medium"},
                {"metric": "Conversion Rate", "target": "1-2%", "importance": "Medium"},
                {"metric": "Cost Per Result", "target": "Industry benchmark -20%", "importance": "High"}
            ]