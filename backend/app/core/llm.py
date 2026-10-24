"""LLM client wrapper for Google Gemini."""
import json
import logging
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.settings import settings

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    """LLM service is unavailable."""
    pass


class LLMBadOutput(Exception):
    """LLM returned invalid output."""
    pass


class LLMClient:
    """Client for Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.google_api_key)
        self.model_name = settings.google_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
    
    def _call_with_retry(self, prompt: str, json_mode: bool = False) -> str:
        """Call LLM with exponential backoff retry."""
        max_retries = 2
        base_delay = 1.0
        
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        for attempt in range(max_retries + 1):
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=generation_config,
                )
                
                response = model.generate_content(prompt)
                
                if not response or not response.text:
                    raise LLMBadOutput("Empty response from LLM")
                
                return response.text
                
            except google_exceptions.ResourceExhausted as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise LLMUnavailable("Rate limit exceeded") from e
                    
            except google_exceptions.GoogleAPIError as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise LLMUnavailable(f"LLM API error: {e}") from e
                    
            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}")
                raise LLMUnavailable(f"LLM error: {e}") from e
        
        raise LLMUnavailable("Max retries exceeded")
    
    def chat_json(self, messages: List[Dict[str, str]], schema_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get JSON response from LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            schema_hint: Optional hint about expected JSON structure
            
        Returns:
            Parsed JSON dict
            
        Raises:
            LLMUnavailable: If LLM is unavailable after retries
            LLMBadOutput: If response is not valid JSON
        """
        # Build prompt from messages
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"Instructions: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        if schema_hint:
            prompt += f"\nRespond with valid JSON matching this structure: {schema_hint}\n"
        else:
            prompt += "\nRespond with valid JSON only.\n"
        
        response_text = self._call_with_retry(prompt, json_mode=True)
        
        # Parse JSON (with cleanup for common issues)
        try:
            # Remove markdown code fences if present
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {response_text[:200]}")
            # One retry with explicit instruction
            retry_prompt = prompt + f"\nPrevious response was invalid JSON. Try again with ONLY valid JSON, no markdown:\n{response_text[:100]}"
            retry_text = self._call_with_retry(retry_prompt, json_mode=True)
            try:
                return json.loads(retry_text.strip())
            except json.JSONDecodeError:
                raise LLMBadOutput(f"Invalid JSON: {e}")
    
    def chat_text(self, messages: List[Dict[str, str]]) -> str:
        """
        Get text response from LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Text response
        """
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"Instructions: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        return self._call_with_retry(prompt, json_mode=False)


class FakeLLM:
    """Fake LLM for testing."""
    
    def __init__(self, responses: Optional[List[Any]] = None):
        """Initialize with canned responses."""
        self.responses = responses or []
        self.call_count = 0
        self.captured_prompts = []
    
    def chat_json(self, messages: List[Dict[str, str]], schema_hint: Optional[str] = None) -> Dict[str, Any]:
        """Return next canned JSON response."""
        self.captured_prompts.append(messages)
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        raise LLMUnavailable("No more fake responses")
    
    def chat_text(self, messages: List[Dict[str, str]]) -> str:
        """Return next canned text response."""
        self.captured_prompts.append(messages)
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return str(response)
        raise LLMUnavailable("No more fake responses")
