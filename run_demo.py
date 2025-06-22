#!/usr/bin/env python3
"""
Demo script for the Distributed TSP System
This script demonstrates how to run the complete system locally.
"""

import signal
import subprocess
import sys
import time

processes = []


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down all processes...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    sys.exit(0)


def start_coordinator():
    """Start the coordinator"""
    print("🚀 Starting Coordinator...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "scripts/start_coordinator.py",
            "--host",
            "localhost",
            "--port",
            "8888",
        ]
    )
    processes.append(proc)
    return proc


def start_workers(num_workers=3):
    """Start multiple workers"""
    worker_procs = []
    for i in range(num_workers):
        print(f"👷 Starting Worker {i + 1}...")
        proc = subprocess.Popen(
            [
                sys.executable,
                "scripts/start_worker.py",
                "--host",
                "localhost",
                "--port",
                "8888",
            ]
        )
        processes.append(proc)
        worker_procs.append(proc)
        time.sleep(1)  # Small delay between workers
    return worker_procs


def run_demo_problem():
    """Run a demo TSP problem"""
    print("🧮 Solving demo TSP problem...")

    # Generate a problem
    subprocess.run(
        [
            sys.executable,
            "scripts/start_client.py",
            "generate",
            "--cities",
            "6",
            "--seed",
            "42",
            "--output",
            "demo_problem.json",
        ]
    )

    # Solve the problem
    subprocess.run(
        [
            sys.executable,
            "scripts/start_client.py",
            "solve",
            "--file",
            "demo_problem.json",
            "--output",
            "demo_result.json",
        ]
    )


def main():
    """Main demo function"""
    print("🎯 Distributed TSP System Demo")
    print("=" * 50)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start coordinator
        start_coordinator()
        time.sleep(3)  # Wait for coordinator to start

        # Start workers
        start_workers(num_workers=3)
        time.sleep(2)  # Wait for workers to register

        # Run demo problem
        run_demo_problem()

        print("\n✅ Demo completed successfully!")
        print("Check demo_result.json for the solution.")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
