#!/usr/bin/env python3
"""
AETHER Enhanced Browser - Focused Backend API Testing
Tests the specific endpoints mentioned in the review request
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

class FocusedAetherTester:
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
    
    async def test_basic_core_functionality(self):
        """Test Basic Core Functionality endpoints"""
        print("\n🌐 TESTING BASIC CORE FUNCTIONALITY")
        print("=" * 60)
        
        results = {}
        
        # GET /api/health (enhanced health check)
        results["health"] = await self.test_api_call("GET", "/health")
        
        # POST /api/browse (webpage fetching)
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        results["browse"] = await self.test_api_call("POST", "/browse", browse_data)
        
        # POST /api/chat (AI assistant with Groq)
        chat_data = {
            "message": "Hello, can you help me understand what this website is about?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        results["chat"] = await self.test_api_call("POST", "/chat", chat_data)
        
        # GET /api/recent-tabs (browsing history)
        results["recent_tabs"] = await self.test_api_call("GET", "/recent-tabs")
        
        # GET /api/recommendations (AI recommendations)
        results["recommendations"] = await self.test_api_call("GET", "/recommendations")
        
        # DELETE /api/clear-history (clear data)
        results["clear_history"] = await self.test_api_call("DELETE", "/clear-history")
        
        return results
    
    async def test_previously_failing_endpoints(self):
        """Test Previously Failing Endpoints (NOW FIXED)"""
        print("\n🔧 TESTING PREVIOUSLY FAILING ENDPOINTS (NOW FIXED)")
        print("=" * 60)
        
        results = {}
        
        # POST /api/summarize (webpage summarization)
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        results["summarize"] = await self.test_api_call("POST", "/summarize", summary_data)
        
        # POST /api/search-suggestions (AI-powered search suggestions)
        search_data = {"query": "artificial intelligence tools"}
        results["search_suggestions"] = await self.test_api_call("POST", "/search-suggestions", search_data)
        
        # POST /api/create-workflow (workflow creation)
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "title"}
            ]
        }
        results["create_workflow"] = await self.test_api_call("POST", "/create-workflow", workflow_data)
        
        # POST /api/enhanced/automation/create-advanced (advanced automation)
        advanced_automation_data = {
            "description": "Advanced automation task for testing",
            "user_session": self.session_id,
            "configuration": {
                "type": "advanced",
                "parallel_execution": True,
                "error_recovery": True
            }
        }
        results["create_advanced_automation"] = await self.test_api_call("POST", "/enhanced/automation/create-advanced", advanced_automation_data)
        
        # POST /api/enhanced/workflows/template/create (workflow templates)
        template_data = {
            "name": "Test Template",
            "description": "A test workflow template",
            "user_session": self.session_id,
            "template": {
                "steps": [
                    {"type": "navigate", "url": "https://example.com"},
                    {"type": "extract", "selector": "h1"}
                ]
            }
        }
        results["create_workflow_template"] = await self.test_api_call("POST", "/enhanced/workflows/template/create", template_data)
        
        # POST /api/enhanced/integrations/oauth/initiate (OAuth flow)
        oauth_data = {
            "provider": "test_provider",
            "user_session": self.session_id
        }
        results["oauth_initiate"] = await self.test_api_call("POST", "/enhanced/integrations/oauth/initiate", oauth_data)
        
        # POST /api/enhanced/integrations/api-key/store (API key storage)
        api_key_data = {
            "name": "Test Integration",
            "api_key": "test_api_key_12345",
            "type": "test_service"
        }
        results["api_key_store"] = await self.test_api_call("POST", "/enhanced/integrations/api-key/store", api_key_data)
        
        return results
    
    async def test_voice_commands_keyboard_shortcuts(self):
        """Test Voice Commands & Keyboard Shortcuts"""
        print("\n🎤 TESTING VOICE COMMANDS & KEYBOARD SHORTCUTS")
        print("=" * 60)
        
        results = {}
        
        # POST /api/voice-command (process voice commands)
        voice_data = {
            "voice_text": "Navigate to the homepage and show me recent tabs",
            "user_session": self.session_id,
            "context": {"current_url": "https://example.com"}
        }
        results["voice_command"] = await self.test_api_call("POST", "/voice-command", voice_data)
        
        # GET /api/voice-commands/available (list available commands)
        results["voice_commands_available"] = await self.test_api_call("GET", "/voice-commands/available", {"user_session": self.session_id})
        
        # POST /api/keyboard-shortcut (execute shortcuts)
        shortcut_data = {
            "shortcut": "ctrl+h",
            "user_session": self.session_id
        }
        results["keyboard_shortcut"] = await self.test_api_call("POST", "/keyboard-shortcut", shortcut_data)
        
        return results
    
    async def test_automation_features(self):
        """Test Automation Features"""
        print("\n⚙️ TESTING AUTOMATION FEATURES")
        print("=" * 60)
        
        results = {}
        
        # POST /api/automate-task (create automation tasks)
        task_data = {
            "message": "Create a task to extract all email addresses from the current page",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        create_result = await self.test_api_call("POST", "/automate-task", task_data)
        results["automate_task"] = create_result
        
        # GET /api/active-automations (list active tasks)
        results["active_automations"] = await self.test_api_call("GET", "/active-automations")
        
        # GET /api/automation-suggestions (context-aware suggestions)
        results["automation_suggestions"] = await self.test_api_call("GET", "/automation-suggestions", {"current_url": "https://example.com"})
        
        # If task was created, test execution, status, and cancellation
        if create_result.get("success") and create_result.get("data", {}).get("task_id"):
            task_id = create_result["data"]["task_id"]
            
            # POST /api/execute-automation/{task_id} (execute automation)
            results["execute_automation"] = await self.test_api_call("POST", f"/execute-automation/{task_id}")
            
            # GET /api/automation-status/{task_id} (get task status)
            results["automation_status"] = await self.test_api_call("GET", f"/automation-status/{task_id}")
            
            # POST /api/cancel-automation/{task_id} (cancel task)
            results["cancel_automation"] = await self.test_api_call("POST", f"/cancel-automation/{task_id}")
        
        return results
    
    async def test_system_overview(self):
        """Test System Overview"""
        print("\n📊 TESTING SYSTEM OVERVIEW")
        print("=" * 60)
        
        results = {}
        
        # GET /api/enhanced/system/overview (comprehensive system status)
        results["system_overview"] = await self.test_api_call("GET", "/enhanced/system/overview")
        
        return results
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n🔄 TESTING CONCURRENT REQUESTS")
        print("=" * 60)
        
        # Create multiple concurrent chat requests
        chat_tasks = []
        for i in range(3):
            chat_data = {
                "message": f"Concurrent test message {i+1}",
                "session_id": f"{self.session_id}_{i}",
                "current_url": "https://example.com"
            }
            task = self.test_api_call("POST", "/chat", chat_data)
            chat_tasks.append(task)
        
        # Wait for all concurrent requests to complete
        concurrent_results = await asyncio.gather(*chat_tasks)
        
        success_count = sum(1 for result in concurrent_results if result.get("success"))
        print(f"Concurrent requests: {success_count}/{len(concurrent_results)} successful")
        
        return {"concurrent_success_rate": success_count / len(concurrent_results)}
    
    async def run_focused_tests(self):
        """Run focused tests based on review request"""
        print(f"\n🚀 STARTING FOCUSED AETHER BACKEND API TESTING")
        print(f"🎯 TESTING SPECIFIC ENDPOINTS FROM REVIEW REQUEST")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        test_results = {}
        
        # Test Basic Core Functionality (6 endpoints)
        test_results["basic_core"] = await self.test_basic_core_functionality()
        
        # Test Previously Failing Endpoints (8 endpoints that were fixed)
        test_results["previously_failing"] = await self.test_previously_failing_endpoints()
        
        # Test Voice Commands & Keyboard Shortcuts
        test_results["voice_keyboard"] = await self.test_voice_commands_keyboard_shortcuts()
        
        # Test Automation Features
        test_results["automation"] = await self.test_automation_features()
        
        # Test System Overview
        test_results["system_overview"] = await self.test_system_overview()
        
        # Test concurrent requests
        test_results["concurrent"] = await self.test_concurrent_requests()
        
        # SUMMARY
        print("\n" + "=" * 80)
        print("📋 FOCUSED TEST SUMMARY - REVIEW REQUEST VALIDATION")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Analyze results by category
        print("\n🎯 CATEGORY RESULTS:")
        
        categories = {
            "Basic Core Functionality (6 endpoints)": test_results["basic_core"],
            "Previously Failing Endpoints (8 endpoints)": test_results["previously_failing"],
            "Voice Commands & Keyboard Shortcuts": test_results["voice_keyboard"],
            "Automation Features": test_results["automation"],
            "System Overview": test_results["system_overview"]
        }
        
        for category, results in categories.items():
            working_count = sum(1 for result in results.values() if result.get("success", False))
            total_count = len(results)
            status = "✅ WORKING" if working_count == total_count else f"⚠️ {working_count}/{total_count} WORKING"
            print(f"  {category}: {status}")
        
        # Critical Issues Analysis
        critical_endpoints = ["/health", "/browse", "/chat", "/enhanced/system/overview"]
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and any(endpoint in r["endpoint"] for endpoint in critical_endpoints)]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  - {failure['method']} {failure['endpoint']}: {failure['details']}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Previously failing endpoints analysis
        previously_failing = test_results["previously_failing"]
        fixed_count = sum(1 for result in previously_failing.values() if result.get("success", False))
        print(f"\n🔧 PREVIOUSLY FAILING ENDPOINTS: {fixed_count}/{len(previously_failing)} NOW WORKING")
        
        for endpoint, result in previously_failing.items():
            status = "✅ FIXED" if result.get("success") else "❌ STILL FAILING"
            print(f"  - {endpoint}: {status}")
        
        # Performance Analysis
        avg_response_time = sum(r["response_time"] for r in self.test_results) / len(self.test_results)
        print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.2f}s")
        
        slow_endpoints = [r for r in self.test_results if r["response_time"] > 2.0]
        if slow_endpoints:
            print("⚠️ SLOW ENDPOINTS (>2s):")
            for slow in slow_endpoints:
                print(f"  - {slow['method']} {slow['endpoint']}: {slow['response_time']:.2f}s")
        
        return test_results

async def main():
    """Main test execution"""
    async with FocusedAetherTester() as tester:
        results = await tester.run_focused_tests()
        
        # Save detailed results
        with open('/app/focused_test_results.json', 'w') as f:
            json.dump({
                "test_summary": results,
                "detailed_results": tester.test_results,
                "test_session": tester.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "backend_url": BASE_URL
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/focused_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())