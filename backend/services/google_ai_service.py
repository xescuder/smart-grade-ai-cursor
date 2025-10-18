"""
Google AI Service

This service class provides a simple interface to interact with Google AI APIs using an API key.
"""
import json
import re

from typing import Any, Dict, Optional
from logging import getLogger

from google import genai
from google.genai import types

from ai_prompts import CATALAN_EXERCISE_EXTRACTION_PROMPT


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

    def analyse_pdf(
        self,
        *,
        pdf_bytes: bytes,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        **kwargs
    ) -> Any:
        """
        Generate content using Gemini model via Google AI API.

        Args:
            pdf_bytes: Raw PDF bytes to analyse (mandatory)
            prompt: The prompt to use for analysis
            model: The Gemini model to use
            **kwargs: Additional arguments (unused)

        Returns:
            Parsed JSON data from the response
        """
        if pdf_bytes is None:
            raise ValueError("analyse_pdf requires pdf_bytes. Provide raw PDF bytes.")

        # Get response from Google AI
        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )

        # Extract text from response
        text = response.candidates[0].content.parts[0].text
        logger = getLogger()
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
                ("Fix unescaped quotes in criteria arrays", lambda s: re.sub(r'"([^"]*)"([^"]*)"([^"]*)"', r'"\1\\"\2\\"\3"', s)),
                ("Fix multiline strings", lambda s: re.sub(r'"([^"]*\n[^"]*)"', lambda m: f'"{m.group(1).replace(chr(10), "\\n").replace(chr(13), "\\r")}"', s)),
            ]
            
            for strategy_name, fix_func in strategies:
                try:
                    fixed_json = fix_func(json_str)
                    json_data = json.loads(fixed_json)
                    logger.info(f"Fixed JSON using strategy: {strategy_name}")
                    return json_data
                except json.JSONDecodeError:
                    continue
            
            # If all strategies fail, try to extract valid JSON parts using regex
            try:
                logger.info("Attempting regex-based JSON extraction")
                # Look for the exercises array pattern
                exercises_match = re.search(r'"exercises"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if exercises_match:
                    exercises_content = exercises_match.group(1)
                    logger.info(f"Found exercises content: {exercises_content[:200]}...")
                    
                    # Try to parse individual exercise objects
                    exercise_pattern = r'\{(.*?)\}'
                    exercises = re.findall(exercise_pattern, exercises_content, re.DOTALL)
                    
                    parsed_exercises = []
                    for i, exercise_str in enumerate(exercises):
                        try:
                            # Clean up the exercise string
                            clean_exercise = exercise_str.strip()
                            if not clean_exercise:
                                continue
                                
                            # Extract description, points, and criteria using regex
                            desc_match = re.search(r'"description"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', clean_exercise)
                            points_match = re.search(r'"points"\s*:\s*"([^"]*)"', clean_exercise)
                            criteria_match = re.search(r'"criteria"\s*:\s*\[(.*?)\]', clean_exercise, re.DOTALL)
                            
                            exercise_obj = {}
                            if desc_match:
                                exercise_obj["description"] = desc_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                            if points_match:
                                exercise_obj["points"] = points_match.group(1)
                            if criteria_match:
                                criteria_content = criteria_match.group(1)
                                # Extract individual criteria strings
                                criteria_items = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', criteria_content)
                                exercise_obj["criteria"] = [item.replace('\\"', '"').replace('\\n', '\n') for item in criteria_items]
                            
                            if exercise_obj:
                                parsed_exercises.append(exercise_obj)
                                logger.info(f"Parsed exercise {i+1}: {exercise_obj.get('description', 'No description')[:50]}...")
                                
                        except Exception as ex_error:
                            logger.warning(f"Failed to parse exercise {i+1}: {ex_error}")
                            continue
                    
                    if parsed_exercises:
                        result = {"exercises": parsed_exercises}
                        logger.info(f"Successfully extracted {len(parsed_exercises)} exercises using regex")
                        return result
                        
            except Exception as regex_error:
                logger.error(f"Regex extraction failed: {regex_error}")
            
            logger.error(f"All JSON fix attempts failed")
            raise ValueError(f"Invalid JSON response from Google AI: {e}")


if __name__ == "__main__":
    pdf_path = "/Users/escuderx/Desktop/PAC1/PAC1_PDP_Enunciat.pdf"
    prompt = CATALAN_EXERCISE_EXTRACTION_PROMPT
    api_key_example = "AIzaSyDDWEU3VnoGadZI5lNiBOrviAoUY4NGyJ8"  # Replace with your actual API key
    generator = GoogleAIService(api_key=api_key_example)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    response = generator.analyse_pdf(pdf_bytes=pdf_bytes, prompt=prompt)
    print(response)
