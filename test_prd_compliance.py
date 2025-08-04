#!/usr/bin/env python3
"""
PRD Compliance Test Suite
Tests implementation against PRD specifications for Instagram and Slack integrations
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all PRD-specified components can be imported"""
    print("🧪 Testing PRD Component Imports...")
    
    try:
        # Core PRD components
        from agents.marketing_agent import MarketingAgent
        from integrations.instagram_client import InstagramClient, InstagramPost
        from integrations.slack_client import SlackClient, SlackNotification
        from integrations.base_integration import BaseIntegration, IntegrationConfig
        from communication.event_bus import event_bus, send_marketing_slack_notification
        from agents.instagram_marketing_extension import InstagramMarketingMixin
        
        print("✅ All PRD components imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_marketing_agent_prd_compliance():
    """Test Marketing Agent compliance with PRD specifications"""
    print("🧪 Testing Marketing Agent PRD Compliance...")
    
    try:
        from agents.marketing_agent import MarketingAgent
        from memory.memory_manager import MemoryManager
        from approvals.approval_manager import ApprovalManager
        
        # Mock memory and approval managers
        class MockMemoryManager:
            async def store_agent_memory(self, **kwargs):
                return {"success": True}
            async def get_agent_private_memory(self, **kwargs):
                return []
            async def semantic_search(self, **kwargs):
                return []
            async def get_global_context_for_agent(self, **kwargs):
                return {"shared_context": {}}
        
        class MockApprovalManager:
            async def request_approval(self, **kwargs):
                return {"approved": True}
        
        # Initialize Marketing Agent
        memory_manager = MockMemoryManager()
        approval_manager = MockApprovalManager()
        
        agent = MarketingAgent(memory_manager, approval_manager)
        
        # Test PRD-specified capabilities
        prd_capabilities = [
            "content marketing", "SEO", "social media", "analytics",
            "brand amplification", "content performance", "viral marketing", "influencer outreach"
        ]
        
        agent_expertise = agent.personality.get("expertise", [])
        
        # Check if agent has PRD-specified expertise
        has_required_expertise = all(
            any(capability.lower() in expertise.lower() for expertise in agent_expertise)
            for capability in ["content", "social media", "analytics"]
        )
        
        # Test Instagram automation features
        has_instagram_features = hasattr(agent, 'instagram_automation_features')
        
        # Test role actions
        required_actions = [
            "instagram_posting", "instagram_dm_automation", 
            "hashtag_optimization", "audience_analysis", "slack_notification"
        ]
        
        has_required_actions = all(action in agent.role_actions for action in required_actions)
        
        if has_required_expertise and has_instagram_features and has_required_actions:
            print("✅ Marketing Agent meets PRD specifications")
            print(f"   - Expertise areas: {len(agent_expertise)}")
            print(f"   - Instagram features: {agent.instagram_automation_features}")
            print(f"   - Role actions: {len(agent.role_actions)}")
            return True
        else:
            print("❌ Marketing Agent missing PRD requirements")
            print(f"   - Has expertise: {has_required_expertise}")
            print(f"   - Has Instagram features: {has_instagram_features}")
            print(f"   - Has required actions: {has_required_actions}")
            return False
            
    except Exception as e:
        print(f"❌ Marketing Agent test failed: {e}")
        return False

def test_instagram_integration_prd_compliance():
    """Test Instagram integration compliance with PRD"""
    print("🧪 Testing Instagram Integration PRD Compliance...")
    
    try:
        from integrations.instagram_client import InstagramClient, InstagramPost
        from integrations.base_integration import IntegrationConfig
        
        # Test InstagramPost model has PRD-specified fields
        post_fields = InstagramPost.__fields__.keys()
        required_fields = ["content", "media_urls", "hashtags"]
        
        has_required_fields = all(field in post_fields for field in required_fields)
        
        # Test InstagramClient has PRD-specified methods
        client_methods = [method for method in dir(InstagramClient) if not method.startswith('_')]
        required_methods = [
            "create_post", "schedule_post", "get_dm_conversations", 
            "send_dm_response", "get_post_analytics", "authenticate", "health_check"
        ]
        
        has_required_methods = all(method in client_methods for method in required_methods)
        
        if has_required_fields and has_required_methods:
            print("✅ Instagram integration meets PRD specifications")
            print(f"   - Post fields: {list(post_fields)}")
            print(f"   - Client methods: {len(client_methods)}")
            return True
        else:
            print("❌ Instagram integration missing PRD requirements")
            print(f"   - Has required fields: {has_required_fields}")
            print(f"   - Has required methods: {has_required_methods}")
            return False
            
    except Exception as e:
        print(f"❌ Instagram integration test failed: {e}")
        return False

def test_slack_integration_prd_compliance():
    """Test Slack integration compliance with PRD"""
    print("🧪 Testing Slack Integration PRD Compliance...")
    
    try:
        from integrations.slack_client import SlackClient, SlackMessage, SlackNotification
        
        # Test SlackNotification model has PRD-specified fields
        notification_fields = SlackNotification.__fields__.keys()
        required_fields = ["agent_name", "event_type", "message", "priority"]
        
        has_required_fields = all(field in notification_fields for field in required_fields)
        
        # Test SlackClient has PRD-specified methods
        client_methods = [method for method in dir(SlackClient) if not method.startswith('_')]
        required_methods = [
            "send_message", "send_agent_notification", "send_workflow_update",
            "send_approval_request", "create_project_channel", "authenticate", "health_check"
        ]
        
        has_required_methods = all(method in client_methods for method in required_methods)
        
        if has_required_fields and has_required_methods:
            print("✅ Slack integration meets PRD specifications")
            print(f"   - Notification fields: {list(notification_fields)}")
            print(f"   - Client methods: {len(client_methods)}")
            return True
        else:
            print("❌ Slack integration missing PRD requirements")
            print(f"   - Has required fields: {has_required_fields}")
            print(f"   - Has required methods: {has_required_methods}")
            return False
            
    except Exception as e:
        print(f"❌ Slack integration test failed: {e}")
        return False

def test_event_bus_prd_compliance():
    """Test Event Bus compliance with PRD"""
    print("🧪 Testing Event Bus PRD Compliance...")
    
    try:
        from communication.event_bus import (
            event_bus, send_slack_notification_via_event_bus,
            send_marketing_slack_notification, send_instagram_automation_notification
        )
        
        # Test event bus has PRD-specified methods
        bus_methods = [method for method in dir(event_bus) if not method.startswith('_')]
        required_methods = [
            "publish", "subscribe", "subscribe_to_topic", "publish_to_topic",
            "send_interrupt", "request_agent_collaboration", "broadcast_update"
        ]
        
        has_required_methods = all(method in bus_methods for method in required_methods)
        
        # Test Slack notification helpers exist
        slack_helpers = [
            send_slack_notification_via_event_bus,
            send_marketing_slack_notification,
            send_instagram_automation_notification
        ]
        
        has_slack_helpers = all(helper is not None for helper in slack_helpers)
        
        if has_required_methods and has_slack_helpers:
            print("✅ Event Bus meets PRD specifications")
            print(f"   - Bus methods: {len(bus_methods)}")
            print(f"   - Slack helpers: {len(slack_helpers)}")
            return True
        else:
            print("❌ Event Bus missing PRD requirements")
            print(f"   - Has required methods: {has_required_methods}")
            print(f"   - Has Slack helpers: {has_slack_helpers}")
            return False
            
    except Exception as e:
        print(f"❌ Event Bus test failed: {e}")
        return False

def test_api_endpoints_prd_compliance():
    """Test API endpoints compliance with PRD"""
    print("🧪 Testing API Endpoints PRD Compliance...")
    
    try:
        from api.integrations_api import router
        
        # Get all routes from the router
        routes = [route.path for route in router.routes]
        
        # PRD-specified endpoints
        required_endpoints = [
            "/api/integrations/instagram/post",
            "/api/integrations/instagram/dms", 
            "/api/integrations/slack/notify",
            "/api/integrations/status"
        ]
        
        # Check if required endpoints exist (accounting for prefix)
        has_required_endpoints = all(
            any(endpoint.replace("/api/integrations", "") in route for route in routes)
            for endpoint in required_endpoints
        )
        
        if has_required_endpoints:
            print("✅ API endpoints meet PRD specifications")
            print(f"   - Available routes: {routes}")
            return True
        else:
            print("❌ API endpoints missing PRD requirements")
            print(f"   - Available routes: {routes}")
            print(f"   - Required endpoints: {required_endpoints}")
            return False
            
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

async def test_integration_workflow():
    """Test complete integration workflow as per PRD"""
    print("🧪 Testing Complete Integration Workflow...")
    
    try:
        from agents.instagram_marketing_extension import InstagramMarketingMixin
        from communication.event_bus import send_marketing_slack_notification
        
        # Mock agent with mixin
        class MockMarketingAgent(InstagramMarketingMixin):
            def __init__(self):
                self.name = "Marketing Intelligence"
                self.memory_manager = MockMemoryManager()
                self.instagram_client = None
                self.slack_client = None
                
            async def _think(self, prompt):
                return "Mock AI response with hashtags #test #marketing #ai"
        
        class MockMemoryManager:
            async def store_agent_memory(self, **kwargs):
                return {"success": True}
        
        agent = MockMarketingAgent()
        
        # Test Instagram post creation workflow
        post_params = {
            "content": "Test post content for PRD compliance",
            "media_urls": ["https://example.com/image.jpg"],
            "hashtags": ["#test", "#prd", "#compliance"]
        }
        
        # This would normally create a post, but we're testing the workflow structure
        result = await agent.create_instagram_post(post_params)
        
        # Test Slack notification workflow
        await send_marketing_slack_notification(
            event_type="test_workflow",
            message="PRD compliance test completed"
        )
        
        print("✅ Integration workflow structure is PRD compliant")
        print(f"   - Post creation workflow: {result.get('success', False)}")
        print("   - Slack notification workflow: Completed")
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow test failed: {e}")
        return False

def main():
    """Run all PRD compliance tests"""
    print("🚀 Starting PRD Compliance Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_marketing_agent_prd_compliance,
        test_instagram_integration_prd_compliance,
        test_slack_integration_prd_compliance,
        test_event_bus_prd_compliance,
        test_api_endpoints_prd_compliance,
    ]
    
    async_tests = [
        test_integration_workflow
    ]
    
    results = []
    
    # Run synchronous tests
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    # Run asynchronous tests
    for test in async_tests:
        try:
            result = asyncio.run(test())
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 PRD Compliance Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is PRD compliant.")
        return 0
    else:
        print("⚠️  Some tests failed. Review implementation against PRD.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)