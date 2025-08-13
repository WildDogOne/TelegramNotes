"""
File system manager for organizing and storing notes.
Handles markdown file creation, directory management, and metadata.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from noteBot.config import config
from noteBot.utils import (
    sanitize_filename, 
    sanitize_class_name, 
    generate_unique_filename,
    format_date_for_filename,
    create_markdown_frontmatter
)

logger = logging.getLogger(__name__)


class NoteMetadata:
    """Data class for note metadata."""
    
    def __init__(self, original_text: str, classification: str, confidence: float,
                 user_id: int, username: Optional[str] = None, 
                 telegram_message_id: Optional[int] = None):
        self.original_text = original_text
        self.classification = classification
        self.confidence = confidence
        self.user_id = user_id
        self.username = username
        self.telegram_message_id = telegram_message_id
        self.created_at = datetime.now()


class FileManager:
    """Manages file system operations for note storage and organization."""
    
    def __init__(self):
        self.notes_directory = config.NOTES_DIRECTORY
        self.backup_enabled = config.BACKUP_ENABLED
        self.max_filename_length = config.MAX_FILENAME_LENGTH
        
        # Ensure notes directory exists
        self._ensure_directory_exists(self.notes_directory)
        
    def save_note(self, note_text: str, class_name: str, suggested_filename: str,
                  metadata: NoteMetadata) -> Tuple[bool, str, Optional[str]]:
        """
        Save a note to the file system.
        
        Args:
            note_text: The note content
            class_name: The classification category
            suggested_filename: Suggested filename from AI
            metadata: Note metadata
            
        Returns:
            Tuple of (success, file_path, error_message)
        """
        try:
            # Sanitize class name and create directory
            clean_class_name = sanitize_class_name(class_name)
            class_directory = self.notes_directory / clean_class_name
            self._ensure_directory_exists(class_directory)
            
            # Generate filename
            date_prefix = format_date_for_filename(metadata.created_at)
            clean_filename = sanitize_filename(suggested_filename, self.max_filename_length - len(date_prefix) - 4)  # -4 for date prefix and .md
            base_filename = f"{date_prefix}_{clean_filename}.md"
            
            # Ensure filename is unique
            final_filename = generate_unique_filename(class_directory, base_filename)
            file_path = class_directory / final_filename
            
            # Create markdown content
            markdown_content = self._create_markdown_content(note_text, metadata)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup(file_path)
                
            logger.info(f"Note saved successfully: {file_path}")
            return True, str(file_path), None
            
        except Exception as e:
            error_msg = f"Failed to save note: {e}"
            logger.error(error_msg)
            return False, "", error_msg

    def read_note(self, filename):
        """Read the content of a file and return it as a string."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return ""
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            return ""



    def get_existing_classes(self) -> List[str]:
        """
        Get list of existing note classes (directory names).
        
        Returns:
            List of existing class names
        """
        try:
            if not self.notes_directory.exists():
                return []
                
            classes = []
            for item in self.notes_directory.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    classes.append(item.name)
                    
            return sorted(classes)
            
        except Exception as e:
            logger.error(f"Error getting existing classes: {e}")
            return []
            
    def get_class_stats(self) -> Dict[str, int]:
        """
        Get statistics about notes per class.
        
        Returns:
            Dictionary mapping class names to note counts
        """
        stats = {}
        
        try:
            for class_dir in self.notes_directory.iterdir():
                if class_dir.is_dir() and not class_dir.name.startswith('.'):
                    note_count = len([f for f in class_dir.iterdir() 
                                    if f.is_file() and f.suffix == '.md'])
                    stats[class_dir.name] = note_count
                    
        except Exception as e:
            logger.error(f"Error getting class statistics: {e}")
            
        return stats
        
    def get_total_notes_count(self) -> int:
        """Get total number of notes across all classes."""
        return sum(self.get_class_stats().values())
        
    def search_notes(self, query: str, class_name: Optional[str] = None) -> List[Dict]:
        """
        Search for notes containing the query text.
        
        Args:
            query: Search query
            class_name: Optional class to limit search to
            
        Returns:
            List of matching note information
        """
        results = []
        query_lower = query.lower()
        
        try:
            search_dirs = []
            if class_name:
                class_dir = self.notes_directory / sanitize_class_name(class_name)
                if class_dir.exists():
                    search_dirs.append(class_dir)
            else:
                search_dirs = [d for d in self.notes_directory.iterdir() 
                             if d.is_dir() and not d.name.startswith('.')]
                
            for class_dir in search_dirs:
                for note_file in class_dir.glob('*.md'):
                    try:
                        with open(note_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        if query_lower in content.lower():
                            results.append({
                                'file_path': str(note_file),
                                'class_name': class_dir.name,
                                'filename': note_file.name,
                                'modified_time': datetime.fromtimestamp(note_file.stat().st_mtime)
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error reading note file {note_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during note search: {e}")
            
        return sorted(results, key=lambda x: x['modified_time'], reverse=True)
        
    def _ensure_directory_exists(self, directory: Path) -> None:
        """Ensure a directory exists, creating it if necessary."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"Cannot create directory {directory}: {e}")
            
    def _create_markdown_content(self, note_text: str, metadata: NoteMetadata) -> str:
        """Create the full markdown content with frontmatter."""
        # Create frontmatter metadata
        frontmatter_data = {
            'title': note_text[:50] + ('...' if len(note_text) > 50 else ''),
            'created_at': metadata.created_at.isoformat(),
            'classification': metadata.classification,
            'confidence': metadata.confidence,
            'user_id': metadata.user_id,
            'telegram_message_id': metadata.telegram_message_id,
        }
        
        if metadata.username:
            frontmatter_data['username'] = metadata.username
            
        # Create the full markdown content
        frontmatter = create_markdown_frontmatter(frontmatter_data)
        
        return f"{frontmatter}{note_text}\n"
        
    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of the saved file."""
        try:
            backup_dir = self.notes_directory / '.backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_filename
            
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            
    def cleanup_old_backups(self, days_to_keep: int = 30) -> None:
        """Clean up old backup files."""
        try:
            backup_dir = self.notes_directory / '.backups'
            if not backup_dir.exists():
                return
                
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for backup_file in backup_dir.glob('*.md'):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.debug(f"Deleted old backup: {backup_file}")
                    
        except Exception as e:
            logger.warning(f"Error during backup cleanup: {e}")
            
    def get_recent_notes(self, limit: int = 10, class_name: Optional[str] = None) -> List[Dict]:
        """
        Get recently created notes.
        
        Args:
            limit: Maximum number of notes to return
            class_name: Optional class to filter by
            
        Returns:
            List of recent note information
        """
        notes = []
        
        try:
            search_dirs = []
            if class_name:
                class_dir = self.notes_directory / sanitize_class_name(class_name)
                if class_dir.exists():
                    search_dirs.append(class_dir)
            else:
                search_dirs = [d for d in self.notes_directory.iterdir() 
                             if d.is_dir() and not d.name.startswith('.')]
                
            for class_dir in search_dirs:
                for note_file in class_dir.glob('*.md'):
                    try:
                        stat = note_file.stat()
                        notes.append({
                            'file_path': str(note_file),
                            'class_name': class_dir.name,
                            'filename': note_file.name,
                            'created_time': datetime.fromtimestamp(stat.st_ctime),
                            'modified_time': datetime.fromtimestamp(stat.st_mtime),
                            'size': stat.st_size
                        })
                    except Exception as e:
                        logger.warning(f"Error reading note file stats {note_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error getting recent notes: {e}")
            
        # Sort by creation time and limit results
        notes.sort(key=lambda x: x['created_time'], reverse=True)
        return notes[:limit]

