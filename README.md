# Telegram Notes Bot

An intelligent Telegram bot that automatically classifies and organizes your notes using AI-powered categorization through Ollama. Transform your scattered thoughts into a structured markdown knowledge base.

## 🌟 Features

- **AI-Powered Classification**: Automatically categorizes notes using Ollama AI models
- **Intelligent Organization**: Creates structured markdown files with metadata
- **Smart Class Management**: Reuses existing categories and suggests new ones when needed
- **Robust File System**: Organized directory structure with backup support
- **User-Friendly Interface**: Interactive commands and inline keyboards
- **Search Functionality**: Find notes across categories with text search
- **Statistics & Analytics**: Track note counts and recent activity
- **Fallback System**: Works even when AI service is unavailable

## 🏗️ Architecture

```
TelegramNotes/
├── bot.py                 # Main Telegram bot application
├── config.py             # Configuration management
├── ollama_client.py      # Ollama AI integration
├── file_manager.py       # File system operations
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── .env.example          # Environment configuration template
├── tests/                # Unit tests
└── notes/                # Generated notes (auto-created)
    ├── cooking/
    │   ├── 2024-01-15_pasta_recipe.md
    │   └── 2024-01-16_chocolate_cake.md
    ├── work/
    │   ├── 2024-01-15_meeting_notes.md
    │   └── 2024-01-16_project_ideas.md
    └── travel/
        └── 2024-01-17_vacation_planning.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Ollama installed and running (local or remote)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/TelegramNotes.git
   cd TelegramNotes
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up Ollama** (if not already installed)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model (e.g., llama3.1)
   ollama pull llama3.1
   ```

5. **Run the bot**
   ```bash
   python noteBot.py
   ```

## ⚙️ Configuration

Edit the `.env` file with your settings:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=30

# Storage Settings
NOTES_DIRECTORY=./notes
BACKUP_ENABLED=true
MAX_FILENAME_LENGTH=100

# Bot Behavior
DEFAULT_CONFIDENCE_THRESHOLD=0.7
MAX_MESSAGE_LENGTH=4000
RATE_LIMIT_MESSAGES_PER_MINUTE=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=telegram_notes_bot.log

# Optional: User Authentication
# ALLOWED_USERS=123456789,987654321
# ADMIN_USER_ID=123456789
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and basic instructions |
| `/help` | Detailed usage guide |
| `/classes` | List all existing note categories |
| `/stats` | Show note count per category |
| `/recent [limit]` | Show recent notes (default: 10) |
| `/search <query>` | Search through notes |

## 📝 Usage Examples

### Basic Note Taking
```
User: "I tried a new pasta recipe today with garlic and olive oil"
Bot: 🔄 Classifying your note...
Bot: ✅ Note saved successfully!
     📁 Category: cooking
     🎯 Confidence: 92%
     📄 File: 2024-01-15_pasta_recipe_garlic_olive_oil.md
```

### New Category Suggestion
```
User: "Planning my workout routine for next week"
Bot: 🤔 I suggest creating a new category 'fitness' for your note (confidence: 85%).
     
     Note preview: Planning my workout routine for next week
     
     What would you like to do?
     [✅ Use 'fitness'] [✏️ Choose different category]
```

### Search Functionality
```
User: /search pasta recipe
Bot: 🔍 Search Results for 'pasta recipe':
     
     1. cooking - pasta_recipe_garlic_olive_oil (2024-01-15)
     2. cooking - pasta_carbonara_notes (2024-01-10)
```

## 📊 File Structure

Each note is saved as a markdown file with YAML frontmatter:

```markdown
---
title: "I tried a new pasta recipe today with garlic and olive oil"
created_at: "2024-01-15T14:30:45.123456"
classification: "cooking"
confidence: 0.92
user_id: 123456789
username: "john_doe"
telegram_message_id: 456
---

I tried a new pasta recipe today with garlic and olive oil. It turned out amazing! The key was using fresh garlic and good quality olive oil. Next time I'll add some parmesan cheese.
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py -v
```

## 🔧 Development

### Project Structure

- **`bot.py`**: Main application with Telegram bot handlers
- **`config.py`**: Configuration management and validation
- **`ollama_client.py`**: AI integration with error handling
- **`file_manager.py`**: File system operations and organization
- **`utils.py`**: Utility functions for text processing
- **`tests/`**: Comprehensive unit test suite

### Adding New Features

1. **New Commands**: Add handlers in `bot.py`
2. **AI Models**: Modify `ollama_client.py` for different models
3. **File Formats**: Extend `file_manager.py` for new formats
4. **Utilities**: Add helper functions to `utils.py`

## 🚨 Troubleshooting

### Common Issues

**Bot not responding**
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify bot is started with `/start` command
- Check logs in `telegram_notes_bot.log`

**Ollama connection failed**
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` configuration
- Verify model is available: `ollama list`

**Permission errors**
- Check `NOTES_DIRECTORY` write permissions
- Ensure user authentication settings if configured

**Classification issues**
- Lower `DEFAULT_CONFIDENCE_THRESHOLD` for more suggestions
- Check Ollama model performance
- Review fallback classification rules

### Logs and Debugging

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

Check log file:
```bash
tail -f telegram_notes_bot.log
```

## 🔒 Security Considerations

- **User Authentication**: Configure `ALLOWED_USERS` for restricted access
- **Rate Limiting**: Built-in protection against spam
- **Input Sanitization**: All user inputs are sanitized
- **File System Security**: Safe filename generation and path handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Ollama](https://ollama.ai/) - Local AI model serving
- [PyYAML](https://pyyaml.org/) - YAML processing for frontmatter

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/TelegramNotes/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/TelegramNotes/discussions)
- **Documentation**: This README and inline code comments

---

**Happy note-taking! 📝✨**
