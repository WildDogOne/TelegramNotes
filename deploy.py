#!/usr/bin/env python3
"""
Deployment script for the Telegram Notes Bot.
Handles setup, configuration validation, and service management.
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_dependencies():
    """Check if all dependencies are installed."""
    try:
        import telegram
        import requests
        import yaml
        import dotenv
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def check_ollama():
    """Check if Ollama is available."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed and running")
            models = result.stdout.strip()
            if models:
                print(f"📋 Available models:\n{models}")
            else:
                print("⚠️  No models found. Run: ollama pull llama3.1")
            return True
        else:
            print("❌ Ollama is not running")
            return False
    except FileNotFoundError:
        print("❌ Ollama is not installed")
        print("Install from: https://ollama.ai/")
        return False


def setup_environment():
    """Set up environment configuration."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env with your configuration")
            return False
        else:
            print("❌ No .env.example file found")
            return False
    else:
        print("✅ .env file exists")
        return True


def validate_config():
    """Validate configuration."""
    try:
        from config import config
        
        if not config.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not set in .env")
            return False
        
        print("✅ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    try:
        from config import config
        
        # Create notes directory
        config.NOTES_DIRECTORY.mkdir(parents=True, exist_ok=True)
        print(f"✅ Notes directory ready: {config.NOTES_DIRECTORY}")
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        print("✅ Logs directory ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating directories: {e}")
        return False


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True


def main():
    """Main deployment function."""
    print("🚀 Telegram Notes Bot Deployment")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama", check_ollama),
        ("Environment", setup_environment),
        ("Configuration", validate_config),
        ("Directories", create_directories),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        if not check_func():
            all_passed = False
            
    if all_passed:
        print("\n🧪 Running tests...")
        if run_tests():
            print("\n" + "=" * 40)
            print("🎉 Deployment successful!")
            print("\nTo start the bot:")
            print("  python bot.py")
            print("\nTo run tests:")
            print("  python run_tests.py")
            print("\nTo run with coverage:")
            print("  python run_tests.py --coverage")
        else:
            print("\n⚠️  Deployment completed with test failures")
            print("The bot should still work, but please review the test results")
    else:
        print("\n" + "=" * 40)
        print("❌ Deployment failed!")
        print("Please fix the issues above and try again")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
