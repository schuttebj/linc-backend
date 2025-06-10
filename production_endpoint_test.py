#!/usr/bin/env python3
"""
LINC Production Server Endpoint Test
Run this directly on the production server to test localhost endpoints
"""

import urllib.request
import json
import time
import base64
from datetime import datetime

# Configuration for production server (localhost)
BASE_URL = "http://localhost:8000"  # Production server runs on port 8000
API_V1 = f"{BASE_URL}/api/v1"

# Basic auth credentials
TEST_CREDENTIALS = "admin:admin123"  # Update with actual credentials

def test_localhost_endpoints():
    """Test endpoints on localhost (production server)"""
    
    print("🚀 LINC Production Server Endpoint Test")
    print(f"📍 Target: {BASE_URL} (localhost)")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    results = []
    
    # Test endpoints
    test_cases = [
        ("GET", "/", False, "Root endpoint"),
        ("GET", "/health", False, "Health check"),
        ("GET", "/health/database", False, "Database health"),
        ("GET", "/api/v1/docs", False, "API Documentation"),
        ("GET", "/api/v1/auth/profile", True, "User profile"),
        ("GET", "/api/v1/countries/config", True, "Country config"),
        ("GET", "/api/v1/files/storage/health", True, "File storage health"),
    ]
    
    for method, endpoint, needs_auth, description in test_cases:
        print(f"Testing: {method} {endpoint}")
        
        # Prepare request
        url = f"{BASE_URL}{endpoint}"
        headers = {'User-Agent': 'LINC-Production-Test/1.0'}
        
        if needs_auth:
            auth_string = base64.b64encode(TEST_CREDENTIALS.encode()).decode()
            headers['Authorization'] = f'Basic {auth_string}'
        
        try:
            req = urllib.request.Request(url, headers=headers)
            start_time = time.time()
            
            with urllib.request.urlopen(req, timeout=10) as response:
                duration = (time.time() - start_time) * 1000
                data = response.read().decode('utf-8')
                
                print(f"  ✅ PASS ({response.status}) {duration:.1f}ms")
                results.append({
                    'endpoint': endpoint,
                    'status': 'PASS',
                    'status_code': response.status,
                    'duration_ms': duration
                })
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            print(f"  ❌ FAIL - {str(e)}")
            results.append({
                'endpoint': endpoint,
                'status': 'FAIL',
                'error': str(e),
                'duration_ms': duration
            })
        
        time.sleep(0.1)  # Small delay
    
    # Summary
    passed = len([r for r in results if r['status'] == 'PASS'])
    failed = len(results) - passed
    
    print("\n" + "=" * 50)
    print("📊 PRODUCTION TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in results:
            if result['status'] == 'FAIL':
                print(f"   • {result['endpoint']} - {result['error']}")
    
    return results

if __name__ == "__main__":
    test_localhost_endpoints() 