"""
Ollama client wrapper for AI-powered note classification.
Handles communication with Ollama API, error handling, and response parsing.
"""

import json
import logging

import requests
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ollama import Client

from noteBot.config import config
from noteBot.constants import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class OllamaClassificationResult:
    """Data class for classification results."""

    def __init__(self, class_name: str, confidence: float, suggested_filename: str,
                 is_new_class: bool = False, raw_response: Optional[str] = None):
        self.class_name = class_name
        self.confidence = confidence
        self.suggested_filename = suggested_filename
        self.is_new_class = is_new_class
        self.raw_response = raw_response
        self.timestamp = datetime.now()


class OllamaClient:
    """Client for interacting with Ollama API for note classification."""

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.session = requests.Session()

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self.session.get(
                config.get_ollama_url("api/tags"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False

    def _ollama_generate(
            self,
            prompt: str,
            output_format: BaseModel,
            model: str = "mistral-small",
            tokens: int = -1,
            context: int = 7168,
            repeat_last: int = 64,
            temperature: float = 0.8,
    ):

        """Send request to Ollama API."""
        try:
            if output_format:
                format = output_format.model_json_schema()
            else:
                format = None
            client = Client(
                host=config.get_ollama_url(),
                headers={'x-some-header': 'some-value'}
            )
            response = client.generate(
                model=model,
                format=format,
                prompt=prompt,
                options={
                    "num_predict": tokens,
                    "num_ctx": context,
                    "repeat_last_n": repeat_last,
                    "temperature": temperature,
                },
            )
            return response
        except Exception as e:
            logger.error(f"Error sending request to Ollama: {e}")
            return None

    def classify_note(self, note_text: str, existing_classes: List[str]) -> Optional[OllamaClassificationResult]:
        """
        Classify a note using Ollama AI.
        
        Args:
            note_text: The note content to classify
            existing_classes: List of existing class names to encourage reuse
            
        Returns:
            OllamaClassificationResult or None if classification fails
        """

        class OutputFormat(BaseModel):
            class_name: str
            confidence: int
            suggested_filename: str

        try:
            prompt = self._build_classification_prompt(note_text, existing_classes)
            response = self._ollama_generate(prompt=prompt, output_format=OutputFormat, model=self.model)
            if response:
                response = json.loads(response.response)
                return self._parse_classification_response(response, existing_classes)

        except Exception as e:
            logger.error(f"Error during note classification: {e}")

        return None

    def _build_classification_prompt(self, note_text: str, existing_classes: List[str]) -> str:
        """Build the classification prompt for Ollama."""

        existing_classes_str = ", ".join(f'"{cls}"' for cls in existing_classes) if existing_classes else "none"

        return CLASSIFICATION_PROMPT.format(existing_classes_str=existing_classes_str, note_text=note_text)

    def _parse_classification_response(self, data: dict, existing_classes: List[str]) -> Optional[
        OllamaClassificationResult]:
        try:

            # Validate required fields
            required_fields = ["class_name", "confidence", "suggested_filename"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in Ollama response")
                    return None

            class_name = str(data["class_name"]).strip().lower()
            confidence = float(data["confidence"])
            suggested_filename = str(data["suggested_filename"]).strip()

            # Validate confidence range
            if not (0.0 <= confidence <= 1.0):
                logger.warning(f"Invalid confidence value: {confidence}, clamping to valid range")
                confidence = max(0.0, min(1.0, confidence))

            # Check if this is a new class
            is_new_class = class_name not in [cls.lower() for cls in existing_classes]

            return OllamaClassificationResult(
                class_name=class_name,
                confidence=confidence,
                suggested_filename=suggested_filename,
                is_new_class=is_new_class,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            logger.debug(f"Raw response: {data}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data types in Ollama response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing Ollama response: {e}")

        return None

    def get_fallback_classification(self, note_text: str) -> OllamaClassificationResult:
        """
        Provide a fallback classification when Ollama is unavailable.
        
        Args:
            note_text: The note content
            
        Returns:
            A basic classification result
        """
        # Simple keyword-based fallback classification
        text_lower = note_text.lower()

        # Basic classification rules
        if any(word in text_lower for word in ['recipe', 'cooking', 'food', 'meal', 'ingredient']):
            class_name = "cooking"
        elif any(word in text_lower for word in ['work', 'meeting', 'project', 'deadline', 'task']):
            class_name = "work"
        elif any(word in text_lower for word in ['travel', 'trip', 'vacation', 'flight', 'hotel']):
            class_name = "travel"
        elif any(word in text_lower for word in ['idea', 'thought', 'remember', 'note']):
            class_name = "ideas"
        else:
            class_name = "general"

        # Generate simple filename from first few words
        words = note_text.split()[:5]
        suggested_filename = "_".join(word.lower() for word in words if word.isalnum())
        if not suggested_filename:
            suggested_filename = "note"

        return OllamaClassificationResult(
            class_name=class_name,
            confidence=0.5,  # Low confidence for fallback
            suggested_filename=suggested_filename,
            is_new_class=True,  # Assume new since we can't check existing classes
            raw_response="Fallback classification (Ollama unavailable)"
        )
