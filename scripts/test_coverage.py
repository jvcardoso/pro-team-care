#!/usr/bin/env python3
"""
Test coverage script with minimum threshold enforcement
"""
import subprocess
import sys
import os
from pathlib import Path

# Configuration
MIN_COVERAGE = 80.0
COVERAGE_FAIL_UNDER = MIN_COVERAGE

def run_command(cmd):
    """Run shell command and return result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def main():
    """Main coverage check function"""
    print("=" * 60)
    print("🧪 PRO TEAM CARE - TEST COVERAGE VERIFICATION")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"📁 Working directory: {project_root}")
    print(f"🎯 Minimum coverage required: {MIN_COVERAGE}%")
    print("")
    
    # Clean previous coverage data
    print("🧹 Cleaning previous coverage data...")
    for pattern in ["htmlcov", ".coverage", "coverage.xml"]:
        if os.path.exists(pattern):
            if os.path.isdir(pattern):
                import shutil
                shutil.rmtree(pattern)
            else:
                os.remove(pattern)
    
    # Run tests with coverage
    print("🚀 Running tests with coverage...")
    test_cmd = [
        "python", "-m", "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        f"--cov-fail-under={COVERAGE_FAIL_UNDER}",
        "-v",
        "tests/"
    ]
    
    result = run_command(test_cmd)
    
    print("\n" + "=" * 60)
    
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED WITH SUFFICIENT COVERAGE!")
        print(f"✅ Coverage meets minimum requirement of {MIN_COVERAGE}%")
        
        # Generate coverage badge info
        print("\n📊 Coverage Information:")
        print("- HTML Report: htmlcov/index.html")
        print("- XML Report: coverage.xml")
        print("- Terminal report shown above")
        
    else:
        print("❌ TESTS FAILED OR COVERAGE INSUFFICIENT!")
        print(f"❌ Coverage below minimum requirement of {MIN_COVERAGE}%")
        print("\nTest Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        sys.exit(1)
    
    # Additional coverage analysis
    print("\n📈 Generating detailed coverage report...")
    coverage_cmd = ["python", "-m", "coverage", "report", "--show-missing"]
    coverage_result = run_command(coverage_cmd)
    
    if coverage_result.stdout:
        print("📋 Detailed Coverage Report:")
        print(coverage_result.stdout)
    
    print("\n🎉 Coverage verification completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()