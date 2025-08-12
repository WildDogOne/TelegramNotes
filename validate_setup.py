#!/usr/bin/env python3
"""
Setup validation script for the Telegram Notes Bot.
Checks if all components can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing module imports...")

    # Set minimal environment for testing imports
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_for_import_validation'

    try:
        modules_to_test = [
            ('utils', 'Utility functions'),
            ('ollama_client', 'Ollama AI client'),
            ('file_manager', 'File management'),
        ]

        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                print(f"  ✅ {description}: OK")
            except ImportError as e:
                print(f"  ❌ {description}: {e}")
                return False

        return True

    finally:
        # Clean up test environment variable
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']


def test_config_with_env():
    """Test config with environment variables set."""
    print("\n⚙️ Testing configuration...")
    
    # Set minimal required environment variables for testing
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_for_validation'
    
    try:
        import config
        print("  ✅ Configuration module: OK")
        print(f"  📁 Notes directory: {config.config.NOTES_DIRECTORY}")
        print(f"  🤖 Ollama URL: {config.config.OLLAMA_BASE_URL}")
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False
    finally:
        # Clean up test environment variable
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']


def test_utilities():
    """Test utility functions."""
    print("\n🛠️ Testing utility functions...")
    
    try:
        from utils import sanitize_filename, extract_keywords, sanitize_class_name
        
        # Test filename sanitization
        test_filename = "Test File: With Special Characters!"
        sanitized = sanitize_filename(test_filename)
        assert sanitized == "Test_File_With_Special_Characters"
        print("  ✅ Filename sanitization: OK")
        
        # Test keyword extraction
        keywords = extract_keywords("This is a test message about cooking pasta", max_keywords=3)
        assert len(keywords) <= 3
        assert "cooking" in keywords
        print("  ✅ Keyword extraction: OK")
        
        # Test class name sanitization
        class_name = sanitize_class_name("Work & Projects!")
        assert class_name == "work_projects"
        print("  ✅ Class name sanitization: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Utility functions error: {e}")
        return False


def test_file_operations():
    """Test file operations without actually creating files."""
    print("\n📁 Testing file operations...")
    
    try:
        import tempfile
        from file_manager import NoteMetadata
        from datetime import datetime
        
        # Test metadata creation
        metadata = NoteMetadata(
            original_text="Test note",
            classification="test",
            confidence=0.95,
            user_id=123456,
            username="testuser"
        )
        
        assert metadata.original_text == "Test note"
        assert metadata.classification == "test"
        assert isinstance(metadata.created_at, datetime)
        print("  ✅ Note metadata: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File operations error: {e}")
        return False


def test_ollama_client():
    """Test Ollama client (without requiring actual connection)."""
    print("\n🤖 Testing Ollama client...")
    
    try:
        from ollama_client import OllamaClient, OllamaClassificationResult
        
        # Test client creation
        client = OllamaClient()
        print("  ✅ Ollama client creation: OK")
        
        # Test classification result
        result = OllamaClassificationResult(
            class_name="test",
            confidence=0.95,
            suggested_filename="test_note",
            is_new_class=False
        )
        
        assert result.class_name == "test"
        assert result.confidence == 0.95
        print("  ✅ Classification result: OK")
        
        # Test fallback classification
        fallback = client.get_fallback_classification("I made pasta today")
        assert fallback.class_name == "cooking"
        print("  ✅ Fallback classification: OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ollama client error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🎯 Telegram Notes Bot - Setup Validation")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config_with_env),
        ("Utility Functions", test_utilities),
        ("File Operations", test_file_operations),
        ("Ollama Client", test_ollama_client),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All validation tests passed!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Configure your TELEGRAM_BOT_TOKEN in .env")
        print("3. Install and start Ollama")
        print("4. Run: python bot.py")
    else:
        print("❌ Some validation tests failed!")
        print("Please check the errors above and fix them before proceeding.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
