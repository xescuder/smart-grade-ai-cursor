"""
AI Prompts for Smart Grade AI System

This module contains all prompts used for AI-powered features:
- Exercise extraction from assignment PDFs
- Submission evaluation and grading
"""
from typing import List

from database import Exercise

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

CATALAN_SUBMISSION_EXTRACTION_PROMPT = """Evalua el contingut de cada exercici adjunt segons l'enunciat següent i criteris d'avaluació:
%s

Retorna un JSON amb el següent contingut:
{
  exercises: [
        {
            "name": "Nom exercici",
            "points": Evaluation points,
            "comments": "Comentaris de l'avaluació de l'exercici"
         }
 ]
}
"""

CATALAN_PUBLIC_REPORT_EXTRACTION_PROMPT = """
Si us plau, analitza l'informe públic del treball dels integrants de l'equip. Revisa que per a cada apartat (1, 2, ...) hi ha una explicació detallada després de la puntuació aportada pel coordinador. Per a cada apart que manqui una explicació descompta 1.5 (sobre 10). No necessito cap anàlisi, retorna únicament un JSON amb el següent contingut:

{
   "points": 0-10
   "comments": "Comentaris sobre els apartats no omplerts, i grau de detall"
}
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
    if language == 'catalan' or language == 'ca':
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
    exercises: List[Exercise],
    language: str,
) -> str:
    if language != 'catalan':
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )

    # Create exercise descriptions with criteria in a formatted string
    exercise_descriptions = []
    for idx, ex in enumerate(exercises, start=1):
        desc = ex.description or "No description provided."
        criteria = ex.evaluation_criteria or "No criteria provided."
        if language == 'catalan':
            exercise_descriptions.append(
                f"Exercici {idx}:\nEnunciat: {desc}\nCriteris d'avaluació: {criteria}\n"
            )

    # Combine all exercise descriptions into a single string
    exercises_text = "\n".join(exercise_descriptions)
    prompt = CATALAN_SUBMISSION_EXTRACTION_PROMPT % exercises_text
    return prompt


# ============================================================================
# REPORT EVALUATION PROMPTS
# ============================================================================

def get_public_report_evaluation_prompt(
    language: str,
) -> str:
    if language != 'catalan':
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )

    prompt = CATALAN_PUBLIC_REPORT_EXTRACTION_PROMPT
    return prompt
