"""
Unit tests for file manager functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from noteBot.file_manager import FileManager, NoteMetadata


class TestFileManager:
    """Test FileManager class functionality."""
    
    @pytest.fixture
    def temp_notes_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
        
    @pytest.fixture
    def file_manager(self, temp_notes_dir):
        """Create a FileManager instance with temporary directory."""
        with patch('file_manager.config') as mock_config:
            mock_config.NOTES_DIRECTORY = temp_notes_dir
            mock_config.BACKUP_ENABLED = False
            mock_config.MAX_FILENAME_LENGTH = 100
            
            return FileManager()
            
    @pytest.fixture
    def sample_metadata(self):
        """Create sample note metadata."""
        return NoteMetadata(
            original_text="Test note content",
            classification="test",
            confidence=0.95,
            user_id=123456,
            username="testuser",
            telegram_message_id=789
        )
        
    def test_save_note_success(self, file_manager, sample_metadata, temp_notes_dir):
        """Test successful note saving."""
        note_text = "This is a test note about cooking pasta."
        class_name = "cooking"
        suggested_filename = "pasta_recipe"
        
        success, file_path, error_msg = file_manager.save_note(
            note_text, class_name, suggested_filename, sample_metadata
        )
        
        assert success is True
        assert error_msg is None
        assert Path(file_path).exists()
        
        # Check directory structure
        class_dir = temp_notes_dir / "cooking"
        assert class_dir.exists()
        assert class_dir.is_dir()
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "This is a test note about cooking pasta." in content
        assert "---" in content  # Frontmatter markers
        assert "classification: cooking" in content
        
    def test_save_note_with_special_characters(self, file_manager, sample_metadata):
        """Test saving note with special characters in filename."""
        note_text = "Test note"
        class_name = "work & projects!"
        suggested_filename = "meeting notes: 2024/01/15"
        
        success, file_path, error_msg = file_manager.save_note(
            note_text, class_name, suggested_filename, sample_metadata
        )
        
        assert success is True
        
        # Check that special characters are sanitized
        path_obj = Path(file_path)
        assert "work_projects" in str(path_obj.parent)
        assert "meeting_notes_2024_01_15" in path_obj.name
        
    def test_get_existing_classes_empty(self, file_manager):
        """Test getting existing classes when none exist."""
        classes = file_manager.get_existing_classes()
        assert classes == []
        
    def test_get_existing_classes_with_data(self, file_manager, temp_notes_dir):
        """Test getting existing classes with data."""
        # Create some class directories
        (temp_notes_dir / "cooking").mkdir()
        (temp_notes_dir / "work").mkdir()
        (temp_notes_dir / "travel").mkdir()
        (temp_notes_dir / ".hidden").mkdir()  # Should be ignored
        
        classes = file_manager.get_existing_classes()
        
        assert len(classes) == 3
        assert "cooking" in classes
        assert "work" in classes
        assert "travel" in classes
        assert ".hidden" not in classes
        assert classes == sorted(classes)  # Should be sorted
        
    def test_get_class_stats(self, file_manager, temp_notes_dir):
        """Test getting class statistics."""
        # Create directories and files
        cooking_dir = temp_notes_dir / "cooking"
        work_dir = temp_notes_dir / "work"
        cooking_dir.mkdir()
        work_dir.mkdir()
        
        # Create some note files
        (cooking_dir / "recipe1.md").touch()
        (cooking_dir / "recipe2.md").touch()
        (work_dir / "meeting.md").touch()
        (cooking_dir / "not_a_note.txt").touch()  # Should be ignored
        
        stats = file_manager.get_class_stats()
        
        assert stats["cooking"] == 2
        assert stats["work"] == 1
        
    def test_get_total_notes_count(self, file_manager, temp_notes_dir):
        """Test getting total notes count."""
        # Create directories and files
        cooking_dir = temp_notes_dir / "cooking"
        work_dir = temp_notes_dir / "work"
        cooking_dir.mkdir()
        work_dir.mkdir()
        
        (cooking_dir / "recipe1.md").touch()
        (cooking_dir / "recipe2.md").touch()
        (work_dir / "meeting.md").touch()
        
        total = file_manager.get_total_notes_count()
        assert total == 3
        
    def test_unique_filename_generation(self, file_manager, sample_metadata, temp_notes_dir):
        """Test that unique filenames are generated for conflicts."""
        note_text = "Test note"
        class_name = "test"
        suggested_filename = "duplicate"
        
        # Save first note
        success1, file_path1, _ = file_manager.save_note(
            note_text, class_name, suggested_filename, sample_metadata
        )
        
        # Save second note with same suggested filename
        success2, file_path2, _ = file_manager.save_note(
            note_text, class_name, suggested_filename, sample_metadata
        )
        
        assert success1 is True
        assert success2 is True
        assert file_path1 != file_path2
        
        # Check that both files exist
        assert Path(file_path1).exists()
        assert Path(file_path2).exists()
        
        # Second file should have a number suffix
        assert "_1.md" in file_path2
        
    def test_search_notes(self, file_manager, sample_metadata, temp_notes_dir):
        """Test note searching functionality."""
        # Create some test notes
        notes_data = [
            ("cooking", "pasta_recipe", "I made delicious pasta with garlic"),
            ("cooking", "cake_recipe", "Chocolate cake recipe for birthday"),
            ("work", "meeting_notes", "Team meeting about project deadlines"),
        ]
        
        for class_name, filename, content in notes_data:
            file_manager.save_note(content, class_name, filename, sample_metadata)
            
        # Test general search
        results = file_manager.search_notes("pasta")
        assert len(results) == 1
        assert results[0]["class_name"] == "cooking"
        
        # Test class-specific search
        results = file_manager.search_notes("recipe", class_name="cooking")
        assert len(results) == 2
        
        # Test case-insensitive search
        results = file_manager.search_notes("PASTA")
        assert len(results) == 1
        
        # Test no results
        results = file_manager.search_notes("nonexistent")
        assert len(results) == 0
        
    def test_get_recent_notes(self, file_manager, sample_metadata, temp_notes_dir):
        """Test getting recent notes."""
        # Create some test notes with different timestamps
        import time
        
        notes_data = [
            ("cooking", "old_recipe", "Old recipe"),
            ("work", "recent_meeting", "Recent meeting notes"),
        ]
        
        for i, (class_name, filename, content) in enumerate(notes_data):
            file_manager.save_note(content, class_name, filename, sample_metadata)
            if i == 0:
                time.sleep(0.1)  # Ensure different timestamps
                
        recent = file_manager.get_recent_notes(limit=5)
        
        assert len(recent) == 2
        # Most recent should be first
        assert "recent_meeting" in recent[0]["filename"]
        
    def test_backup_creation(self, temp_notes_dir, sample_metadata):
        """Test backup file creation when enabled."""
        with patch('file_manager.config') as mock_config:
            mock_config.NOTES_DIRECTORY = temp_notes_dir
            mock_config.BACKUP_ENABLED = True
            mock_config.MAX_FILENAME_LENGTH = 100
            
            file_manager = FileManager()
            
            success, file_path, _ = file_manager.save_note(
                "Test note", "test", "backup_test", sample_metadata
            )
            
            assert success is True
            
            # Check that backup directory exists
            backup_dir = temp_notes_dir / ".backups"
            assert backup_dir.exists()
            
            # Check that backup file was created
            backup_files = list(backup_dir.glob("*.md"))
            assert len(backup_files) == 1
