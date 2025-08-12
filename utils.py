"""
Utility functions for the Telegram Notes Bot.
Includes text sanitization, validation, and helper functions.
"""

import re
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The original filename string
        max_length: Maximum length for the filename
        
    Returns:
        A sanitized filename safe for cross-platform use
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)  # Windows forbidden chars
    filename = re.sub(r'[^\w\s\-_.]', '', filename)   # Keep only alphanumeric, spaces, hyphens, underscores, dots
    filename = re.sub(r'\s+', '_', filename)          # Replace spaces with underscores
    filename = re.sub(r'_+', '_', filename)           # Collapse multiple underscores
    filename = filename.strip('._')                   # Remove leading/trailing dots and underscores
    
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
        
    # Truncate if too long, but preserve extension if present
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = f"{name[:max_name_length]}.{ext}"
        else:
            filename = filename[:max_length]
            
    return filename


def sanitize_class_name(class_name: str) -> str:
    """
    Sanitize a class name for use as a directory name.
    
    Args:
        class_name: The original class name
        
    Returns:
        A sanitized class name safe for directory creation
    """
    # Convert to lowercase and replace spaces with underscores
    class_name = class_name.lower().strip()
    class_name = re.sub(r'[^\w\s\-]', '', class_name)  # Keep only alphanumeric, spaces, hyphens
    class_name = re.sub(r'\s+', '_', class_name)       # Replace spaces with underscores
    class_name = re.sub(r'_+', '_', class_name)        # Collapse multiple underscores
    class_name = class_name.strip('_')                 # Remove leading/trailing underscores
    
    # Ensure it's not empty
    if not class_name:
        class_name = "uncategorized"
        
    return class_name


def generate_unique_filename(directory: Path, base_filename: str) -> str:
    """
    Generate a unique filename in the given directory.
    
    Args:
        directory: The target directory
        base_filename: The desired base filename
        
    Returns:
        A unique filename that doesn't exist in the directory
    """
    if not (directory / base_filename).exists():
        return base_filename
        
    # Split filename and extension
    if '.' in base_filename:
        name, ext = base_filename.rsplit('.', 1)
        ext = f".{ext}"
    else:
        name, ext = base_filename, ""
        
    # Try numbered variations
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        if not (directory / new_filename).exists():
            return new_filename
        counter += 1


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime object as a string for use in filenames and metadata.
    
    Args:
        dt: The datetime object to format (defaults to current time)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d_%H-%M-%S")


def format_date_for_filename(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime object as a date string for use in filenames.
    
    Args:
        dt: The datetime object to format (defaults to current time)
        
    Returns:
        Formatted date string (YYYY-MM-DD)
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


def create_markdown_frontmatter(metadata: Dict[str, Any]) -> str:
    """
    Create YAML frontmatter for markdown files.
    
    Args:
        metadata: Dictionary of metadata to include
        
    Returns:
        Formatted YAML frontmatter string
    """
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, str):
            # Escape quotes and handle multiline strings
            if '\n' in value or '"' in value:
                value = value.replace('\\', '\\\\').replace('"', '\\"')
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f'{key}: "{value}"')
        else:
            lines.append(f'{key}: {value}')
    lines.append("---")
    lines.append("")  # Empty line after frontmatter
    return '\n'.join(lines)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with an optional suffix.
    
    Args:
        text: The text to truncate
        max_length: Maximum length of the result
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
        
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix


def extract_keywords(text: str, max_keywords: int = 5) -> list:
    """
    Extract potential keywords from text for use in classification prompts.
    
    Args:
        text: The input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of potential keywords
    """
    # Simple keyword extraction - remove common words and get unique terms
    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    # Extract words and filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [word for word in words if word not in common_words]
    
    # Return unique keywords, limited by max_keywords
    unique_keywords = list(dict.fromkeys(keywords))  # Preserve order while removing duplicates
    return unique_keywords[:max_keywords]
