# Google AI Extraction Implementation

## Summary

Successfully migrated the `extract_exercises_from_pdf` method to use Google AI Service (Gemini) for direct PDF analysis instead of Ollama.

## Changes Made

### 1. Configuration (`backend/core/config.py`)
- Added `GOOGLE_AI_API_KEY` setting
- Added `GOOGLE_AI_MODEL` setting (default: `gemini-2.0-flash-exp`)

### 2. Environment Variables (`backend/.env`)
- Added `GOOGLE_AI_API_KEY=your_google_ai_api_key_here`
- Added `GOOGLE_AI_MODEL=gemini-2.0-flash-exp`

### 3. AI Service (`backend/services/ai_service.py`)
Completely refactored the `extract_exercises_from_pdf` method to:

#### Step 1: Get PDF from Database
- Checks if PDF exists in `pdf_file_data` (binary data in DB) or `pdf_file_path` (filesystem)
- Prefers database storage for security and portability

#### Step 2: Store PDF in Temporary Directory
- If PDF is in database bytes:
  - Creates a temporary file using `tempfile.mkstemp()`
  - Writes PDF bytes to the temporary file
  - Uses the temp file path for processing
- If PDF is on filesystem:
  - Uses the existing file path directly

#### Step 3: Use Google AI Service
- Calls `google_ai_service.analyse_pdf()` with:
  - File path (temporary or existing)
  - Catalan extraction prompt
  - Configured Gemini model
- Google AI directly processes the PDF without text extraction

#### Step 4: Parse and Display Response
The method now:
- Receives JSON response from Google AI containing exercises
- Handles both array and object response formats
- Extracts `exercises` key if response is wrapped in an object
- Parses each exercise:
  - `description`: Exercise description text
  - `points`: Weight/percentage (handles both string "20%" and numeric 20 formats)
  - `criteria`: Evaluation criteria (handles both array and string formats)
- Validates all required fields
- Converts criteria arrays to formatted text with bullet points
- Creates Exercise records in the database
- Returns structured response with extracted exercises

#### Step 5: Cleanup
- Automatically removes temporary PDF file (if created from DB bytes)
- Ensures cleanup happens even if errors occur (using `finally` block)

### 4. Google AI Service (`backend/services/google_ai_service.py`)
- Cleaned up to remove hardcoded API keys
- Improved documentation
- Model default updated to `gemini-2.0-flash-exp`

## How to Access Response Content

Based on the `GenerateContentResponse` structure you provided, the content is accessed as:

```python
response = client.models.generate_content(...)

# Access the text content
text = response.candidates[0].content.parts[0].text

# The text contains JSON (possibly wrapped in markdown)
# Remove markdown markers and parse
json_str = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
json_data = json.loads(json_str)

# Now json_data contains the exercises
exercises = json_data['exercises']  # if wrapped in object
# or
exercises = json_data  # if it's an array directly
```

## Response Structure Handling

The implementation handles multiple response formats:

1. **Array Format**:
```json
[
  {
    "description": "...",
    "points": "20%",
    "criteria": ["Criteri 1", "Criteri 2"]
  }
]
```

2. **Object Format with exercises key**:
```json
{
  "exercises": [
    {
      "description": "...",
      "points": "20%",
      "criteria": ["Criteri 1", "Criteri 2"]
    }
  ]
}
```

3. **Single Exercise**:
```json
{
  "description": "...",
  "points": "20%",
  "criteria": ["Criteri 1", "Criteri 2"]
}
```

## Benefits

1. **No Text Extraction Required**: Google AI processes PDFs directly
2. **Better Accuracy**: Vision models can see formatting, tables, and structure
3. **Simpler Code**: No need for PyMuPDF or other PDF parsing libraries
4. **Temporary Storage**: Database PDFs are safely written to temp files
5. **Automatic Cleanup**: Temp files are always removed after processing
6. **Robust Error Handling**: Validates all fields and handles multiple formats

## Testing

To test the implementation:

1. Ensure the Google AI API key is set in `.env`
2. Upload a PDF to an assignment
3. Click the "AI Extract" button
4. The system will:
   - Retrieve PDF from database
   - Create temporary file
   - Send to Google AI
   - Parse and display exercises
   - Clean up temporary file

## Model Configuration

The default model is `gemini-2.0-flash-exp` which supports:
- Direct PDF upload
- Fast processing
- Structured JSON output
- Catalan language understanding

You can change the model in `.env`:
```bash
GOOGLE_AI_MODEL=gemini-2.0-flash-exp
# or
GOOGLE_AI_MODEL=gemini-1.5-pro
# or
GOOGLE_AI_MODEL=gemini-1.5-flash
```

