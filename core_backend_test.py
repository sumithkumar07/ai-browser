#!/usr/bin/env python3
"""
AETHER Core Backend API Testing - Focus on Core Functionality
Testing the core endpoints that should be working based on review request
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://feature-benchmark.preview.emergentagent.com"

class CoreBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AETHER-Core-Tester/1.0'
        })
        self.results = []
        
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
        print(f"{status_emoji} {method} {endpoint} - {status_code} ({response_time:.3f}s)")
        if details and len(details) < 100:
            print(f"    {details}")
        
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Dict = None, expected_status: List[int] = [200, 201]) -> Dict:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
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
                details = f"Success: {response_data.get('success', 'N/A')}"
            except:
                details = f"Text response: {response.text[:50]}..."
                
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

    def test_core_browser_functionality(self):
        """Test Core Browser APIs that should be working"""
        print("\n🌐 Testing Core Browser Functionality...")
        
        # 1. Health Check
        self.test_endpoint("/api/health", "GET")
        
        # 2. Browse Page
        browse_data = {
            "url": "https://example.com",
            "title": "Example Domain"
        }
        self.test_endpoint("/api/browse", "POST", browse_data)
        
        # 3. Chat with AI
        chat_data = {
            "message": "Hello, can you help me test this API?",
            "session_id": str(uuid.uuid4()),
            "current_url": "https://example.com"
        }
        self.test_endpoint("/api/chat", "POST", chat_data)
        
        # 4. Get Recent Tabs
        self.test_endpoint("/api/recent-tabs", "GET")
        
        # 5. Get Recommendations
        self.test_endpoint("/api/recommendations", "GET")
        
        # 6. Clear History
        self.test_endpoint("/api/clear-history", "DELETE")

    def test_enhanced_features(self):
        """Test Enhanced Features that were previously failing"""
        print("\n🚀 Testing Enhanced Features...")
        
        # 1. Summarize Page
        summarize_data = {
            "url": "https://example.com",
            "length": "medium"
        }
        self.test_endpoint("/api/summarize", "POST", summarize_data)
        
        # 2. Search Suggestions
        search_data = {
            "query": "artificial intelligence"
        }
        self.test_endpoint("/api/search-suggestions", "POST", search_data)
        
        # 3. Create Workflow
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow for API validation",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "extract", "selector": "h1"}
            ]
        }
        self.test_endpoint("/api/create-workflow", "POST", workflow_data)

    def test_voice_commands(self):
        """Test Voice Command Features"""
        print("\n🎤 Testing Voice Commands...")
        
        # 1. Process Voice Command
        voice_data = {
            "command": "navigate to google.com"
        }
        self.test_endpoint("/api/voice-command", "POST", voice_data)

    def test_automation_features(self):
        """Test Basic Automation Features"""
        print("\n⚙️ Testing Automation Features...")
        
        # 1. Create Automation Task
        automation_data = {
            "task_name": "Test Data Extraction",
            "url": "https://example.com",
            "action_type": "extract_text",
            "parameters": {
                "selector": "h1",
                "attribute": "text"
            }
        }
        self.test_endpoint("/api/automate-task", "POST", automation_data)

    def run_core_test(self):
        """Run core functionality tests"""
        print("🚀 Starting AETHER Core Backend API Testing")
        print(f"Backend URL: {self.base_url}")
        print("=" * 70)
        
        start_time = time.time()
        
        # Test core functionality first
        self.test_core_browser_functionality()
        
        # Test enhanced features
        self.test_enhanced_features()
        
        # Test voice commands
        self.test_voice_commands()
        
        # Test automation
        self.test_automation_features()
        
        total_time = time.time() - start_time
        
        # Generate summary
        return self.generate_summary(total_time)

    def generate_summary(self, total_time: float):
        """Generate test summary"""
        print("\n" + "=" * 70)
        print("📊 CORE BACKEND TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if total_tests > 0:
            avg_response_time = sum(r['response_time'] for r in self.results) / total_tests
            print(f"Average Response Time: {avg_response_time:.3f}s")
        
        # Show working endpoints
        working_endpoints = [r for r in self.results if r['success']]
        if working_endpoints:
            print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
            for result in working_endpoints:
                print(f"  • {result['method']} {result['endpoint']} - {result['status_code']}")
        
        # Show failed endpoints
        failed_endpoints = [r for r in self.results if not r['success']]
        if failed_endpoints:
            print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
            for result in failed_endpoints:
                print(f"  • {result['method']} {result['endpoint']} - {result['status_code']}")
        
        # Assessment
        if success_rate >= 80:
            print("\n🎉 ASSESSMENT: Core functionality is working well!")
        elif success_rate >= 50:
            print("\n⚠️ ASSESSMENT: Partial functionality - some core features working")
        else:
            print("\n❌ ASSESSMENT: Major issues found - core functionality not working")
            
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_time': total_time,
            'results': self.results
        }

def main():
    """Main test execution"""
    tester = CoreBackendTester()
    summary = tester.run_core_test()
    
    # Save results to file
    with open('/app/core_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Core test results saved to: /app/core_test_results.json")
    
    return summary['success_rate'] >= 50

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)