"""
AI Prompts for Smart Grade AI System

This module contains all prompts used for AI-powered features:
- Exercise extraction from assignment PDFs
- Submission evaluation and grading
"""
from typing import List

from database import Exercise
from logging import getLogger

logger = getLogger(__name__)

# ============================================================================
# EXERCISE EXTRACTION PROMPTS
# ============================================================================

CATALAN_EXERCISE_EXTRACTION_PROMPT = """Analitza el text del document i retorna NOMÉS un JSON amb l'estructura següent d'exemple:
{
    "exercises": [
        {
            "description": "Descripció de l'exercici",
            "weight": "20%",
            "criteria": [
                "Criteri 1",
                "Criteri 2"
            ]
        },
    ]
}

Interpreta el pes (weight) com el percentatge que representa cada exercici del total de l'assignatura. Els criteris són els requisits principals per a cada exercici.
"""

CATALAN_SUBMISSION_EXTRACTION_PROMPT = """Evalua el contingut de cada exercici adjunt segons l'enunciat següent i criteris d'avaluació:
%s

Si està ben fet l'exercici, no incloguis comentaris de l'avaluació. Inclou comentaris de l'avaluació només si el contingut avaluat de l'exercici és excepcional, o si bé manquen complir els criteris d'avaluació o la qualitat de l'exercici és dolenta.

Retorna un JSON amb el següent contingut:
{
  exercises: [
        {
            "name": "Nom exercici",
            "points": Puntuació de 0.0 a 10.0 (amb decimals),
            "comments": "Comentaris de l'avaluació de l'exercici"
         }
 ]
}

IMPORTANT: Les puntuacions han de ser entre 0.0 i 10.0 amb decimals (per exemple: 8.5, 7.25, 9.0). No utilitzis l'escala de 0-100.

La llista d'exercicis ha de ser exactament la mateixa que la llista d'exercicis indicada a l'inici.

"""

CATALAN_PUBLIC_REPORT_EXTRACTION_PROMPT = """
Si us plau, analitza l'informe públic del treball dels integrants de l'equip. Revisa que per a cada apartat (1, 2, ...) hi ha una explicació detallada després de la puntuació aportada pel coordinador. Per a cada apart que manqui una explicació descompta 1.5 (sobre 10). No necessito cap anàlisi, retorna únicament un JSON amb el següent contingut:

{
   "points": Puntuació de 0.0 a 10.0 (amb decimals)
   "comments": "Comentaris sobre els apartats no omplerts, i grau de detall"
}

IMPORTANT: Identifica en els comentaris els apartats que no han estat omplerts. Per exemple cal justificar la resposta després de cada valoració.
IMPORTANT: La puntuació ha de ser entre 0.0 i 10.0 amb decimals (per exemple: 8.5, 7.25, 9.0). No utilitzis l'escala de 0-100.
IMPORTANT: Escriu els comentaris EXCLUSIVAMENT en català i manté el format JSON indicat sense afegir cap text addicional fora del JSON.
"""

CATALAN_PRIVATE_REPORT_EXTRACTION_PROMPT = """
Analitza l'informe annex de valoració del(s) coordinador(s) %s del treball dels integrants de l'equip: %s. 

Retorna un JSON amb la següent informació:

{
   "coordinators": [{
         "name": "Nom coordinador",
         "points": Puntuació de 0.0 a 10.0 (amb decimals), segons si ha introduït detall a totes les preguntes i com és el detall
         "commments": "Comentaris de la puntuació"
   }, {
         "name": "Nom coordinador",
         "points": Puntuació de 0.0 a 10.0 (amb decimals), segons si ha introduït detall a totes les preguntes i com és el detall
         "commments": "Comentaris de la puntuació"
   }, ...],
   "members": [
      {
          "name": "Nom integrant",
          "points": Puntuació de 0.0 a 10.0 (amb decimals) atorgada a la nota global,
          "comments":  "Afegir comentaris relacionats amb l'integrant, recollits dels diferents apartats"
      }, {"name":  ...},...
   ]
}

IMPORTANT: Totes les puntuacions han de ser entre 0.0 i 10.0 amb decimals (per exemple: 8.5, 7.25, 9.0). No utilitzis l'escala de 0-100.
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
    
    # Normalize language to lowercase for comparison
    language_lower = language.lower() if language else 'catalan'
    
    if language_lower not in ['catalan', 'ca']:
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )

    # Create exercise descriptions with criteria in a formatted string
    logger.info(f"Found {len(exercises)} exercises for assignment")
    exercise_descriptions = []
    for i, exercise in enumerate(exercises):
        logger.info(f"Exercise {i+1}: {exercise.description[:100]}...")
        logger.info(f"Exercise {i+1} criteria: {exercise.evaluation_criteria[:100] if exercise.evaluation_criteria else 'None'}...")

        desc = exercise.description or ""
        criteria = exercise.evaluation_criteria or ""

        # Use normalized language for comparison
        if language_lower in ['catalan', 'ca']:
            exercise_descriptions.append(
                    f"Exercici {i + 1}:\nEnunciat: {desc}\nCriteris d'avaluació: {criteria}\n"
            )
    
    # Combine all exercise descriptions into a single string
    exercises_text = "\n".join(exercise_descriptions)
    logger.info(f"Exercises text: {exercises_text}")
    prompt = CATALAN_SUBMISSION_EXTRACTION_PROMPT % exercises_text
    return prompt


# ============================================================================
# REPORT EVALUATION PROMPTS
# ============================================================================

def get_public_report_evaluation_prompt(
    language: str,
) -> str:
    if language != 'catalan' and language != 'ca':
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )

    prompt = CATALAN_PUBLIC_REPORT_EXTRACTION_PROMPT
    return prompt


def get_private_report_evaluation_prompt(
    coordinators_names: List[str],
    students_names: List[str],
    language: str,
) -> str:
    if language != 'catalan' and language != 'ca':
        raise ValueError(
            f"No AI extraction prompt defined for language: '{language}'. "
            f"Currently supported languages: catalan. "
            f"Please add a prompt for '{language}' in ai_prompts.py"
        )   

    prompt = CATALAN_PRIVATE_REPORT_EXTRACTION_PROMPT % (", ".join(coordinators_names), ", ".join(students_names))  
    return prompt