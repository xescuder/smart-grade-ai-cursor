"""
Google AI Service

This service class provides a simple interface to interact with Google AI APIs using an API key.
"""
import json
import re
import pathlib
from typing import Any, Dict, Optional
from logging_config import logger

from google import genai
from google.genai import types

class GoogleAIService:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://generativelanguage.googleapis.combeta2"
        self.client = genai.Client(api_key=api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    def _params(self) -> Dict[str, str]:
        return {"key": self.api_key}

    def analyse_pdf(self, file_path: str, prompt: str, model: str = "gemini-2.0-flash-exp", **kwargs) -> Any:
        """
        Generate content using Gemini model via Google AI API.

        Args:
            file_path: Path to the PDF file
            prompt: The prompt to use for analysis
            model: The Gemini model to use
            **kwargs: Additional arguments (unused)

        Returns:
            Parsed JSON data from the response
        """
        filepath = pathlib.Path(file_path)

        # Get response from Google AI
        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=filepath.read_bytes(),
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )

        # Extract text from response
        text = response.candidates[0].content.parts[0].text
        logger.info(f"Raw Google AI response: {text[:500]}...")  # Log first 500 chars

        # Remove markdown code block markers if present
        json_str = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
        logger.info(f"Cleaned JSON string: {json_str[:500]}...")  # Log first 500 chars

        # Parse and return JSON with better error handling
        try:
            json_data = json.loads(json_str)
            logger.info(f"Successfully parsed JSON with {len(json_data) if isinstance(json_data, (list, dict)) else 'unknown'} items")
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Problematic JSON string: {json_str}")
            
            # Try multiple JSON fixing strategies
            strategies = [
                ("Fix unescaped quotes in strings", lambda s: re.sub(r'(?<!\\)"(?![,}\]])', r'\\"', s)),
                ("Fix missing quotes around property names", lambda s: re.sub(r'(\w+):', r'"\1":', s)),
                ("Fix trailing commas", lambda s: re.sub(r',(\s*[}\]])', r'\1', s)),
                ("Fix single quotes to double quotes", lambda s: s.replace("'", '"')),
            ]
            
            for strategy_name, fix_func in strategies:
                try:
                    fixed_json = fix_func(json_str)
                    json_data = json.loads(fixed_json)
                    logger.info(f"Fixed JSON using strategy: {strategy_name}")
                    return json_data
                except json.JSONDecodeError:
                    continue
            
            # If all strategies fail, try to extract valid JSON parts
            try:
                # Try to find the largest valid JSON substring
                for i in range(len(json_str), 0, -1):
                    try:
                        partial_json = json_str[:i]
                        json_data = json.loads(partial_json)
                        logger.warning(f"Extracted partial JSON (first {i} characters)")
                        return json_data
                    except json.JSONDecodeError:
                        continue
            except:
                pass
            
            logger.error(f"All JSON fix attempts failed")
            raise ValueError(f"Invalid JSON response from Google AI: {e}")


if __name__ == "__main__":
    pdf_path = "/Users/escuderx/Desktop/PAC1_PDP_Enunciat.pdf"
    prompt = "Extract the exercises from the PDF in a structured format."
    api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
    generator = GoogleAIService(api_key=api_key)
    response = generator.analyse_pdf(file_path=pdf_path, prompt=prompt)
    print(response)
