#!/usr/bin/env python3
"""
Automated Authentication System Test Suite
Run with: python test_auth.py
"""

import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any

# Set environment variables for local testing
os.environ.update({
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
    'DB_NAME': 'zathdb',
    'DB_USER': 'amruthae',
    'DB_PASS': ''
})

BASE_URL = "http://localhost:8000"
test_results = []

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, success: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if success else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
    print(f"{Colors.BOLD}{name}{Colors.ENDC}: {status}")
    if details:
        print(f"  {Colors.BLUE}{details}{Colors.ENDC}")
    test_results.append((name, success))

async def test_endpoint(session: aiohttp.ClientSession, method: str, path: str, 
                       headers: Dict = None, data: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
    """Test an endpoint and return response"""
    url = f"{BASE_URL}{path}"
    
    if headers is None:
        headers = {}
    
    if data:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    
    async with session.request(method, url, headers=headers, data=data) as response:
        response_data = await response.json() if response.content_type == 'application/json' else await response.text()
        return {
            'status': response.status,
            'data': response_data,
            'headers': dict(response.headers)
        }

async def run_tests():
    """Run all authentication tests"""
    print(f"{Colors.BOLD}🔐 ZATH Authentication System Test Suite{Colors.ENDC}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print(f"\n{Colors.YELLOW}1. Testing Server Health{Colors.ENDC}")
        response = await test_endpoint(session, "GET", "/")
        success = response['status'] == 200 and "ZATH is listening" in str(response['data'])
        print_test("Health Check", success, f"Status: {response['status']}")
        
        # Test 2: Register User
        print(f"\n{Colors.YELLOW}2. Testing User Registration{Colors.ENDC}")
        import time
        user_data = {"email": f"automated-test-{int(time.time())}@example.com"}
        response = await test_endpoint(session, "POST", "/auth/register", data=user_data)
        success = response['status'] == 200 and 'api_key' in response['data']
        print_test("User Registration", success, f"Status: {response['status']}")
        
        if success:
            api_key = response['data']['api_key']
            user_id = response['data']['id']
            print(f"  Generated API Key: {api_key[:20]}...")
        else:
            print(f"  {Colors.RED}Registration failed, skipping subsequent tests{Colors.ENDC}")
            return
        
        # Test 3: Protected Endpoint Without Auth
        print(f"\n{Colors.YELLOW}3. Testing Protected Endpoint Without Authentication{Colors.ENDC}")
        response = await test_endpoint(session, "GET", "/protected")
        success = response['status'] == 401 and "API key required" in str(response['data'])
        print_test("Protected Endpoint - No Auth", success, f"Status: {response['status']}")
        
        # Test 4: Protected Endpoint With X-API-Key
        print(f"\n{Colors.YELLOW}4. Testing Protected Endpoint With X-API-Key Header{Colors.ENDC}")
        headers = {"X-API-Key": api_key}
        response = await test_endpoint(session, "GET", "/protected", headers=headers)
        success = response['status'] == 200 and 'user_id' in response['data']
        print_test("Protected Endpoint - X-API-Key", success, f"Status: {response['status']}")
        
        # Test 5: Protected Endpoint With Authorization Header
        print(f"\n{Colors.YELLOW}5. Testing Protected Endpoint With Authorization Header{Colors.ENDC}")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = await test_endpoint(session, "GET", "/protected", headers=headers)
        success = response['status'] == 200 and 'user_id' in response['data']
        print_test("Protected Endpoint - Authorization", success, f"Status: {response['status']}")
        
        # Test 6: Invalid API Key
        print(f"\n{Colors.YELLOW}6. Testing Invalid API Key{Colors.ENDC}")
        headers = {"X-API-Key": "invalid-key-123"}
        response = await test_endpoint(session, "GET", "/protected", headers=headers)
        success = response['status'] == 401 and "Invalid API key" in str(response['data'])
        print_test("Invalid API Key", success, f"Status: {response['status']}")
        
        # Test 7: Regenerate API Key
        print(f"\n{Colors.YELLOW}7. Testing API Key Regeneration{Colors.ENDC}")
        headers = {"X-API-Key": api_key}
        response = await test_endpoint(session, "POST", "/auth/regenerate-key", headers=headers)
        success = response['status'] == 200 and 'api_key' in response['data']
        print_test("API Key Regeneration", success, f"Status: {response['status']}")
        
        if success:
            new_api_key = response['data']['api_key']
            print(f"  New API Key: {new_api_key[:20]}...")
            
            # Test 8: Old Key No Longer Works
            print(f"\n{Colors.YELLOW}8. Testing Old API Key Invalidation{Colors.ENDC}")
            headers = {"X-API-Key": api_key}  # Old key
            response = await test_endpoint(session, "GET", "/protected", headers=headers)
            success = response['status'] == 401 and "Invalid API key" in str(response['data'])
            print_test("Old API Key Invalidation", success, f"Status: {response['status']}")
            
            # Test 9: New Key Works
            print(f"\n{Colors.YELLOW}9. Testing New API Key{Colors.ENDC}")
            headers = {"X-API-Key": new_api_key}  # New key
            response = await test_endpoint(session, "GET", "/protected", headers=headers)
            success = response['status'] == 200 and 'user_id' in response['data']
            print_test("New API Key Works", success, f"Status: {response['status']}")
        
        # Test 10: Duplicate Registration
        print(f"\n{Colors.YELLOW}10. Testing Duplicate Registration{Colors.ENDC}")
        duplicate_data = {"email": user_data["email"]}  # Use same email for duplicate test
        response = await test_endpoint(session, "POST", "/auth/register", data=duplicate_data)
        success = response['status'] == 400 and "already exists" in str(response['data'])
        print_test("Duplicate Registration", success, f"Status: {response['status']}")
        
        # Test 11: Invalid Email Format
        print(f"\n{Colors.YELLOW}11. Testing Invalid Email Format{Colors.ENDC}")
        invalid_data = {"email": "invalid-email"}
        response = await test_endpoint(session, "POST", "/auth/register", data=invalid_data)
        success = response['status'] == 422  # Validation error
        print_test("Invalid Email Format", success, f"Status: {response['status']}")
        
        # Test 12: Regenerate Key Without Auth
        print(f"\n{Colors.YELLOW}12. Testing Regenerate Key Without Authentication{Colors.ENDC}")
        response = await test_endpoint(session, "POST", "/auth/regenerate-key")
        success = response['status'] == 401 and "API key required" in str(response['data'])
        print_test("Regenerate Key - No Auth", success, f"Status: {response['status']}")

async def main():
    """Main test runner"""
    try:
        await run_tests()
        
        # Summary
        print(f"\n{Colors.BOLD}📊 Test Summary{Colors.ENDC}")
        print("=" * 30)
        
        passed = sum(1 for _, success in test_results if success)
        total = len(test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.ENDC}")
        print(f"Failed: {Colors.RED}{total - passed}{Colors.ENDC}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}🎉 All tests passed! Authentication system is working correctly.{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}❌ Some tests failed. Please check the implementation.{Colors.ENDC}")
            sys.exit(1)
            
    except aiohttp.ClientConnectorError:
        print(f"{Colors.RED}❌ Cannot connect to server. Make sure the server is running on {BASE_URL}{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Test execution failed: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
