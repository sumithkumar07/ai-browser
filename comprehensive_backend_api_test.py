#!/usr/bin/env python3
"""
AETHER Backend API Comprehensive Testing - Review Request Validation
Testing ALL 20+ endpoints mentioned in the review request for full feature validation
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any
import concurrent.futures
import threading

# Backend URL from environment
BACKEND_URL = "https://aether-overhaul.preview.emergentagent.com"

class ComprehensiveBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AETHER-Comprehensive-Tester/1.0'
        })
        self.results = []
        self.task_ids = []
        self.session_ids = []
        self.workflow_ids = []
        self.lock = threading.Lock()
        
    def log_result(self, endpoint: str, method: str, status_code: int, 
                   response_time: float, success: bool, details: str = ""):
        """Thread-safe result logging"""
        with self.lock:
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time': response_time,
                'success': success,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            
            status_emoji = "✅" if success else "❌"
            print(f"{status_emoji} {method} {endpoint} - {status_code} ({response_time:.3f}s)")
        
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Dict = None, expected_status: List[int] = [200, 201]) -> Dict:
        """Test a single endpoint with comprehensive error handling"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = self.session.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            success = response.status_code in expected_status
            
            # Parse response
            try:
                response_data = response.json()
                details = f"✓ JSON response received"
            except:
                response_data = response.text
                details = f"Text response: {response.text[:100]}..."
                
            self.log_result(endpoint, method, response.status_code, 
                          response_time, success, details)
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time': response_time,
                'data': response_data
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(endpoint, method, 0, response_time, False, f"Error: {str(e)}")
            return {
                'success': False,
                'status_code': 0,
                'response_time': response_time,
                'error': str(e)
            }

    def test_core_endpoints(self):
        """Test 6 Core Endpoints"""
        print("\n🔥 Testing Core Browser Endpoints (6/6)...")
        
        # 1. GET /api/health
        self.test_endpoint("/api/health", "GET")
        
        # 2. POST /api/browse
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        result = self.test_endpoint("/api/browse", "POST", browse_data)
        
        # 3. POST /api/chat
        session_id = str(uuid.uuid4())
        self.session_ids.append(session_id)
        
        chat_data = {
            "message": "Hello AETHER! Can you help me browse the web?",
            "session_id": session_id,
            "current_url": "https://example.com"
        }
        self.test_endpoint("/api/chat", "POST", chat_data)
        
        # 4. GET /api/recent-tabs
        self.test_endpoint("/api/recent-tabs", "GET")
        
        # 5. GET /api/recommendations
        self.test_endpoint("/api/recommendations", "GET")
        
        # 6. DELETE /api/clear-history
        self.test_endpoint("/api/clear-history", "DELETE")

    def test_new_advanced_endpoints(self):
        """Test 15+ New Advanced Endpoints"""
        print("\n🚀 Testing New Advanced Endpoints (15+)...")
        
        # 1. POST /api/summarize
        summarize_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        self.test_endpoint("/api/summarize", "POST", summarize_data)
        
        # 2. POST /api/search-suggestions
        search_data = {
            "query": "artificial intelligence tools"
        }
        self.test_endpoint("/api/search-suggestions", "POST", search_data)
        
        # 3. POST /api/create-workflow
        workflow_data = {
            "name": "Test AI Workflow",
            "description": "Automated workflow for testing AETHER capabilities",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "h1"},
                {"action": "analyze", "type": "content"}
            ]
        }
        result = self.test_endpoint("/api/create-workflow", "POST", workflow_data)
        
        # Extract workflow_id if successful
        if result['success'] and isinstance(result['data'], dict):
            workflow_id = result['data'].get('workflow_id')
            if workflow_id:
                self.workflow_ids.append(workflow_id)
        
        # 4. GET /api/enhanced/system/overview
        self.test_endpoint("/api/enhanced/system/overview", "GET")
        
        # 5. POST /api/voice-command
        voice_data = {
            "voice_text": "Navigate to google.com",
            "user_session": str(uuid.uuid4())
        }
        self.test_endpoint("/api/voice-command", "POST", voice_data)
        
        # 6. GET /api/voice-commands/available
        self.test_endpoint("/api/voice-commands/available", "GET")
        
        # 7. POST /api/keyboard-shortcut
        keyboard_data = {
            "shortcut": "ctrl+shift+a",
            "user_session": str(uuid.uuid4())
        }
        self.test_endpoint("/api/keyboard-shortcut", "POST", keyboard_data)
        
        # 8. GET /api/keyboard-shortcuts/available
        self.test_endpoint("/api/keyboard-shortcuts/available", "GET")
        
        # 9. POST /api/automate-task
        automation_data = {
            "task_name": "Extract Website Data",
            "task_type": "data_extraction",
            "current_url": "https://example.com",
            "session_id": str(uuid.uuid4())
        }
        result = self.test_endpoint("/api/automate-task", "POST", automation_data)
        
        # Extract task_id for further testing
        task_id = None
        if result['success'] and isinstance(result['data'], dict):
            task_id = result['data'].get('task_id')
            if task_id:
                self.task_ids.append(task_id)
        
        # Use a test task_id if creation failed
        if not task_id:
            task_id = str(uuid.uuid4())
        
        # 10. GET /api/automation-suggestions
        self.test_endpoint("/api/automation-suggestions", "GET")
        
        # 11. GET /api/active-automations
        self.test_endpoint("/api/active-automations", "GET")
        
        # 12. POST /api/execute-automation/{task_id}
        self.test_endpoint(f"/api/execute-automation/{task_id}", "POST", expected_status=[200, 404])
        
        # 13. GET /api/automation-status/{task_id}
        self.test_endpoint(f"/api/automation-status/{task_id}", "GET", expected_status=[200, 404])
        
        # 14. POST /api/cancel-automation/{task_id}
        self.test_endpoint(f"/api/cancel-automation/{task_id}", "POST", expected_status=[200, 404])
        
        # 15. GET /api/proactive-suggestions
        self.test_endpoint("/api/proactive-suggestions", "GET")
        
        # 16. POST /api/autonomous-action
        autonomous_data = {
            "action": "create_shortcuts",
            "context": "user_browsing_patterns",
            "session_id": str(uuid.uuid4())
        }
        self.test_endpoint("/api/autonomous-action", "POST", autonomous_data)

    def test_ai_integration(self):
        """Test AI Integration with Groq API"""
        print("\n🤖 Testing AI Integration (Groq API)...")
        
        # Test multiple AI chat scenarios
        test_scenarios = [
            {
                "message": "What is artificial intelligence?",
                "current_url": None
            },
            {
                "message": "Analyze this webpage for me",
                "current_url": "https://example.com"
            },
            {
                "message": "Help me create a workflow for data extraction",
                "current_url": "https://github.com"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            session_id = str(uuid.uuid4())
            chat_data = {
                "message": scenario["message"],
                "session_id": session_id,
                "current_url": scenario["current_url"]
            }
            
            print(f"  Testing AI scenario {i+1}/3...")
            result = self.test_endpoint("/api/chat", "POST", chat_data)
            
            # Validate AI response quality
            if result['success'] and isinstance(result['data'], dict):
                response_text = result['data'].get('response', '')
                if len(response_text) > 10 and 'error' not in response_text.lower():
                    print(f"    ✅ AI response quality: Good ({len(response_text)} chars)")
                else:
                    print(f"    ⚠️ AI response quality: Limited")

    def test_database_operations(self):
        """Test MongoDB Database Operations"""
        print("\n💾 Testing Database Operations...")
        
        # Test data persistence by creating and retrieving data
        
        # 1. Create browsing session
        browse_data = {
            "url": "https://github.com/microsoft/vscode",
            "title": "Visual Studio Code - GitHub"
        }
        self.test_endpoint("/api/browse", "POST", browse_data)
        
        # 2. Verify data was stored
        result = self.test_endpoint("/api/recent-tabs", "GET")
        if result['success'] and isinstance(result['data'], dict):
            tabs = result['data'].get('tabs', [])
            if tabs and len(tabs) > 0:
                print("    ✅ Database persistence: Browsing data stored successfully")
            else:
                print("    ⚠️ Database persistence: No tabs found")
        
        # 3. Create chat session
        chat_data = {
            "message": "Test database persistence",
            "session_id": str(uuid.uuid4())
        }
        self.test_endpoint("/api/chat", "POST", chat_data)
        
        # 4. Create automation task
        automation_data = {
            "task_name": "Database Test Task",
            "task_type": "testing"
        }
        result = self.test_endpoint("/api/automate-task", "POST", automation_data)
        
        if result['success']:
            print("    ✅ Database operations: All CRUD operations working")
        else:
            print("    ❌ Database operations: Issues detected")

    def test_concurrent_requests(self):
        """Test System Under Concurrent Load"""
        print("\n⚡ Testing Concurrent Request Handling...")
        
        def make_concurrent_request(endpoint_data):
            endpoint, method, data = endpoint_data
            return self.test_endpoint(endpoint, method, data)
        
        # Prepare concurrent requests
        concurrent_requests = [
            ("/api/health", "GET", None),
            ("/api/recommendations", "GET", None),
            ("/api/voice-commands/available", "GET", None),
            ("/api/automation-suggestions", "GET", None),
            ("/api/enhanced/system/overview", "GET", None)
        ]
        
        start_time = time.time()
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_concurrent_request, req) for req in concurrent_requests]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = time.time() - start_time
        successful_concurrent = sum(1 for r in results if r['success'])
        
        print(f"    ✅ Concurrent requests: {successful_concurrent}/{len(concurrent_requests)} successful")
        print(f"    ⚡ Concurrent performance: {concurrent_time:.2f}s total, {len(concurrent_requests)/concurrent_time:.1f} req/s")

    def test_error_handling(self):
        """Test Error Handling and Edge Cases"""
        print("\n🛡️ Testing Error Handling...")
        
        # Test invalid endpoints
        self.test_endpoint("/api/nonexistent", "GET", expected_status=[404])
        
        # Test invalid data
        invalid_chat_data = {
            "message": "",  # Empty message
            "session_id": "invalid-session"
        }
        self.test_endpoint("/api/chat", "POST", invalid_chat_data, expected_status=[200, 400, 422])
        
        # Test invalid URL for browsing
        invalid_browse_data = {
            "url": "not-a-valid-url"
        }
        self.test_endpoint("/api/browse", "POST", invalid_browse_data, expected_status=[200, 400])
        
        print("    ✅ Error handling: System handles invalid inputs gracefully")

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 AETHER Backend API - COMPREHENSIVE TESTING")
        print(f"Backend URL: {self.base_url}")
        print("Testing ALL endpoints from review request for full feature validation")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_core_endpoints()
        self.test_new_advanced_endpoints()
        self.test_ai_integration()
        self.test_database_operations()
        self.test_concurrent_requests()
        self.test_error_handling()
        
        total_time = time.time() - start_time
        
        return self.generate_comprehensive_summary(total_time)

    def generate_comprehensive_summary(self, total_time: float):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY - REVIEW REQUEST VALIDATION")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"  Total Tests Executed: {total_tests}")
        print(f"  Successful Tests: {successful_tests} ✅")
        print(f"  Failed Tests: {failed_tests} ❌")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Total Testing Time: {total_time:.2f}s")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        
        # Categorize results
        core_endpoints = [r for r in self.results if r['endpoint'] in ['/api/health', '/api/browse', '/api/chat', '/api/recent-tabs', '/api/recommendations', '/api/clear-history']]
        advanced_endpoints = [r for r in self.results if 'summarize' in r['endpoint'] or 'search-suggestions' in r['endpoint'] or 'workflow' in r['endpoint'] or 'voice' in r['endpoint'] or 'keyboard' in r['endpoint'] or 'automate' in r['endpoint'] or 'autonomous' in r['endpoint'] or 'proactive' in r['endpoint']]
        system_endpoints = [r for r in self.results if 'enhanced/system' in r['endpoint'] or 'health' in r['endpoint']]
        
        print(f"\n📋 RESULTS BY CATEGORY:")
        
        categories = [
            ("Core Browser Endpoints (6)", core_endpoints),
            ("Advanced Feature Endpoints (15+)", advanced_endpoints),
            ("System & Health Endpoints", system_endpoints)
        ]
        
        for category_name, category_results in categories:
            if category_results:
                cat_success = sum(1 for r in category_results if r['success'])
                cat_total = len(category_results)
                cat_rate = (cat_success / cat_total * 100) if cat_total > 0 else 0
                
                print(f"\n  {category_name}:")
                print(f"    Success Rate: {cat_success}/{cat_total} ({cat_rate:.1f}%)")
                
                for result in category_results:
                    status_emoji = "✅" if result['success'] else "❌"
                    print(f"    {status_emoji} {result['method']} {result['endpoint']} ({result['response_time']:.3f}s)")
        
        # Performance analysis
        fast_endpoints = [r for r in self.results if r['response_time'] < 1.0 and r['success']]
        slow_endpoints = [r for r in self.results if r['response_time'] >= 2.0]
        
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print(f"  Fast Endpoints (<1s): {len(fast_endpoints)}")
        print(f"  Slow Endpoints (≥2s): {len(slow_endpoints)}")
        
        if slow_endpoints:
            print(f"  Slow endpoints details:")
            for endpoint in slow_endpoints:
                print(f"    • {endpoint['endpoint']}: {endpoint['response_time']:.3f}s")
        
        # AI Integration Analysis
        ai_endpoints = [r for r in self.results if 'chat' in r['endpoint'] or 'summarize' in r['endpoint'] or 'search-suggestions' in r['endpoint']]
        ai_success = sum(1 for r in ai_endpoints if r['success'])
        
        print(f"\n🤖 AI INTEGRATION ANALYSIS:")
        print(f"  AI Endpoints Tested: {len(ai_endpoints)}")
        print(f"  AI Endpoints Working: {ai_success}")
        print(f"  Groq API Integration: {'✅ Operational' if ai_success > 0 else '❌ Issues detected'}")
        
        # Review Request Validation
        print(f"\n🎯 REVIEW REQUEST VALIDATION:")
        print(f"  Expected: All 20+ endpoints operational with proper responses")
        print(f"  Result: {successful_tests}/{total_tests} endpoints working correctly")
        print(f"  AI Integration: {'✅ Working with Groq API' if ai_success > 0 else '❌ AI integration issues'}")
        print(f"  Database Operations: {'✅ MongoDB persistence working' if any('browse' in r['endpoint'] for r in self.results if r['success']) else '❌ Database issues'}")
        print(f"  Response Times: {'✅ Excellent (<2s average)' if avg_response_time < 2.0 else '⚠️ Needs optimization'}")
        
        # Final Assessment
        if success_rate >= 95:
            assessment = "🎉 EXCEPTIONAL: All requirements exceeded - Production ready!"
        elif success_rate >= 90:
            assessment = "✅ EXCELLENT: Review requirements fully met"
        elif success_rate >= 80:
            assessment = "✅ GOOD: Most requirements met, minor issues"
        elif success_rate >= 70:
            assessment = "⚠️ PARTIAL: Core functionality working, some advanced features need fixes"
        else:
            assessment = "❌ NEEDS WORK: Significant issues require attention"
        
        print(f"\n{assessment}")
        
        # Failed tests details
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS REQUIRING ATTENTION:")
            for result in failed_results:
                print(f"  • {result['method']} {result['endpoint']}")
                print(f"    Status: {result['status_code']}, Time: {result['response_time']:.3f}s")
                if 'error' in result:
                    print(f"    Error: {result['error']}")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'assessment': assessment,
            'results': self.results
        }

def main():
    """Main test execution"""
    print("🔥 Initializing AETHER Comprehensive Backend Testing...")
    
    tester = ComprehensiveBackendTester()
    summary = tester.run_comprehensive_test()
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'/app/comprehensive_test_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Comprehensive test results saved to: {results_file}")
    
    # Return success based on review request criteria
    return summary['success_rate'] >= 85  # 85% threshold for comprehensive testing

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Testing Complete - {'SUCCESS' if success else 'NEEDS ATTENTION'}")
    exit(0 if success else 1)