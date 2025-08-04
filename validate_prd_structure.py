#!/usr/bin/env python3
"""
PRD Structure Validation
Validates code structure and syntax compliance with PRD specifications
"""

import ast
import os
import sys
from typing import List, Dict, Any

def validate_file_syntax(filepath: str) -> Dict[str, Any]:
    """Validate Python file syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to validate syntax
        tree = ast.parse(content)
        
        # Extract classes and functions
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        return {
            "valid": True,
            "classes": classes,
            "functions": functions,
            "lines": len(content.split('\n'))
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"Syntax error: {e}",
            "line": e.lineno
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

def validate_prd_compliance():
    """Validate PRD compliance through code structure analysis"""
    print("🔍 PRD Structure Validation")
    print("=" * 50)
    
    # Files to validate based on PRD requirements
    prd_files = {
        "Marketing Agent": "backend/agents/marketing_agent.py",
        "Instagram Client": "backend/integrations/instagram_client.py", 
        "Slack Client": "backend/integrations/slack_client.py",
        "Base Integration": "backend/integrations/base_integration.py",
        "Instagram Extension": "backend/agents/instagram_marketing_extension.py",
        "Event Bus": "backend/communication/event_bus.py",
        "Integrations API": "backend/api/integrations_api.py"
    }
    
    results = {}
    
    for name, filepath in prd_files.items():
        print(f"📁 Validating {name}...")
        
        if not os.path.exists(filepath):
            results[name] = {"valid": False, "error": "File not found"}
            print(f"   ❌ File not found: {filepath}")
            continue
        
        validation = validate_file_syntax(filepath)
        results[name] = validation
        
        if validation["valid"]:
            print(f"   ✅ Syntax valid ({validation['lines']} lines)")
            print(f"      Classes: {len(validation['classes'])}, Functions: {len(validation['functions'])}")
        else:
            print(f"   ❌ {validation['error']}")
        
        print()
    
    return results

def check_prd_requirements():
    """Check specific PRD requirements in code"""
    print("🎯 Checking PRD-Specific Requirements")
    print("=" * 50)
    
    requirements_met = []
    
    # Check Marketing Agent PRD requirements
    try:
        with open("backend/agents/marketing_agent.py", 'r') as f:
            marketing_content = f.read()
        
        # PRD specifies Marketing Intelligence Agent capabilities
        marketing_requirements = [
            "instagram_posting",
            "dm_automation", 
            "hashtag_optimization",
            "audience_analysis",
            "content_generation",
            "seo_analysis"
        ]
        
        marketing_met = sum(1 for req in marketing_requirements if req in marketing_content)
        requirements_met.append(("Marketing Agent Capabilities", marketing_met, len(marketing_requirements)))
        
        print(f"📊 Marketing Agent: {marketing_met}/{len(marketing_requirements)} capabilities found")
        
    except Exception as e:
        print(f"❌ Marketing Agent check failed: {e}")
    
    # Check Instagram Integration PRD requirements
    try:
        with open("backend/integrations/instagram_client.py", 'r') as f:
            instagram_content = f.read()
        
        # PRD specifies Instagram automation features
        instagram_requirements = [
            "create_post",
            "schedule_post", 
            "get_dm_conversations",
            "send_dm_response",
            "get_post_analytics",
            "InstagramPost",
            "InstagramDM"
        ]
        
        instagram_met = sum(1 for req in instagram_requirements if req in instagram_content)
        requirements_met.append(("Instagram Integration", instagram_met, len(instagram_requirements)))
        
        print(f"📊 Instagram Integration: {instagram_met}/{len(instagram_requirements)} features found")
        
    except Exception as e:
        print(f"❌ Instagram Integration check failed: {e}")
    
    # Check Slack Integration PRD requirements
    try:
        with open("backend/integrations/slack_client.py", 'r') as f:
            slack_content = f.read()
        
        # PRD specifies Slack notification features
        slack_requirements = [
            "send_message",
            "send_agent_notification",
            "send_workflow_update", 
            "send_approval_request",
            "create_project_channel",
            "SlackMessage",
            "SlackNotification"
        ]
        
        slack_met = sum(1 for req in slack_requirements if req in slack_content)
        requirements_met.append(("Slack Integration", slack_met, len(slack_requirements)))
        
        print(f"📊 Slack Integration: {slack_met}/{len(slack_requirements)} features found")
        
    except Exception as e:
        print(f"❌ Slack Integration check failed: {e}")
    
    # Check Event Bus PRD requirements
    try:
        with open("backend/communication/event_bus.py", 'r') as f:
            eventbus_content = f.read()
        
        # PRD specifies event-driven communication
        eventbus_requirements = [
            "publish",
            "subscribe",
            "broadcast_update",
            "send_slack_notification_via_event_bus",
            "send_marketing_slack_notification",
            "AgentEvent"
        ]
        
        eventbus_met = sum(1 for req in eventbus_requirements if req in eventbus_content)
        requirements_met.append(("Event Bus", eventbus_met, len(eventbus_requirements)))
        
        print(f"📊 Event Bus: {eventbus_met}/{len(eventbus_requirements)} features found")
        
    except Exception as e:
        print(f"❌ Event Bus check failed: {e}")
    
    print()
    return requirements_met

def check_architecture_compliance():
    """Check architecture compliance with PRD"""
    print("🏗️ Architecture Compliance Check")
    print("=" * 50)
    
    architecture_checks = []
    
    # Check directory structure
    required_dirs = [
        "backend/integrations",
        "backend/agents", 
        "backend/communication",
        "backend/api",
        "backend/memory",
        "backend/workflows"
    ]
    
    dirs_exist = sum(1 for dir_path in required_dirs if os.path.exists(dir_path))
    architecture_checks.append(("Directory Structure", dirs_exist, len(required_dirs)))
    print(f"📁 Directory Structure: {dirs_exist}/{len(required_dirs)} required directories found")
    
    # Check integration files
    integration_files = [
        "backend/integrations/__init__.py",
        "backend/integrations/base_integration.py",
        "backend/integrations/instagram_client.py",
        "backend/integrations/slack_client.py"
    ]
    
    files_exist = sum(1 for file_path in integration_files if os.path.exists(file_path))
    architecture_checks.append(("Integration Files", files_exist, len(integration_files)))
    print(f"📄 Integration Files: {files_exist}/{len(integration_files)} files found")
    
    # Check API structure
    api_files = [
        "backend/api/integrations_api.py",
        "backend/main.py"
    ]
    
    api_files_exist = sum(1 for file_path in api_files if os.path.exists(file_path))
    architecture_checks.append(("API Structure", api_files_exist, len(api_files)))
    print(f"🔌 API Structure: {api_files_exist}/{len(api_files)} API files found")
    
    print()
    return architecture_checks

def main():
    """Run complete PRD validation"""
    print("🚀 AgentFlow PRD Compliance Validation")
    print("=" * 60)
    print()
    
    # Validate file syntax
    syntax_results = validate_prd_compliance()
    
    # Check PRD requirements
    requirement_results = check_prd_requirements()
    
    # Check architecture compliance
    architecture_results = check_architecture_compliance()
    
    # Summary
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    # Syntax validation summary
    valid_files = sum(1 for result in syntax_results.values() if result["valid"])
    total_files = len(syntax_results)
    print(f"✅ Syntax Validation: {valid_files}/{total_files} files valid")
    
    # Requirements summary
    total_req_met = sum(met for _, met, _ in requirement_results)
    total_req_possible = sum(total for _, _, total in requirement_results)
    print(f"🎯 PRD Requirements: {total_req_met}/{total_req_possible} requirements met ({total_req_met/total_req_possible*100:.1f}%)")
    
    # Architecture summary
    total_arch_met = sum(met for _, met, _ in architecture_results)
    total_arch_possible = sum(total for _, _, total in architecture_results)
    print(f"🏗️ Architecture Compliance: {total_arch_met}/{total_arch_possible} components found ({total_arch_met/total_arch_possible*100:.1f}%)")
    
    # Overall compliance
    overall_score = (valid_files/total_files + total_req_met/total_req_possible + total_arch_met/total_arch_possible) / 3
    print(f"🎉 Overall PRD Compliance: {overall_score*100:.1f}%")
    
    if overall_score >= 0.9:
        print("🌟 EXCELLENT: Implementation is highly PRD compliant!")
        return 0
    elif overall_score >= 0.8:
        print("✅ GOOD: Implementation meets most PRD requirements")
        return 0
    elif overall_score >= 0.7:
        print("⚠️ FAIR: Implementation needs some improvements")
        return 1
    else:
        print("❌ POOR: Implementation requires significant changes")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)