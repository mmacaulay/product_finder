"""
JSON parsing utilities with multiple strategies for handling LLM responses.

Implements robust parsing to handle common LLM output variations.
"""

import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class JSONParseError(Exception):
    """Exception raised when JSON parsing fails after all strategies"""

    pass


def parse_llm_json(
    raw_response: str, strict: bool = False
) -> tuple[Dict[str, Any], str]:
    """
    Parse JSON from LLM response using multiple strategies.

    Strategies (in order):
    1. Direct JSON parse (raw_response is pure JSON)
    2. Extract from markdown code blocks (```json ... ```)
    3. Extract from triple backticks without json tag (``` ... ```)
    4. Find first { to last } (JSON embedded in text)

    Args:
        raw_response: The raw string response from LLM
        strict: If True, only try direct JSON parse (no fallbacks)

    Returns:
        Tuple of (parsed JSON dict, strategy name)

    Raises:
        JSONParseError: If all parsing strategies fail
    """
    if not raw_response or not raw_response.strip():
        raise JSONParseError("Empty response from LLM")

    # Strategy 1: Direct JSON parse
    try:
        result = json.loads(raw_response.strip())
        return result, "direct"
    except json.JSONDecodeError as e:
        if strict:
            raise JSONParseError(f"Direct JSON parse failed: {e}")
        logger.debug(f"Strategy 1 (direct parse) failed: {e}")

    # Strategy 2: Extract from markdown code block with json tag
    try:
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, raw_response, re.DOTALL)
        if match:
            json_str = match.group(1)
            result = json.loads(json_str)
            logger.debug("Strategy 2 (markdown json block) succeeded")
            return result, "markdown_json"
    except (json.JSONDecodeError, AttributeError) as e:
        logger.debug(f"Strategy 2 (markdown json block) failed: {e}")

    # Strategy 3: Extract from any markdown code block
    try:
        pattern = r"```\s*(\{.*?\})\s*```"
        match = re.search(pattern, raw_response, re.DOTALL)
        if match:
            json_str = match.group(1)
            result = json.loads(json_str)
            logger.debug("Strategy 3 (markdown code block) succeeded")
            return result, "markdown_block"
    except (json.JSONDecodeError, AttributeError) as e:
        logger.debug(f"Strategy 3 (markdown code block) failed: {e}")

    # Strategy 4: Find first { to last } (JSON embedded in text)
    try:
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start != -1 and end != -1 and start < end:
            json_str = raw_response[start : end + 1]
            result = json.loads(json_str)
            logger.debug("Strategy 4 (extract braces) succeeded")
            return result, "extract_braces"
    except json.JSONDecodeError as e:
        logger.debug(f"Strategy 4 (extract braces) failed: {e}")

    # All strategies failed
    preview = raw_response[:200] + ("..." if len(raw_response) > 200 else "")
    raise JSONParseError(
        f"Failed to parse JSON from LLM response after all strategies. "
        f"Response preview: {preview}"
    )


def create_error_response(
    error_message: str, raw_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response when parsing fails.

    Args:
        error_message: Description of the error
        raw_response: Optional raw response from LLM

    Returns:
        Error dict that can be stored in database
    """
    return {
        "error": "parsing_failed",
        "error_message": error_message,
        "confidence": "none",
        "raw_response": raw_response[:500] if raw_response else None,
    }


def sanitize_json_string(text: str) -> str:
    """
    Sanitize a string that might contain JSON by removing common issues.

    Args:
        text: Raw text possibly containing JSON

    Returns:
        Sanitized text more likely to parse as JSON
    """
    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove common markdown artifacts
    text = text.replace("```json", "").replace("```", "")

    # Remove newlines within strings (common LLM issue)
    # This is a simple approach - more sophisticated cleaning could be added

    return text


def validate_json_structure(
    data: Dict[str, Any], required_keys: Optional[list] = None
) -> bool:
    """
    Validate basic structure of parsed JSON.

    Args:
        data: Parsed JSON data
        required_keys: Optional list of keys that must be present

    Returns:
        True if valid structure
    """
    if not isinstance(data, dict):
        return False

    if required_keys:
        return all(key in data for key in required_keys)

    return True
