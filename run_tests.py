#!/usr/bin/env python3
"""
Test runner for BrandGPT application.
Provides different test suites and options for comprehensive testing.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="BrandGPT Test Runner")
    parser.add_argument(
        "--suite",
        choices=["all", "unit", "integration", "auth", "ingestion", "query", "performance"],
        default="unit",
        help="Test suite to run"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["uv", "run", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Skip slow tests if requested
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Select test suite
    if args.suite == "all":
        cmd.append("tests/")
    elif args.suite == "unit":
        cmd.extend([
            "tests/test_auth.py",
            "tests/test_sessions.py",
        ])
    elif args.suite == "integration":
        cmd.append("tests/integration/")
    elif args.suite == "auth":
        cmd.append("tests/test_auth.py")
    elif args.suite == "ingestion":
        cmd.append("tests/test_ingestion.py")
    elif args.suite == "query":
        cmd.append("tests/test_query.py")
    elif args.suite == "performance":
        cmd.append("tests/test_performance.py")
    
    print("=" * 60)
    print(f"Running BrandGPT Test Suite: {args.suite}")
    print("=" * 60)
    
    success = run_command(cmd)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()