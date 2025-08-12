"""
Unit tests for utility functions.
"""

from datetime import datetime
from pathlib import Path
import tempfile

from noteBot.utils import (
    sanitize_filename,
    sanitize_class_name,
    generate_unique_filename,
    format_timestamp,
    format_date_for_filename,
    create_markdown_frontmatter,
    truncate_text,
    extract_keywords
)


class TestSanitizeFilename:
    """Test filename sanitization."""
    
    def test_basic_sanitization(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("hello world") == "hello_world"
        assert sanitize_filename("test-file_name.txt") == "test-file_name.txt"
        
    def test_forbidden_characters(self):
        """Test removal of forbidden characters."""
        assert sanitize_filename('file<>:"/\\|?*name') == "filename"
        assert sanitize_filename("file with spaces") == "file_with_spaces"
        
    def test_unicode_normalization(self):
        """Test unicode character normalization."""
        assert sanitize_filename("café") == "cafe"
        assert sanitize_filename("naïve") == "naive"
        
    def test_length_limiting(self):
        """Test filename length limiting."""
        long_name = "a" * 150
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) == 50
        
    def test_extension_preservation(self):
        """Test that file extensions are preserved when truncating."""
        long_name = "a" * 100 + ".txt"
        result = sanitize_filename(long_name, max_length=50)
        assert result.endswith(".txt")
        assert len(result) == 50
        
    def test_empty_filename(self):
        """Test handling of empty filenames."""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"


class TestSanitizeClassName:
    """Test class name sanitization."""
    
    def test_basic_sanitization(self):
        """Test basic class name sanitization."""
        assert sanitize_class_name("Work Projects") == "work_projects"
        assert sanitize_class_name("COOKING RECIPES") == "cooking_recipes"
        
    def test_special_characters(self):
        """Test removal of special characters."""
        assert sanitize_class_name("work & projects!") == "work_projects"
        assert sanitize_class_name("notes-2024") == "notes-2024"
        
    def test_empty_class_name(self):
        """Test handling of empty class names."""
        assert sanitize_class_name("") == "uncategorized"
        assert sanitize_class_name("   ") == "uncategorized"


class TestGenerateUniqueFilename:
    """Test unique filename generation."""
    
    def test_unique_filename_no_conflict(self):
        """Test when no conflict exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = generate_unique_filename(temp_path, "test.txt")
            assert result == "test.txt"
            
    def test_unique_filename_with_conflict(self):
        """Test when filename conflicts exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create conflicting file
            (temp_path / "test.txt").touch()
            
            result = generate_unique_filename(temp_path, "test.txt")
            assert result == "test_1.txt"
            
            # Create another conflict
            (temp_path / "test_1.txt").touch()
            result = generate_unique_filename(temp_path, "test.txt")
            assert result == "test_2.txt"


class TestFormatting:
    """Test date and time formatting functions."""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = format_timestamp(dt)
        assert result == "2024-01-15_14-30-45"
        
    def test_format_date_for_filename(self):
        """Test date formatting for filenames."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = format_date_for_filename(dt)
        assert result == "2024-01-15"
        
    def test_current_time_default(self):
        """Test that current time is used when no datetime provided."""
        result = format_timestamp()
        assert len(result) == 19  # YYYY-MM-DD_HH-MM-SS format
        assert "_" in result
        assert "-" in result


class TestMarkdownFrontmatter:
    """Test markdown frontmatter creation."""
    
    def test_basic_frontmatter(self):
        """Test basic frontmatter creation."""
        metadata = {
            "title": "Test Note",
            "created_at": "2024-01-15T14:30:45",
            "classification": "test",
            "confidence": 0.95
        }
        
        result = create_markdown_frontmatter(metadata)
        
        assert result.startswith("---\n")
        assert result.endswith("---\n\n")
        assert 'title: "Test Note"' in result
        assert 'confidence: 0.95' in result
        
    def test_multiline_values(self):
        """Test handling of multiline values in frontmatter."""
        metadata = {
            "content": "Line 1\nLine 2",
            "simple": "value"
        }
        
        result = create_markdown_frontmatter(metadata)
        assert 'content: "Line 1\\nLine 2"' in result


class TestTextUtilities:
    """Test text utility functions."""
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "This is a long text that should be truncated"
        result = truncate_text(text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")
        
    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, max_length=20)
        assert result == text
        
    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "I tried a new pasta recipe with garlic and olive oil today"
        keywords = extract_keywords(text, max_keywords=3)
        
        assert len(keywords) <= 3
        assert "tried" in keywords
        assert "pasta" in keywords
        assert "recipe" in keywords
        
        # Common words should be filtered out
        assert "and" not in keywords
        assert "with" not in keywords
        
    def test_extract_keywords_empty_text(self):
        """Test keyword extraction from empty text."""
        keywords = extract_keywords("", max_keywords=5)
        assert keywords == []
        
    def test_extract_keywords_unique(self):
        """Test that duplicate keywords are removed."""
        text = "pasta pasta recipe recipe cooking"
        keywords = extract_keywords(text, max_keywords=5)
        
        # Should contain unique keywords only
        assert len(keywords) == len(set(keywords))
        assert "pasta" in keywords
        assert "recipe" in keywords
