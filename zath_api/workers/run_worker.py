#!/usr/bin/env python3
"""
Worker process runner - Simple entry point for the job worker.

This script provides a clean entry point to start the job worker process.
The main logic is contained in the JobWorker class in job_worker.py.
"""

import asyncio
import signal
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.job_worker import main as worker_main


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the worker
    asyncio.run(worker_main())
