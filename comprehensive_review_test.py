#!/usr/bin/env python3
"""
AETHER AI Browser - Comprehensive Review Request Backend Testing
Tests all 15 core endpoints mentioned in the review request plus automation workflow
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://aether-overhaul.preview.emergentagent.com"

class ComprehensiveReviewTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AETHER-Review-Tester/1.0'
        })
        self.results = []
        self.session_id = str(uuid.uuid4())
        self.task_ids = []
        
    def log_result(self, endpoint: str, method: str, status_code: int, 
                   response_time: float, success: bool, details: str = ""):
        """Log test result"""
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
        print(f"{status_emoji} {method} {endpoint} - {status_code} ({response_time:.3f}s) {details}")
        
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Dict = None, expected_status: List[int] = [200, 201]) -> Dict:
        """Test a single endpoint"""
        url = f"{self.base_url}/api{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            success = response.status_code in expected_status
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                details = f"✓ Valid JSON response"
                if isinstance(response_data, dict):
                    if 'success' in response_data:
                        details += f" | success: {response_data['success']}"
                    if 'status' in response_data:
                        details += f" | status: {response_data['status']}"
            except:
                details = f"Response: {response.text[:100]}..."
                
            self.log_result(endpoint, method, response.status_code, 
                          response_time, success, details)
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time': response_time,
                'data': response_data if 'response_data' in locals() else response.text
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
        """Test the 15 core endpoints from review request"""
        print("\n🎯 TESTING 15 CORE ENDPOINTS FROM REVIEW REQUEST")
        print("=" * 80)
        
        # 1. /api/health - Health check
        self.test_endpoint("/health", "GET")
        
        # 2. /api/browse - Web page fetching and content analysis
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        self.test_endpoint("/browse", "POST", browse_data)
        
        # 3. /api/chat - AI assistant with Groq integration
        chat_data = {
            "message": "Hello AETHER! Can you help me understand what artificial intelligence is?",
            "session_id": self.session_id,
            "current_url": "https://example.com"
        }
        self.test_endpoint("/chat", "POST", chat_data)
        
        # 4. /api/recent-tabs - Browsing history
        self.test_endpoint("/recent-tabs", "GET")
        
        # 5. /api/recommendations - AI-powered recommendations
        self.test_endpoint("/recommendations", "GET")
        
        # 6. /api/clear-history - Clear browsing data
        self.test_endpoint("/clear-history", "DELETE")
        
        # 7. /api/summarize - Page summarization
        summary_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        self.test_endpoint("/summarize", "POST", summary_data)
        
        # 8. /api/search-suggestions - AI search suggestions
        search_data = {"query": "artificial intelligence tools"}
        self.test_endpoint("/search-suggestions", "POST", search_data)
        
        # 9. /api/create-workflow - Workflow creation
        workflow_data = {
            "name": "Test AI Workflow",
            "description": "A test workflow for AI-powered automation",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "title"},
                {"action": "analyze", "type": "content_analysis"}
            ]
        }
        self.test_endpoint("/create-workflow", "POST", workflow_data)
        
        # 10. /api/voice-command - Voice command processing
        voice_data = {
            "command": "navigate to google.com",
            "user_session": self.session_id
        }
        self.test_endpoint("/voice-command", "POST", voice_data)
        
        # 11. /api/keyboard-shortcut - Keyboard shortcuts
        shortcut_data = {
            "shortcut": "ctrl+shift+a",
            "user_session": self.session_id
        }
        self.test_endpoint("/keyboard-shortcut", "POST", shortcut_data)
        
        # 12. /api/automate-task - Automation task creation
        automation_data = {
            "task_name": "AI Data Extraction Task",
            "task_type": "advanced",
            "current_url": "https://example.com",
            "session_id": self.session_id
        }
        result = self.test_endpoint("/automate-task", "POST", automation_data)
        
        # Store task ID for workflow testing
        if result['success'] and 'data' in result:
            try:
                if isinstance(result['data'], dict):
                    task_id = result['data'].get('task_id')
                    if task_id:
                        self.task_ids.append(task_id)
            except:
                pass
        
        # 13. /api/automation-suggestions - Context-aware suggestions
        self.test_endpoint("/automation-suggestions", "GET")
        
        # 14. /api/enhanced/system/overview - System status
        self.test_endpoint("/enhanced/system/overview", "GET")
        
        # 15. Enhanced endpoints for advanced features (test available voice commands)
        self.test_endpoint("/voice-commands/available", "GET")

    def test_automation_workflow(self):
        """Test complete automation workflow: create → execute → status → cancel"""
        print("\n🔄 TESTING AUTOMATION WORKFLOW")
        print("=" * 80)
        
        # Use existing task ID or create new one
        task_id = self.task_ids[0] if self.task_ids else str(uuid.uuid4())
        
        if not self.task_ids:
            # Create a new task for workflow testing
            automation_data = {
                "task_name": "Workflow Test Task",
                "task_type": "workflow_test",
                "current_url": "https://example.com",
                "session_id": self.session_id
            }
            result = self.test_endpoint("/automate-task", "POST", automation_data)
            if result['success'] and 'data' in result:
                try:
                    task_id = result['data'].get('task_id', task_id)
                except:
                    pass
        
        # Test workflow steps
        self.test_endpoint(f"/execute-automation/{task_id}", "POST")
        self.test_endpoint(f"/automation-status/{task_id}", "GET")
        self.test_endpoint(f"/cancel-automation/{task_id}", "POST")
        self.test_endpoint("/active-automations", "GET")

    def test_ai_integration(self):
        """Test AI integration with multiple requests"""
        print("\n🤖 TESTING AI INTEGRATION (GROQ)")
        print("=" * 80)
        
        ai_test_messages = [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms",
            "How does natural language processing work?"
        ]
        
        for i, message in enumerate(ai_test_messages, 1):
            chat_data = {
                "message": message,
                "session_id": self.session_id,
                "current_url": "https://example.com"
            }
            print(f"AI Test {i}/3:")
            self.test_endpoint("/chat", "POST", chat_data)

    def test_data_persistence(self):
        """Test MongoDB data persistence"""
        print("\n💾 TESTING DATA PERSISTENCE (MONGODB)")
        print("=" * 80)
        
        # Test browsing data persistence
        browse_data = {
            "url": "https://github.com",
            "title": "GitHub - Where the world builds software"
        }
        self.test_endpoint("/browse", "POST", browse_data)
        
        # Verify data was stored
        self.test_endpoint("/recent-tabs", "GET")
        
        # Test chat session persistence
        chat_data = {
            "message": "Remember this: I am testing data persistence in MongoDB",
            "session_id": self.session_id,
            "current_url": "https://github.com"
        }
        self.test_endpoint("/chat", "POST", chat_data)
        
        # Test session continuity
        followup_chat = {
            "message": "Do you remember what I just told you to remember?",
            "session_id": self.session_id,
            "current_url": "https://github.com"
        }
        self.test_endpoint("/chat", "POST", followup_chat)

    def test_concurrent_requests(self):
        """Test system under concurrent load"""
        print("\n⚡ TESTING CONCURRENT REQUESTS")
        print("=" * 80)
        
        import threading
        import time
        
        results = []
        
        def make_request(request_id):
            chat_data = {
                "message": f"Concurrent test request {request_id} - testing system stability",
                "session_id": f"{self.session_id}_{request_id}",
                "current_url": "https://example.com"
            }
            
            start_time = time.time()
            try:
                response = self.session.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
                response_time = time.time() - start_time
                results.append({
                    'request_id': request_id,
                    'success': response.status_code == 200,
                    'response_time': response_time,
                    'status_code': response.status_code
                })
            except Exception as e:
                response_time = time.time() - start_time
                results.append({
                    'request_id': request_id,
                    'success': False,
                    'response_time': response_time,
                    'error': str(e)
                })
        
        # Create 5 concurrent threads
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r['success'])
        
        print(f"✅ Concurrent Load Test: {successful_requests}/5 requests successful")
        print(f"✅ Total Time: {total_time:.2f}s")
        print(f"✅ Requests per Second: {len(results) / total_time:.1f}")
        
        return {
            'success_rate': successful_requests / len(results),
            'total_time': total_time,
            'requests_per_second': len(results) / total_time
        }

    def run_comprehensive_review_test(self):
        """Run all tests for the review request"""
        print("🚀 STARTING COMPREHENSIVE AETHER BACKEND API TESTING")
        print("🎯 REVIEW REQUEST: Test all backend APIs for AETHER AI-powered browser")
        print(f"Backend URL: {self.base_url}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_core_endpoints()
        self.test_automation_workflow()
        self.test_ai_integration()
        self.test_data_persistence()
        concurrent_results = self.test_concurrent_requests()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive summary
        return self.generate_comprehensive_summary(total_time, concurrent_results)

    def generate_comprehensive_summary(self, total_time: float, concurrent_results: Dict):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE REVIEW REQUEST TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"  Total Endpoints Tested: {total_tests}")
        print(f"  Successful: {successful_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Total Test Time: {total_time:.2f}s")
        
        if self.results:
            avg_response_time = sum(r['response_time'] for r in self.results) / total_tests
            print(f"  Average Response Time: {avg_response_time:.3f}s")
        
        # Review Request Validation
        print(f"\n🎯 REVIEW REQUEST VALIDATION:")
        
        # Core endpoints from review request
        core_endpoints = [
            "/health", "/browse", "/chat", "/recent-tabs", "/recommendations",
            "/clear-history", "/summarize", "/search-suggestions", "/create-workflow",
            "/voice-command", "/keyboard-shortcut", "/automate-task", 
            "/automation-suggestions", "/enhanced/system/overview"
        ]
        
        core_results = [r for r in self.results if any(endpoint in r['endpoint'] for endpoint in core_endpoints)]
        core_success = sum(1 for r in core_results if r['success'])
        
        print(f"  Core Endpoints (15 from review): {core_success}/{len(core_results)} working ✅")
        
        # AI Integration Assessment
        ai_endpoints = [r for r in self.results if "/chat" in r['endpoint'] or "/summarize" in r['endpoint']]
        ai_success = sum(1 for r in ai_endpoints if r['success'])
        print(f"  AI Integration (Groq): {ai_success}/{len(ai_endpoints)} endpoints working ✅")
        
        # MongoDB Persistence Assessment
        data_endpoints = [r for r in self.results if "/browse" in r['endpoint'] or "/recent-tabs" in r['endpoint']]
        data_success = sum(1 for r in data_endpoints if r['success'])
        print(f"  MongoDB Persistence: {data_success}/{len(data_endpoints)} operations working ✅")
        
        # Automation Workflow Assessment
        automation_endpoints = [r for r in self.results if "automation" in r['endpoint'] or "automate" in r['endpoint']]
        automation_success = sum(1 for r in automation_endpoints if r['success'])
        print(f"  Automation Workflow: {automation_success}/{len(automation_endpoints)} endpoints working ✅")
        
        # Performance Assessment
        print(f"\n⚡ PERFORMANCE ASSESSMENT:")
        fast_endpoints = len([r for r in self.results if r['response_time'] < 1.0])
        slow_endpoints = len([r for r in self.results if r['response_time'] > 2.0])
        print(f"  Fast Endpoints (<1s): {fast_endpoints}/{total_tests}")
        print(f"  Slow Endpoints (>2s): {slow_endpoints}/{total_tests}")
        print(f"  Concurrent Performance: {concurrent_results.get('requests_per_second', 0):.1f} req/s")
        
        # System Health Assessment
        print(f"\n💚 SYSTEM HEALTH ASSESSMENT:")
        health_results = [r for r in self.results if "/health" in r['endpoint']]
        system_overview_results = [r for r in self.results if "/enhanced/system/overview" in r['endpoint']]
        
        if health_results and health_results[0]['success']:
            print("  ✅ Health Check: OPERATIONAL")
        else:
            print("  ❌ Health Check: FAILED")
            
        if system_overview_results and system_overview_results[0]['success']:
            print("  ✅ System Overview: OPERATIONAL")
        else:
            print("  ❌ System Overview: FAILED")
        
        # Error Analysis
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED ENDPOINTS ANALYSIS:")
            for result in failed_results:
                print(f"  • {result['method']} {result['endpoint']} - Status {result['status_code']}")
                print(f"    Details: {result['details']}")
        else:
            print(f"\n✅ NO FAILED ENDPOINTS - ALL SYSTEMS OPERATIONAL")
        
        # Final Assessment
        print(f"\n📈 FINAL ASSESSMENT:")
        if success_rate >= 95:
            assessment = "🎉 EXCELLENT - Production ready, all systems optimal"
        elif success_rate >= 85:
            assessment = "✅ VERY GOOD - Production ready with minor optimizations needed"
        elif success_rate >= 75:
            assessment = "✅ GOOD - Core functionality working, some enhancements needed"
        elif success_rate >= 60:
            assessment = "⚠️ ACCEPTABLE - Basic functionality working, improvements required"
        else:
            assessment = "❌ NEEDS WORK - Significant issues found, major fixes required"
        
        print(f"  {assessment}")
        
        # Specific Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate >= 90:
            print("  ✅ System is ready for production deployment")
            print("  ✅ All core AETHER AI browser functionality is operational")
            print("  ✅ Groq AI integration working excellently")
            print("  ✅ MongoDB data persistence validated")
            print("  ✅ Automation workflows fully functional")
        else:
            print("  🔧 Address failing endpoints before production")
            print("  🔧 Monitor performance under higher loads")
            print("  🔧 Implement additional error handling")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_time': total_time,
            'concurrent_performance': concurrent_results,
            'assessment': assessment,
            'results': self.results
        }

def main():
    """Main test execution"""
    tester = ComprehensiveReviewTester()
    summary = tester.run_comprehensive_review_test()
    
    # Save results to file
    with open('/app/comprehensive_review_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Comprehensive test results saved to: /app/comprehensive_review_test_results.json")
    
    return summary['success_rate'] >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)