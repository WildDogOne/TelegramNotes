"""
Unit tests for the main noteBot functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram import Update, User, Message
from telegram.ext import ContextTypes

from noteBot.botClass import TelegramNotesBot


class TestTelegramNotesBot:
    """Test TelegramNotesBot class functionality."""
    
    @pytest.fixture
    def bot(self):
        """Create a TelegramNotesBot instance for testing."""
        with patch('noteBot.config') as mock_config:
            mock_config.is_user_allowed.return_value = True
            mock_config.is_admin_user.return_value = False
            mock_config.MAX_MESSAGE_LENGTH = 4000
            mock_config.DEFAULT_CONFIDENCE_THRESHOLD = 0.7
            
            return TelegramNotesBot()
            
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update."""
        update = MagicMock(spec=Update)
        update.effective_user = User(
            id=123456,
            first_name="Test",
            is_bot=False,
            username="testuser"
        )
        update.message = MagicMock(spec=Message)
        update.message.message_id = 789
        update.message.text = "Test message"
        update.message.reply_text = AsyncMock()
        return update
        
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
        
    @pytest.mark.asyncio
    async def test_start_command_authorized_user(self, bot, mock_update, mock_context):
        """Test /start command for authorized user."""
        with patch('noteBot.config.is_user_allowed', return_value=True):
            await bot.start_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Welcome to the Telegram Notes Bot" in call_args[0][0]
            
    @pytest.mark.asyncio
    async def test_start_command_unauthorized_user(self, bot, mock_update, mock_context):
        """Test /start command for unauthorized user."""
        with patch('noteBot.config.is_user_allowed', return_value=False):
            await bot.start_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "not authorized" in call_args[0][0]
            
    @pytest.mark.asyncio
    async def test_help_command(self, bot, mock_update, mock_context):
        """Test /help command."""
        await bot.help_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Detailed Help" in call_args[0][0]
        assert "Commands:" in call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_classes_command_no_classes(self, bot, mock_update, mock_context):
        """Test /classes command when no classes exist."""
        with patch.object(bot.file_manager, 'get_existing_classes', return_value=[]):
            await bot.classes_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "No note categories exist" in call_args[0][0]
            
    @pytest.mark.asyncio
    async def test_classes_command_with_classes(self, bot, mock_update, mock_context):
        """Test /classes command with existing classes."""
        mock_classes = ["cooking", "work", "travel"]
        
        with patch.object(bot.file_manager, 'get_existing_classes', return_value=mock_classes):
            await bot.classes_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "Existing Note Categories" in message_text
            for class_name in mock_classes:
                assert class_name in message_text
                
    @pytest.mark.asyncio
    async def test_stats_command(self, bot, mock_update, mock_context):
        """Test /stats command."""
        mock_stats = {"cooking": 5, "work": 3, "travel": 2}
        
        with patch.object(bot.file_manager, 'get_class_stats', return_value=mock_stats):
            await bot.stats_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "Note Statistics" in message_text
            assert "Total Notes: 10" in message_text
            assert "cooking: 5 notes" in message_text
            
    @pytest.mark.asyncio
    async def test_recent_command_default_limit(self, bot, mock_update, mock_context):
        """Test /recent command with default limit."""
        mock_notes = [
            {
                'class_name': 'cooking',
                'filename': 'pasta_recipe.md',
                'created_time': MagicMock()
            }
        ]
        mock_notes[0]['created_time'].strftime.return_value = "2024-01-15 14:30"
        
        with patch.object(bot.file_manager, 'get_recent_notes', return_value=mock_notes):
            await bot.recent_command(mock_update, mock_context)
            
            # Check that get_recent_notes was called with default limit
            bot.file_manager.get_recent_notes.assert_called_once_with(limit=10)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "Recent Notes" in message_text
            assert "cooking" in message_text
            assert "pasta_recipe" in message_text
            
    @pytest.mark.asyncio
    async def test_recent_command_custom_limit(self, bot, mock_update, mock_context):
        """Test /recent command with custom limit."""
        mock_context.args = ["5"]
        
        with patch.object(bot.file_manager, 'get_recent_notes', return_value=[]):
            await bot.recent_command(mock_update, mock_context)
            
            # Check that get_recent_notes was called with custom limit
            bot.file_manager.get_recent_notes.assert_called_once_with(limit=5)
            
    @pytest.mark.asyncio
    async def test_recent_command_invalid_limit(self, bot, mock_update, mock_context):
        """Test /recent command with invalid limit."""
        mock_context.args = ["invalid"]
        
        await bot.recent_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Invalid limit" in call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_search_command_no_args(self, bot, mock_update, mock_context):
        """Test /search command without arguments."""
        mock_context.args = []
        
        await bot.search_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Search Usage" in call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_search_command_with_results(self, bot, mock_update, mock_context):
        """Test /search command with results."""
        mock_context.args = ["pasta", "recipe"]
        mock_results = [
            {
                'class_name': 'cooking',
                'filename': 'pasta_recipe.md',
                'modified_time': MagicMock()
            }
        ]
        mock_results[0]['modified_time'].strftime.return_value = "2024-01-15"
        
        with patch.object(bot.file_manager, 'search_notes', return_value=mock_results):
            await bot.search_command(mock_update, mock_context)
            
            # Check that search_notes was called with correct query
            bot.file_manager.search_notes.assert_called_once_with("pasta recipe", None)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "Search Results" in message_text
            assert "cooking" in message_text
            
    @pytest.mark.asyncio
    async def test_handle_note_message_too_long(self, bot, mock_update, mock_context):
        """Test handling of messages that are too long."""
        mock_update.message.text = "x" * 5000  # Exceeds MAX_MESSAGE_LENGTH
        
        with patch('noteBot.config.MAX_MESSAGE_LENGTH', 4000):
            await bot.handle_note_message(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "too long" in call_args[0][0]
            
    @pytest.mark.asyncio
    async def test_handle_note_message_unauthorized(self, bot, mock_update, mock_context):
        """Test handling of messages from unauthorized users."""
        with patch('noteBot.config.is_user_allowed', return_value=False):
            await bot.handle_note_message(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "not authorized" in call_args[0][0]
