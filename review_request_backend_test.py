#!/usr/bin/env python3
"""
AETHER AI Browser - Review Request Backend API Testing
Tests all endpoints mentioned in the comprehensive review request
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

class ReviewRequestTester:
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

    async def test_core_browser_apis(self):
        """Test Core Browser APIs (5 endpoints from review request)"""
        print("\n🌐 TESTING CORE BROWSER APIs")
        print("=" * 60)
        
        results = {}
        
        # POST /api/browse - Web page fetching and content analysis
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        results["browse"] = await self.test_api_call("POST", "/browse", browse_data)
        
        # POST /api/chat - AI assistant with Groq integration
        chat_data = {
            "message": "Hello, can you help me understand what this website is about?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        results["chat"] = await self.test_api_call("POST", "/chat", chat_data)
        
        # GET /api/recent-tabs - Browsing history retrieval
        results["recent_tabs"] = await self.test_api_call("GET", "/recent-tabs")
        
        # GET /api/recommendations - AI-powered recommendations
        results["recommendations"] = await self.test_api_call("GET", "/recommendations")
        
        # DELETE /api/clear-history - Clear browsing data
        results["clear_history"] = await self.test_api_call("DELETE", "/clear-history")
        
        return results

    async def test_enhanced_features(self):
        """Test Enhanced Features (8 endpoints from server.py)"""
        print("\n🚀 TESTING ENHANCED FEATURES")
        print("=" * 60)
        
        results = {}
        
        # POST /api/summarize - Webpage summarization
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        results["summarize"] = await self.test_api_call("POST", "/summarize", summary_data)
        
        # POST /api/search-suggestions - AI search suggestions
        search_data = {"query": "artificial intelligence tools"}
        results["search_suggestions"] = await self.test_api_call("POST", "/search-suggestions", search_data)
        
        # POST /api/create-workflow - Workflow creation
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow for validation",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "title"}
            ]
        }
        results["create_workflow"] = await self.test_api_call("POST", "/create-workflow", workflow_data)
        
        # POST /api/enhanced/automation/create-advanced - Advanced automation
        advanced_automation_data = {
            "type": "advanced_data_extraction",
            "target_url": "https://example.com",
            "extraction_rules": [
                {"selector": "title", "attribute": "text"},
                {"selector": "h1", "attribute": "text"}
            ],
            "user_session": self.session_id
        }
        results["create_advanced_automation"] = await self.test_api_call("POST", "/enhanced/automation/create-advanced", advanced_automation_data)
        
        # POST /api/enhanced/workflows/template/create - Workflow templates
        template_data = {
            "name": "Test Template",
            "description": "A test workflow template",
            "template_type": "data_extraction",
            "steps": [
                {"action": "navigate", "url": "{{target_url}}"},
                {"action": "extract", "selector": "{{selector}}"}
            ],
            "parameters": ["target_url", "selector"]
        }
        results["create_workflow_template"] = await self.test_api_call("POST", "/enhanced/workflows/template/create", template_data)
        
        # POST /api/enhanced/integrations/oauth/initiate - OAuth flows
        oauth_data = {
            "provider": "test_provider",
            "redirect_uri": "https://example.com/callback",
            "scopes": ["read", "write"],
            "user_session": self.session_id
        }
        results["oauth_initiate"] = await self.test_api_call("POST", "/enhanced/integrations/oauth/initiate", oauth_data)
        
        # POST /api/enhanced/integrations/api-key/store - API key storage
        api_key_data = {
            "name": "Test Integration",
            "type": "api_service",
            "api_key": "test_api_key_12345"
        }
        results["store_api_key"] = await self.test_api_call("POST", "/enhanced/integrations/api-key/store", api_key_data)
        
        # GET /api/enhanced/system/overview - System status
        results["system_overview"] = await self.test_api_call("GET", "/enhanced/system/overview")
        
        return results

    async def test_voice_keyboard_features(self):
        """Test Voice & Keyboard Features (3 endpoints)"""
        print("\n🎤 TESTING VOICE & KEYBOARD FEATURES")
        print("=" * 60)
        
        results = {}
        
        # POST /api/voice-command - Voice command processing
        voice_data = {
            "command": "navigate to google.com",
            "user_session": self.session_id,
            "context": {"current_url": "https://example.com"}
        }
        results["voice_command"] = await self.test_api_call("POST", "/voice-command", voice_data)
        
        # GET /api/voice-commands/available - Available voice commands
        results["available_voice_commands"] = await self.test_api_call("GET", "/voice-commands/available")
        
        # POST /api/keyboard-shortcut - Keyboard shortcuts
        shortcut_data = {
            "shortcut": "ctrl+h",
            "user_session": self.session_id
        }
        results["keyboard_shortcut"] = await self.test_api_call("POST", "/keyboard-shortcut", shortcut_data)
        
        return results

    async def test_health_performance(self):
        """Test Health & Performance (1 endpoint)"""
        print("\n💚 TESTING HEALTH & PERFORMANCE")
        print("=" * 60)
        
        results = {}
        
        # GET /api/health - Health check
        results["health"] = await self.test_api_call("GET", "/health")
        
        return results

    async def test_concurrent_load(self):
        """Test concurrent requests handling"""
        print("\n🔄 TESTING CONCURRENT LOAD")
        print("=" * 60)
        
        # Create multiple concurrent chat requests
        chat_tasks = []
        for i in range(5):
            chat_data = {
                "message": f"Concurrent test message {i+1} - testing AI integration under load",
                "session_id": f"{self.session_id}_{i}",
                "current_url": "https://example.com"
            }
            task = self.test_api_call("POST", "/chat", chat_data)
            chat_tasks.append(task)
        
        # Wait for all concurrent requests to complete
        start_time = time.time()
        concurrent_results = await asyncio.gather(*chat_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        success_count = sum(1 for result in concurrent_results if isinstance(result, dict) and result.get("success"))
        
        print(f"Concurrent requests: {success_count}/{len(concurrent_results)} successful in {total_time:.2f}s")
        print(f"Requests per second: {len(concurrent_results) / total_time:.1f}")
        
        return {
            "concurrent_success_rate": success_count / len(concurrent_results),
            "total_time": total_time,
            "requests_per_second": len(concurrent_results) / total_time
        }

    async def test_data_persistence(self):
        """Test MongoDB data persistence"""
        print("\n💾 TESTING DATA PERSISTENCE")
        print("=" * 60)
        
        # Test browsing history persistence
        browse_data = {
            "url": "https://github.com",
            "title": "GitHub"
        }
        browse_result = await self.test_api_call("POST", "/browse", browse_data)
        
        # Verify data was stored by checking recent tabs
        tabs_result = await self.test_api_call("GET", "/recent-tabs")
        
        # Test chat session persistence
        chat_data = {
            "message": "This message should be persisted in MongoDB",
            "session_id": self.session_id,
            "current_url": "https://github.com"
        }
        chat_result = await self.test_api_call("POST", "/chat", chat_data)
        
        # Test another message in same session to verify history
        followup_chat_data = {
            "message": "Do you remember my previous message?",
            "session_id": self.session_id,
            "current_url": "https://github.com"
        }
        followup_result = await self.test_api_call("POST", "/chat", followup_chat_data)
        
        return {
            "browse_persistence": browse_result.get("success", False),
            "tabs_retrieval": tabs_result.get("success", False),
            "chat_persistence": chat_result.get("success", False),
            "session_continuity": followup_result.get("success", False)
        }

    async def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n⚠️ TESTING ERROR HANDLING")
        print("=" * 60)
        
        # Test invalid URL for browse
        invalid_browse_data = {
            "url": "not-a-valid-url",
            "title": "Invalid URL Test"
        }
        await self.test_api_call("POST", "/browse", invalid_browse_data, expected_status=400)
        
        # Test empty chat message
        empty_chat_data = {
            "message": "",
            "session_id": self.session_id
        }
        await self.test_api_call("POST", "/chat", empty_chat_data, expected_status=422)
        
        # Test invalid endpoint
        await self.test_api_call("GET", "/nonexistent-endpoint", expected_status=404)
        
        return True

    async def run_review_request_tests(self):
        """Run all tests specified in the review request"""
        print(f"\n🚀 STARTING COMPREHENSIVE BACKEND API TESTING")
        print(f"🎯 REVIEW REQUEST: Test all backend APIs end-to-end")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        start_time = time.time()
        test_results = {}
        
        # Test all categories from review request
        test_results["core_browser_apis"] = await self.test_core_browser_apis()
        test_results["enhanced_features"] = await self.test_enhanced_features()
        test_results["voice_keyboard_features"] = await self.test_voice_keyboard_features()
        test_results["health_performance"] = await self.test_health_performance()
        
        # Additional comprehensive tests
        test_results["concurrent_load"] = await self.test_concurrent_load()
        test_results["data_persistence"] = await self.test_data_persistence()
        test_results["error_handling"] = await self.test_error_handling()
        
        total_time = time.time() - start_time
        
        # COMPREHENSIVE SUMMARY
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE BACKEND API TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.successful_endpoints / self.total_endpoints_tested * 100) if self.total_endpoints_tested > 0 else 0
        
        print(f"Total Endpoints Tested: {self.total_endpoints_tested}")
        print(f"Successful: {self.successful_endpoints} ✅")
        print(f"Failed: {self.failed_endpoints} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Test Time: {total_time:.2f}s")
        
        if self.test_results:
            avg_response_time = sum(r['response_time'] for r in self.test_results) / len(self.test_results)
            print(f"Average Response Time: {avg_response_time:.2f}s")
        
        # Category Results
        print("\n🎯 REVIEW REQUEST CATEGORIES:")
        
        categories = {
            "Core Browser APIs (5 endpoints)": test_results["core_browser_apis"],
            "Enhanced Features (8 endpoints)": test_results["enhanced_features"], 
            "Voice & Keyboard Features (3 endpoints)": test_results["voice_keyboard_features"],
            "Health & Performance (1 endpoint)": test_results["health_performance"]
        }
        
        for category, results in categories.items():
            if isinstance(results, dict):
                working_count = sum(1 for result in results.values() if isinstance(result, dict) and result.get("success", False))
                total_count = len(results)
                status = "✅ ALL WORKING" if working_count == total_count else f"⚠️ {working_count}/{total_count} WORKING"
                print(f"  {category}: {status}")
        
        # AI Integration Validation
        print("\n🤖 AI INTEGRATION VALIDATION:")
        ai_endpoints = [r for r in self.test_results if "/chat" in r["endpoint"] or "/summarize" in r["endpoint"] or "/search-suggestions" in r["endpoint"]]
        ai_working = len([r for r in ai_endpoints if r["status"] == "PASS"])
        print(f"  Groq API Integration: {ai_working}/{len(ai_endpoints)} endpoints working")
        
        # MongoDB Persistence Validation
        print("\n💾 MONGODB PERSISTENCE VALIDATION:")
        persistence_results = test_results.get("data_persistence", {})
        if isinstance(persistence_results, dict):
            persistence_working = sum(1 for result in persistence_results.values() if result)
            print(f"  Data Persistence: {persistence_working}/{len(persistence_results)} tests passed")
        
        # Performance Analysis
        print("\n⚡ PERFORMANCE ANALYSIS:")
        if self.test_results:
            fast_endpoints = len([r for r in self.test_results if r["response_time"] < 1.0])
            slow_endpoints = len([r for r in self.test_results if r["response_time"] > 2.0])
            print(f"  Fast Endpoints (<1s): {fast_endpoints}")
            print(f"  Slow Endpoints (>2s): {slow_endpoints}")
        
        concurrent_results = test_results.get("concurrent_load", {})
        if isinstance(concurrent_results, dict) and "requests_per_second" in concurrent_results:
            print(f"  Concurrent Performance: {concurrent_results['requests_per_second']:.1f} req/s")
        
        # Critical Issues Analysis
        critical_endpoints = ["/health", "/browse", "/chat", "/enhanced/system/overview"]
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and any(endpoint in r["endpoint"] for endpoint in critical_endpoints)]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  - {failure['method']} {failure['endpoint']}: {failure['details']}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Underutilized Features Detection
        print("\n🔍 UNDERUTILIZED FEATURES DETECTION:")
        advanced_endpoints = [r for r in self.test_results if "enhanced" in r["endpoint"] or "workflow" in r["endpoint"] or "automation" in r["endpoint"]]
        advanced_working = len([r for r in advanced_endpoints if r["status"] == "PASS"])
        if advanced_working > 0:
            print(f"  Advanced Features Available: {advanced_working} enhanced endpoints working")
            print("  Recommendation: Frontend could utilize more advanced backend capabilities")
        else:
            print("  No advanced features detected or working")
        
        # Final Assessment
        print(f"\n📈 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("  🎉 EXCELLENT - All systems operational, production-ready")
        elif success_rate >= 80:
            print("  ✅ GOOD - Core functionality working, minor issues present")
        elif success_rate >= 70:
            print("  ⚠️ ACCEPTABLE - System functional but needs improvements")
        else:
            print("  ❌ NEEDS WORK - Significant issues found, requires attention")
        
        # Specific Recommendations
        print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
        if success_rate >= 90:
            print("  - System is ready for production deployment")
            print("  - Consider load testing with higher concurrent users")
            print("  - Monitor performance metrics in production")
        else:
            failing_endpoints = [r for r in self.test_results if r["status"] == "FAIL"]
            if failing_endpoints:
                print("  - Fix failing endpoints before production deployment")
                for failure in failing_endpoints[:3]:  # Show first 3 failures
                    print(f"    • {failure['method']} {failure['endpoint']}: {failure['details']}")
        
        return {
            "total_endpoints": self.total_endpoints_tested,
            "successful": self.successful_endpoints,
            "failed": self.failed_endpoints,
            "success_rate": success_rate,
            "total_time": total_time,
            "test_results": test_results
        }

async def main():
    """Main test execution"""
    async with ReviewRequestTester() as tester:
        results = await tester.run_review_request_tests()
        
        # Save detailed results
        with open('/app/review_request_test_results.json', 'w') as f:
            json.dump({
                "test_summary": results,
                "detailed_results": tester.test_results,
                "test_session": tester.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "backend_url": BASE_URL
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: /app/review_request_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())