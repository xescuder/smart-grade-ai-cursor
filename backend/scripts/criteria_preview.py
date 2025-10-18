import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests

# Allow running as a standalone script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import settings
from database import AsyncSessionLocal
from crud import get_assignment
from ai_prompts import get_exercise_extraction_prompt
from services.google_ai_service import GoogleAIService
import fitz  # PyMuPDF


def _build_ollama_payload(*, model: str, prompt: str, temperature: float, force_json: bool) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": temperature,
    }
    if force_json:
        payload["format"] = "json"
    return payload


def _parse_exercises_from_ai_response(ai_response: str) -> List[Dict[str, Any]]:
    parsed = json.loads(ai_response)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        if "exercises" in parsed and isinstance(parsed["exercises"], list):
            return parsed["exercises"]
        return [parsed]
    raise ValueError(f"Unexpected AI response type: {type(parsed)}")


def _extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    pdf_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pdf_text += page.get_text()
    doc.close()
    return pdf_text


async def _load_pdf_text_from_assignment(assignment_id: int) -> str:
    async with AsyncSessionLocal() as db:
        assignment = await get_assignment(db, assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        pdf_file_data = getattr(assignment, "pdf_file_data", None)
        pdf_file_path = assignment.pdf_file_path

        if not pdf_file_data and not pdf_file_path:
            raise ValueError("Assignment has no PDF associated")

        temp_path: Optional[str] = None
        try:
            if pdf_file_data:
                import tempfile

                fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix=f"assignment_{assignment_id}_")
                with os.fdopen(fd, "wb") as tmp:
                    tmp.write(pdf_file_data)
                file_path = temp_path
            else:
                if pdf_file_path.startswith("gdrive:"):
                    raise ValueError("Google Drive PDFs are not supported by this script")
                file_path = pdf_file_path.lstrip("/")
                if not os.path.exists(file_path):
                    raise ValueError(f"PDF file not found on disk: {file_path}")

            return _extract_text_from_pdf(file_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


def _load_pdf_text_from_path(pdf_path: str) -> str:
    # Use the path as-is if it's absolute, otherwise resolve relative to cwd
    if os.path.isabs(pdf_path):
        clean_path = pdf_path
    else:
        clean_path = os.path.abspath(pdf_path)
    if not os.path.exists(clean_path):
        raise ValueError(f"PDF file not found: {clean_path}")
    return _extract_text_from_pdf(clean_path)


def _detect_language(text: str) -> str:
    text_lower = text.lower()
    catalan_words = ['és', 'està', 'han', 'per', 'amb', 'del', 'els', 'les', 'una', 'un', 'que', 'de', 'la', 'el', 'en', 'i', 'a', 'exercici', 'exercicis', 'lliurament', 'lliuraments', 'resultat', 'secció', 'apartat']
    spanish_words = ['es', 'está', 'han', 'por', 'con', 'del', 'los', 'las', 'una', 'un', 'que', 'de', 'la', 'el', 'en', 'y', 'a', 'ejercicio', 'ejercicios', 'entrega', 'entregas', 'resultado', 'sección', 'apartado']
    english_words = ['is', 'are', 'have', 'for', 'with', 'the', 'a', 'an', 'that', 'of', 'in', 'and', 'exercise', 'exercises', 'deliverable', 'deliverables', 'result', 'section', 'part']
    catalan_count = sum(1 for w in catalan_words if w in text_lower)
    spanish_count = sum(1 for w in spanish_words if w in text_lower)
    english_count = sum(1 for w in english_words if w in text_lower)
    if catalan_count > spanish_count and catalan_count > english_count:
        return 'catalan'
    if spanish_count > english_count:
        return 'spanish'
    return 'english'


def _format_preview(exercises: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for idx, ex in enumerate(exercises, start=1):
        description = (ex.get("description") or "").strip()
        points = ex.get("points")
        criteria = ex.get("criteria")
        lines.append(f"Exercise {idx} ({points}):")
        if description:
            lines.append(f"  Description: {description[:200]}{'…' if len(description) > 200 else ''}")
        if isinstance(criteria, list):
            if criteria:
                lines.append("  Criteria:")
                for c in criteria:
                    if not c:
                        continue
                    lines.append(f"    - {str(c).strip()}")
        elif isinstance(criteria, str):
            crit = criteria.strip()
            if crit:
                lines.append("  Criteria:")
                for line in crit.splitlines():
                    if line.strip():
                        lines.append(f"    - {line.strip('- ').strip()}")
        lines.append("")
    return "\n".join(lines).strip()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview evaluation criteria using Ollama or Google AI without modifying the database"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--assignment-id", type=int, help="Assignment ID to read PDF from the database (Ollama only)")
    group.add_argument("--pdf", type=str, help="Path to a PDF on disk")
    parser.add_argument("--provider", type=str, choices=["ollama", "google"], default="ollama", help="AI provider to use")
    parser.add_argument("--model", type=str, default=getattr(settings, "OLLAMA_MODEL", "llama2"), help="Model to use (Ollama: model name; Google: Gemini model)")
    parser.add_argument("--temperature", type=float, default=float(getattr(settings, "OLLAMA_TEMPERATURE", 0.2)), help="Sampling temperature")
    parser.add_argument("--language", type=str, default=None, help="Force language (catalan|spanish|english)")
    parser.add_argument("--max-chars", type=int, default=4000, help="Max characters to send to AI (Ollama)")
    parser.add_argument("--google-api-key", type=str, default=os.environ.get("GOOGLE_API_KEY", ""), help="Google API key (for provider=google)")
    args = parser.parse_args()

    if args.provider == "google":
        if not args.pdf:
            raise SystemExit("--pdf is required when --provider=google")
        if not args.google_api_key:
            raise SystemExit("Provide --google-api-key or set GOOGLE_API_KEY in env for Google provider")
        pdf_text = _load_pdf_text_from_path(args.pdf)
    else:
        # Ollama path: load from assignment or disk and use text-only extraction
        if args.assignment_id is not None:
            pdf_text = await _load_pdf_text_from_assignment(args.assignment_id)
        else:
            pdf_text = _load_pdf_text_from_path(args.pdf)

    if not pdf_text.strip():
        raise SystemExit("No text extracted from PDF")

    detected_language = args.language or _detect_language(pdf_text)

    system_prompt = get_exercise_extraction_prompt(detected_language)
    user_message = f"Extract exercises from this PDF text:\n\n{pdf_text[: (args.max_chars if args.provider=='ollama' else 200)]}..."
    prompt = f"{system_prompt}\n\n{user_message}"

    exercises: List[Dict[str, Any]]
    if args.provider == "google":
        # Use Google Gemini with PDF as binary input
        google = GoogleAIService(api_key=args.google_api_key)
        # Read bytes here and pass to service
        with open(args.pdf, "rb") as f:
            pdf_bytes = f.read()
        result = google.analyse_pdf(pdf_bytes=pdf_bytes, prompt=prompt, model=args.model)
        # Normalise to a list of exercises
        if isinstance(result, list):
            exercises = result
        elif isinstance(result, dict):
            exercises = result.get("exercises", [result])
        else:
            raise SystemExit(f"Unexpected Google AI response type: {type(result)}")
    else:
        # Ollama flow
        force_json = detected_language == "catalan"
        payload = _build_ollama_payload(
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
            force_json=force_json,
        )
        resp = requests.post(
            getattr(settings, "ollama_api_generate_url", f"{getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate"),
            json=payload,
            timeout=float(getattr(settings, "OLLAMA_TIMEOUT", 60)),
        )
        if resp.status_code != 200:
            raise SystemExit(f"Ollama API error {resp.status_code}: {resp.text[:500]}")
        ai_response = resp.json().get("response", "").strip()
        if not ai_response:
            raise SystemExit("Empty response from Ollama")
        try:
            exercises = _parse_exercises_from_ai_response(ai_response)
        except json.JSONDecodeError as e:
            print("AI response is not valid JSON. Preview first 800 chars:")
            print(ai_response[:800])
            raise SystemExit(f"JSON parse error: {e}")

    print(f"Detected language: {detected_language}")
    print("")
    print(_format_preview(exercises))


if __name__ == "__main__":
    asyncio.run(main())
