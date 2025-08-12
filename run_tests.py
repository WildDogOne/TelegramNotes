#!/usr/bin/env python3
"""
Test runner script for the Telegram Notes Bot.
Runs all tests and provides a summary of results.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all tests and return the result."""
    print("🧪 Running Telegram Notes Bot Test Suite")
    print("=" * 50)
    
    # Ensure we're in the project directory
    project_root = Path(__file__).parent
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=False)
        
        print("\n" + "=" * 50)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_tests_with_coverage():
    """Run tests with coverage report."""
    print("🧪 Running Tests with Coverage Report")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=False)
        
        print("\n" + "=" * 50)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest or coverage not found. Please install test dependencies:")
        print("   pip install pytest pytest-cov")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        return run_tests_with_coverage()
    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
