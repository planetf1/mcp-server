#!/usr/bin/env python3
"""
Script to run all tests with coverage reporting and generate a summary.
"""
import subprocess
import sys
import os

def main():
    """Run tests and generate reports."""
    # Ensure we're in the project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the tests
    cmd = [
        "python", "-m", "pytest",
        "--cov=tools",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
        "--cov-report=xml:coverage.xml",
        "-v"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    # Create a GitHub Actions compatible summary
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        # If running in GitHub Actions, use the test_results_summary.py script
        summary_cmd = ["python", "tests/run_tests_and_report.py"]
        subprocess.run(summary_cmd)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
