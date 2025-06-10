#!/usr/bin/env python3
"""
LINC Quick Endpoint Testing Suite
Simple endpoint testing with basic authentication
"""

import urllib.request
import urllib.parse
import json
import time
import base64
from datetime import datetime

# Configuration - UPDATE THESE WITH YOUR ACTUAL DEPLOYMENT URL
BASE_URL = "https://your-actual-deployment-url.onrender.com"  # ⚠️ UPDATE THIS
API_V1 = f"{BASE_URL}/api/v1"

# Test with basic auth (username:password)
TEST_CREDENTIALS = "your-admin:your-password"  # ⚠️ UPDATE THIS

def make_request(method, endpoint, data=None, auth=True):
    """Make HTTP request with basic authentication"""
    url = f"{API_V1}{endpoint}"
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'LINC-Endpoint-Tester/1.0'
    }
    
    # Add basic auth if needed
    if auth:
        auth_string = base64.b64encode(TEST_CREDENTIALS.encode()).decode()
        headers['Authorization'] = f'Basic {auth_string}'
    
    # Prepare request
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            duration = time.time() - start_time
            response_data = response.read().decode('utf-8')
            try:
                parsed_data = json.loads(response_data)
            except:
                parsed_data = response_data
            
            return {
                'success': True,
                'status_code': response.status,
                'data': parsed_data,
                'duration': duration
            }
    except urllib.error.HTTPError as e:
        duration = time.time() - start_time
        try:
            error_data = e.read().decode('utf-8')
            try:
                parsed_error = json.loads(error_data)
            except:
                parsed_error = error_data
        except:
            parsed_error = str(e)
        
        return {
            'success': False,
            'status_code': e.code,
            'error': parsed_error,
            'duration': duration
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'status_code': None,
            'error': str(e),
            'duration': duration
        }

def test_endpoints():
    """Test all main endpoints"""
    results = []
    start_time = datetime.now()
    
    print("🚀 LINC Quick Endpoint Test")
    print(f"📍 Target: {BASE_URL}")
    print(f"⏰ Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Define test endpoints
    test_cases = [
        # Health endpoints (no auth)
        ("GET", "/", False, "Root endpoint"),
        ("GET", "/health", False, "Health check"),
        ("GET", "/health/database", False, "Database health"),
        
        # Authentication required endpoints
        ("GET", "/auth/profile", True, "User profile"),
        ("GET", "/users/current", True, "Current user info"),
        ("GET", "/users/", True, "List users"),
        ("GET", "/countries/config", True, "Country configuration"),
        ("GET", "/countries/features", True, "Country features"),
        ("GET", "/countries/license-types", True, "License types"),
        ("GET", "/persons/search?q=test", True, "Person search"),
        ("GET", "/licenses/", True, "List licenses"),
        ("GET", "/licenses/types", True, "License types"),
        ("GET", "/files/storage/health", True, "File storage health"),
        ("GET", "/files/storage/metrics", True, "Storage metrics"),
        
        # Admin endpoints
        ("POST", "/admin/init-database", True, "Initialize database"),
    ]
    
    for method, endpoint, needs_auth, description in test_cases:
        print(f"Testing: {method} {endpoint} - {description}")
        
        result = make_request(method, endpoint, auth=needs_auth)
        
        # Log result
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration_ms = round(result['duration'] * 1000, 2)
        
        print(f"  {status} ({result['status_code']}) {duration_ms}ms")
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('detail', str(error_msg))
            print(f"    Error: {error_msg}")
        
        # Store result
        results.append({
            'endpoint': endpoint,
            'method': method,
            'description': description,
            'success': result['success'],
            'status_code': result['status_code'],
            'duration_ms': duration_ms,
            'error': result.get('error') if not result['success'] else None,
            'response_summary': _summarize_response(result.get('data')) if result['success'] else None
        })
        
        # Small delay between requests
        time.sleep(0.1)
    
    # Generate summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    passed = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])
    success_rate = (passed / len(results) * 100) if results else 0
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print(f"⏱️ Total Duration: {total_duration:.2f}s")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in results:
            if not result['success']:
                print(f"   • {result['method']} {result['endpoint']} - {result['error']}")
    
    # Generate detailed report
    report = {
        'test_summary': {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': round(total_duration, 2),
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'success_rate_percent': round(success_rate, 2),
            'base_url': BASE_URL
        },
        'detailed_results': results
    }
    
    # Save report
    report_filename = f"linc_quick_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved: {report_filename}")
    print("🎉 Testing Complete!")
    
    return report

def _summarize_response(data):
    """Summarize response data"""
    if isinstance(data, dict):
        return {
            'type': 'object',
            'keys': list(data.keys()),
            'success': data.get('success'),
            'service': data.get('service'),
            'status': data.get('status')
        }
    elif isinstance(data, list):
        return {
            'type': 'array',
            'length': len(data)
        }
    else:
        return {'type': type(data).__name__}

if __name__ == "__main__":
    test_endpoints() 