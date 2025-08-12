"""
Configuration management for the Telegram Notes Bot.
Handles environment variables, validation, and default values.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the Telegram Notes Bot."""

    def __init__(self):
        """Initialize configuration with environment variables and validation."""
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

        # Ollama Configuration
        self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "30"))

        # Notes Storage Configuration
        self.NOTES_DIRECTORY: Path = Path(os.getenv("NOTES_DIRECTORY", "../notes"))
        self.BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
        self.MAX_FILENAME_LENGTH: int = int(os.getenv("MAX_FILENAME_LENGTH", "100"))

        # Bot Behavior Configuration
        self.DEFAULT_CONFIDENCE_THRESHOLD: float = float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.7"))
        self.MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
        self.RATE_LIMIT_MESSAGES_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_MESSAGES_PER_MINUTE", "10"))

        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: str = os.getenv("LOG_FILE", "../telegram_notes_bot.log")

        # Optional User Authentication
        self.ALLOWED_USERS: Optional[List[int]] = None
        self.ADMIN_USER_ID: Optional[int] = None

        self._validate_required_config()
        self._parse_optional_config()
        self._setup_directories()

    def _validate_required_config(self) -> None:
        """Validate that all required configuration is present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if self.OLLAMA_TIMEOUT <= 0:
            raise ValueError("OLLAMA_TIMEOUT must be a positive integer")

        if self.MAX_FILENAME_LENGTH <= 0:
            raise ValueError("MAX_FILENAME_LENGTH must be a positive integer")

        if not (0.0 <= self.DEFAULT_CONFIDENCE_THRESHOLD <= 1.0):
            raise ValueError("DEFAULT_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")

    def _parse_optional_config(self) -> None:
        """Parse optional configuration values."""
        # Parse allowed users
        allowed_users_str = os.getenv("ALLOWED_USERS")
        if allowed_users_str:
            try:
                self.ALLOWED_USERS = [int(user_id.strip()) for user_id in allowed_users_str.split(",")]
            except ValueError:
                logger.warning("Invalid ALLOWED_USERS format. User authentication disabled.")

        # Parse admin user ID
        admin_user_str = os.getenv("ADMIN_USER_ID")
        if admin_user_str:
            try:
                self.ADMIN_USER_ID = int(admin_user_str)
            except ValueError:
                logger.warning("Invalid ADMIN_USER_ID format. Admin features disabled.")

    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        try:
            self.NOTES_DIRECTORY.mkdir(parents=True, exist_ok=True)
            logger.info(f"Notes directory ready: {self.NOTES_DIRECTORY}")
        except Exception as e:
            raise ValueError(f"Cannot create notes directory {self.NOTES_DIRECTORY}: {e}")

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to use the bot."""
        if self.ALLOWED_USERS is None:
            return True  # No restrictions
        return user_id in self.ALLOWED_USERS

    def is_admin_user(self, user_id: int) -> bool:
        """Check if a user is an admin."""
        return self.ADMIN_USER_ID is not None and user_id == self.ADMIN_USER_ID

    def get_ollama_url(self, endpoint: str = "") -> str:
        """Get the full Ollama API URL for a given endpoint."""
        base_url = self.OLLAMA_BASE_URL.rstrip("/")
        if endpoint:
            endpoint = endpoint.lstrip("/")
            return f"{base_url}/{endpoint}"
        return base_url


# Global configuration instance
config = Config()
