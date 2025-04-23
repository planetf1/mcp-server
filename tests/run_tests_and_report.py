#!/usr/bin/env python3
"""
Run pytest tests and generate a summary report in Markdown format.
This can be used as a GitHub Action step.
"""
import os
import sys
import subprocess
import json
import datetime

def run_tests():
    """Run pytest with coverage and capture results."""
    # Run pytest with coverage options
    result = subprocess.run(
        [
            "python", "-m", "pytest",
            "--cov=tools",
            "--cov-report=term",
            "--cov-report=html:coverage_html",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
            "-v"
        ],
        capture_output=True,
        text=True
    )
    
    return result

def parse_coverage_data():
    """Parse the coverage JSON file to extract statistics."""
    try:
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        
        # Get per-file coverage
        files_coverage = []
        for file_path, data in coverage_data.get("files", {}).items():
            if file_path.startswith("tools/"):
                files_coverage.append({
                    "file": file_path,
                    "coverage": data.get("summary", {}).get("percent_covered", 0),
                    "missing_lines": len(data.get("missing_lines", [])),
                    "executed_lines": len(data.get("executed_lines", []))
                })
        
        return {
            "total_coverage": total_coverage,
            "files_coverage": sorted(files_coverage, key=lambda x: x["file"])
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total_coverage": 0,
            "files_coverage": []
        }

def generate_markdown_report(test_result, coverage_data):
    """Generate a Markdown report summarizing test and coverage results."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine test status
    test_status = "✅ Passed" if test_result.returncode == 0 else "❌ Failed"
    
    report = f"""# Test Results Summary ({now})

## Test Status: {test_status}

- Return Code: {test_result.returncode}
- Total Coverage: {coverage_data['total_coverage']:.2f}%

## Coverage Details

| File | Coverage | Executed Lines | Missing Lines |
|------|----------|---------------|--------------|
"""
    
    for file_data in coverage_data["files_coverage"]:
        report += f"| {file_data['file']} | {file_data['coverage']:.2f}% | {file_data['executed_lines']} | {file_data['missing_lines']} |\n"
    
    report += """
## Test Output

<details>
<summary>Click to expand test output</summary>

```
"""
    report += test_result.stdout
    report += "\n```\n</details>\n"
    
    if test_result.stderr:
        report += """
## Error Output

<details>
<summary>Click to expand error output</summary>

```
"""
        report += test_result.stderr
        report += "\n```\n</details>\n"
    
    return report

def main():
    """Run tests and generate report."""
    print("Running tests...")
    test_result = run_tests()
    print("Parsing coverage data...")
    coverage_data = parse_coverage_data()
    print("Generating report...")
    report = generate_markdown_report(test_result, coverage_data)
    
    # Write to a file
    with open("test_results_summary.md", "w") as f:
        f.write(report)
    
    # If running in GitHub Actions, output to the summary
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(report)
    
    # Also print to console
    print(report)
    
    # Return the test result code
    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
