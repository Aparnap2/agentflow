#!/usr/bin/env python3
"""
Test script for Instagram and Slack integrations
Tests import statements and basic functionality without external dependencies
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test all integration imports"""
    print("🧪 Testing integration imports...")
    
    try:
        # Test base integration
        from integrations.base_integration import BaseIntegration, IntegrationConfig
        print("✅ Base integration imports successful")
        
        # Test Instagram client
        from integrations.instagram_client import InstagramClient, InstagramPost, InstagramDM
        print("✅ Instagram client imports successful")
        
        # Test Slack client
        from integrations.slack_client import SlackClient, SlackMessage, SlackNotification
        print("✅ Slack client imports successful")
        
        # Test marketing agent extension
        from agents.instagram_marketing_extension import InstagramMarketingMixin
        print("✅ Marketing extension imports successful")
        
        # Test API endpoints
        from api.integrations_api import router
        print("✅ Integration API imports successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_model_creation():
    """Test Pydantic model creation"""
    print("\n🧪 Testing model creation...")
    
    try:
        from integrations.instagram_client import InstagramPost
        from integrations.slack_client import SlackNotification
        from integrations.base_integration import IntegrationConfig
        
        # Test Instagram post model
        post = InstagramPost(
            content="Test post content",
            hashtags=["test", "agentflow"],
            media_urls=["https://example.com/image.jpg"]
        )
        print("✅ Instagram post model creation successful")
        
        # Test Slack notification model
        notification = SlackNotification(
            agent_name="Marketing",
            event_type="test",
            message="Test notification"
        )
        print("✅ Slack notification model creation successful")
        
        # Test integration config
        config = IntegrationConfig(
            api_key="test_key",
            base_url="https://api.example.com"
        )
        print("✅ Integration config model creation successful")
        
        return True
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_syntax():
    """Test Python syntax of all files"""
    print("\n🧪 Testing Python syntax...")
    
    files_to_check = [
        'backend/integrations/__init__.py',
        'backend/integrations/base_integration.py',
        'backend/integrations/instagram_client.py',
        'backend/integrations/slack_client.py',
        'backend/agents/instagram_marketing_extension.py',
        'backend/api/integrations_api.py'
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"✅ {file_path} syntax OK")
        except SyntaxError as e:
            print(f"❌ {file_path} syntax error: {e}")
            return False
        except FileNotFoundError:
            print(f"⚠️  {file_path} not found")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting AgentFlow Integration Tests\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Model Creation Tests", test_model_creation),
        ("Syntax Tests", test_syntax)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Integration setup is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())