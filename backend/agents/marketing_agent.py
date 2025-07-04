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
    """Marketing Agent responsible for content strategy and SEO"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "creative and data-driven",
            "focus": "brand awareness and lead generation",
            "expertise": ["content marketing", "SEO", "social media", "analytics"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.7,
            "confidence_threshold": 0.6,
            "description": "Plans content strategy, SEO optimization, and social media campaigns"
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
        else:
            return await self._general_marketing_analysis(task, context)
    
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
        """General marketing analysis and recommendations"""
        
        vision_data = context.get("cofounder_output", {})
        if not vision_data:
            shared_context = await self.memory_manager.get_shared_context()
            vision_data = shared_context.get("cofounder_output", [{}])[0].get("content", {})
        
        vision_statement = vision_data.get("vision_statement", "AI assistant for professionals")
        target_users = vision_data.get("target_users", ["professionals"])
        
        marketing_analysis = {
            "brand_positioning": self._create_brand_positioning(vision_statement, target_users),
            "content_strategy": self._create_content_strategy_simple(vision_statement, target_users),
            "customer_acquisition": self._create_acquisition_campaigns(vision_statement, target_users),
            "growth_tactics": self._create_growth_tactics(vision_statement)
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="marketing_analysis",
            content=marketing_analysis,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
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