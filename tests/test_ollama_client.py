"""
Unit tests for Ollama client functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

from noteBot.ollama_client import OllamaClient, OllamaClassificationResult


class TestOllamaClient:
    """Test OllamaClient class functionality."""
    
    @pytest.fixture
    def ollama_client(self):
        """Create an OllamaClient instance for testing."""
        with patch('ollama_client.config') as mock_config:
            mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
            mock_config.OLLAMA_MODEL = "llama3.1"
            mock_config.OLLAMA_TIMEOUT = 30
            mock_config.get_ollama_url = lambda endpoint: f"http://localhost:11434/{endpoint}"
            
            return OllamaClient()
            
    def test_is_available_success(self, ollama_client):
        """Test successful availability check."""
        with patch.object(ollama_client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            assert ollama_client.is_available() is True
            
    def test_is_available_failure(self, ollama_client):
        """Test failed availability check."""
        with patch.object(ollama_client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            assert ollama_client.is_available() is False
            
    def test_classify_note_success(self, ollama_client):
        """Test successful note classification."""
        note_text = "I tried a new pasta recipe with garlic and olive oil"
        existing_classes = ["cooking", "work", "travel"]
        
        # Mock successful API response
        mock_response_data = {
            "response": '{"class": "cooking", "confidence": 0.95, "suggested_filename": "pasta_recipe_garlic_olive_oil"}'
        }
        
        with patch.object(ollama_client.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = ollama_client.classify_note(note_text, existing_classes)
            
            assert result is not None
            assert isinstance(result, OllamaClassificationResult)
            assert result.class_name == "cooking"
            assert result.confidence == 0.95
            assert result.suggested_filename == "pasta_recipe_garlic_olive_oil"
            assert result.is_new_class is False  # "cooking" exists in existing_classes
            
    def test_classify_note_new_class(self, ollama_client):
        """Test classification suggesting a new class."""
        note_text = "Planning my workout routine for next week"
        existing_classes = ["cooking", "work", "travel"]
        
        mock_response_data = {
            "response": '{"class": "fitness", "confidence": 0.88, "suggested_filename": "workout_routine_planning"}'
        }
        
        with patch.object(ollama_client.session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = ollama_client.classify_note(note_text, existing_classes)
            
            assert result is not None
            assert result.class_name == "fitness"
            assert result.is_new_class is True  # "fitness" not in existing_classes
            
    def test_classify_note_api_error(self, ollama_client):
        """Test handling of API errors."""
        note_text = "Test note"
        existing_classes = []
        
        with patch.object(ollama_client.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()
            
            result = ollama_client.classify_note(note_text, existing_classes)
            
            assert result is None
            
    def test_classify_note_timeout(self, ollama_client):
        """Test handling of API timeout."""
        note_text = "Test note"
        existing_classes = []
        
        with patch.object(ollama_client.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()
            
            result = ollama_client.classify_note(note_text, existing_classes)
            
            assert result is None
            
    def test_parse_classification_response_valid_json(self, ollama_client):
        """Test parsing valid JSON response."""
        response = '{"class": "work", "confidence": 0.92, "suggested_filename": "meeting_notes"}'
        existing_classes = ["work", "cooking"]
        
        result = ollama_client._parse_classification_response(response, existing_classes)
        
        assert result is not None
        assert result.class_name == "work"
        assert result.confidence == 0.92
        assert result.suggested_filename == "meeting_notes"
        assert result.is_new_class is False
        
    def test_parse_classification_response_invalid_json(self, ollama_client):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"
        existing_classes = []
        
        result = ollama_client._parse_classification_response(response, existing_classes)
        
        assert result is None
        
    def test_parse_classification_response_missing_fields(self, ollama_client):
        """Test parsing JSON with missing required fields."""
        response = '{"class": "work", "confidence": 0.92}'  # Missing suggested_filename
        existing_classes = []
        
        result = ollama_client._parse_classification_response(response, existing_classes)
        
        assert result is None
        
    def test_parse_classification_response_invalid_confidence(self, ollama_client):
        """Test parsing JSON with invalid confidence value."""
        response = '{"class": "work", "confidence": 1.5, "suggested_filename": "test"}'
        existing_classes = []
        
        result = ollama_client._parse_classification_response(response, existing_classes)
        
        assert result is not None
        assert result.confidence == 1.0  # Should be clamped to valid range
        
    def test_parse_classification_response_json_in_text(self, ollama_client):
        """Test parsing JSON embedded in other text."""
        response = 'Here is the classification: {"class": "work", "confidence": 0.85, "suggested_filename": "notes"} and some more text.'
        existing_classes = []
        
        result = ollama_client._parse_classification_response(response, existing_classes)
        
        assert result is not None
        assert result.class_name == "work"
        assert result.confidence == 0.85
        
    def test_get_fallback_classification_cooking(self, ollama_client):
        """Test fallback classification for cooking-related text."""
        note_text = "I made a delicious pasta recipe with fresh ingredients"
        
        result = ollama_client.get_fallback_classification(note_text)
        
        assert result.class_name == "cooking"
        assert result.confidence == 0.5
        assert result.is_new_class is True
        assert "pasta" in result.suggested_filename
        
    def test_get_fallback_classification_work(self, ollama_client):
        """Test fallback classification for work-related text."""
        note_text = "Meeting with the project team about upcoming deadlines"
        
        result = ollama_client.get_fallback_classification(note_text)
        
        assert result.class_name == "work"
        assert result.confidence == 0.5
        
    def test_get_fallback_classification_travel(self, ollama_client):
        """Test fallback classification for travel-related text."""
        note_text = "Planning my vacation trip to Europe next summer"
        
        result = ollama_client.get_fallback_classification(note_text)
        
        assert result.class_name == "travel"
        assert result.confidence == 0.5
        
    def test_get_fallback_classification_general(self, ollama_client):
        """Test fallback classification for general text."""
        note_text = "Random thoughts about life and philosophy"
        
        result = ollama_client.get_fallback_classification(note_text)
        
        assert result.class_name == "general"
        assert result.confidence == 0.5
        
    def test_build_classification_prompt(self, ollama_client):
        """Test building classification prompt."""
        note_text = "I tried a new pasta recipe with garlic"
        existing_classes = ["cooking", "work"]
        
        prompt = ollama_client._build_classification_prompt(note_text, existing_classes)
        
        assert "pasta recipe with garlic" in prompt
        assert '"cooking", "work"' in prompt
        assert "JSON" in prompt
        assert "confidence" in prompt
        
    def test_build_classification_prompt_no_existing_classes(self, ollama_client):
        """Test building prompt with no existing classes."""
        note_text = "Test note"
        existing_classes = []
        
        prompt = ollama_client._build_classification_prompt(note_text, existing_classes)
        
        assert "none" in prompt.lower()
        assert "Test note" in prompt


class TestOllamaClassificationResult:
    """Test OllamaClassificationResult data class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        result = OllamaClassificationResult(
            class_name="cooking",
            confidence=0.95,
            suggested_filename="pasta_recipe",
            is_new_class=False,
            raw_response='{"class": "cooking"}'
        )
        
        assert result.class_name == "cooking"
        assert result.confidence == 0.95
        assert result.suggested_filename == "pasta_recipe"
        assert result.is_new_class is False
        assert result.raw_response == '{"class": "cooking"}'
        assert result.timestamp is not None
        
    def test_default_values(self):
        """Test initialization with default values."""
        result = OllamaClassificationResult(
            class_name="work",
            confidence=0.8,
            suggested_filename="meeting"
        )
        
        assert result.is_new_class is False
        assert result.raw_response is None
