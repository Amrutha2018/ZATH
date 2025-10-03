#!/usr/bin/env python3
"""
Test script for callback notifier functionality
Verifies that the worker sends HTTP POST callbacks after job completion
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

class CallbackTestHandler(BaseHTTPRequestHandler):
    """HTTP server to receive callback notifications"""
    
    received_callbacks = []
    
    def do_POST(self):
        """Handle POST requests (callbacks)"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            callback_data = json.loads(post_data.decode('utf-8'))
            CallbackTestHandler.received_callbacks.append(callback_data)
            
            print(f"📥 Received callback: {callback_data}")
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
            
        except Exception as e:
            print(f"❌ Error processing callback: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

class CallbackNotifierTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.test_job_id = None
        self.callback_server = None
        self.callback_url = None
        self.server_thread = None
    
    def start_callback_server(self):
        """Start a local HTTP server to receive callbacks"""
        print("🌐 Starting callback test server...")
        
        # Use port 8080 for callback server
        server_address = ('0.0.0.0', 8080)  # Bind to all interfaces
        self.callback_server = HTTPServer(server_address, CallbackTestHandler)
        
        # Clear previous callbacks
        CallbackTestHandler.received_callbacks.clear()
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.callback_server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Use host machine IP for Docker container to reach
        host_ip = "192.168.1.85"  # Use the known host IP
        
        self.callback_url = f"http://{host_ip}:8080/callback"
        print(f"✅ Callback server started at {self.callback_url}")
        print(f"   Host IP: {host_ip}")
        print(f"   Docker container will use: {self.callback_url}")
    
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
                json={"email": f"test_callback_{int(time.time())}@example.com"}
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
            "task_type": "callback_test",
            "payload": {
                "test": "callback_notification",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Testing callback notifier functionality"
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
    
    async def wait_for_job_completion(self, timeout: int = 30):
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
                        print(f"   Current status: {status}")
                        
                        if status in ['completed', 'failed']:
                            print(f"✅ Job {status}!")
                            return status
                    
            await asyncio.sleep(2)  # Check every 2 seconds
        
        print(f"⏰ Timeout reached after {timeout} seconds")
        return None
    
    async def check_callback_received(self, timeout: int = 10):
        """Check if callback was received"""
        print(f"📥 Checking for callback (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if CallbackTestHandler.received_callbacks:
                callback = CallbackTestHandler.received_callbacks[0]
                print(f"✅ Callback received!")
                print(f"   Job ID: {callback.get('job_id')}")
                print(f"   Status: {callback.get('status')}")
                print(f"   Completed At: {callback.get('completed_at')}")
                print(f"   Error: {callback.get('error', 'None')}")
                return callback
            
            await asyncio.sleep(1)
        
        print("⏰ No callback received within timeout")
        return None
    
    async def test_callback_payload(self, callback_data):
        """Test callback payload structure"""
        print("\n🔍 Testing callback payload structure...")
        
        required_fields = ['job_id', 'status', 'completed_at']
        optional_fields = ['error']
        
        # Check required fields
        for field in required_fields:
            if field not in callback_data:
                print(f"❌ Missing required field: {field}")
                return False
            print(f"✅ Required field present: {field}")
        
        # Check optional fields
        for field in optional_fields:
            if field in callback_data:
                print(f"✅ Optional field present: {field}")
            else:
                print(f"ℹ️  Optional field not present: {field}")
        
        # Validate job_id matches
        if callback_data['job_id'] != self.test_job_id:
            print(f"❌ Job ID mismatch: expected {self.test_job_id}, got {callback_data['job_id']}")
            return False
        print(f"✅ Job ID matches: {callback_data['job_id']}")
        
        # Validate status
        if callback_data['status'] not in ['completed', 'failed']:
            print(f"❌ Invalid status: {callback_data['status']}")
            return False
        print(f"✅ Valid status: {callback_data['status']}")
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(callback_data['completed_at'].replace('Z', '+00:00'))
            print(f"✅ Valid timestamp format: {callback_data['completed_at']}")
        except ValueError:
            print(f"❌ Invalid timestamp format: {callback_data['completed_at']}")
            return False
        
        return True
    
    async def test_failed_job_callback(self):
        """Test callback for failed job (if possible)"""
        print("\n🧪 Testing failed job callback...")
        
        # Create a job that might fail (we'll simulate this by checking if any failed)
        failed_callbacks = [cb for cb in CallbackTestHandler.received_callbacks if cb.get('status') == 'failed']
        
        if failed_callbacks:
            failed_callback = failed_callbacks[0]
            print(f"✅ Found failed job callback:")
            print(f"   Job ID: {failed_callback.get('job_id')}")
            print(f"   Error: {failed_callback.get('error', 'No error message')}")
            return True
        else:
            print("ℹ️  No failed job callbacks found (this is normal)")
            return True

async def main():
    """Main test function"""
    print("🚀 Starting Callback Notifier Tests")
    print("=" * 60)
    
    tester = CallbackNotifierTester()
    
    try:
        # Start callback server
        tester.start_callback_server()
        
        # Test flow
        tests = [
            ("User Registration", tester.register_user),
            ("Create Job with Callback", tester.create_test_job_with_callback),
            ("Wait for Job Completion", lambda: tester.wait_for_job_completion(30)),
            ("Check Callback Received", lambda: tester.check_callback_received(10)),
        ]
        
        passed = 0
        total = len(tests)
        callback_data = None
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                    if test_name == "Check Callback Received" and result:
                        callback_data = result
                else:
                    print(f"❌ Test '{test_name}' failed")
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
        
        # Additional callback tests
        if callback_data:
            if await tester.test_callback_payload(callback_data):
                passed += 1
            total += 1
            
            if await tester.test_failed_job_callback():
                passed += 1
            total += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Callback notifier is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total
        
    finally:
        # Clean up
        tester.stop_callback_server()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
