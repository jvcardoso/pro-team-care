#!/usr/bin/env python3
"""
Smart coverage script that progresses towards 80% goal
"""
import subprocess
import sys
import re
from pathlib import Path

def get_current_coverage():
    """Get current coverage percentage"""
    result = subprocess.run([
        "python", "-m", "pytest", "--cov=app", "--cov-report=term", "-q", "tests/"
    ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    
    # Extract coverage percentage from output
    coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
    if coverage_match:
        return float(coverage_match.group(1))
    return 0.0

def main():
    print("🎯 SMART COVERAGE PROGRESSION TO 80%")
    print("=" * 50)
    
    current_coverage = get_current_coverage()
    target_coverage = 80.0
    
    print(f"📊 Current Coverage: {current_coverage}%")
    print(f"🎯 Target Coverage: {target_coverage}%")
    
    if current_coverage >= target_coverage:
        print("✅ COVERAGE TARGET ACHIEVED!")
        # Run with strict threshold
        result = subprocess.run([
            "python", "-m", "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
            f"--cov-fail-under={target_coverage}",
            "-v", "tests/"
        ])
        sys.exit(result.returncode)
    
    else:
        # Progressive approach - set threshold to current + 5%
        progressive_threshold = min(current_coverage + 5, target_coverage)
        
        print(f"📈 Progressive Threshold: {progressive_threshold}%")
        print("🚧 RUNNING TESTS WITH PROGRESSIVE THRESHOLD")
        print("=" * 50)
        
        result = subprocess.run([
            "python", "-m", "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
            f"--cov-fail-under={progressive_threshold}",
            "-v", "tests/"
        ])
        
        if result.returncode == 0:
            print("✅ PROGRESSIVE COVERAGE TARGET MET!")
            print(f"💡 Next goal: Improve coverage to {min(progressive_threshold + 5, target_coverage)}%")
        
        return result.returncode

if __name__ == "__main__":
    sys.exit(main())