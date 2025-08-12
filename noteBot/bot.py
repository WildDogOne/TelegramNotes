"""
Telegram Bot for Note Classification and Organization.
Main bot application with handlers for user interactions.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from noteBot.config import config
from noteBot.constants import HELP_MESSAGE, WELCOME_MESSAGE
from noteBot.ollama_client import OllamaClient
from noteBot.file_manager import FileManager, NoteMetadata
from noteBot.utils import truncate_text, user_allowed

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL.upper()),
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TelegramNotesBot:
    """Main Telegram bot class for note classification and organization."""

    def __init__(self):
        self.ollama_client = OllamaClient()
        self.file_manager = FileManager()
        self.pending_classifications: Dict[int, Dict] = {}  # Store pending user confirmations

    @user_allowed
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        welcome_message = WELCOME_MESSAGE.format(user=user)
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"User {user.id} ({user.username}) started the bot")

    @user_allowed
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_message = HELP_MESSAGE
        await update.message.reply_text(help_message, parse_mode='Markdown')

    @user_allowed
    async def classes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /classes command."""

        existing_classes = self.file_manager.get_existing_classes()

        if not existing_classes:
            await update.message.reply_text(
                "No note categories exist yet.\n\nSend me your first note to get started!"
            )
            return

        class_list = "\n".join(f"• `{cls}`" for cls in existing_classes)
        message = f"**Existing Note Categories ({len(existing_classes)}):**\n\n{class_list}"

        await update.message.reply_text(message, parse_mode='Markdown')

    @user_allowed
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /stats command."""

        stats = self.file_manager.get_class_stats()
        total_notes = sum(stats.values())

        if not stats:
            await update.message.reply_text(
                "No notes found.\n\nSend me your first note to get started!"
            )
            return

        # Sort by note count (descending)
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        stats_lines = []
        for class_name, count in sorted_stats:
            percentage = (count / total_notes * 100) if total_notes > 0 else 0
            stats_lines.append(f"• `{class_name}`: {count} notes ({percentage:.1f}%)")

        stats_text = "\n".join(stats_lines)
        message = f"📊 **Note Statistics:**\n\n{stats_text}\n\n**Total Notes:** {total_notes}"

        await update.message.reply_text(message, parse_mode='Markdown')

    @user_allowed
    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /recent command."""

        # Parse limit from command arguments
        limit = 10
        if context.args:
            try:
                limit = int(context.args[0])
                limit = max(1, min(limit, 50))  # Clamp between 1 and 50
            except ValueError:
                await update.message.reply_text("❌ Invalid limit. Please provide a number between 1 and 50.")
                return

        recent_notes = self.file_manager.get_recent_notes(limit=limit)

        if not recent_notes:
            await update.message.reply_text("📝 No notes found.")
            return

        notes_lines = []
        for note in recent_notes:
            created_time = note['created_time'].strftime("%Y-%m-%d %H:%M")
            filename = note['filename'].replace('.md', '')
            notes_lines.append(f"• `{note['class_name']}` - {filename} ({created_time})")

        notes_text = "\n".join(notes_lines)
        message = f"📝 **Recent Notes ({len(recent_notes)}):**\n\n{notes_text}"

        await update.message.reply_text(message, parse_mode='Markdown')

    @user_allowed
    async def handle_note_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming note messages."""
        user = update.effective_user

        note_text = update.message.text

        if len(note_text) > config.MAX_MESSAGE_LENGTH:
            await update.message.reply_text(
                f"❌ Note is too long. Maximum length is {config.MAX_MESSAGE_LENGTH} characters."
            )
            return

        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Classifying your note...")

        try:
            # Get existing classes for context
            existing_classes = self.file_manager.get_existing_classes()

            # Classify the note
            classification_result = None
            if self.ollama_client.is_available():
                classification_result = self.ollama_client.classify_note(note_text, existing_classes)

            if not classification_result:
                # Use fallback classification
                classification_result = self.ollama_client.get_fallback_classification(note_text)
                await processing_msg.edit_text("⚠️ AI service unavailable, using fallback classification...")

            # Handle new class suggestions
            if classification_result.is_new_class and classification_result.confidence >= config.DEFAULT_CONFIDENCE_THRESHOLD:
                await self._handle_new_class_suggestion(update, context, note_text, classification_result,
                                                        processing_msg)
            else:
                # Save the note directly
                await self._save_note_directly(update, context, note_text, classification_result, processing_msg)

        except Exception as e:
            logger.error(f"Error processing note from user {user.id}: {e}")
            await processing_msg.edit_text("❌ An error occurred while processing your note. Please try again.")

    async def _handle_new_class_suggestion(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           note_text: str, classification_result, processing_msg) -> None:
        """Handle suggestions for new note classes."""
        user_id = update.effective_user.id

        # Store pending classification
        self.pending_classifications[user_id] = {
            'note_text': note_text,
            'classification_result': classification_result,
            'original_message_id': update.message.message_id,
            'timestamp': datetime.now()
        }

        # Create inline keyboard for user choice
        keyboard = [
            [InlineKeyboardButton(f"✅ Use '{classification_result.class_name}'",
                                  callback_data=f"accept_class_{user_id}")],
            [InlineKeyboardButton("✏️ Choose different category",
                                  callback_data=f"custom_class_{user_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confidence_percent = int(classification_result.confidence * 100)
        message = (
            f"🤔 I suggest creating a new category **'{classification_result.class_name}'** "
            f"for your note (confidence: {confidence_percent}%).\n\n"
            f"**Note preview:** {truncate_text(note_text, 100)}\n\n"
            f"What would you like to do?"
        )

        await processing_msg.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def _save_note_directly(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  note_text: str, classification_result, processing_msg) -> None:
        """Save a note directly without user confirmation."""
        user = update.effective_user

        # Create metadata
        metadata = NoteMetadata(
            original_text=note_text,
            classification=classification_result.class_name,
            confidence=classification_result.confidence,
            user_id=user.id,
            username=user.username,
            telegram_message_id=update.message.message_id
        )

        # Save the note
        success, file_path, error_msg = self.file_manager.save_note(
            note_text,
            classification_result.class_name,
            classification_result.suggested_filename,
            metadata
        )

        if success:
            confidence_percent = int(classification_result.confidence * 100)
            message = (
                f"✅ **Note saved successfully!**\n\n"
                f"📁 **Category:** `{classification_result.class_name}`\n"
                f"🎯 **Confidence:** {confidence_percent}%\n"
                f"📄 **File:** `{Path(file_path).name}`"
            )

            if classification_result.confidence < config.DEFAULT_CONFIDENCE_THRESHOLD:
                message += f"\n\n⚠️ *Low confidence classification. You can move this note to a different category if needed.*"

        else:
            message = f"❌ **Failed to save note:** {error_msg}"

        await processing_msg.edit_text(message, parse_mode='Markdown')

    @user_allowed
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard button presses."""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data

        if user_id not in self.pending_classifications:
            await query.edit_message_text("❌ No pending classification found. Please send a new note.")
            return

        pending = self.pending_classifications[user_id]

        if data == f"accept_class_{user_id}":
            # User accepted the suggested class
            await self._save_note_from_pending(query, pending)
            del self.pending_classifications[user_id]

        elif data == f"custom_class_{user_id}":
            # User wants to provide custom class
            await query.edit_message_text(
                "✏️ **Please reply with your preferred category name.**\n\n"
                f"Note: {truncate_text(pending['note_text'], 100)}\n\n"
                "Send the category name as your next message.",
                parse_mode='Markdown'
            )
            # Keep the pending classification for the next message

    @user_allowed
    async def handle_custom_class_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle custom class name input from user."""
        user_id = update.effective_user.id

        if user_id not in self.pending_classifications:
            # This is a regular note, not a custom class response
            await self.handle_note_message(update, context)
            return

        custom_class = update.message.text.strip().lower()
        pending = self.pending_classifications[user_id]

        # Update the classification result with custom class
        pending['classification_result'].class_name = custom_class
        pending['classification_result'].is_new_class = custom_class not in self.file_manager.get_existing_classes()

        # Save the note with custom class
        processing_msg = await update.message.reply_text("💾 Saving note with your custom category...")

        await self._save_note_from_pending_with_message(processing_msg, pending)
        del self.pending_classifications[user_id]

    async def _save_note_from_pending(self, query, pending) -> None:
        """Save a note from pending classification data."""
        classification_result = pending['classification_result']
        note_text = pending['note_text']

        # Create metadata
        metadata = NoteMetadata(
            original_text=note_text,
            classification=classification_result.class_name,
            confidence=classification_result.confidence,
            user_id=query.from_user.id,
            username=query.from_user.username,
            telegram_message_id=pending.get('original_message_id')
        )

        # Save the note
        success, file_path, error_msg = self.file_manager.save_note(
            note_text,
            classification_result.class_name,
            classification_result.suggested_filename,
            metadata
        )

        if success:
            confidence_percent = int(classification_result.confidence * 100)
            message = (
                f"✅ **Note saved successfully!**\n\n"
                f"📁 **Category:** `{classification_result.class_name}`\n"
                f"🎯 **Confidence:** {confidence_percent}%\n"
                f"📄 **File:** `{Path(file_path).name}`"
            )
        else:
            message = f"❌ **Failed to save note:** {error_msg}"

        await query.edit_message_text(message, parse_mode='Markdown')

    async def _save_note_from_pending_with_message(self, message, pending) -> None:
        """Save a note from pending classification data with a message to edit."""
        classification_result = pending['classification_result']
        note_text = pending['note_text']

        # Create metadata
        metadata = NoteMetadata(
            original_text=note_text,
            classification=classification_result.class_name,
            confidence=classification_result.confidence,
            user_id=message.chat.id,  # This might need adjustment based on context
            username=None,  # We don't have username in this context
            telegram_message_id=pending.get('original_message_id')
        )

        # Save the note
        success, file_path, error_msg = self.file_manager.save_note(
            note_text,
            classification_result.class_name,
            classification_result.suggested_filename,
            metadata
        )

        if success:
            response = (
                f"✅ **Note saved successfully!**\n\n"
                f"📁 **Category:** `{classification_result.class_name}`\n"
                f"📄 **File:** `{Path(file_path).name}`"
            )
        else:
            response = f"❌ **Failed to save note:** {error_msg}"

        await message.edit_text(response, parse_mode='Markdown')

    @user_allowed
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /search command."""

        if not context.args:
            await update.message.reply_text(
                "🔍 **Search Usage:**\n\n"
                "`/search <query>` - Search through all notes\n"
                "`/search <query> in <category>` - Search within a specific category\n\n"
                "**Examples:**\n"
                "• `/search pasta recipe`\n"
                "• `/search meeting in work`",
                parse_mode='Markdown'
            )
            return

        # Parse search query and optional category
        query_parts = ' '.join(context.args)
        class_name = None

        if ' in ' in query_parts:
            query, class_part = query_parts.rsplit(' in ', 1)
            class_name = class_part.strip()
        else:
            query = query_parts

        # Perform search
        results = self.file_manager.search_notes(query, class_name)

        if not results:
            search_scope = f" in category '{class_name}'" if class_name else ""
            await update.message.reply_text(
                f"🔍 No notes found for '{query}'{search_scope}."
            )
            return

        # Format results
        results_lines = []
        for i, result in enumerate(results[:10], 1):  # Limit to 10 results
            modified_time = result['modified_time'].strftime("%Y-%m-%d")
            filename = result['filename'].replace('.md', '')
            results_lines.append(
                f"{i}. `{result['class_name']}` - {filename} ({modified_time})"
            )

        results_text = "\n".join(results_lines)
        total_results = len(results)
        showing = min(10, total_results)

        message = f"🔍 **Search Results for '{query}':**\n\n{results_text}"

        if total_results > 10:
            message += f"\n\n*Showing {showing} of {total_results} results*"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors that occur during bot operation."""
        logger.error(f"Exception while handling an update: {context.error}")

        # Try to send error message to user if possible
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again later."
                )
            except Exception:
                pass  # Ignore errors when trying to send error message


def main() -> None:
    """Main function to run the Telegram bot."""
    logger.info("Starting Telegram Notes Bot...")

    # Validate configuration
    try:
        if not config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            sys.exit(1)

        logger.info(f"Notes directory: {config.NOTES_DIRECTORY}")
        logger.info(f"Ollama URL: {config.OLLAMA_BASE_URL}")
        logger.info(f"Ollama Model: {config.OLLAMA_MODEL}")

    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Create bot instance
    bot = TelegramNotesBot()

    # Test Ollama connection
    if bot.ollama_client.is_available():
        logger.info("✅ Ollama service is available")
    else:
        logger.warning("⚠️ Ollama service is not available - using fallback classification")

    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("classes", bot.classes_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("recent", bot.recent_command))
    application.add_handler(CommandHandler("search", bot.search_command))

    # Add callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))

    # Add message handler for notes (with custom class handling)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        bot.handle_custom_class_message
    ))

    # Add error handler
    application.add_error_handler(bot.error_handler)

    # Start the bot
    logger.info("🤖 Bot is starting...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
