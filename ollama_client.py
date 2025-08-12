"""
Ollama client wrapper for AI-powered note classification.
Handles communication with Ollama API, error handling, and response parsing.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import config
from utils import extract_keywords

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
            
    def classify_note(self, note_text: str, existing_classes: List[str]) -> Optional[OllamaClassificationResult]:
        """
        Classify a note using Ollama AI.
        
        Args:
            note_text: The note content to classify
            existing_classes: List of existing class names to encourage reuse
            
        Returns:
            OllamaClassificationResult or None if classification fails
        """
        try:
            prompt = self._build_classification_prompt(note_text, existing_classes)
            response = self._send_request(prompt)
            
            if response:
                return self._parse_classification_response(response, existing_classes)
                
        except Exception as e:
            logger.error(f"Error during note classification: {e}")
            
        return None
        
    def _build_classification_prompt(self, note_text: str, existing_classes: List[str]) -> str:
        """Build the classification prompt for Ollama."""
        keywords = extract_keywords(note_text, max_keywords=5)
        keywords_str = ", ".join(keywords) if keywords else "none identified"
        
        existing_classes_str = ", ".join(f'"{cls}"' for cls in existing_classes) if existing_classes else "none"
        
        prompt = f"""You are a note classification assistant. Your task is to classify the following note into an appropriate category and suggest a filename.

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

EXTRACTED KEYWORDS: {keywords_str}

Respond with JSON in this exact format:
{{
    "class": "category_name",
    "confidence": 0.95,
    "suggested_filename": "descriptive_filename_without_extension"
}}

JSON Response:"""

        return prompt
        
    def _send_request(self, prompt: str) -> Optional[str]:
        """Send request to Ollama API."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent classification
                    "top_p": 0.9,
                    "num_predict": 200   # Limit response length
                }
            }
            
            logger.debug(f"Sending request to Ollama: {config.get_ollama_url('api/generate')}")
            
            response = self.session.post(
                config.get_ollama_url("api/generate"),
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "response" in result:
                return result["response"].strip()
            else:
                logger.error(f"Unexpected Ollama response format: {result}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama request: {e}")
            
        return None
        
    def _parse_classification_response(self, response: str, existing_classes: List[str]) -> Optional[OllamaClassificationResult]:
        """Parse the JSON response from Ollama."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in Ollama response")
                return None
                
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["class", "confidence", "suggested_filename"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in Ollama response")
                    return None
                    
            class_name = str(data["class"]).strip().lower()
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
                raw_response=response
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            logger.debug(f"Raw response: {response}")
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
