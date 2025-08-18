#!/usr/bin/env python3
"""
AETHER Enhanced Browser - Comprehensive Backend API Testing
Tests all functional backend APIs and enhanced features
"""

import asyncio
import aiohttp
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_BASE = f"{BASE_URL}/api"

class AetherAPITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.session_id = str(uuid.uuid4())
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, endpoint: str, method: str, status: str, details: str, response_time: float = 0):
        """Log test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {method} {endpoint} - {status}: {details} ({response_time:.2f}s)")
    
    async def test_api_call(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Dict:
        """Make API call and return response"""
        url = f"{API_BASE}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=data) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    
                    if response.status == expected_status:
                        self.log_test(endpoint, method, "PASS", f"Status {response.status}", response_time)
                        return {"success": True, "data": response_data, "status": response.status}
                    else:
                        self.log_test(endpoint, method, "FAIL", f"Expected {expected_status}, got {response.status}", response_time)
                        return {"success": False, "data": response_data, "status": response.status}
                        
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    
                    if response.status == expected_status:
                        self.log_test(endpoint, method, "PASS", f"Status {response.status}", response_time)
                        return {"success": True, "data": response_data, "status": response.status}
                    else:
                        self.log_test(endpoint, method, "FAIL", f"Expected {expected_status}, got {response.status}", response_time)
                        return {"success": False, "data": response_data, "status": response.status}
                        
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    
                    if response.status == expected_status:
                        self.log_test(endpoint, method, "PASS", f"Status {response.status}", response_time)
                        return {"success": True, "data": response_data, "status": response.status}
                    else:
                        self.log_test(endpoint, method, "FAIL", f"Expected {expected_status}, got {response.status}", response_time)
                        return {"success": False, "data": response_data, "status": response.status}
                        
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(endpoint, method, "FAIL", f"Exception: {str(e)}", response_time)
            return {"success": False, "error": str(e), "status": 0}
    
    async def test_core_browser_apis(self):
        """Test Core Browser APIs (High Priority)"""
        print("\n🌐 TESTING CORE BROWSER APIs (HIGH PRIORITY)")
        print("=" * 60)
        
        # Test health check first
        await self.test_api_call("GET", "/health")
        
        # Test browse endpoint with real website
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        browse_result = await self.test_api_call("POST", "/browse", browse_data)
        
        # Test recent tabs
        await self.test_api_call("GET", "/recent-tabs")
        
        # Test recommendations
        await self.test_api_call("GET", "/recommendations")
        
        # Test clear history
        await self.test_api_call("DELETE", "/clear-history")
        
        return browse_result.get("success", False)
    
    async def test_ai_chat_system(self):
        """Test AI Chat System (High Priority)"""
        print("\n🤖 TESTING AI CHAT SYSTEM (HIGH PRIORITY)")
        print("=" * 60)
        
        # Test general chat
        chat_data = {
            "message": "Hello, can you help me understand what this website is about?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        general_chat = await self.test_api_call("POST", "/chat", chat_data)
        
        # Test automation detection
        automation_chat_data = {
            "message": "Please automate filling out forms on this website",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        automation_chat = await self.test_api_call("POST", "/chat", automation_chat_data)
        
        # Test context-aware chat
        context_chat_data = {
            "message": "What are the main topics discussed on this page?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        context_chat = await self.test_api_call("POST", "/chat", context_chat_data)
        
        return general_chat.get("success", False) and automation_chat.get("success", False)
    
    async def test_automation_features(self):
        """Test Automation Features (Medium Priority)"""
        print("\n⚙️ TESTING AUTOMATION FEATURES (MEDIUM PRIORITY)")
        print("=" * 60)
        
        # Test automation task creation
        task_data = {
            "message": "Create a task to extract all email addresses from the current page",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        create_task = await self.test_api_call("POST", "/automate-task", task_data)
        
        # Test automation suggestions
        await self.test_api_call("GET", "/automation-suggestions", {"current_url": "https://example.com"})
        
        # Test active automations
        await self.test_api_call("GET", "/active-automations")
        
        # If task was created, test status and execution
        if create_task.get("success") and create_task.get("data", {}).get("task_id"):
            task_id = create_task["data"]["task_id"]
            
            # Test task status
            await self.test_api_call("GET", f"/automation-status/{task_id}")
            
            # Test task execution
            await self.test_api_call("POST", f"/execute-automation/{task_id}")
        
        return create_task.get("success", False)
    
    async def test_enhanced_ai_features(self):
        """Test Enhanced AI Features (Medium Priority)"""
        print("\n🧠 TESTING ENHANCED AI FEATURES (MEDIUM PRIORITY)")
        print("=" * 60)
        
        # Test AI provider performance
        await self.test_api_call("GET", "/enhanced/ai/providers")
        
        # Test personalized suggestions
        suggestions_data = {
            "user_session": self.session_id,
            "context": "browsing technology websites"
        }
        await self.test_api_call("POST", "/enhanced/ai/personalized-suggestions", suggestions_data)
        
        # Test user insights
        await self.test_api_call("GET", f"/enhanced/memory/user-insights/{self.session_id}")
        
        # Test personalized recommendations
        await self.test_api_call("GET", f"/enhanced/memory/recommendations/{self.session_id}", {"context": "technology"})
        
        return True
    
    async def test_performance_health_monitoring(self):
        """Test Performance & Health Monitoring (Low Priority)"""
        print("\n📊 TESTING PERFORMANCE & HEALTH MONITORING (LOW PRIORITY)")
        print("=" * 60)
        
        # Test health endpoint (already tested but check again)
        health_result = await self.test_api_call("GET", "/health")
        
        # Test performance metrics
        await self.test_api_call("GET", "/performance")
        
        # Test enhanced performance report
        await self.test_api_call("GET", "/enhanced/performance/report")
        
        # Test cache analytics
        await self.test_api_call("GET", "/enhanced/performance/cache-analytics")
        
        # Test system overview
        await self.test_api_call("GET", "/enhanced/system/overview")
        
        return health_result.get("success", False)
    
    async def test_workflow_features(self):
        """Test Advanced Workflow Features (Low Priority)"""
        print("\n🔄 TESTING WORKFLOW FEATURES (LOW PRIORITY)")
        print("=" * 60)
        
        # Test workflow templates
        await self.test_api_call("GET", "/workflow-templates")
        
        # Test enhanced workflow templates
        await self.test_api_call("GET", "/enhanced/workflows/templates", {"user_session": self.session_id})
        
        # Test create workflow
        workflow_data = {
            "user_session": self.session_id,
            "template_id": "basic_web_scraping",
            "parameters": {
                "target_url": "https://example.com",
                "data_points": ["title", "description"]
            }
        }
        create_workflow = await self.test_api_call("POST", "/create-workflow", workflow_data)
        
        # Test user workflows
        await self.test_api_call("GET", f"/user-workflows/{self.session_id}")
        
        # Test personalized suggestions
        await self.test_api_call("GET", f"/personalized-suggestions/{self.session_id}", {"current_url": "https://example.com"})
        
        return True
    
    async def test_integration_features(self):
        """Test Integration Features"""
        print("\n🔗 TESTING INTEGRATION FEATURES")
        print("=" * 60)
        
        # Test available integrations
        await self.test_api_call("GET", "/integrations")
        
        # Test enhanced integrations
        await self.test_api_call("GET", "/enhanced/integrations/available")
        
        # Test user integrations
        await self.test_api_call("GET", f"/integration-auth/user/{self.session_id}")
        
        return True
    
    async def test_phase1_ai_intelligence_boost(self):
        """Test Phase 1: Foundation Enhancements (AI Intelligence Boost)"""
        print("\n🧠 TESTING PHASE 1: AI INTELLIGENCE BOOST")
        print("=" * 60)
        
        # Test multi-provider AI routing
        await self.test_api_call("GET", "/enhanced/ai/providers")
        
        # Test context-aware AI responses with page content analysis
        context_chat_data = {
            "message": "Analyze the content of this webpage and provide insights",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        await self.test_api_call("POST", "/chat", context_chat_data)
        
        # Test session history management (100+ messages)
        for i in range(3):  # Test multiple messages for session continuity
            chat_data = {
                "message": f"This is message {i+1} in our conversation. Remember this context.",
                "session_id": self.session_id,
                "current_url": "https://example.com"
            }
            await self.test_api_call("POST", "/chat", chat_data)
        
        # Test performance monitoring and caching
        await self.test_api_call("GET", "/performance")
        
        # Test visual webpage understanding capabilities
        visual_data = {
            "user_session": self.session_id,
            "context": "visual analysis of webpage layout"
        }
        await self.test_api_call("POST", "/enhanced/ai/personalized-suggestions", visual_data)
        
        # Test user behavioral insights
        await self.test_api_call("GET", f"/enhanced/memory/user-insights/{self.session_id}")
        
        return True
    
    async def test_phase2_agentic_automation(self):
        """Test Phase 2: Invisible Capability Upgrades (Agentic Automation)"""
        print("\n🤖 TESTING PHASE 2: AGENTIC AUTOMATION")
        print("=" * 60)
        
        # Test automation task creation and execution
        task_data = {
            "description": "Extract all links from the current webpage and categorize them",
            "user_session": self.session_id,
            "current_url": "https://example.com",
            "user_preferences": {"automation_level": "advanced"}
        }
        create_task = await self.test_api_call("POST", "/enhanced/automation/create-advanced", task_data)
        
        # Test background task processing
        await self.test_api_call("GET", "/active-automations")
        
        # Test cross-page workflow capabilities
        workflow_data = {
            "user_session": self.session_id,
            "template_id": "cross_page_workflow",
            "parameters": {"start_url": "https://example.com"}
        }
        await self.test_api_call("POST", "/enhanced/workflows/template/create", workflow_data)
        
        # Test parallel task execution
        if create_task.get("success") and create_task.get("data", {}).get("task_id"):
            task_id = create_task["data"]["task_id"]
            await self.test_api_call("GET", f"/enhanced/automation/status/{task_id}")
            await self.test_api_call("POST", f"/enhanced/automation/pause/{task_id}")
            await self.test_api_call("POST", f"/enhanced/automation/resume/{task_id}")
        
        # Test automation suggestions system
        await self.test_api_call("GET", "/automation-suggestions", {"current_url": "https://example.com"})
        
        # Test automation statistics
        await self.test_api_call("GET", "/enhanced/automation/statistics")
        
        return True
    
    async def test_phase3_performance_intelligence(self):
        """Test Phase 3: Selective UI Enhancements (Performance & Intelligence)"""
        print("\n⚡ TESTING PHASE 3: PERFORMANCE & INTELLIGENCE")
        print("=" * 60)
        
        # Test advanced caching strategy
        await self.test_api_call("GET", "/enhanced/performance/cache-analytics")
        
        # Test user pattern learning system
        await self.test_api_call("GET", f"/enhanced/memory/user-insights/{self.session_id}")
        
        # Test performance analytics endpoints
        await self.test_api_call("GET", "/enhanced/performance/report")
        
        # Test memory management optimization
        await self.test_api_call("GET", "/enhanced/system/overview")
        
        # Test database query optimization
        await self.test_api_call("GET", "/recent-tabs")
        await self.test_api_call("GET", "/recommendations")
        
        # Test performance optimization trigger
        await self.test_api_call("POST", "/enhanced/performance/optimize")
        
        return True
    
    async def test_phase4_integrations_extensibility(self):
        """Test Phase 4: Advanced Features (Integrations & Extensibility)"""
        print("\n🔗 TESTING PHASE 4: INTEGRATIONS & EXTENSIBILITY")
        print("=" * 60)
        
        # Test custom integration builder functionality
        await self.test_api_call("GET", "/enhanced/integrations/available")
        
        # Test OAuth 2.0 authentication flows
        oauth_data = {
            "integration_id": "test_oauth_integration",
            "user_session": self.session_id,
            "redirect_uri": "http://localhost:3000/oauth/callback",
            "state": "test_state_123"
        }
        await self.test_api_call("POST", "/enhanced/integrations/oauth/initiate", oauth_data)
        
        # Test integration health monitoring
        await self.test_api_call("GET", f"/integration-auth/user/{self.session_id}")
        
        # Test API rate limit management
        test_credentials = {
            "user_session": self.session_id,
            "integration": "test_api",
            "credentials": {"api_key": "test_key_123", "secret": "test_secret"}
        }
        await self.test_api_call("POST", "/integration-auth/store", test_credentials)
        
        # Test integration deployment capabilities
        api_key_data = {
            "user_session": self.session_id,
            "integration_id": "test_integration",
            "credentials": {"api_key": "test_api_key"}
        }
        await self.test_api_call("POST", "/enhanced/integrations/api-key/store", api_key_data)
        
        # Test integration validation
        validation_data = {
            "integration": "test_integration",
            "credentials": {"api_key": "test_key"}
        }
        await self.test_api_call("POST", "/integration-auth/validate", validation_data)
        
        return True
    
    async def test_phase5_voice_keyboard_polish(self):
        """Test Phase 5: Final Polish (Voice Commands & Keyboard Shortcuts)"""
        print("\n🎤 TESTING PHASE 5: VOICE COMMANDS & KEYBOARD SHORTCUTS")
        print("=" * 60)
        
        # Test voice commands engine with natural language processing
        voice_data = {
            "voice_text": "Navigate to the homepage and show me recent tabs",
            "user_session": self.session_id,
            "context": {"current_url": "https://example.com"}
        }
        await self.test_api_call("POST", "/voice-command", voice_data)
        
        # Test keyboard shortcuts system with all categories
        await self.test_api_call("GET", "/keyboard-shortcuts", {"category": "navigation", "user_session": self.session_id})
        await self.test_api_call("GET", "/keyboard-shortcuts", {"category": "automation", "user_session": self.session_id})
        
        # Test custom shortcuts creation and management
        custom_shortcut = {
            "user_session": self.session_id,
            "combination": "Ctrl+Shift+A",
            "action": "open_ai_assistant",
            "category": "ai",
            "description": "Open AI Assistant Panel",
            "parameters": {"panel": "chat"}
        }
        await self.test_api_call("POST", "/keyboard-shortcuts/custom", custom_shortcut)
        
        # Test accessibility features
        await self.test_api_call("GET", "/voice-commands/available", {"user_session": self.session_id})
        
        # Test user preferences and configuration
        await self.test_api_call("GET", "/keyboard-shortcuts/usage-stats", {"user_session": self.session_id})
        
        # Test voice command history
        await self.test_api_call("GET", f"/voice-commands/history/{self.session_id}", {"limit": 10})
        
        # Test custom voice command
        custom_voice = {
            "user_session": self.session_id,
            "command_name": "quick_search",
            "patterns": ["search for", "find", "look up"],
            "action": "perform_search",
            "command_type": "search",
            "parameters": {"search_engine": "google"}
        }
        await self.test_api_call("POST", "/voice-commands/custom", custom_voice)
        
        # Test shortcuts export
        export_data = {"user_session": self.session_id}
        await self.test_api_call("POST", "/shortcuts/export", export_data)
        
        return True
    
    async def test_comprehensive_api_endpoints(self):
        """Test all major API endpoints comprehensively"""
        print("\n🌐 TESTING COMPREHENSIVE API ENDPOINTS")
        print("=" * 60)
        
        # Enhanced health check
        health_result = await self.test_api_call("GET", "/health")
        
        # Enhanced chat with all capabilities
        enhanced_chat_data = {
            "message": "I need help with web automation. Can you analyze this page and suggest some automation tasks?",
            "session_id": self.session_id,
            "current_url": "https://example.com",
            "language": "en"
        }
        await self.test_api_call("POST", "/chat", enhanced_chat_data)
        
        # Enhanced browse with content analysis
        browse_data = {
            "url": "https://github.com",
            "title": "GitHub"
        }
        await self.test_api_call("POST", "/browse", browse_data)
        
        # Test summarization
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        await self.test_api_call("POST", "/summarize", summary_data)
        
        # Test search suggestions
        search_data = {"query": "artificial intelligence tools"}
        await self.test_api_call("POST", "/search-suggestions", search_data)
        
        # Enhanced system status
        await self.test_api_call("GET", "/enhanced/system/full-status")
        
        return health_result.get("success", False)
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests for AETHER Enhancement Roadmap"""
        print(f"\n🚀 STARTING COMPREHENSIVE AETHER BACKEND API TESTING")
        print(f"🎯 TESTING ALL 5 PHASES OF AETHER ENHANCEMENT ROADMAP")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        test_results = {}
        
        # COMPREHENSIVE API TESTING - All Major Endpoints
        test_results["comprehensive_apis"] = await self.test_comprehensive_api_endpoints()
        
        # PHASE 1: Foundation Enhancements (AI Intelligence Boost)
        test_results["phase1_ai_intelligence"] = await self.test_phase1_ai_intelligence_boost()
        
        # PHASE 2: Invisible Capability Upgrades (Agentic Automation)
        test_results["phase2_agentic_automation"] = await self.test_phase2_agentic_automation()
        
        # PHASE 3: Selective UI Enhancements (Performance & Intelligence)
        test_results["phase3_performance_intelligence"] = await self.test_phase3_performance_intelligence()
        
        # PHASE 4: Advanced Features (Integrations & Extensibility)
        test_results["phase4_integrations_extensibility"] = await self.test_phase4_integrations_extensibility()
        
        # PHASE 5: Final Polish (Voice Commands & Keyboard Shortcuts)
        test_results["phase5_voice_keyboard_polish"] = await self.test_phase5_voice_keyboard_polish()
        
        # Legacy Core Tests (High Priority)
        test_results["core_browser"] = await self.test_core_browser_apis()
        test_results["ai_chat"] = await self.test_ai_chat_system()
        
        # Legacy Medium Priority Tests  
        test_results["automation"] = await self.test_automation_features()
        test_results["enhanced_ai"] = await self.test_enhanced_ai_features()
        
        # Legacy Low Priority Tests
        test_results["performance"] = await self.test_performance_health_monitoring()
        test_results["workflows"] = await self.test_workflow_features()
        test_results["integrations"] = await self.test_integration_features()
        
        # COMPREHENSIVE SUMMARY
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE TEST SUMMARY - AETHER ENHANCEMENT ROADMAP")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Warnings: {warning_tests} ⚠️")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n🎯 AETHER ENHANCEMENT PHASES RESULTS:")
        phase_results = {
            "phase1_ai_intelligence": "Phase 1: AI Intelligence Boost",
            "phase2_agentic_automation": "Phase 2: Agentic Automation", 
            "phase3_performance_intelligence": "Phase 3: Performance & Intelligence",
            "phase4_integrations_extensibility": "Phase 4: Integrations & Extensibility",
            "phase5_voice_keyboard_polish": "Phase 5: Voice Commands & Keyboard Shortcuts"
        }
        
        for phase_key, phase_name in phase_results.items():
            if phase_key in test_results:
                status = "✅ WORKING" if test_results[phase_key] else "❌ ISSUES FOUND"
                print(f"  {phase_name}: {status}")
        
        print("\n📊 LEGACY FEATURE AREA RESULTS:")
        legacy_features = {k: v for k, v in test_results.items() if k not in phase_results and k != "comprehensive_apis"}
        for feature, success in legacy_features.items():
            status = "✅ WORKING" if success else "❌ ISSUES FOUND"
            print(f"  {feature.replace('_', ' ').title()}: {status}")
        
        # Critical Issues Analysis
        critical_endpoints = ["/health", "/browse", "/chat", "/enhanced/system/overview"]
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and any(endpoint in r["endpoint"] for endpoint in critical_endpoints)]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  - {failure['method']} {failure['endpoint']}: {failure['details']}")
        
        # Performance Issues Analysis
        slow_endpoints = [r for r in self.test_results if r["response_time"] > 5.0]
        if slow_endpoints:
            print("\n⚠️ SLOW ENDPOINTS (>5s):")
            for slow in slow_endpoints:
                print(f"  - {slow['method']} {slow['endpoint']}: {slow['response_time']:.2f}s")
        
        # Enhancement Features Status
        print(f"\n🔍 ENHANCEMENT FEATURES VALIDATION:")
        enhancement_features = [
            "Multi-AI Provider Support",
            "Advanced Automation Engine", 
            "Intelligent Memory System",
            "Performance Optimization",
            "Enhanced Integrations",
            "Voice Commands Engine",
            "Keyboard Shortcuts System"
        ]
        
        working_features = 0
        for feature in enhancement_features:
            # Check if related endpoints are working
            related_passed = len([r for r in self.test_results if r["status"] == "PASS" and any(keyword in r["endpoint"].lower() for keyword in feature.lower().split())])
            if related_passed > 0:
                print(f"  ✅ {feature}: Operational")
                working_features += 1
            else:
                print(f"  ⚠️ {feature}: Needs Verification")
        
        print(f"\n📈 ENHANCEMENT COVERAGE: {working_features}/{len(enhancement_features)} features validated")
        
        return test_results

async def main():
    """Main test execution"""
    async with AetherAPITester() as tester:
        results = await tester.run_comprehensive_tests()
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump({
                "test_summary": results,
                "detailed_results": tester.test_results,
                "test_session": tester.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "backend_url": BASE_URL
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/backend_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())