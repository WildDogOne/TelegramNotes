"""
Telegram Bot for Note Classification and Organization.
Main noteBot application with handlers for user interactions.
"""

import logging
import sys
from noteBot.bot import TelegramNotesBot

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from noteBot.config import config

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

def main() -> None:
    """Main function to run the Telegram noteBot."""
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

    # Create noteBot instance
    bot = TelegramNotesBot()

    # Test Ollama connection
    if bot.ollama_client.is_available():
        logger.info("Ollama service is available")
    else:
        logger.warning("Ollama service is not available - using fallback classification")

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

    # Start the noteBot
    logger.info("Bot is starting...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running noteBot: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
