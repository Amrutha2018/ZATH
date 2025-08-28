#!/usr/bin/env python3
"""
Test script for callback retry logic
Tests the enhanced callback system with exponential backoff retries
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

class RetryTestHandler(BaseHTTPRequestHandler):
    """HTTP server to test callback retry logic"""
    
    received_callbacks = []
    fail_count = 0  # Number of times to fail before succeeding
    current_attempts = 0
    
    def do_POST(self):
        """Handle POST requests (callbacks) with configurable failure"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        RetryTestHandler.current_attempts += 1
        
        try:
            callback_data = json.loads(post_data.decode('utf-8'))
            RetryTestHandler.received_callbacks.append({
                'attempt': RetryTestHandler.current_attempts,
                'data': callback_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            print(f"📥 Received callback attempt {RetryTestHandler.current_attempts}: {callback_data}")
            
            # Fail the first N attempts, then succeed
            if RetryTestHandler.current_attempts <= RetryTestHandler.fail_count:
                print(f"❌ Intentionally failing attempt {RetryTestHandler.current_attempts}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Intentional failure"}).encode())
            else:
                print(f"✅ Succeeding on attempt {RetryTestHandler.current_attempts}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            
        except Exception as e:
            print(f"❌ Error processing callback: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

class CallbackRetryTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.test_job_id = None
        self.callback_server = None
        self.callback_url = None
        self.server_thread = None
    
    def start_callback_server(self, fail_count: int = 0):
        """Start a local HTTP server to test callback retries"""
        print(f"🌐 Starting callback retry test server (will fail {fail_count} times)...")
        
        # Configure failure count
        RetryTestHandler.fail_count = fail_count
        RetryTestHandler.current_attempts = 0
        RetryTestHandler.received_callbacks.clear()
        
        # Use port 8080 for callback server
        server_address = ('0.0.0.0', 8080)
        self.callback_server = HTTPServer(server_address, RetryTestHandler)
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.callback_server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Use host machine IP for Docker container to reach
        host_ip = "192.168.1.85"
        self.callback_url = f"http://{host_ip}:8080/callback"
        print(f"✅ Callback server started at {self.callback_url}")
        print(f"   Will fail {fail_count} times before succeeding")
    
    def stop_callback_server(self):
        """Stop the callback test server"""
        if self.callback_server:
            print("🛑 Stopping callback test server...")
            self.callback_server.shutdown()
            self.callback_server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=2)
            print("✅ Callback server stopped")
    
    async def register_user(self):
        """Register a test user and get API key"""
        print("🔐 Registering test user...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/register",
                headers={"Content-Type": "application/json"},
                json={"email": f"test_callback_retry_{int(time.time())}@example.com"}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    self.api_key = user_data["api_key"]
                    print(f"✅ User registered with API key: {self.api_key[:10]}...")
                    return True
                else:
                    print(f"❌ Failed to register user: {response.status}")
                    return False
    
    async def create_test_job_with_callback(self):
        """Create a test job with callback URL"""
        print("📝 Creating test job with callback...")
        test_job_data = {
            "task_type": "callback_retry_test",
            "payload": {
                "test": "callback_retry_logic",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Testing callback retry functionality"
            },
            "callback_url": self.callback_url
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/jobs",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=test_job_data
            ) as response:
                if response.status == 202:
                    job_response = await response.json()
                    self.test_job_id = job_response["job_id"]
                    print(f"✅ Test job created with ID: {self.test_job_id}")
                    print(f"   Callback URL: {self.callback_url}")
                    return True
                else:
                    print(f"❌ Failed to create test job: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def wait_for_job_completion(self, timeout: int = 60):
        """Wait for job to be completed by worker"""
        print(f"⏳ Waiting for job completion (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/jobs/{self.test_job_id}",
                    headers={"X-API-Key": self.api_key}
                ) as response:
                    if response.status == 200:
                        job_status = await response.json()
                        status = job_status['status']
                        retry_count = job_status['retry_count']
                        print(f"   Current status: {status}, Retry count: {retry_count}")
                        
                        if status in ['completed', 'failed']:
                            print(f"✅ Job {status}!")
                            return status, retry_count
                    
            await asyncio.sleep(2)  # Check every 2 seconds
        
        print(f"⏰ Timeout reached after {timeout} seconds")
        return None, None
    
    async def analyze_callback_attempts(self):
        """Analyze the callback attempts and timing"""
        print(f"\n📊 Analyzing callback attempts...")
        
        if not RetryTestHandler.received_callbacks:
            print("❌ No callbacks received")
            return False
        
        print(f"✅ Received {len(RetryTestHandler.received_callbacks)} callback attempts:")
        
        for i, callback in enumerate(RetryTestHandler.received_callbacks):
            attempt = callback['attempt']
            timestamp = callback['timestamp']
            data = callback['data']
            
            print(f"   Attempt {attempt}: {timestamp}")
            print(f"     Job ID: {data.get('job_id')}")
            print(f"     Status: {data.get('status')}")
        
        # Check timing between attempts (should be exponential backoff)
        if len(RetryTestHandler.received_callbacks) > 1:
            print(f"\n⏱️  Timing analysis:")
            for i in range(1, len(RetryTestHandler.received_callbacks)):
                prev_time = datetime.fromisoformat(RetryTestHandler.received_callbacks[i-1]['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(RetryTestHandler.received_callbacks[i]['timestamp'].replace('Z', '+00:00'))
                delay = (curr_time - prev_time).total_seconds()
                print(f"   Delay between attempt {i} and {i+1}: {delay:.1f}s")
        
        return True
    
    async def test_retry_count_in_database(self, expected_retries: int):
        """Test that retry count is properly stored in database"""
        print(f"\n🗄️  Testing retry count in database...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/{self.test_job_id}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    job_status = await response.json()
                    actual_retries = job_status['retry_count']
                    
                    # For successful callbacks, retry count should be 0
                    # For failed callbacks, retry count should be 4 (all retries exhausted)
                    if expected_retries == 0 and actual_retries == 0:
                        print(f"✅ Retry count correct for success: {actual_retries}")
                        return True
                    elif expected_retries == 4 and actual_retries == 4:
                        print(f"✅ Retry count correct for failure: {actual_retries}")
                        return True
                    else:
                        print(f"❌ Retry count mismatch: expected {expected_retries}, got {actual_retries}")
                        return False
                else:
                    print(f"❌ Failed to get job status: {response.status}")
                    return False

async def test_scenario(fail_count: int, expected_retries: int, scenario_name: str):
    """Test a specific retry scenario"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing Scenario: {scenario_name}")
    print(f"   Will fail {fail_count} times, expect {expected_retries} retries")
    print(f"{'='*60}")
    
    tester = CallbackRetryTester()
    
    try:
        # Start callback server with specific failure count
        tester.start_callback_server(fail_count)
        
        # Test flow
        if not await tester.register_user():
            return False
        
        if not await tester.create_test_job_with_callback():
            return False
        
        status, retry_count = await tester.wait_for_job_completion(60)
        if not status:
            return False
        
        if not await tester.analyze_callback_attempts():
            return False
        
        if not await tester.test_retry_count_in_database(expected_retries):
            return False
        
        print(f"✅ Scenario '{scenario_name}' completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Scenario '{scenario_name}' failed with exception: {str(e)}")
        return False
    finally:
        tester.stop_callback_server()

async def main():
    """Main test function"""
    print("🚀 Starting Callback Retry Logic Tests")
    print("=" * 60)
    
    scenarios = [
        (0, 0, "Immediate Success"),
        (1, 0, "One Failure Then Success"),
        (2, 0, "Two Failures Then Success"),
        (3, 0, "Three Failures Then Success"),
        (4, 4, "All Retries Exhausted"),
    ]
    
    passed = 0
    total = len(scenarios)
    
    for fail_count, expected_retries, scenario_name in scenarios:
        if await test_scenario(fail_count, expected_retries, scenario_name):
            passed += 1
        else:
            print(f"❌ Scenario '{scenario_name}' failed")
    
    print(f"\n{'='*60}")
    print(f"📊 Final Test Results: {passed}/{total} scenarios passed")
    
    if passed == total:
        print("🎉 All scenarios passed! Callback retry logic is working correctly.")
    else:
        print("⚠️  Some scenarios failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
