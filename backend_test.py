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
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print(f"\n🚀 STARTING COMPREHENSIVE AETHER BACKEND API TESTING")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        test_results = {}
        
        # High Priority Tests
        test_results["core_browser"] = await self.test_core_browser_apis()
        test_results["ai_chat"] = await self.test_ai_chat_system()
        
        # Medium Priority Tests  
        test_results["automation"] = await self.test_automation_features()
        test_results["enhanced_ai"] = await self.test_enhanced_ai_features()
        
        # Low Priority Tests
        test_results["performance"] = await self.test_performance_health_monitoring()
        test_results["workflows"] = await self.test_workflow_features()
        test_results["integrations"] = await self.test_integration_features()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📊 FEATURE AREA RESULTS:")
        for feature, success in test_results.items():
            status = "✅ WORKING" if success else "❌ ISSUES FOUND"
            print(f"  {feature.replace('_', ' ').title()}: {status}")
        
        # Critical Issues
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and any(endpoint in r["endpoint"] for endpoint in ["/health", "/browse", "/chat"])]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  - {failure['method']} {failure['endpoint']}: {failure['details']}")
        
        # Performance Issues
        slow_endpoints = [r for r in self.test_results if r["response_time"] > 5.0]
        if slow_endpoints:
            print("\n⚠️ SLOW ENDPOINTS (>5s):")
            for slow in slow_endpoints:
                print(f"  - {slow['method']} {slow['endpoint']}: {slow['response_time']:.2f}s")
        
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