#!/usr/bin/env python3
"""
Example usage demonstration for the Telegram Notes Bot components.
This script shows how the various components work together.
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Import our modules
from config import Config
from ollama_client import OllamaClient
from file_manager import FileManager, NoteMetadata
from utils import sanitize_filename, extract_keywords


async def demonstrate_classification():
    """Demonstrate AI classification functionality."""
    print("🤖 AI Classification Demo")
    print("-" * 30)
    
    # Create Ollama client
    ollama_client = OllamaClient()
    
    # Test notes
    test_notes = [
        "I tried a new pasta recipe today with garlic and olive oil",
        "Meeting with the team tomorrow at 2 PM about the project deadline",
        "Remember to book flight tickets for vacation to Italy",
        "Learned a new Python technique for handling async operations",
        "Grocery list: milk, bread, eggs, tomatoes, cheese"
    ]
    
    existing_classes = ["cooking", "work", "travel"]
    
    for note in test_notes:
        print(f"\n📝 Note: {note}")
        
        # Check if Ollama is available
        if ollama_client.is_available():
            result = ollama_client.classify_note(note, existing_classes)
            if result:
                print(f"🎯 Classification: {result.class_name}")
                print(f"📊 Confidence: {result.confidence:.2f}")
                print(f"📄 Suggested filename: {result.suggested_filename}")
                print(f"🆕 New class: {result.is_new_class}")
            else:
                print("❌ Classification failed")
        else:
            print("⚠️  Ollama not available, using fallback...")
            result = ollama_client.get_fallback_classification(note)
            print(f"🎯 Fallback classification: {result.class_name}")
            print(f"📊 Confidence: {result.confidence:.2f}")


def demonstrate_file_management():
    """Demonstrate file management functionality."""
    print("\n📁 File Management Demo")
    print("-" * 30)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock config for demo
        import config
        original_notes_dir = config.config.NOTES_DIRECTORY
        config.config.NOTES_DIRECTORY = Path(temp_dir)
        
        try:
            # Create file manager
            file_manager = FileManager()
            
            # Demo notes
            demo_notes = [
                {
                    "text": "Delicious pasta carbonara recipe with eggs and pancetta",
                    "class": "cooking",
                    "filename": "pasta_carbonara_recipe"
                },
                {
                    "text": "Team standup meeting notes - discussed sprint progress",
                    "class": "work", 
                    "filename": "standup_meeting_notes"
                },
                {
                    "text": "Planning trip to Japan - need to research hotels in Tokyo",
                    "class": "travel",
                    "filename": "japan_trip_planning"
                }
            ]
            
            # Save demo notes
            for note_data in demo_notes:
                metadata = NoteMetadata(
                    original_text=note_data["text"],
                    classification=note_data["class"],
                    confidence=0.95,
                    user_id=123456,
                    username="demo_user"
                )
                
                success, file_path, error = file_manager.save_note(
                    note_data["text"],
                    note_data["class"],
                    note_data["filename"],
                    metadata
                )
                
                if success:
                    print(f"✅ Saved: {Path(file_path).name}")
                else:
                    print(f"❌ Failed to save: {error}")
            
            # Show statistics
            print(f"\n📊 Statistics:")
            stats = file_manager.get_class_stats()
            for class_name, count in stats.items():
                print(f"  {class_name}: {count} notes")
            
            print(f"📝 Total notes: {file_manager.get_total_notes_count()}")
            
            # Show existing classes
            classes = file_manager.get_existing_classes()
            print(f"📂 Classes: {', '.join(classes)}")
            
            # Demonstrate search
            print(f"\n🔍 Search results for 'pasta':")
            search_results = file_manager.search_notes("pasta")
            for result in search_results:
                print(f"  - {result['class_name']}: {result['filename']}")
                
            # Show recent notes
            print(f"\n📅 Recent notes:")
            recent = file_manager.get_recent_notes(limit=3)
            for note in recent:
                print(f"  - {note['class_name']}: {note['filename']}")
                
        finally:
            # Restore original config
            config.config.NOTES_DIRECTORY = original_notes_dir


def demonstrate_utilities():
    """Demonstrate utility functions."""
    print("\n🛠️  Utility Functions Demo")
    print("-" * 30)
    
    # Test filename sanitization
    test_filenames = [
        "My Recipe: Pasta & Sauce!",
        "Meeting Notes (2024/01/15)",
        "Travel Plans - Europe Trip",
        "café notes with accénts"
    ]
    
    print("📄 Filename sanitization:")
    for filename in test_filenames:
        sanitized = sanitize_filename(filename)
        print(f"  '{filename}' → '{sanitized}'")
    
    # Test keyword extraction
    test_texts = [
        "I tried a new pasta recipe with garlic and olive oil",
        "Meeting with the team about project deadlines and deliverables",
        "Planning vacation trip to Italy with hotel bookings"
    ]
    
    print(f"\n🔤 Keyword extraction:")
    for text in test_texts:
        keywords = extract_keywords(text, max_keywords=3)
        print(f"  '{text[:40]}...' → {keywords}")


def demonstrate_config():
    """Demonstrate configuration management."""
    print("\n⚙️  Configuration Demo")
    print("-" * 30)
    
    # Show current configuration (without sensitive data)
    print("📋 Current configuration:")
    print(f"  Notes directory: {config.config.NOTES_DIRECTORY}")
    print(f"  Ollama URL: {config.config.OLLAMA_BASE_URL}")
    print(f"  Ollama model: {config.config.OLLAMA_MODEL}")
    print(f"  Max filename length: {config.config.MAX_FILENAME_LENGTH}")
    print(f"  Confidence threshold: {config.config.DEFAULT_CONFIDENCE_THRESHOLD}")
    print(f"  Backup enabled: {config.config.BACKUP_ENABLED}")


async def main():
    """Run all demonstrations."""
    print("🎯 Telegram Notes Bot - Component Demonstration")
    print("=" * 50)
    
    try:
        # Run demonstrations
        demonstrate_config()
        demonstrate_utilities()
        demonstrate_file_management()
        await demonstrate_classification()
        
        print("\n" + "=" * 50)
        print("✅ All demonstrations completed successfully!")
        print("\nTo start the actual bot:")
        print("  1. Configure your .env file")
        print("  2. Run: python bot.py")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
