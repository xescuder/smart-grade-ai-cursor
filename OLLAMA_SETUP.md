# 🤖 Local AI with Ollama - Setup Guide

## Overview

Your Smart Grade AI system now uses **Ollama** for local AI processing instead of external APIs. This provides:

- ✅ **Complete Privacy**: All processing happens locally
- ✅ **No API Costs**: Free to use
- ✅ **Offline Capable**: Works without internet
- ✅ **Fast Processing**: Local models are often faster
- ✅ **Model Choice**: Use different AI models as needed

## 🚀 Quick Setup

### Step 1: Install Ollama

**macOS (Homebrew):**
```bash
brew install ollama
```

**macOS/Linux/Windows:**
Download from [ollama.ai](https://ollama.ai) and install

### Step 2: Start Ollama Service
```bash
ollama serve
```
*Keep this running in a terminal window*

### Step 3: Install a Model
```bash
# Default model (good balance of speed/quality)
ollama pull llama2

# Or try other models:
ollama pull mistral        # Faster, good for code
ollama pull codellama      # Specialized for code tasks
ollama pull llama2:13b     # Larger, more capable
```

### Step 4: Test the Integration
1. Restart your backend server
2. Upload a PDF to an assignment
3. Click the AI Brain icon (🧠)
4. Try extracting exercises!

## 📋 Recommended Models

### Text-Only Models
| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `llama2` | 3.8GB | Fast | Good | General tasks, quick testing |
| `mistral` | 4.1GB | Fast | Good | Code analysis, technical content |
| `codellama` | 3.8GB | Fast | Excellent | Programming assignments |
| `llama2:13b` | 7.3GB | Slower | Excellent | Complex document analysis |

### Vision Models (Recommended for PDF Evaluation) 🎯
| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **`llava`** ⭐ | 4.7GB | Medium | Excellent | **PDFs with images, diagrams, screenshots** |
| `llava:13b` | 8GB | Slower | Best | Complex visual analysis, detailed feedback |
| `bakllava` | 4.7GB | Medium | Good | Document-focused visual analysis |

**Vision models can analyze:**
- ✅ Diagrams & Flowcharts
- ✅ Screenshots & UI mockups  
- ✅ Mathematical equations
- ✅ Code snippets (even as images)
- ✅ Charts & Graphs
- ✅ Mixed text + visual content

## 🎯 Vision Model Setup (NEW!)

For evaluating PDFs with images, diagrams, and visual content:

### Quick Setup
```bash
# Install vision model (recommended)
ollama pull llava

# Test it
ollama run llava
```

The system will **automatically use the vision model** when:
- ✅ LLaVA model is installed
- ✅ PDF contains visual elements
- ✅ Vision mode is enabled (default: ON)

### How It Works
1. **PDF → Images**: Converts each PDF page to PNG images
2. **Vision Analysis**: LLaVA "sees" the images along with text
3. **Better Evaluation**: Can assess diagrams, screenshots, and visual elements
4. **Automatic Fallback**: If vision fails, uses text-only analysis

### Configuration
Vision evaluation is **enabled by default**. To disable:
```json
// In frontend API call
{
  "assignment_id": 123,
  "use_vision": false  // Disable vision, use text-only
}
```

## 🔧 Configuration Options

Create `/backend/.env` file with these optional settings:

```env
# Ollama Configuration (all optional)
OLLAMA_BASE_URL=http://localhost:11434  # Default
OLLAMA_VISION_MODEL=llava              # Vision model for AI evaluation
OLLAMA_TEXT_MODEL=llama2               # Text-only model

# Database (already configured)
DATABASE_URL=postgresql+asyncpg://smartgrade:@localhost:5432/smartgrade_db
```

### Using Different Models

To use a different model:
```bash
# Install the model
ollama pull mistral

# Set environment variable
export OLLAMA_MODEL=mistral

# Or add to .env file
echo "OLLAMA_MODEL=mistral" >> /backend/.env
```

## 🛠 Troubleshooting

### Common Issues

**1. "Ollama not running" Error**
```bash
# Start Ollama service
ollama serve
```

**2. "No models available" Error**
```bash
# Install a model
ollama pull llama2

# Check installed models
ollama list
```

**3. "Model not found" Error**
```bash
# Check available models
ollama list

# Install the specific model
ollama pull llama2
```

**4. Slow Processing**
- Try a smaller model: `ollama pull mistral`
- Ensure adequate RAM (8GB+ recommended)
- Close other applications

### Performance Tips

**For Better Speed:**
- Use `mistral` or `llama2:7b` models
- Ensure 8GB+ RAM available
- Run on SSD storage

**For Better Quality:**
- Use `llama2:13b` or larger models
- Increase RAM allocation
- Use more specific prompts

## 📊 Model Comparison

### Llama2 (Default)
- **Size**: 3.8GB
- **Performance**: Balanced
- **Best for**: General PDF analysis
- **Install**: `ollama pull llama2`

### Mistral
- **Size**: 4.1GB  
- **Performance**: Fast
- **Best for**: Quick processing
- **Install**: `ollama pull mistral`

### CodeLlama
- **Size**: 3.8GB
- **Performance**: Excellent for code
- **Best for**: Programming assignments
- **Install**: `ollama pull codellama`

## 🔍 Testing the Feature

### Verify Ollama is Working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test a model
ollama run llama2 "Hello, how are you?"
```

### Test with Your App
1. **Start Services**:
   - `ollama serve` (in one terminal)
   - Start your backend server (in another terminal)

2. **Check Backend Logs**:
   - Should see: "✅ Ollama is running with models: llama2"
   - Not: "⚠️ Ollama not running"

3. **Test PDF Extraction**:
   - Upload a PDF with exercises
   - Click the Brain icon (🧠)
   - Should process locally and extract exercises

## 💡 Advanced Usage

### Custom Models
```bash
# Use specialized models for specific tasks
ollama pull deepseek-coder    # For coding assignments
ollama pull zephyr           # For general analysis
ollama pull neural-chat      # For conversational tasks
```

### Model Management
```bash
# List installed models
ollama list

# Remove unused models to save space
ollama rm llama2:13b

# Update models
ollama pull llama2
```

## 🎯 Expected Performance

**Typical Processing Times:**
- Small PDF (1-2 pages): 10-30 seconds
- Medium PDF (3-5 pages): 30-60 seconds  
- Large PDF (6+ pages): 1-3 minutes

**System Requirements:**
- **Minimum**: 8GB RAM, 4GB free disk space
- **Recommended**: 16GB RAM, 10GB free disk space
- **Optimal**: 32GB RAM, SSD storage

## 🔒 Privacy & Security

- ✅ All processing happens locally on your machine
- ✅ No data sent to external servers
- ✅ No API keys or accounts needed
- ✅ Your PDFs never leave your computer
- ✅ Complete offline capability

Your AI-powered assignment analysis is now completely private and local!

## 🚀 Vision Model Benefits

### Why Use Vision Models?

**Traditional text-only evaluation:**
- ❌ Misses diagrams and visual documentation
- ❌ Can't verify UI screenshots  
- ❌ Ignores charts and graphs
- ❌ May miss important visual context

**With vision model (LLaVA):**
- ✅ **Sees** diagrams, flowcharts, UML diagrams
- ✅ **Analyzes** UI mockups and screenshots
- ✅ **Evaluates** code output screenshots
- ✅ **Understands** mathematical notation and equations
- ✅ **Assesses** data visualizations and charts
- ✅ **Complete context** - text + images together

### Real-World Examples

**Software Engineering Assignment:**
- Evaluate UML diagrams for correctness
- Assess UI mockup quality
- Verify application screenshots match requirements
- Check database schema diagrams

**Data Science Project:**
- Analyze charts and graphs
- Evaluate visualization quality
- Assess mathematical formulas in images
- Review code output screenshots

**System Design:**
- Evaluate architecture diagrams
- Assess network topology diagrams
- Review sequence diagrams
- Check component interaction diagrams

### Performance Notes
- **First run**: ~30-60 seconds (PDF→images conversion + AI analysis)
- **Subsequent runs**: Faster due to model caching
- **Page limit**: 10 pages max to ensure reasonable processing time
- **Fallback**: Automatically uses text-only if vision fails

### Quick Test
```bash
# Test vision model with a simple question
ollama run llava "Describe what you see in this image" --image ./path/to/image.png
```

