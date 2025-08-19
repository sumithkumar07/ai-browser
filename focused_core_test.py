#!/usr/bin/env python3
"""
AETHER Browser - Focused Core Functionality Testing
Tests the specific endpoints mentioned in the review request
"""

import asyncio
import aiohttp
import json
import uuid
import time
from datetime import datetime

# Backend URL from review request
BASE_URL = "https://smooth-evolution.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

class CoreAPITester:
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
    
    async def test_api_call(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200):
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
    
    async def test_core_browser_functionality(self):
        """Test core browser endpoints mentioned in review request"""
        print("\n🌐 TESTING CORE BROWSER FUNCTIONALITY")
        print("=" * 60)
        
        results = {}
        
        # 1. Health check
        print("\n1. Testing Health Check...")
        health_result = await self.test_api_call("GET", "/health")
        results["health"] = health_result.get("success", False)
        
        # 2. Browse endpoint
        print("\n2. Testing Browse Functionality...")
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        browse_result = await self.test_api_call("POST", "/browse", browse_data)
        results["browse"] = browse_result.get("success", False)
        
        # 3. Recent tabs
        print("\n3. Testing Recent Tabs...")
        recent_tabs_result = await self.test_api_call("GET", "/recent-tabs")
        results["recent_tabs"] = recent_tabs_result.get("success", False)
        
        # 4. Recommendations
        print("\n4. Testing Recommendations...")
        recommendations_result = await self.test_api_call("GET", "/recommendations")
        results["recommendations"] = recommendations_result.get("success", False)
        
        # 5. Clear history
        print("\n5. Testing Clear History...")
        clear_result = await self.test_api_call("DELETE", "/clear-history")
        results["clear_history"] = clear_result.get("success", False)
        
        return results
    
    async def test_ai_chat_functionality(self):
        """Test AI chat endpoint"""
        print("\n🤖 TESTING AI CHAT FUNCTIONALITY")
        print("=" * 60)
        
        results = {}
        
        # Test basic chat
        print("\n1. Testing Basic Chat...")
        chat_data = {
            "message": "Hello, can you help me browse the web more efficiently?",
            "session_id": self.session_id
        }
        basic_chat = await self.test_api_call("POST", "/chat", chat_data)
        results["basic_chat"] = basic_chat.get("success", False)
        
        # Test context-aware chat
        print("\n2. Testing Context-Aware Chat...")
        context_chat_data = {
            "message": "What is this website about?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        context_chat = await self.test_api_call("POST", "/chat", context_chat_data)
        results["context_chat"] = context_chat.get("success", False)
        
        # Test session continuity
        print("\n3. Testing Session Continuity...")
        followup_chat_data = {
            "message": "Can you remember what we just discussed?",
            "session_id": self.session_id
        }
        followup_chat = await self.test_api_call("POST", "/chat", followup_chat_data)
        results["session_continuity"] = followup_chat.get("success", False)
        
        return results
    
    async def test_enhanced_features(self):
        """Test enhanced features that are working"""
        print("\n⚡ TESTING ENHANCED FEATURES")
        print("=" * 60)
        
        results = {}
        
        # Test summarization
        print("\n1. Testing Page Summarization...")
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        summary_result = await self.test_api_call("POST", "/summarize", summary_data)
        results["summarize"] = summary_result.get("success", False)
        
        # Test search suggestions
        print("\n2. Testing Search Suggestions...")
        search_data = {"query": "artificial intelligence"}
        search_result = await self.test_api_call("POST", "/search-suggestions", search_data)
        results["search_suggestions"] = search_result.get("success", False)
        
        # Test voice commands
        print("\n3. Testing Voice Commands...")
        voice_data = {"command": "navigate to google.com"}
        voice_result = await self.test_api_call("POST", "/voice-command", voice_data)
        results["voice_commands"] = voice_result.get("success", False)
        
        # Test system overview
        print("\n4. Testing System Overview...")
        system_result = await self.test_api_call("GET", "/enhanced/system/overview")
        results["system_overview"] = system_result.get("success", False)
        
        return results
    
    async def test_database_connectivity(self):
        """Test MongoDB database operations"""
        print("\n💾 TESTING DATABASE CONNECTIVITY")
        print("=" * 60)
        
        results = {}
        
        # Test data persistence through browse -> recent tabs flow
        print("\n1. Testing Data Persistence...")
        
        # Clear existing data
        await self.test_api_call("DELETE", "/clear-history")
        
        # Add some browsing data
        browse_data = {
            "url": "https://github.com",
            "title": "GitHub"
        }
        browse_result = await self.test_api_call("POST", "/browse", browse_data)
        
        # Check if data persists in recent tabs
        tabs_result = await self.test_api_call("GET", "/recent-tabs")
        
        if browse_result.get("success") and tabs_result.get("success"):
            tabs_data = tabs_result.get("data", {}).get("tabs", [])
            if tabs_data and any("github.com" in tab.get("url", "") for tab in tabs_data):
                results["data_persistence"] = True
                print("✅ Data persistence working - GitHub tab found in recent tabs")
            else:
                results["data_persistence"] = False
                print("❌ Data persistence failed - GitHub tab not found")
        else:
            results["data_persistence"] = False
            print("❌ Data persistence test failed - browse or tabs endpoint failed")
        
        return results
    
    async def test_performance_metrics(self):
        """Test performance of working endpoints"""
        print("\n⚡ TESTING PERFORMANCE METRICS")
        print("=" * 60)
        
        # Test multiple concurrent requests
        print("\n1. Testing Concurrent Requests...")
        
        tasks = []
        for i in range(3):
            chat_data = {
                "message": f"Test message {i+1}",
                "session_id": f"{self.session_id}_{i}"
            }
            task = self.test_api_call("POST", "/chat", chat_data)
            tasks.append(task)
        
        concurrent_results = await asyncio.gather(*tasks)
        successful_concurrent = sum(1 for result in concurrent_results if result.get("success"))
        
        print(f"Concurrent requests: {successful_concurrent}/3 successful")
        
        # Calculate average response times
        response_times = [r["response_time"] for r in self.test_results if r["status"] == "PASS"]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"Average response time: {avg_response_time:.2f}s")
        
        return {"concurrent_success": successful_concurrent >= 2, "avg_response_time": avg_response_time if response_times else 0}
    
    async def run_focused_tests(self):
        """Run focused tests on core functionality"""
        print(f"\n🚀 AETHER BROWSER - FOCUSED CORE FUNCTIONALITY TESTING")
        print(f"Backend URL: {BASE_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        all_results = {}
        
        # Test core browser functionality
        all_results["core_browser"] = await self.test_core_browser_functionality()
        
        # Test AI chat functionality
        all_results["ai_chat"] = await self.test_ai_chat_functionality()
        
        # Test enhanced features
        all_results["enhanced_features"] = await self.test_enhanced_features()
        
        # Test database connectivity
        all_results["database"] = await self.test_database_connectivity()
        
        # Test performance
        all_results["performance"] = await self.test_performance_metrics()
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📋 FOCUSED TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n🎯 CORE FUNCTIONALITY STATUS:")
        
        # Core browser endpoints
        core_endpoints = ["health", "browse", "recent_tabs", "recommendations", "clear_history"]
        core_working = sum(1 for endpoint in core_endpoints if all_results["core_browser"].get(endpoint, False))
        print(f"  Core Browser APIs: {core_working}/5 working ({'✅' if core_working >= 4 else '❌'})")
        
        # AI chat functionality
        ai_endpoints = ["basic_chat", "context_chat", "session_continuity"]
        ai_working = sum(1 for endpoint in ai_endpoints if all_results["ai_chat"].get(endpoint, False))
        print(f"  AI Chat System: {ai_working}/3 working ({'✅' if ai_working >= 2 else '❌'})")
        
        # Enhanced features
        enhanced_endpoints = ["summarize", "search_suggestions", "voice_commands", "system_overview"]
        enhanced_working = sum(1 for endpoint in enhanced_endpoints if all_results["enhanced_features"].get(endpoint, False))
        print(f"  Enhanced Features: {enhanced_working}/4 working ({'✅' if enhanced_working >= 2 else '❌'})")
        
        # Database connectivity
        db_working = all_results["database"].get("data_persistence", False)
        print(f"  Database Operations: {'✅ Working' if db_working else '❌ Issues'}")
        
        # Performance
        perf_working = all_results["performance"].get("concurrent_success", False)
        avg_time = all_results["performance"].get("avg_response_time", 0)
        print(f"  Performance: {'✅ Good' if perf_working and avg_time < 2.0 else '⚠️ Needs attention'} (avg: {avg_time:.2f}s)")
        
        # Overall assessment
        critical_working = core_working >= 4 and ai_working >= 2 and db_working
        print(f"\n🏆 OVERALL STATUS: {'✅ PRODUCTION READY' if critical_working else '⚠️ NEEDS ATTENTION'}")
        
        if not critical_working:
            print("\n🔧 CRITICAL ISSUES:")
            if core_working < 4:
                failed_core = [endpoint for endpoint in core_endpoints if not all_results["core_browser"].get(endpoint, False)]
                print(f"  - Core browser endpoints failing: {failed_core}")
            if ai_working < 2:
                failed_ai = [endpoint for endpoint in ai_endpoints if not all_results["ai_chat"].get(endpoint, False)]
                print(f"  - AI chat endpoints failing: {failed_ai}")
            if not db_working:
                print(f"  - Database connectivity issues")
        
        return all_results

async def main():
    """Main test execution"""
    async with CoreAPITester() as tester:
        results = await tester.run_focused_tests()
        
        # Save results
        with open('/app/focused_core_test_results.json', 'w') as f:
            json.dump({
                "test_summary": results,
                "detailed_results": tester.test_results,
                "test_session": tester.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "backend_url": BASE_URL
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: /app/focused_core_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())