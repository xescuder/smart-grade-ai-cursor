# AI PDF Exercise Extraction Setup

## Configuration Overview

Smart Grade AI now uses **centralized configuration management** following twelve-factor app principles. All AI-related settings are managed through the `.env` file.

## Quick Setup

### 1. Copy Environment Template

```bash
cd backend
cp env.example .env
```

### 2. Configure AI Services

Edit the `.env` file with your AI service configuration:

```env
# ============================================================================
# AI SERVICE CONFIGURATION - OLLAMA (Local AI)
# ============================================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120
OLLAMA_TEMPERATURE=0.1

# ============================================================================
# AI SERVICE CONFIGURATION - OPENAI (Optional)
# ============================================================================
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# ============================================================================
# AI SERVICE CONFIGURATION - ANTHROPIC (Optional)
# ============================================================================
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=4000
```

### 3. Choose Your AI Provider

#### Option A: Ollama (Local, Free)

**Install Ollama:**

```bash
# macOS
brew install ollama

# Start Ollama server
ollama serve

# Pull a model
ollama pull llama2
```

**Configure in .env:**

```env
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

#### Option B: OpenAI (Cloud, Paid)

1. Get API key from [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Add to `.env`:

```env
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4
```

#### Option C: Anthropic Claude (Cloud, Paid)

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `.env`:

```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

## Features Enabled

With AI configured, the system provides:

- 🤖 **AI-Powered Exercise Extraction**: Analyze PDF content and extract exercises
- 📋 **Intelligent Parsing**: Identify distinct exercises/problems automatically
- 🎯 **Smart Point Allocation**: Assign appropriate point values (totaling 100)
- 🌐 **Multi-Language Support**: Works with Catalan, Spanish, and English
- 🔄 **Multiple AI Providers**: Choose between Ollama (local), OpenAI, or Anthropic
- ⚠️ **Safe Replacement**: Preview and confirm before replacing existing exercises
- 🔧 **Error Handling**: Graceful fallbacks with user feedback

## Usage

### Exercise Extraction

1. Upload a PDF to an assignment
2. Click the AI (🧠) icon in the assignment row
3. Confirm the extraction (this will replace existing exercises)
4. AI will process the PDF and create new exercises

### Submission Grading (Coming Soon)

1. Submit student work
2. AI evaluates against rubric criteria
3. Generate detailed feedback and scores
4. Review and adjust as needed

## Configuration Details

All AI configuration is now centralized in:

- **Environment File**: `backend/.env`
- **Configuration Module**: `backend/core/config.py`
- **Documentation**: `backend/CONFIGURATION_GUIDE.md`

### Key Configuration Options

```env
# Enable/disable AI features
ENABLE_AI_EXTRACTION=true
ENABLE_AI_GRADING=true

# AI provider selection
DEFAULT_AI_PROVIDER=ollama  # or openai, anthropic

# Model-specific settings
OLLAMA_MODEL=llama2
OLLAMA_TEMPERATURE=0.1
OLLAMA_TIMEOUT=120

# Vision model (for image-based PDFs)
ENABLE_VISION_MODEL=false
VISION_MODEL_NAME=gpt-4-vision-preview
```

## Troubleshooting

### Ollama Not Available

**Error**: `Ollama not available at http://localhost:11434`

**Solutions**:
1. Start Ollama: `ollama serve`
2. Check OLLAMA_BASE_URL in `.env`
3. Verify Ollama is running: `curl http://localhost:11434/api/tags`
4. Pull a model: `ollama pull llama2`

### Model Not Found

**Error**: `Model 'llama2' not found`

**Solutions**:
1. List available models: `ollama list`
2. Pull the model: `ollama pull llama2`
3. Update OLLAMA_MODEL in `.env` to match available model

### OpenAI API Error

**Error**: `OpenAI API key not configured`

**Solutions**:
1. Verify `.env` file exists in `backend/` directory
2. Check `OPENAI_API_KEY` is set correctly
3. Ensure no extra spaces: `OPENAI_API_KEY=sk-...` (not `OPENAI_API_KEY = sk-...`)
4. Restart the backend server

### Configuration Not Loading

**Error**: Settings not reflecting changes

**Solutions**:
1. Restart the backend server
2. Check `.env` file location (must be in `backend/`)
3. Verify file name is exactly `.env` (not `env` or `.env.txt`)
4. Check for syntax errors in `.env` file

## Advanced Configuration

### Custom Ollama Server

If running Ollama on a different machine:

```env
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Multiple Models

Switch models based on task:

```env
# General extraction
OLLAMA_MODEL=llama2

# Complex documents
OLLAMA_MODEL=mixtral
```

### Performance Tuning

```env
# Faster responses, less accurate
OLLAMA_TEMPERATURE=0.3

# Slower responses, more accurate
OLLAMA_TEMPERATURE=0.1

# Longer timeout for complex PDFs
OLLAMA_TIMEOUT=300
```

## See Also

- [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md) - Complete configuration reference
- [README_CONFIGURATION.md](./README_CONFIGURATION.md) - Quick configuration guide
- [env.example](./env.example) - All available configuration options

