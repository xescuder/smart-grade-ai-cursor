"""
AI Prompts for Smart Grade AI System

This module contains all prompts used for AI-powered features:
- Exercise extraction from assignment PDFs
- Submission evaluation and grading
"""

# ============================================================================
# EXERCISE EXTRACTION PROMPTS
# ============================================================================

CATALAN_EXERCISE_EXTRACTION_PROMPT = """Analitza el text del document i retorna NOMÉS un JSON amb l'estructura següent d'exemple:
{
    "exercises": [
        {
            "description": "Descripció de l'exercici",
            "points": "20%",
            "criteria": [
                "Criteri 1",
                "Criteri 2"
            ]
        },
    ]
}

Interpreta els punts de lliurament com els requisits principals o criteris per a cada exercici.
"""


# ============================================================================
# EXERCISE EXTRACTION PROMPT
# ============================================================================

def get_exercise_extraction_prompt(language: str) -> str:
    """
    Get the appropriate exercise extraction prompt based on detected language.

    Args:
        language: Detected language code ('catalan', 'spanish', 'english', etc.)

    Returns:
        The appropriate extraction prompt

    Raises:
        ValueError: If no prompt is defined for the detected language
    """
    if language == 'catalan':
        return CATALAN_EXERCISE_EXTRACTION_PROMPT
    else:
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )


# ============================================================================
# SUBMISSION EVALUATION PROMPTS
# ============================================================================

def get_submission_evaluation_prompt(
    assignment_name: str,
    assignment_description: str,
    exercises_info: list,
    pdf_content: str = "",
    use_vision: bool = False,
    num_pages: int = 0
) -> str:
    """
    Generate the complete evaluation prompt for a student submission.
    
    Args:
        assignment_name: Name of the assignment
        assignment_description: Description of the assignment
        exercises_info: List of dicts with exercise details (id, points, description, evaluation_criteria)
        pdf_content: Text content extracted from the PDF (optional)
        use_vision: Whether vision model is being used
        num_pages: Number of pages in the submission (for vision models)
    
    Returns:
        Complete prompt string for AI evaluation
    """
    
    # Vision-specific note if using vision models
    vision_note = ""
    if use_vision and num_pages > 0:
        vision_note = f"""
IMPORTANT: This submission includes {num_pages} pages with visual content.
- You MUST analyze ALL {num_pages} pages thoroughly
- SKIP front pages, cover pages, index, and table of contents - focus on actual exercise responses
- Examine BOTH text content AND visual elements (diagrams, screenshots, charts, code, tables)
- Evaluate the quality, correctness, and completeness of any visual documentation
- Check if diagrams match the requirements and are technically correct
- Assess UI screenshots, code output, mathematical notation, and data visualizations
- Look for exercise responses scattered across different pages
"""
    
    # Build the main prompt
    prompt = f"""You are an expert academic evaluator analyzing a COMPLETE STUDENT SUBMISSION.

{'=' * 80}
ASSIGNMENT INFORMATION
{'=' * 80}
Assignment: {assignment_name}
Description: {assignment_description}

{'=' * 80}
EXERCISES TO EVALUATE (Total: {len(exercises_info)} exercises)
{'=' * 80}
You must evaluate ALL {len(exercises_info)} exercises listed below.
Each exercise may be answered in different sections/pages of the submission.

"""
    
    # Add each exercise
    for i, exercise in enumerate(exercises_info):
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXERCISE {i + 1} [ID: {exercise['id']}] - Weight: {exercise['points']} points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task Description:
{exercise['description']}

Evaluation Criteria:
{exercise['evaluation_criteria']}

"""
    
    # Add submission context if PDF text is available
    submission_context = ""
    if pdf_content:
        max_text_length = 30000  # First 30K characters
        submission_context = f"""
{'=' * 80}
STUDENT SUBMISSION - TEXT CONTENT (First {max_text_length} characters)
{'=' * 80}
{pdf_content[:max_text_length]}
{"..." if len(pdf_content) > max_text_length else ""}
"""
    
    # Add evaluation instructions
    prompt += f"""{vision_note}
{'=' * 80}
CRITICAL EVALUATION INSTRUCTIONS
{'=' * 80}

YOUR TASK:
1. Read through the ENTIRE submission (ALL pages/images provided)
   - SKIP the front page/cover page/index/table of contents
   - Focus on the actual content pages with exercise responses
2. For EACH of the {len(exercises_info)} exercises listed above:
   - Search for the student's response throughout the submission
   - The response may be in ANY section or page - don't assume order
   - Evaluate WHAT THE STUDENT ACTUALLY SUBMITTED (not the requirements)
   - Consider text, diagrams, code snippets, screenshots, tables, charts
   - Ignore table of contents, front pages, and index pages
3. If an exercise is not addressed, still include it with low score (1-2 points)
4. Be specific - cite actual content, page sections, or visual elements you evaluated
5. Use the same language as the submission for comments

{submission_context}

{'=' * 80}
REQUIRED OUTPUT FORMAT - MUST INCLUDE ALL {len(exercises_info)} EXERCISES
{'=' * 80}

Return a JSON object with this EXACT structure:
{{
    "exercise_grades": [
        {{
            "exercise_id": <exercise_id_from_above>,
            "description": "<exact description from exercise list above>",
            "comments": "<your detailed evaluation comments - what was good, what was missing, what could be improved>",
            "points": <awarded_points_number>
        }},
        ... repeat for ALL {len(exercises_info)} exercises
    ]
}}

CRITICAL REQUIREMENTS:
- You MUST include exactly {len(exercises_info)} exercise evaluations
- Use the exact exercise_id values from the list above
- Points must be between 0 and the maximum for that exercise
- Comments should be detailed and reference specific submission content
- Write comments in the same language as the student submission
- Do NOT include any text before or after the JSON object
- Start your response with {{ and end with }}

Now analyze the submission and return the JSON evaluation:"""
    
    return prompt



