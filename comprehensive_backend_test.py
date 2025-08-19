#!/usr/bin/env python3
"""
AETHER AI Browser - COMPREHENSIVE Backend API Testing
Tests ALL endpoints including advanced features as requested in review
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

class ComprehensiveAetherTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.session_id = str(uuid.uuid4())
        self.total_endpoints_tested = 0
        self.successful_endpoints = 0
        self.failed_endpoints = 0
        
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
        self.total_endpoints_tested += 1
        
        if status == "PASS":
            self.successful_endpoints += 1
        elif status == "FAIL":
            self.failed_endpoints += 1
        
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
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"text": await response.text()}
                    
                    if response.status == expected_status:
                        self.log_test(endpoint, method, "PASS", f"Status {response.status}", response_time)
                        return {"success": True, "data": response_data, "status": response.status}
                    else:
                        self.log_test(endpoint, method, "FAIL", f"Expected {expected_status}, got {response.status}", response_time)
                        return {"success": False, "data": response_data, "status": response.status}
                        
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    response_time = time.time() - start_time
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"text": await response.text()}
                    
                    if response.status == expected_status:
                        self.log_test(endpoint, method, "PASS", f"Status {response.status}", response_time)
                        return {"success": True, "data": response_data, "status": response.status}
                    else:
                        self.log_test(endpoint, method, "FAIL", f"Expected {expected_status}, got {response.status}", response_time)
                        return {"success": False, "data": response_data, "status": response.status}
                        
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    response_time = time.time() - start_time
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"text": await response.text()}
                    
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

    async def test_basic_browser_functionality(self):
        """Test basic browser functionality endpoints"""
        print("\n🌐 TESTING BASIC BROWSER FUNCTIONALITY")
        print("=" * 60)
        
        # Health check
        await self.test_api_call("GET", "/health")
        
        # Browse functionality
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        await self.test_api_call("POST", "/browse", browse_data)
        
        # Recent tabs
        await self.test_api_call("GET", "/recent-tabs")
        
        # Recommendations
        await self.test_api_call("GET", "/recommendations")
        
        # Clear history
        await self.test_api_call("DELETE", "/clear-history")

    async def test_ai_integration_groq(self):
        """Test AI integration with Groq API"""
        print("\n🤖 TESTING AI INTEGRATION (GROQ API)")
        print("=" * 60)
        
        # Basic chat
        chat_data = {
            "message": "Hello, can you help me understand what this website is about?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        await self.test_api_call("POST", "/chat", chat_data)
        
        # Context-aware chat
        context_chat_data = {
            "message": "What are the main topics discussed on this page?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        await self.test_api_call("POST", "/chat", context_chat_data)
        
        # Summarization
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        await self.test_api_call("POST", "/summarize", summary_data)
        
        # Search suggestions
        search_data = {"query": "artificial intelligence tools"}
        await self.test_api_call("POST", "/search-suggestions", search_data)

    async def test_platform_integrations(self):
        """Test platform integration endpoints"""
        print("\n🔗 TESTING PLATFORM INTEGRATIONS")
        print("=" * 60)
        
        # Platform status
        await self.test_api_call("GET", "/platforms/status")
        
        # Test platform connection (without actual credentials)
        platform_data = {
            "platform": "twitter",
            "credentials": {
                "api_key": "test_key",
                "api_secret": "test_secret",
                "access_token": "test_token",
                "access_token_secret": "test_token_secret"
            }
        }
        await self.test_api_call("POST", "/platforms/connect", platform_data, expected_status=400)  # Expected to fail without real credentials
        
        # Twitter endpoints (will fail without connection but test endpoint existence)
        tweet_data = {"text": "Test tweet from AETHER browser"}
        await self.test_api_call("POST", "/twitter/tweet", tweet_data, expected_status=400)
        
        await self.test_api_call("GET", "/twitter/search", {"query": "AI browser", "max_results": 5}, expected_status=400)
        
        engagement_data = {
            "hashtags": ["#AI", "#browser"],
            "actions_per_hashtag": 3
        }
        await self.test_api_call("POST", "/twitter/engagement-automation", engagement_data, expected_status=400)
        
        # GitHub endpoints (will fail without connection but test endpoint existence)
        repo_data = {
            "name": "test-repo",
            "description": "Test repository from AETHER",
            "private": False
        }
        await self.test_api_call("POST", "/github/repository", repo_data, expected_status=400)
        
        await self.test_api_call("GET", "/github/repositories/testuser", expected_status=400)
        
        issue_data = {
            "owner": "testuser",
            "repo": "test-repo",
            "title": "Test issue",
            "body": "This is a test issue",
            "labels": ["bug", "test"]
        }
        await self.test_api_call("POST", "/github/issue", issue_data, expected_status=400)
        
        await self.test_api_call("GET", "/github/analyze/testuser/test-repo", expected_status=400)

    async def test_cross_page_workflows(self):
        """Test cross-page workflow engine"""
        print("\n🔄 TESTING CROSS-PAGE WORKFLOW ENGINE")
        print("=" * 60)
        
        # Create workflow
        workflow_data = {
            "name": "Test Cross-Page Workflow",
            "description": "A test workflow for comprehensive testing",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "title"},
                {"action": "navigate", "url": "https://httpbin.org/json"},
                {"action": "extract", "selector": "body"}
            ],
            "variables": {"test_var": "test_value"},
            "session_data": {"user_id": self.session_id}
        }
        create_result = await self.test_api_call("POST", "/workflows/create", workflow_data)
        
        # List workflows
        await self.test_api_call("GET", "/workflows")
        
        # If workflow was created, test execution and status
        if create_result.get("success") and create_result.get("data", {}).get("workflow_id"):
            workflow_id = create_result["data"]["workflow_id"]
            
            # Execute workflow
            await self.test_api_call("POST", f"/workflows/{workflow_id}/execute")
            
            # Get workflow status
            await self.test_api_call("GET", f"/workflows/{workflow_id}/status")
            
            # Cancel workflow
            await self.test_api_call("DELETE", f"/workflows/{workflow_id}")

    async def test_predictive_automation(self):
        """Test predictive automation engine"""
        print("\n🔮 TESTING PREDICTIVE AUTOMATION ENGINE")
        print("=" * 60)
        
        # Test predictive engine
        await self.test_api_call("GET", "/predictive/test")
        
        # Analyze user behavior
        behavior_data = {
            "user_session": self.session_id,
            "action_history": [
                {"action": "navigate", "url": "https://example.com", "timestamp": datetime.now().isoformat()},
                {"action": "click", "element": "button", "timestamp": datetime.now().isoformat()},
                {"action": "extract", "data": "title", "timestamp": datetime.now().isoformat()}
            ]
        }
        await self.test_api_call("POST", "/predictive/analyze-behavior", behavior_data)
        
        # Optimize workflow
        optimization_data = {
            "workflow_id": "test_workflow",
            "performance_metrics": {
                "execution_time": 5.2,
                "success_rate": 0.85,
                "error_count": 2
            },
            "user_feedback": "positive"
        }
        await self.test_api_call("POST", "/predictive/optimize-workflow", optimization_data)

    async def test_collaborative_agents(self):
        """Test collaborative agent system"""
        print("\n👥 TESTING COLLABORATIVE AGENT SYSTEM")
        print("=" * 60)
        
        # Test collaborative system
        await self.test_api_call("GET", "/collaborative/test")
        
        # Register user
        user_data = {
            "user_id": self.session_id,
            "username": "test_user",
            "email": "test@example.com",
            "role": "member",
            "skills": ["web_automation", "data_analysis"]
        }
        await self.test_api_call("POST", "/collaborative/register-user", user_data)
        
        # Create collaborative workflow
        collab_workflow_data = {
            "name": "Test Collaborative Workflow",
            "description": "A test collaborative workflow",
            "participant_ids": [self.session_id],
            "tasks": [
                {"task_id": "task1", "description": "Extract data from website", "assigned_to": self.session_id},
                {"task_id": "task2", "description": "Analyze extracted data", "assigned_to": self.session_id}
            ],
            "collaboration_mode": "parallel",
            "type": "data_analysis",
            "complexity": "medium",
            "created_by": self.session_id
        }
        create_collab_result = await self.test_api_call("POST", "/collaborative/workflows", collab_workflow_data)
        
        # List collaborative workflows
        await self.test_api_call("GET", "/collaborative/workflows", {"user_id": self.session_id})
        
        # Get user dashboard
        await self.test_api_call("GET", f"/collaborative/users/{self.session_id}/dashboard")
        
        # If collaborative workflow was created, test execution and status
        if create_collab_result.get("success") and create_collab_result.get("data", {}).get("workflow_id"):
            workflow_id = create_collab_result["data"]["workflow_id"]
            
            # Execute collaborative workflow
            await self.test_api_call("POST", f"/collaborative/workflows/{workflow_id}/execute")
            
            # Get collaborative workflow status
            await self.test_api_call("GET", f"/collaborative/workflows/{workflow_id}/status")
            
            # Cancel collaborative workflow
            await self.test_api_call("DELETE", f"/collaborative/workflows/{workflow_id}", {"user_id": self.session_id})

    async def test_automation_workflows(self):
        """Test automation workflow system"""
        print("\n⚙️ TESTING AUTOMATION WORKFLOWS")
        print("=" * 60)
        
        # Create automation task
        task_data = {
            "message": "Create a task to extract all email addresses from the current page",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        create_task_result = await self.test_api_call("POST", "/automate-task", task_data)
        
        # Get automation suggestions
        await self.test_api_call("GET", "/automation-suggestions", {"current_url": "https://example.com"})
        
        # Get active automations
        await self.test_api_call("GET", "/active-automations")
        
        # If task was created, test execution and management
        if create_task_result.get("success") and create_task_result.get("data", {}).get("task_id"):
            task_id = create_task_result["data"]["task_id"]
            
            # Execute automation
            await self.test_api_call("POST", f"/execute-automation/{task_id}")
            
            # Get automation status
            await self.test_api_call("GET", f"/automation-status/{task_id}")
            
            # Cancel automation
            await self.test_api_call("POST", f"/cancel-automation/{task_id}")
        
        # Create workflow
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "title"}
            ]
        }
        await self.test_api_call("POST", "/create-workflow", workflow_data)

    async def test_voice_commands_keyboard_shortcuts(self):
        """Test voice commands and keyboard shortcuts"""
        print("\n🎤 TESTING VOICE COMMANDS & KEYBOARD SHORTCUTS")
        print("=" * 60)
        
        # Process voice command
        voice_data = {
            "voice_text": "Navigate to the homepage and show me recent tabs",
            "user_session": self.session_id,
            "context": {"current_url": "https://example.com"}
        }
        await self.test_api_call("POST", "/voice-command", voice_data)
        
        # Get available voice commands
        await self.test_api_call("GET", "/voice-commands/available", {"user_session": self.session_id})
        
        # Execute keyboard shortcut
        shortcut_data = {
            "shortcut": "ctrl+h",
            "user_session": self.session_id
        }
        await self.test_api_call("POST", "/keyboard-shortcut", shortcut_data)

    async def test_desktop_companion_endpoints(self):
        """Test desktop companion endpoints"""
        print("\n🖥️ TESTING DESKTOP COMPANION ENDPOINTS")
        print("=" * 60)
        
        # Desktop companion status
        await self.test_api_call("GET", "/desktop/status")
        
        # Computer use API - screenshot
        screenshot_data = {"action": "screenshot"}
        await self.test_api_call("POST", "/desktop/computer-use", screenshot_data)
        
        # Computer use API - click
        click_data = {
            "action": "click",
            "position": {"x": 100, "y": 200}
        }
        await self.test_api_call("POST", "/desktop/computer-use", click_data)
        
        # Computer use API - type
        type_data = {
            "action": "type",
            "text": "Hello from AETHER desktop companion"
        }
        await self.test_api_call("POST", "/desktop/computer-use", type_data)

    async def test_extension_bridge(self):
        """Test browser extension bridge"""
        print("\n🔌 TESTING BROWSER EXTENSION BRIDGE")
        print("=" * 60)
        
        # Page analysis from extension
        page_analysis_data = {
            "action": "page_analysis",
            "data": {
                "tabId": "tab_123",
                "url": "https://example.com",
                "analysis": {
                    "title": "Example Domain",
                    "links": ["https://example.com/link1", "https://example.com/link2"],
                    "forms": 1,
                    "images": 0
                }
            }
        }
        await self.test_api_call("POST", "/extension-bridge", page_analysis_data)
        
        # Create automation from extension
        create_automation_data = {
            "action": "create_automation",
            "data": {
                "url": "https://example.com",
                "automation_type": "data_extraction"
            }
        }
        await self.test_api_call("POST", "/extension-bridge", create_automation_data)
        
        # Data extraction from extension
        data_extraction_data = {
            "action": "data_extraction",
            "data": {
                "extraction": {
                    "title": "Example Domain",
                    "description": "This domain is for use in illustrative examples"
                }
            }
        }
        await self.test_api_call("POST", "/extension-bridge", data_extraction_data)

    async def test_demo_endpoints(self):
        """Test demo endpoints showing AETHER capabilities"""
        print("\n🎯 TESTING DEMO ENDPOINTS")
        print("=" * 60)
        
        # Fellou.ai comparison demo
        await self.test_api_call("GET", "/demo/fellou-comparison")
        
        # Performance metrics demo
        await self.test_api_call("GET", "/demo/performance-metrics")

    async def test_performance_monitoring(self):
        """Test performance and monitoring endpoints"""
        print("\n📊 TESTING PERFORMANCE & MONITORING")
        print("=" * 60)
        
        # Enhanced system overview
        await self.test_api_call("GET", "/enhanced/system/overview")
        
        # Performance metrics
        await self.test_api_call("GET", "/performance")
        
        # Enhanced performance report
        await self.test_api_call("GET", "/enhanced/performance/report")
        
        # Cache analytics
        await self.test_api_call("GET", "/enhanced/performance/cache-analytics")

    async def test_concurrent_request_handling(self):
        """Test concurrent request handling"""
        print("\n🔄 TESTING CONCURRENT REQUEST HANDLING")
        print("=" * 60)
        
        # Create multiple concurrent requests
        concurrent_tasks = []
        
        for i in range(5):
            chat_data = {
                "message": f"Concurrent test message {i+1}",
                "session_id": f"{self.session_id}_{i}",
                "current_url": "https://example.com"
            }
            task = self.test_api_call("POST", "/chat", chat_data)
            concurrent_tasks.append(task)
        
        # Wait for all concurrent requests
        start_time = time.time()
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_requests = sum(1 for result in results if isinstance(result, dict) and result.get("success"))
        
        print(f"Concurrent requests: {successful_requests}/{len(results)} successful in {total_time:.2f}s")
        
        return {
            "concurrent_success_rate": successful_requests / len(results),
            "total_time": total_time,
            "requests_per_second": len(results) / total_time
        }

    async def test_error_handling_edge_cases(self):
        """Test error handling and edge cases"""
        print("\n⚠️ TESTING ERROR HANDLING & EDGE CASES")
        print("=" * 60)
        
        # Test invalid endpoints
        await self.test_api_call("GET", "/invalid-endpoint", expected_status=404)
        
        # Test malformed requests
        await self.test_api_call("POST", "/chat", {"invalid": "data"}, expected_status=422)
        
        # Test empty requests
        await self.test_api_call("POST", "/browse", {}, expected_status=422)
        
        # Test very long messages
        long_message_data = {
            "message": "A" * 10000,  # Very long message
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        await self.test_api_call("POST", "/chat", long_message_data)

    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print(f"\n🚀 STARTING COMPREHENSIVE AETHER BACKEND API TESTING")
        print(f"🎯 TESTING ALL ENDPOINTS INCLUDING ADVANCED FEATURES")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Test all categories
        await self.test_basic_browser_functionality()
        await self.test_ai_integration_groq()
        await self.test_platform_integrations()
        await self.test_cross_page_workflows()
        await self.test_predictive_automation()
        await self.test_collaborative_agents()
        await self.test_automation_workflows()
        await self.test_voice_commands_keyboard_shortcuts()
        await self.test_desktop_companion_endpoints()
        await self.test_extension_bridge()
        await self.test_demo_endpoints()
        await self.test_performance_monitoring()
        
        # Test concurrent handling and error cases
        concurrent_results = await self.test_concurrent_request_handling()
        await self.test_error_handling_edge_cases()
        
        total_time = time.time() - start_time
        
        # COMPREHENSIVE SUMMARY
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE TEST SUMMARY - ALL ENDPOINTS TESTED")
        print("=" * 80)
        
        success_rate = (self.successful_endpoints / self.total_endpoints_tested * 100) if self.total_endpoints_tested > 0 else 0
        
        print(f"Total Endpoints Tested: {self.total_endpoints_tested}")
        print(f"Successful: {self.successful_endpoints} ✅")
        print(f"Failed: {self.failed_endpoints} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Test Time: {total_time:.2f}s")
        print(f"Average Response Time: {sum(r['response_time'] for r in self.test_results) / len(self.test_results):.2f}s")
        
        # Categorize results
        print("\n🎯 FEATURE CATEGORY RESULTS:")
        
        categories = {
            "Basic Browser Functionality": ["/health", "/browse", "/recent-tabs", "/recommendations", "/clear-history"],
            "AI Integration (Groq)": ["/chat", "/summarize", "/search-suggestions"],
            "Platform Integrations": ["/platforms/status", "/platforms/connect", "/twitter/", "/github/"],
            "Cross-Page Workflows": ["/workflows/create", "/workflows/", "/workflows/"],
            "Predictive Automation": ["/predictive/test", "/predictive/analyze-behavior", "/predictive/optimize-workflow"],
            "Collaborative Agents": ["/collaborative/test", "/collaborative/register-user", "/collaborative/workflows"],
            "Automation Workflows": ["/automate-task", "/automation-suggestions", "/active-automations"],
            "Voice & Keyboard": ["/voice-command", "/voice-commands/available", "/keyboard-shortcut"],
            "Desktop Companion": ["/desktop/status", "/desktop/computer-use"],
            "Extension Bridge": ["/extension-bridge"],
            "Demo Endpoints": ["/demo/fellou-comparison", "/demo/performance-metrics"],
            "Performance Monitoring": ["/enhanced/system/overview", "/performance", "/enhanced/performance/"]
        }
        
        for category, endpoints in categories.items():
            category_tests = [r for r in self.test_results if any(endpoint in r["endpoint"] for endpoint in endpoints)]
            if category_tests:
                category_success = len([r for r in category_tests if r["status"] == "PASS"])
                category_total = len(category_tests)
                category_rate = (category_success / category_total * 100) if category_total > 0 else 0
                status = "✅ WORKING" if category_rate >= 80 else "⚠️ PARTIAL" if category_rate >= 50 else "❌ ISSUES"
                print(f"  {category}: {category_success}/{category_total} ({category_rate:.1f}%) {status}")
        
        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        avg_response_time = sum(r["response_time"] for r in self.test_results) / len(self.test_results)
        fast_endpoints = len([r for r in self.test_results if r["response_time"] < 1.0])
        slow_endpoints = len([r for r in self.test_results if r["response_time"] > 2.0])
        
        print(f"  Average Response Time: {avg_response_time:.2f}s")
        print(f"  Fast Endpoints (<1s): {fast_endpoints}")
        print(f"  Slow Endpoints (>2s): {slow_endpoints}")
        
        if concurrent_results:
            print(f"  Concurrent Performance: {concurrent_results['requests_per_second']:.1f} req/s")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and any(endpoint in r["endpoint"] for endpoint in ["/health", "/chat", "/browse"])]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  - {failure['method']} {failure['endpoint']}: {failure['details']}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Unused functionality detection
        print(f"\n🔍 UNUSED FUNCTIONALITY DETECTION:")
        unused_endpoints = [r for r in self.test_results if r["status"] == "FAIL" and "404" in r["details"]]
        if unused_endpoints:
            print("  Potentially unused endpoints:")
            for unused in unused_endpoints:
                print(f"    - {unused['method']} {unused['endpoint']}")
        else:
            print("  All tested endpoints are implemented")
        
        # Final assessment
        print(f"\n📈 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("  🎉 EXCELLENT - System is production-ready with high reliability")
        elif success_rate >= 80:
            print("  ✅ GOOD - System is functional with minor issues")
        elif success_rate >= 70:
            print("  ⚠️ ACCEPTABLE - System works but needs improvements")
        else:
            print("  ❌ NEEDS WORK - System has significant issues")
        
        return {
            "total_endpoints": self.total_endpoints_tested,
            "successful": self.successful_endpoints,
            "failed": self.failed_endpoints,
            "success_rate": success_rate,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "concurrent_performance": concurrent_results
        }

async def main():
    """Main test execution"""
    async with ComprehensiveAetherTester() as tester:
        results = await tester.run_comprehensive_tests()
        
        # Save detailed results
        with open('/app/comprehensive_test_results.json', 'w') as f:
            json.dump({
                "test_summary": results,
                "detailed_results": tester.test_results,
                "test_session": tester.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "backend_url": BASE_URL
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/comprehensive_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())