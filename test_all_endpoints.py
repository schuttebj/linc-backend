#!/usr/bin/env python3
"""
LINC Comprehensive Endpoint Testing Suite
Tests all API endpoints and generates a master validation report
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
from io import BytesIO
from pathlib import Path

# Configuration
BASE_URL = "https://linc-backend.onrender.com"  # Update with your actual deployment URL
API_V1 = f"{BASE_URL}/api/v1"

# Test credentials (update with actual test credentials)
TEST_ADMIN = {
    "username": "admin",
    "password": "admin123"
}

TEST_USER = {
    "username": "testuser",
    "password": "testpass123"
}

class EndpointTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_result(self, endpoint: str, method: str, status: str, 
                   status_code: int = None, response_data: Any = None, 
                   error: str = None, duration: float = None):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status,  # PASS, FAIL, SKIP
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2) if duration else None,
            "error": error,
            "response_summary": self._summarize_response(response_data) if response_data else None
        }
        self.test_results.append(result)
        
        # Print real-time status
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        duration_str = f" ({result['duration_ms']}ms)" if duration else ""
        print(f"{status_symbol} {method} {endpoint}{duration_str}")
        if error:
            print(f"   Error: {error}")

    def _summarize_response(self, data: Any) -> Dict[str, Any]:
        """Create a summary of response data"""
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "success": data.get("success"),
                "message": data.get("message", "")[:100]
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "first_item_keys": list(data[0].keys()) if data and isinstance(data[0], dict) else None
            }
        else:
            return {"type": type(data).__name__, "value": str(data)[:100]}

    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple[bool, Any, float]:
        """Make HTTP request and return success, data, duration"""
        start_time = time.time()
        try:
            url = f"{self.api_v1}{endpoint}"
            response = self.session.request(method, url, timeout=30, **kwargs)
            duration = time.time() - start_time
            
            try:
                data = response.json()
            except:
                data = response.text
            
            return response.status_code < 400, {
                "status_code": response.status_code,
                "data": data
            }, duration
            
        except Exception as e:
            duration = time.time() - start_time
            return False, {"error": str(e)}, duration

    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        print("\n🔐 Authenticating as admin...")
        
        # Try JWT login first
        success, response, duration = self.make_request(
            "POST", "/auth/login",
            json=TEST_ADMIN
        )
        
        if success and "access_token" in response.get("data", {}):
            self.admin_token = response["data"]["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            self.log_result("/auth/login", "POST", "PASS", 
                          response["status_code"], response["data"], duration=duration)
            return True
        
        # Try basic auth as fallback
        auth = base64.b64encode(f"{TEST_ADMIN['username']}:{TEST_ADMIN['password']}".encode()).decode()
        self.session.headers.update({"Authorization": f"Basic {auth}"})
        
        # Test basic auth with profile endpoint
        success, response, duration = self.make_request("GET", "/auth/profile")
        if success:
            self.log_result("/auth/profile", "GET", "PASS", 
                          response["status_code"], response["data"], duration=duration)
            return True
        
        self.log_result("/auth/login", "POST", "FAIL", 
                       response.get("status_code"), None, 
                       error="Authentication failed", duration=duration)
        return False

    def test_health_endpoints(self):
        """Test all health and system endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/health/database"),
        ]
        
        for method, endpoint in endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔑 Testing Authentication Endpoints...")
        
        # Test user registration (if enabled)
        test_user_data = {
            "username": "endpoint_test_user",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        endpoints_to_test = [
            ("POST", "/auth/register", {"json": test_user_data}),
            ("GET", "/auth/profile", {}),
            ("GET", "/auth/permissions", {}),
            ("GET", "/auth/roles", {}),
        ]
        
        for method, endpoint, kwargs in endpoints_to_test:
            success, response, duration = self.make_request(method, endpoint, **kwargs)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def test_user_management_endpoints(self):
        """Test user management endpoints"""
        print("\n👥 Testing User Management Endpoints...")
        
        endpoints = [
            ("GET", "/users/"),
            ("GET", "/users/current"),
            ("GET", "/users/roles"),
            ("GET", "/users/permissions"),
        ]
        
        for method, endpoint in endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def test_country_endpoints(self):
        """Test country configuration endpoints"""
        print("\n🌍 Testing Country Configuration Endpoints...")
        
        endpoints = [
            ("GET", "/countries/config"),
            ("GET", "/countries/features"),
            ("GET", "/countries/license-types"),
            ("GET", "/countries/id-document-types"),
            ("GET", "/countries/printing-config"),
        ]
        
        for method, endpoint in endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def test_person_management_endpoints(self):
        """Test person management endpoints"""
        print("\n👤 Testing Person Management Endpoints...")
        
        # Test search endpoint
        success, response, duration = self.make_request("GET", "/persons/search?q=test")
        status = "PASS" if success else "FAIL"
        error = response.get("error") if not success else None
        self.log_result("/persons/search", "GET", status, 
                       response.get("status_code"), response.get("data"), 
                       error=error, duration=duration)
        
        # Test person creation
        test_person = {
            "identification_type": "RSA_ID",
            "identification_number": "9001010001088",
            "first_name": "John",
            "surname": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "nationality": "ZA"
        }
        
        success, response, duration = self.make_request("POST", "/persons/", json=test_person)
        status = "PASS" if success else "FAIL"
        error = response.get("error") if not success else None
        person_id = None
        
        if success and response.get("data", {}).get("id"):
            person_id = response["data"]["id"]
        
        self.log_result("/persons/", "POST", status, 
                       response.get("status_code"), response.get("data"), 
                       error=error, duration=duration)
        
        # If person was created, test other person endpoints
        if person_id:
            person_endpoints = [
                ("GET", f"/persons/{person_id}"),
                ("GET", f"/persons/{person_id}/history"),
                ("GET", f"/persons/{person_id}/applications"),
                ("GET", f"/persons/{person_id}/licenses"),
            ]
            
            for method, endpoint in person_endpoints:
                success, response, duration = self.make_request(method, endpoint)
                status = "PASS" if success else "FAIL"
                error = response.get("error") if not success else None
                
                self.log_result(endpoint, method, status, 
                              response.get("status_code"), response.get("data"), 
                              error=error, duration=duration)

    def test_license_endpoints(self):
        """Test license management endpoints"""
        print("\n📄 Testing License Management Endpoints...")
        
        endpoints = [
            ("GET", "/licenses/"),
            ("GET", "/licenses/types"),
            ("GET", "/licenses/applications"),
            ("GET", "/licenses/test-centers"),
        ]
        
        for method, endpoint in endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def test_file_storage_endpoints(self):
        """Test file storage endpoints"""
        print("\n📁 Testing File Storage Endpoints...")
        
        # Test storage health and metrics (admin only)
        endpoints = [
            ("GET", "/files/storage/health"),
            ("GET", "/files/storage/metrics"),
            ("GET", "/files/storage/largest-files"),
        ]
        
        for method, endpoint in endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)
        
        # Test file upload (create a small test image)
        test_image_data = self.create_test_image()
        files = {"file": ("test_photo.jpg", test_image_data, "image/jpeg")}
        
        # Test citizen photo upload
        success, response, duration = self.make_request(
            "POST", "/files/upload/citizen-photo?citizen_id=test-citizen-001",
            files=files
        )
        status = "PASS" if success else "FAIL"
        error = response.get("error") if not success else None
        
        self.log_result("/files/upload/citizen-photo", "POST", status, 
                       response.get("status_code"), response.get("data"), 
                       error=error, duration=duration)

    def create_test_image(self) -> BytesIO:
        """Create a small test image for file upload testing"""
        # Create a simple 10x10 pixel image data
        image_data = BytesIO()
        # Simple JPEG header + minimal data (this is a mock - real implementation would use PIL)
        test_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB'
        image_data.write(test_data)
        image_data.seek(0)
        return image_data

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n⚙️ Testing Admin Endpoints...")
        
        admin_endpoints = [
            ("POST", "/admin/init-database"),
            ("GET", "/health/database"),
        ]
        
        for method, endpoint in admin_endpoints:
            success, response, duration = self.make_request(method, endpoint)
            status = "PASS" if success else "FAIL"
            error = response.get("error") if not success else None
            
            self.log_result(endpoint, method, status, 
                          response.get("status_code"), response.get("data"), 
                          error=error, duration=duration)

    def generate_master_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by endpoint category
        categories = {
            "Health & System": [r for r in self.test_results if any(cat in r["endpoint"] for cat in ["/", "/health"])],
            "Authentication": [r for r in self.test_results if "/auth" in r["endpoint"]],
            "User Management": [r for r in self.test_results if "/users" in r["endpoint"]],
            "Country Config": [r for r in self.test_results if "/countries" in r["endpoint"]],
            "Person Management": [r for r in self.test_results if "/persons" in r["endpoint"]],
            "License Management": [r for r in self.test_results if "/licenses" in r["endpoint"]],
            "File Storage": [r for r in self.test_results if "/files" in r["endpoint"]],
            "Admin Functions": [r for r in self.test_results if "/admin" in r["endpoint"]],
        }
        
        report = {
            "test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": round(total_duration, 2),
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate_percent": round(success_rate, 2),
                "base_url": self.base_url
            },
            "category_results": {},
            "detailed_results": self.test_results,
            "failed_tests": [r for r in self.test_results if r["status"] == "FAIL"],
            "performance_summary": {
                "fastest_response": min([r["duration_ms"] for r in self.test_results if r["duration_ms"]], default=0),
                "slowest_response": max([r["duration_ms"] for r in self.test_results if r["duration_ms"]], default=0),
                "average_response": round(sum([r["duration_ms"] for r in self.test_results if r["duration_ms"]]) / 
                                        len([r for r in self.test_results if r["duration_ms"]]), 2) if self.test_results else 0
            }
        }
        
        # Add category summaries
        for category, results in categories.items():
            if results:
                category_passed = len([r for r in results if r["status"] == "PASS"])
                category_total = len(results)
                report["category_results"][category] = {
                    "total": category_total,
                    "passed": category_passed,
                    "failed": category_total - category_passed,
                    "success_rate": round((category_passed / category_total * 100), 2) if category_total > 0 else 0
                }
        
        return report

    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"🚀 Starting LINC Endpoint Testing Suite")
        print(f"📍 Target: {self.base_url}")
        print(f"⏰ Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Test basic health endpoints (no auth required)
        self.test_health_endpoints()
        
        # Step 2: Authenticate
        if not self.authenticate_admin():
            print("❌ Authentication failed - some tests will be skipped")
        
        # Step 3: Run all endpoint tests
        self.test_authentication_endpoints()
        self.test_user_management_endpoints()
        self.test_country_endpoints()
        self.test_person_management_endpoints()
        self.test_license_endpoints()
        self.test_file_storage_endpoints()
        self.test_admin_endpoints()
        
        # Step 4: Generate and save report
        report = self.generate_master_report()
        
        # Save report to file
        report_filename = f"linc_endpoint_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {report['test_summary']['passed']}")
        print(f"❌ Failed: {report['test_summary']['failed']}")
        print(f"⏭️ Skipped: {report['test_summary']['skipped']}")
        print(f"📊 Success Rate: {report['test_summary']['success_rate_percent']}%")
        print(f"⏱️ Total Duration: {report['test_summary']['total_duration_seconds']}s")
        print(f"📄 Detailed Report: {report_filename}")
        
        if report['test_summary']['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for failed_test in report['failed_tests']:
                print(f"   • {failed_test['method']} {failed_test['endpoint']} - {failed_test['error']}")
        
        print("\n🎉 Testing Complete!")
        return report

def main():
    """Main testing function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    tester = EndpointTester(base_url)
    report = tester.run_all_tests()
    
    # Return appropriate exit code
    sys.exit(0 if report['test_summary']['failed'] == 0 else 1)

if __name__ == "__main__":
    main() 