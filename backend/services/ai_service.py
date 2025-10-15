"""
AI Service for handling AI-powered operations like PDF exercise extraction
"""
import os
import json
import re
import tempfile
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ai_prompts import CATALAN_EXERCISE_EXTRACTION_PROMPT
from core.config import settings
from services.google_ai_service import GoogleAIService
from repositories.assignment_repository import AssignmentRepository
from logging_config import logger

class AIExtractionService:
    """Service for AI-powered exercise extraction from PDFs"""
    
    def __init__(self):
        self.google_ai_service = None
        if settings.GOOGLE_AI_API_KEY:
            self.google_ai_service = GoogleAIService(api_key=settings.GOOGLE_AI_API_KEY)
            logger.info(f"✅ Google AI Service initialized with model: {settings.GOOGLE_AI_MODEL}")
        else:
            logger.warning("⚠️ Google AI API key not configured")

    async def extract_exercises_from_pdf(self, assignment_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Extract exercises from PDF using Google AI Service with direct PDF analysis

        Args:
            assignment_id: ID of the assignment
            db: Database session
            
        Returns:
            Dictionary with extraction results
        """
        # Create repository instance
        assignment_repo = AssignmentRepository(db)

        # Get assignment and verify PDF exists
        assignment = await assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
        
        # Get PDF bytes from database
        pdf_file_data = getattr(assignment, "pdf_file_data", None)

        # Debug logging
        logger.info(f"AI Extract Debug - Assignment {assignment_id}:")
        logger.info(f"  PDF file data present: {pdf_file_data is not None}")
        logger.info(f"  PDF file data size: {len(pdf_file_data) if pdf_file_data else 0} bytes")
        logger.info(f"  PDF file name: {assignment.pdf_file_name}")
        
        if not pdf_file_data:
            raise ValueError("No PDF file data found for this assignment. PDF must be stored in database.")

        # Check if Google AI is available
        if not self.google_ai_service:
            raise ValueError(
                f"Google AI Service not available. "
                f"Please set GOOGLE_AI_API_KEY in your environment or .env file"
            )
        
        # Create temporary file from database bytes
        temp_path = None
        try:
            # Create temporary file from database bytes
            fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment_id}_")
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(pdf_file_data)
            file_path = temp_path
            logger.info(f"✅ Created temporary PDF file from database bytes: {file_path}")

            logger.info(f"Starting Google AI extraction for assignment {assignment_id}")

            # Use Google AI to extract exercises directly from PDF
            logger.info(f"🤖 Using Google AI Service ({settings.GOOGLE_AI_MODEL}) to extract exercises")

            exercises_data = []
            try:
                # Use Catalan prompt for extraction
                prompt = CATALAN_EXERCISE_EXTRACTION_PROMPT

                # Call Google AI Service with PDF
                parsed_response = self.google_ai_service.analyse_pdf(
                    file_path=file_path,
                    prompt=prompt,
                    model=settings.GOOGLE_AI_MODEL
                )
                
                logger.info(f"Successfully received response from Google AI")
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

                logger.info(f"✅ Google AI extraction successful: {len(exercises_data)} exercises extracted")

            except ValueError:
                # Re-raise ValueError with original message
                raise
            except Exception as e:
                logger.error(f"Google AI extraction error: {e}")
                raise ValueError(f"Google AI extraction failed: {str(e)}")

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
            
            # Use repository to replace exercises
            created_exercises = await assignment_repo.replace_exercises(
                assignment_id=assignment_id,
                exercises_data=exercises_data
            )

            return {
                "success": True,
                "message": f"Successfully extracted {len(created_exercises)} exercises using Google AI",
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
                "extraction_method": "google_ai_direct_pdf",
                "model": settings.GOOGLE_AI_MODEL,
                "num_exercises": len(created_exercises)
            }
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise

        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"🗑️ Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")


# Create a singleton instance
ai_extraction_service = AIExtractionService()
