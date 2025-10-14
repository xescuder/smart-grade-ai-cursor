"""
AI Service for handling AI-powered operations like PDF exercise extraction
"""
import os
import json
import re
import tempfile
import logging
import requests
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import Exercise
from crud import get_assignment
from ai_prompts import get_exercise_extraction_prompt
from core.config import settings

logger = logging.getLogger(__name__)

class AIExtractionService:
    """Service for AI-powered exercise extraction from PDFs"""
    
    def __init__(self):
        self.ollama_available = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(settings.ollama_api_tags_url, timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                logger.info(f"✅ Ollama is running with models: {', '.join(model_names)}")
                logger.info(f"   Using Ollama at: {settings.OLLAMA_BASE_URL}")
                logger.info(f"   Default model: {settings.OLLAMA_MODEL}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Ollama not available at {settings.OLLAMA_BASE_URL}: {e}")
        return False
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        text_lower = text.lower()
        
        # Catalan indicators
        catalan_words = ['és', 'està', 'han', 'per', 'amb', 'del', 'els', 'les', 'una', 'un', 'que', 'de', 'la', 'el', 'en', 'i', 'a', 'exercici', 'exercicis', 'lliurament', 'lliuraments', 'resultat', 'secció', 'apartat']
        catalan_count = sum(1 for word in catalan_words if word in text_lower)
        
        # Spanish indicators  
        spanish_words = ['es', 'está', 'han', 'por', 'con', 'del', 'los', 'las', 'una', 'un', 'que', 'de', 'la', 'el', 'en', 'y', 'a', 'ejercicio', 'ejercicios', 'entrega', 'entregas', 'resultado', 'sección', 'apartado']
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        
        # English indicators
        english_words = ['is', 'are', 'have', 'for', 'with', 'the', 'a', 'an', 'that', 'of', 'in', 'and', 'exercise', 'exercises', 'deliverable', 'deliverables', 'result', 'section', 'part']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        logger.info(f"Language detection counts - Catalan: {catalan_count}, Spanish: {spanish_count}, English: {english_count}")
        
        if catalan_count > spanish_count and catalan_count > english_count:
            return 'catalan'
        elif spanish_count > english_count:
            return 'spanish'
        else:
            return 'english'
    
    
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        doc = fitz.open(file_path)
        pdf_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()
        return pdf_text
    
    async def extract_exercises_from_pdf(self, assignment_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Extract exercises from PDF using AI with language detection
        
        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            Dictionary with extraction results
        """
        # Get assignment and verify PDF exists
        assignment = await get_assignment(db, assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
        
        # Check if PDF exists in either storage method
        pdf_file_data = getattr(assignment, "pdf_file_data", None)
        pdf_file_path = assignment.pdf_file_path
        
        # Debug logging
        logger.info(f"AI Extract Debug - Assignment {assignment_id}:")
        logger.info(f"  PDF file data present: {pdf_file_data is not None}")
        logger.info(f"  PDF file data size: {len(pdf_file_data) if pdf_file_data else 0} bytes")
        logger.info(f"  PDF file path: {pdf_file_path}")
        logger.info(f"  PDF file name: {assignment.pdf_file_name}")
        
        if not pdf_file_data and not pdf_file_path:
            raise ValueError("No PDF file found for this assignment")
        
        # Check if Ollama is available
        if not self.ollama_available:
            raise ValueError(
                f"Ollama not available at {settings.OLLAMA_BASE_URL}. "
                f"Please install and start Ollama: 'brew install ollama && ollama serve' "
                f"then 'ollama pull {settings.OLLAMA_MODEL}'"
            )
        
        # Determine PDF source: prefer DB bytes, else filesystem path
        temp_path = None
        try:
            if pdf_file_data:
                try:
                    # Create temporary file from database bytes
                    fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment_id}_")
                    with os.fdopen(fd, "wb") as tmp:
                        tmp.write(pdf_file_data)
                    file_path = temp_path
                    logger.info(f"Using PDF from database bytes (temp file: {file_path})")
                except Exception as e:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    raise ValueError(f"Failed to prepare PDF bytes for extraction: {str(e)}")
            else:
                # Use filesystem path
                if pdf_file_path.startswith("gdrive:"):
                    raise ValueError("AI extraction from Google Drive reference not supported")
                file_path = pdf_file_path.lstrip('/')
                if not os.path.exists(file_path):
                    raise ValueError("PDF file not found on server")
                logger.info(f"Using PDF from filesystem: {file_path}")
            
            logger.info(f"Starting AI extraction for assignment {assignment_id}, file: {file_path}")
            
            # Extract text from PDF
            logger.info("Extracting text from PDF using direct PyMuPDF...")
            pdf_text = self._extract_text_from_pdf(file_path)
            logger.info(f"PDF text extracted: {len(pdf_text)} characters")
            
            if not pdf_text.strip():
                raise ValueError("Could not extract text from PDF")
            
            # Detect language of the PDF text
            detected_language = self._detect_language(pdf_text)
            logger.info(f"Detected PDF language: {detected_language}")
            
            # Get appropriate system prompt
            logger.info(f"Getting extraction prompt for {detected_language} language")
            system_prompt = get_exercise_extraction_prompt(detected_language)
            
            # Use AI to extract exercises directly from PDF text
            logger.info(f"🤖 Using AI to extract exercises for {detected_language} language")
            
            exercises_data = []
            try:
                user_message = f"Extract exercises from this PDF text:\n\n{pdf_text[:4000]}..."  # Limit text for API
                
                # Use JSON format mode for Catalan to force JSON output
                request_payload = {
                    "model": settings.OLLAMA_MODEL,
                    "prompt": f"{system_prompt}\n\n{user_message}",
                    "stream": False,
                    "temperature": settings.OLLAMA_TEMPERATURE
                }
                
                # Force JSON mode for catalan language
                if detected_language == 'catalan':
                    request_payload["format"] = "json"
                    logger.info("🔧 Using JSON format mode for Catalan language extraction")
                
                response = requests.post(
                    settings.ollama_api_generate_url,
                    json=request_payload,
                    timeout=settings.OLLAMA_TIMEOUT
                )
                
                if response.status_code == 200:
                    ai_response = response.json()["response"].strip()
                    logger.info(f"AI response received: {len(ai_response)} characters")
                    logger.info(f"AI response preview (first 500 chars): {ai_response[:500]}")
                    
                    # Parse JSON response - can be array or object
                    parsed_response = json.loads(ai_response)
                    logger.info(f"Successfully parsed JSON response")
                    logger.info(f"Full JSON parsed: {json.dumps(parsed_response, indent=2, ensure_ascii=False)}")
                    
                    # Handle both array and object responses
                    if isinstance(parsed_response, list):
                        exercises_json = parsed_response
                        logger.info(f"AI returned array with {len(exercises_json)} exercises")
                    elif isinstance(parsed_response, dict):
                        # Check if it's a wrapper object with an exercises array
                        if 'exercises' in parsed_response:
                            exercises_json = parsed_response['exercises']
                            logger.info(f"AI returned object with 'exercises' key containing {len(exercises_json)} exercises")
                        else:
                            # Single exercise as object - wrap it in array
                            exercises_json = [parsed_response]
                            logger.info(f"AI returned single exercise object, wrapped in array")
                    else:
                        raise ValueError(f"AI returned unexpected JSON type: {type(parsed_response)}")
                    
                    if not exercises_json:
                        raise ValueError("AI returned empty exercise list")
                    
                    # Convert to our format
                    for i, ex in enumerate(exercises_json):
                        # Extract description (required)
                        description = ex.get("description", "").strip()
                        if not description:
                            raise ValueError(f"Exercise {i+1}: Missing or empty 'description' field! Full exercise data: {ex}")
                        
                        # Extract points (required) - handle both numeric and string formats
                        raw_points = ex.get("points")
                        logger.info(f"Exercise {i+1}: raw points value = {raw_points} (type: {type(raw_points).__name__ if raw_points is not None else 'None'})")
                        
                        if raw_points is None:
                            raise ValueError(f"Exercise {i+1}: Missing 'points' field! Full exercise data: {ex}")
                        
                        if isinstance(raw_points, str):
                            # Try to extract number from string like "25%", "(25%)", "25", etc.
                            match = re.search(r'(\d+)', raw_points)
                            if match:
                                points_value = int(match.group(1))
                                logger.info(f"Exercise {i+1}: extracted points {points_value} from string '{raw_points}'")
                            else:
                                raise ValueError(f"Exercise {i+1}: Could not extract number from points string: '{raw_points}'")
                        elif isinstance(raw_points, (int, float)):
                            points_value = int(raw_points)
                            logger.info(f"Exercise {i+1}: using numeric points value {points_value}")
                        else:
                            raise ValueError(f"Exercise {i+1}: Invalid points type {type(raw_points)}, value: {raw_points}")
                        
                        # Validate points range
                        if points_value < 0 or points_value > 100:
                            raise ValueError(f"Exercise {i+1}: Points must be between 0 and 100, got: {points_value}")
                        
                        # Extract criteria (required) - handle both array and string formats
                        raw_criteria = ex.get("criteria")
                        if raw_criteria is None:
                            raise ValueError(f"Exercise {i+1}: Missing 'criteria' field! Full exercise data: {ex}")
                        
                        if isinstance(raw_criteria, list):
                            if not raw_criteria:
                                raise ValueError(f"Exercise {i+1}: 'criteria' array is empty")
                            # Join array items with newlines and bullet points
                            criteria_text = "\n".join([f"- {criterion}" for criterion in raw_criteria if criterion])
                            logger.info(f"Exercise {i+1}: converted {len(raw_criteria)} criteria items to text")
                        elif isinstance(raw_criteria, str):
                            criteria_text = raw_criteria.strip()
                            if not criteria_text:
                                raise ValueError(f"Exercise {i+1}: 'criteria' string is empty")
                            logger.info(f"Exercise {i+1}: using criteria as string")
                        else:
                            raise ValueError(f"Exercise {i+1}: Invalid criteria type {type(raw_criteria)}")
                            
                        exercise_data = {
                            "description": description,
                            "points": points_value,
                            "order": i + 1,
                            "evaluation_criteria": criteria_text
                        }
                        exercises_data.append(exercise_data)
                        logger.info(f"Exercise {i+1}: final points = {points_value}, criteria length = {len(criteria_text)} chars")
                        
                    logger.info(f"✅ AI extraction successful: {len(exercises_data)} exercises extracted")
                    
                else:
                    raise ValueError(f"AI API request failed with status {response.status_code}: {response.text[:200]}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"AI response was: {ai_response[:500]}")
                raise ValueError(f"AI did not return valid JSON. Error: {e}")
            except ValueError:
                # Re-raise ValueError with original message
                raise
            except Exception as e:
                logger.error(f"AI extraction error: {e}")
                raise ValueError(f"AI extraction failed: {str(e)}")
            
            logger.info(f"✅ Created {len(exercises_data)} exercises using {detected_language} language detection")
            
            # Log all extracted exercises with their points
            logger.info("=" * 80)
            logger.info("EXTRACTED EXERCISES SUMMARY:")
            logger.info("=" * 80)
            for i, ex_data in enumerate(exercises_data):
                logger.info(f"Exercise {i+1}:")
                logger.info(f"  Points: {ex_data.get('points')} (type: {type(ex_data.get('points')).__name__})")
                logger.info(f"  Description: {ex_data.get('description', '')[:100]}...")
                logger.info(f"  Criteria: {ex_data.get('evaluation_criteria', '')[:80]}...")
            logger.info("=" * 80)
            
            # Database update: Replace existing exercises with AI-extracted ones
            logger.info(f"Replacing {len(assignment.exercises)} existing exercises with {len(exercises_data)} new AI-extracted exercises")
            
            # Delete existing exercises
            for exercise in assignment.exercises:
                await db.delete(exercise)
            await db.commit()
            
            # Create new exercises from AI-extracted data
            created_exercises = []
            for exercise_data in exercises_data:
                new_exercise = Exercise(
                    assignment_id=assignment_id,
                    description=exercise_data["description"],
                    points=exercise_data["points"],
                    order=exercise_data["order"],
                    evaluation_criteria=exercise_data.get("evaluation_criteria", "")
                )
                db.add(new_exercise)
                created_exercises.append(new_exercise)
            
            await db.commit()
            
            # Refresh exercises to get IDs
            for exercise in created_exercises:
                await db.refresh(exercise)
            
            logger.info(f"✅ Successfully created {len(created_exercises)} exercises using AI with {detected_language} language detection")
            
            return {
                "success": True,
                "message": f"Successfully extracted {len(created_exercises)} exercises using AI with {detected_language} language detection",
                "exercises": [
                    {
                        "id": exercise.id,
                        "description": exercise.description,
                        "points": exercise.points,
                        "order": exercise.order,
                        "evaluation_criteria": exercise.evaluation_criteria
                    }
                    for exercise in created_exercises
                ],
                "extraction_method": f"ai_with_language_detection_{detected_language}",
                "detected_language": detected_language,
                "pdf_text_length": len(pdf_text)
            }
            
        finally:
            # Clean up temporary file if created from database bytes
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")


# Create a singleton instance
ai_extraction_service = AIExtractionService()
