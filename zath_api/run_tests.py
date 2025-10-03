#!/usr/bin/env python3
"""
Test runner script for ZATH API
Usage: python run_tests.py [options]
"""
import subprocess
import sys
import os

def run_pytest_tests():
    """Run pytest tests"""
    print("🧪 Running pytest tests...")
    result = subprocess.run([
        "python", "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

def run_legacy_tests():
    """Run legacy test suite"""
    print("🔧 Running legacy test suite...")
    result = subprocess.run([
        "python", "tests/test_authentication.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--legacy":
            return run_legacy_tests()
        elif sys.argv[1] == "--help":
            print("Usage: python run_tests.py [--legacy]")
            print("  --legacy: Run legacy test suite")
            print("  (default): Run pytest tests")
            return 0
    
    return run_pytest_tests()

if __name__ == "__main__":
    sys.exit(main())
