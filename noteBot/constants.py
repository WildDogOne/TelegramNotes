WELCOME_MESSAGE = """
**Welcome to the Telegram Notes Bot!**

Hi {user.first_name}! I'm here to help you organize your notes using AI classification.

**How it works:**
1. Send me any text message as a note
2. I'll classify it using AI and suggest a category
3. Your note will be saved as a markdown file in an organized structure

**Available commands:**
• `/start` - Show this welcome message
• `/classes` - List all existing note categories
• `/stats` - Show statistics about your notes
• `/recent` - Show your recent notes
• `/help` - Detailed usage instructions

**Just send me a message to get started!**
"""

HELP_MESSAGE = """
**Detailed Help - Telegram Notes Bot**

**Basic Usage:**
Simply send me any text message, and I'll:
1. Analyze your note using AI
2. Suggest an appropriate category
3. Save it as a markdown file with metadata

**Commands:**
• `/start` - Welcome message and basic info
• `/classes` - List all existing note categories
• `/stats` - Show note count per category
• `/recent [limit]` - Show recent notes (default: 10)
• `/search <query>` - Search through your notes
• `/help` - This detailed help

**Examples:**
• "I tried a new pasta recipe with garlic and olive oil"
  → Likely classified as "cooking"
  
• "Meeting with John tomorrow at 2 PM about the project"
  → Likely classified as "work" or "meetings"
  
• "Remember to book flight tickets for vacation"
  → Likely classified as "travel" or "reminders"

**Features:**
• AI-powered classification using Ollama
• Organized file structure: `notes/category/YYYY-MM-DD_filename.md`
• Markdown files with metadata headers
• Automatic backup system
• Search functionality
• Statistics and recent notes tracking

**Note Categories:**
The noteBot will try to reuse existing categories when possible. If it suggests a new category, you can approve it or provide your own preferred category name.

**File Organization:**
Your notes are saved in a structured format:
```
notes/
├── cooking/
│   ├── 2024-01-15_pasta_recipe.md
│   └── 2024-01-16_chocolate_cake.md
├── work/
│   ├── 2024-01-15_project_meeting.md
│   └── 2024-01-16_deadline_reminder.md
└── travel/
    └── 2024-01-17_vacation_planning.md
```
"""


CLASSIFICATION_PROMPT = """
You are a note classification assistant. Your task is to classify the following note into an appropriate category and suggest a filename.

IMPORTANT INSTRUCTIONS:
1. STRONGLY PREFER existing categories over creating new ones
2. Only suggest a new category if the note clearly doesn't fit any existing category
3. Use lowercase with underscores for category names (e.g., "work_projects", "cooking_recipes")
4. Provide a confidence score between 0.0 and 1.0
5. Suggest a descriptive filename without extension
6. Respond ONLY with valid JSON in the exact format shown below

EXISTING CATEGORIES: {existing_classes_str}

NOTE TO CLASSIFY:
"{note_text}"

Respond with JSON in this exact format:
{{
    "class": "category_name",
    "confidence": 0.95,
    "suggested_filename": "descriptive_filename_without_extension"
}}

JSON Response:"""
