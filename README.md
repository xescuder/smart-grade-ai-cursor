# Smart Grade AI

An AI-powered grading system built with modern web technologies to revolutionize education through automated assignment grading and feedback.

## 🚀 Features

- **AI-Powered Grading**: Advanced AI models provide accurate, consistent grading
- **Custom Rubrics**: Create detailed grading criteria aligned with your objectives
- **Multiple Formats**: Support for PDF, DOCX, and text file submissions
- **Real-time Analytics**: Track student performance and identify learning gaps
- **Responsive Design**: Beautiful, modern UI with sticky navigation
- **Role-based Access**: Separate interfaces for teachers and students
- **Batch Processing**: Grade multiple submissions simultaneously

## 🏗️ Architecture

Smart Grade AI follows a modern **three-tier architecture** with clear separation of concerns, twelve-factor configuration, and database-first design principles.

### 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
│  Teachers, Students, Administrators                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Next.js 14 Frontend (TypeScript + React)            │      │
│  │  • App Router for routing                            │      │
│  │  • shadcn/ui components                              │      │
│  │  • Tailwind CSS styling                              │      │
│  │  • Real-time updates                                 │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  FastAPI Backend (Python + Async)                    │      │
│  │  • RESTful API endpoints                             │      │
│  │  • JWT Authentication                                │      │
│  │  • Business logic services                           │      │
│  │  • AI integration layer                              │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL   │  │  AI Services │  │ File Storage │         │
│  │   Database   │  │  (Ollama/    │  │  (Database-  │         │
│  │  (Primary)   │  │   OpenAI)    │  │   First)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 🎨 Frontend Architecture (Next.js + TypeScript)

#### Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5+ for type safety
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React hooks and server components
- **HTTP Client**: Fetch API with custom wrappers

#### Component Structure
```
frontend/src/
├── app/                           # Next.js App Router
│   ├── layout.tsx                 # Root layout with header
│   ├── page.tsx                   # Landing page
│   ├── assignment-management/     # Assignment CRUD
│   ├── classroom-management/      # Classroom management
│   ├── course-management/         # Course & semester mgmt
│   ├── group-management/          # Student groups
│   ├── submission-management/     # Submission review
│   └── admin/                     # Admin features
│       ├── ai-settings/          # AI configuration
│       └── section-config/       # PDF extraction config
├── components/                    # Reusable components
│   ├── ui/                       # shadcn/ui primitives
│   ├── assignment-*.tsx          # Assignment components
│   ├── exercise-*.tsx            # Exercise components
│   ├── pdf-*.tsx                 # PDF viewers/uploaders
│   └── submission-*.tsx          # Submission components
├── lib/
│   ├── api.ts                    # API client functions
│   └── utils.ts                  # Utility functions
└── types/
    └── assignment.ts             # TypeScript interfaces
```

#### Key Features
- **Master-Detail Interface**: Efficient assignment management
- **PDF Viewer Integration**: Inline PDF viewing with database storage
- **Real-time Updates**: Optimistic UI updates
- **Responsive Design**: Mobile-first approach
- **Type Safety**: Full TypeScript coverage

### ⚙️ Backend Architecture (FastAPI + Python)

#### Technology Stack
- **Framework**: FastAPI (async/await support)
- **Language**: Python 3.8+ with type hints
- **ORM**: SQLAlchemy 2.0 (async)
- **Database Driver**: AsyncPG for PostgreSQL
- **Validation**: Pydantic v2
- **Authentication**: JWT tokens
- **AI Integration**: Ollama (local), OpenAI, Anthropic

#### Backend Structure
```
backend/
├── api/                          # API layer
│   └── routers/                  # Organized endpoints
│       ├── assignments.py        # Assignment CRUD
│       ├── submissions.py        # Submission handling
│       ├── grading.py           # AI grading
│       ├── auth.py              # Authentication
│       └── users.py             # User management
├── core/
│   └── config.py                # Centralized configuration
├── services/
│   └── ai_service.py            # AI integration service
├── models/                      # (Defined in database.py)
├── crud.py                      # Database operations
├── database.py                  # Models & DB config
├── ai_prompts.py               # AI prompt templates
└── db_server.py                # Main application server
```

#### Configuration Management (Twelve-Factor)
All configuration managed through environment variables:

```python
# backend/.env
BACKEND_PORT=8000
FRONTEND_PORT=3000
DATABASE_URL=postgresql+asyncpg://...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
SECRET_KEY=<secure-random-key>
```

**Key Configuration Features**:
- Centralized in `core/config.py`
- Type-safe with Pydantic
- Environment-specific configs
- Automatic CORS configuration
- Computed properties (URLs, etc.)

### 🗄️ Database Architecture

#### PostgreSQL Schema

**Core Entities**:

```sql
-- Courses & Academic Structure
courses (id, code, name, department, credits)
semesters (id, course_id, name, year, season, start_date, end_date)
classrooms (id, course_id, semester_id, name, teacher_name, language)
groups (id, classroom_id, name, members_json)

-- Assignments & Exercises
assignments (id, name, description, due_date, language, created_by)
  ├── pdf_file_data (bytea) ──────→ Database-first PDF storage
  ├── pdf_file_path (varchar) ────→ Filesystem fallback
  └── exercises (one-to-many)

exercises (id, assignment_id, description, points, order, evaluation_criteria)

-- Many-to-Many: Assignments ↔ Classrooms
assignment_classroom (assignment_id, classroom_id, created_at)

-- Submissions & Grading
submissions (id, assignment_id, group_id, course_id, semester_id)
  ├── pdf_file_data (bytea) ──────→ Database-first storage
  ├── total_score, percentage_score
  ├── grade_breakdown (json) ─────→ Per-exercise scores
  ├── teacher_feedback (text)
  └── ai_feedback (text)

-- Configuration
ai_settings (id, key, value) ──────→ Dynamic AI configuration
section_extraction_configs ────────→ PDF parsing rules
```

#### Database Design Principles
- **Database-First Storage**: PDFs stored in PostgreSQL (bytea)
- **Fallback Support**: Filesystem and Google Drive references
- **ACID Compliance**: Transactional consistency
- **Async Operations**: Non-blocking database queries
- **Connection Pooling**: Efficient resource management

### 🤖 AI Integration Architecture

#### Multi-Provider Support

```
┌──────────────────────────────────────────────────────┐
│            AI Service Abstraction Layer              │
│         (services/ai_service.py)                     │
└──────────────────────────────────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
    ┌─────────┐ ┌─────────┐ ┌──────────┐
    │ Ollama  │ │ OpenAI  │ │Anthropic │
    │ (Local) │ │  GPT-4  │ │  Claude  │
    └─────────┘ └─────────┘ └──────────┘
```

#### AI Features

**1. Exercise Extraction from PDFs**
```python
# Multi-language support (Catalan, Spanish, English)
1. PDF Upload → Database Storage
2. Text Extraction (PyMuPDF)
3. Language Detection
4. AI Extraction (Ollama/GPT)
5. JSON Parsing & Validation
6. Exercise Creation in DB
```

**2. Submission Grading** (In Development)
```python
# AI-powered evaluation
1. Retrieve submission PDF
2. Extract text + images
3. Load rubric & criteria
4. AI analysis per exercise
5. Generate scores + feedback
6. Store in grade_breakdown
```

#### AI Configuration
```env
# Ollama (Local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TEMPERATURE=0.1
OLLAMA_TIMEOUT=120

# OpenAI (Cloud)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic (Cloud)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet
```

### 📦 Data Flow Architecture

#### Assignment Creation Flow
```
Teacher (Frontend)
    ↓ POST /api/assignments
Backend API
    ↓ create_assignment()
Database
    ← Assignment Created
Backend
    → 201 Response
Frontend
    → UI Update
```

#### PDF Upload & Storage Flow
```
Upload PDF (Frontend)
    ↓ POST /api/assignments/{id}/upload/statement
Backend
    ↓ Read file bytes
    ↓ Store in assignment.pdf_file_data (Database)
    ↓ Set pdf_file_name, pdf_mime_type
Database
    ← PDF Stored (bytea)
Backend
    → 200 Success
Frontend
    → Show PDF viewer (StreamingResponse from DB)
```

#### AI Exercise Extraction Flow
```
Click AI Extract (Frontend)
    ↓ POST /api/assignments/{id}/extract-exercises
Backend
    ↓ Retrieve PDF from database
    ↓ Extract text (PyMuPDF)
    ↓ Detect language
    ↓ Generate AI prompt
    ↓ Call Ollama/OpenAI
AI Service
    ← JSON response (exercises)
Backend
    ↓ Parse & validate JSON
    ↓ Replace existing exercises
    ↓ Store in database
Database
    ← Exercises Saved
Backend
    → Exercise list
Frontend
    → Update UI with extracted exercises
```

### 🔐 Security Architecture

#### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: Teacher vs Student permissions
- **Token Expiry**: Configurable timeout
- **Secure Secrets**: Environment-based configuration

#### Data Security
- **Input Validation**: Pydantic models
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS Protection**: Configured origins
- **File Upload Limits**: Size and type restrictions
- **Password Hashing**: Secure credential storage (planned)

### 🌐 API Architecture

#### RESTful Endpoints

**Assignments**
- `GET /api/assignments` - List all
- `POST /api/assignments` - Create new
- `GET /api/assignments/{id}` - Get details
- `PUT /api/assignments/{id}` - Update
- `DELETE /api/assignments/{id}` - Delete

**PDF Management**
- `POST /api/assignments/{id}/upload/statement` - Upload PDF
- `GET /api/assignments/{id}/pdf` - View PDF (from DB)
- `POST /api/assignments/{id}/extract-exercises` - AI extraction

**Exercises**
- `GET /api/assignments/{id}/exercises` - List exercises
- `PUT /api/assignments/{id}/exercises` - Bulk update

**Submissions**
- `POST /api/submissions` - Submit assignment
- `GET /api/submissions` - List submissions
- `POST /api/submissions/{id}/grade` - Grade submission

**Admin**
- `GET /api/admin/section-configs` - PDF extraction rules
- `GET /api/admin/ai-settings` - AI configuration

#### Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### 🔄 Deployment Architecture

#### Development
```yaml
Frontend: localhost:3000 (npm run dev)
Backend:  localhost:8000 (python3 db_server.py)
Database: localhost:5432 (PostgreSQL)
AI:       localhost:11434 (Ollama)
```

#### Production (Docker)
```yaml
services:
  frontend:
    image: smart-grade-ai-frontend
    ports: ["3000:3000"]
    env: .env.production
  
  backend:
    image: smart-grade-ai-backend
    ports: ["8000:8000"]
    env: .env.production
    depends_on: [db, ollama]
  
  db:
    image: postgres:15
    volumes: [pgdata:/var/lib/postgresql/data]
  
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
```

### 📈 Performance Optimizations

#### Backend
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Database connection reuse
- **Database Indexing**: Optimized queries
- **Streaming Responses**: Efficient PDF delivery
- **Lazy Loading**: On-demand data fetching

#### Frontend
- **Server Components**: Reduced client-side JavaScript
- **Code Splitting**: Optimized bundle sizes
- **Image Optimization**: Next.js automatic optimization
- **Caching**: API response caching

### 🧩 Key Design Patterns

1. **Repository Pattern**: CRUD operations abstraction
2. **Service Layer**: Business logic separation
3. **Dependency Injection**: FastAPI's DI system
4. **Factory Pattern**: AI service creation
5. **Strategy Pattern**: Multiple AI providers
6. **Observer Pattern**: Real-time updates (planned)

### 📊 Technology Choices & Rationale

| Component | Technology | Why |
|-----------|-----------|-----|
| Frontend Framework | Next.js 14 | SSR, App Router, React Server Components |
| Backend Framework | FastAPI | Async support, auto OpenAPI docs, type safety |
| Database | PostgreSQL | ACID compliance, JSON support, reliability |
| ORM | SQLAlchemy 2.0 | Async support, mature, type-safe |
| AI (Local) | Ollama | Privacy, no API costs, offline support |
| AI (Cloud) | OpenAI/Anthropic | Advanced models, production-grade |
| PDF Storage | Database (bytea) | Simplicity, backups, atomic operations |
| Configuration | Pydantic Settings | Type safety, validation, twelve-factor |
| UI Components | shadcn/ui | Customizable, accessible, modern |

---

**Architecture Status**: Production-Ready ✅  
**Last Updated**: October 14, 2025  
**Documentation**: See `/backend/CONFIGURATION_GUIDE.md`, `/PORT_CONFIGURATION.md`

## 📁 Project Structure

```
smart-grade-ai-cursor/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # Reusable UI components
│   │   │   └── ui/         # shadcn/ui components
│   │   └── lib/            # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── backend/                 # FastAPI backend application
│   ├── api/                # API routes and handlers
│   │   └── routers/        # Organized API endpoints
│   ├── core/               # Core configuration
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   └── requirements.txt    # Python dependencies
└── .cursor/                # Cursor IDE rules and configurations
    └── rules/              # Development guidelines
```

## 🚀 Local Deployment Guide

This guide will walk you through setting up Smart Grade AI on your local machine from scratch.

### 📋 Prerequisites

Before starting, ensure you have the following installed:

| Software | Version | Purpose |
|----------|---------|---------|
| **Node.js** | 18+ | Frontend development |
| **Python** | 3.8+ | Backend API |
| **PostgreSQL** | 15+ | Database |
| **Ollama** (Optional) | Latest | Local AI (free alternative to OpenAI) |
| **Git** | Latest | Clone repository |

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/smart-grade-ai-cursor.git
cd smart-grade-ai-cursor
```

### Step 2: Database Setup (PostgreSQL)

#### Install PostgreSQL

**macOS (Homebrew)**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows**:
Download and install from [postgresql.org](https://www.postgresql.org/download/)

#### Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE smartgrade_db;
CREATE USER smartgrade WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE smartgrade_db TO smartgrade;

# Exit PostgreSQL
\q
```

#### Verify Database Connection

```bash
psql -U smartgrade -d smartgrade_db -h localhost
# If successful, you'll see the PostgreSQL prompt
# Type \q to exit
```

### Step 3: Backend Setup

#### Navigate to Backend Directory

```bash
cd backend
```

#### Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
# Copy the environment template
cp env.example .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Edit `.env` File

Open `backend/.env` and configure:

```env
# ============================================================================
# REQUIRED CONFIGURATION
# ============================================================================

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Database (update with your password)
DATABASE_URL=postgresql+asyncpg://smartgrade:your_password@localhost:5432/smartgrade_db

# Security (paste the generated secret key)
SECRET_KEY=<paste-generated-key-here>

# ============================================================================
# AI CONFIGURATION (Choose one)
# ============================================================================

# Option 1: Ollama (Local, Free) - Recommended for getting started
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
DEFAULT_AI_PROVIDER=ollama

# Option 2: OpenAI (Cloud, Paid)
# OPENAI_API_KEY=sk-your-api-key-here
# DEFAULT_AI_PROVIDER=openai

# Option 3: Anthropic (Cloud, Paid)
# ANTHROPIC_API_KEY=sk-ant-your-api-key-here
# DEFAULT_AI_PROVIDER=anthropic
```

#### Initialize Database

```bash
# Run database initialization (creates tables)
python3 init_db.py

# Or start the server (it will auto-initialize)
python3 db_server.py
```

The server will display:
```
🚀 Starting Smart Grade AI Backend
   Backend:  http://0.0.0.0:8000
   Frontend: http://localhost:3000
   CORS Origins: 2 configured
```

#### Verify Backend is Running

```bash
# In a new terminal
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","database":"postgresql"}
```

### Step 4: Frontend Setup

#### Open New Terminal

```bash
# Navigate to frontend directory (from project root)
cd frontend
```

#### Install Node.js Dependencies

```bash
npm install
```

#### Configure Frontend Environment

```bash
# Copy environment template
cp env.example.txt .env.local
```

#### Edit `.env.local`

```env
# Frontend Configuration
PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

# Features
NEXT_PUBLIC_ENABLE_AI_GRADING=true
NEXT_PUBLIC_ENABLE_PDF_VIEWER=true
```

#### Start Frontend Development Server

```bash
npm run dev
```

The frontend will display:
```
- Local:        http://localhost:3000
- Ready in XXXms
```

### Step 5: AI Service Setup (Optional but Recommended)

#### Option A: Ollama (Local, Free) ⭐ Recommended

**Install Ollama**:

**macOS**:
```bash
brew install ollama
```

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**:
Download from [ollama.com](https://ollama.com)

**Start Ollama Server**:
```bash
# In a new terminal
ollama serve
```

**Pull AI Model**:
```bash
# Download llama2 model (default)
ollama pull llama2

# Or use a Catalan-optimized model
ollama pull jobautomation/openeurollm-catalan:latest
```

**Verify Ollama**:
```bash
curl http://localhost:11434/api/tags

# Should list available models
```

#### Option B: OpenAI (Cloud)

1. Get API key from [platform.openai.com](https://platform.openai.com/api-keys)
2. Add to `backend/.env`:
```env
OPENAI_API_KEY=sk-your-actual-api-key
DEFAULT_AI_PROVIDER=openai
```

#### Option C: Anthropic Claude (Cloud)

1. Get API key from [console.anthropic.com](https://console.anthropic.com/)
2. Add to `backend/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key
DEFAULT_AI_PROVIDER=anthropic
```

### Step 6: Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **📚 API Documentation (Swagger)**: http://localhost:8000/docs
- **📖 Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Step 7: Verify Installation

#### Test Backend API

```bash
# Check health
curl http://localhost:8000/health

# List assignments
curl http://localhost:8000/api/assignments

# Check AI availability (if using Ollama)
curl http://localhost:11434/api/tags
```

#### Test Frontend

1. Open http://localhost:3000
2. Navigate to "Assignment Management"
3. Try creating a test assignment
4. Upload a PDF
5. Click "AI Extract" to test AI integration

### 📁 Complete Directory Structure After Setup

```
smart-grade-ai-cursor/
├── backend/
│   ├── venv/              # Python virtual environment
│   ├── .env               # ✅ Your configuration
│   ├── uploads/           # PDF storage directory
│   └── server.pid         # Running server PID
├── frontend/
│   ├── node_modules/      # Node dependencies
│   ├── .env.local         # ✅ Your frontend config
│   └── .next/             # Build artifacts
└── README.md
```

### 🔧 Common Setup Issues & Solutions

#### Issue: Database Connection Failed

**Error**: `could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
# macOS:
brew services start postgresql@15
# Linux:
sudo systemctl start postgresql
```

#### Issue: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port in backend/.env
BACKEND_PORT=8001
```

#### Issue: Ollama Not Available

**Error**: `Ollama not available at http://localhost:11434`

**Solution**:
```bash
# Start Ollama in separate terminal
ollama serve

# Pull required model
ollama pull llama2

# Verify
curl http://localhost:11434/api/tags
```

#### Issue: Frontend Can't Connect to Backend

**Error**: `Failed to fetch` or CORS errors

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `FRONTEND_PORT` in `backend/.env` matches frontend port
3. Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
4. Restart both servers

#### Issue: npm install Fails

**Error**: Various npm errors

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

#### Issue: Python Dependencies Conflict

**Error**: Package version conflicts

**Solution**:
```bash
# Update pip
pip install --upgrade pip

# Install with specific versions
pip install -r requirements.txt --upgrade

# If still issues, recreate virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🛑 Stopping the Application

#### Stop All Services

```bash
# Stop backend
kill $(cat backend/server.pid)
# Or: pkill -f "python3 db_server.py"

# Stop frontend (Ctrl+C in terminal)
# Or: pkill -f "next-server"

# Stop Ollama (if running)
pkill -f ollama

# Stop PostgreSQL (optional)
# macOS:
brew services stop postgresql@15
# Linux:
sudo systemctl stop postgresql
```

### 🔄 Restarting the Application

```bash
# Backend
cd backend
source venv/bin/activate  # Activate virtual environment
python3 db_server.py

# Frontend (new terminal)
cd frontend
npm run dev

# Ollama (if using - new terminal)
ollama serve
```

### 📊 Quick Start Summary

```bash
# One-time setup
git clone <repository>
cd smart-grade-ai-cursor

# Database
createdb smartgrade_db

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your settings
python3 db_server.py

# Frontend (new terminal)
cd frontend
npm install
cp env.example.txt .env.local
npm run dev

# Ollama (new terminal - optional)
ollama serve
ollama pull llama2

# Access at http://localhost:3000
```

### 📚 Next Steps

After successful installation:

1. **Create Your First Assignment**
   - Navigate to "Assignment Management"
   - Click "Create Assignment"
   - Fill in details and save

2. **Upload PDF & Extract Exercises**
   - Click on your assignment
   - Upload PDF statement
   - Click "AI Extract" to automatically extract exercises

3. **Configure Classrooms**
   - Go to "Course Management"
   - Create courses and semesters
   - Set up classrooms

4. **Test AI Grading**
   - Go to "Submission Management"
   - Submit a test assignment
   - Use AI grading features

5. **Explore Admin Features**
   - AI Settings: Configure AI prompts
   - Section Config: Customize PDF extraction

### 🔗 Additional Resources

- **📚 API Documentation (Swagger)**: http://localhost:8000/docs ⭐
- **📖 API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Configuration Guide**: `/backend/CONFIGURATION_GUIDE.md`
- **Port Configuration**: `/PORT_CONFIGURATION.md`
- **PDF Storage**: `/backend/PDF_DATABASE_STORAGE.md`
- **AI Setup**: `/backend/AI_SETUP.md`

---

**Need Help?** Check the troubleshooting section above or review the documentation files in the `/backend/` directory.

## 🎨 UI Components

The project uses **shadcn/ui** components for a modern, accessible design:

- Sticky header with responsive navigation
- Beautiful landing page with feature showcase
- Role-based navigation (teacher/student views)
- Mobile-friendly responsive design
- Dark mode support (coming soon)

## 🤖 AI Integration

- **OpenAI GPT-4**: Primary grading engine
- **Anthropic Claude**: Alternative AI model
- **Custom Prompts**: Configurable grading criteria
- **Confidence Scoring**: AI provides confidence levels
- **Manual Override**: Teachers can adjust AI grades

## 🔧 Development Guidelines

The project follows established coding standards defined in `.cursor/rules/`:

- **TypeScript Standards**: Strict typing, proper interfaces
- **AI/ML Best Practices**: Error handling, prompt engineering
- **Code Quality**: Testing, documentation, security
- **API Design**: RESTful endpoints, proper status codes

## 📚 API Documentation

### Interactive Swagger UI

**Live API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

The backend provides **auto-generated, interactive API documentation** using OpenAPI (Swagger):

#### Features:
✅ **Try it Out**: Test API endpoints directly from your browser  
✅ **Schema Validation**: See request/response models with examples  
✅ **Authentication**: Test with real JWT tokens  
✅ **Organized by Tags**: Endpoints grouped by functionality  
✅ **Real-time**: Always up-to-date with code changes  

#### Alternative Documentation:
- **ReDoc** (clean, print-friendly): [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Key API Endpoints

#### 🏥 Health & Status
- `GET /health` - System health check
- `GET /api/health` - Detailed service status

#### 📝 Assignments
- `GET /api/assignments` - List all assignments
- `POST /api/assignments` - Create new assignment
- `GET /api/assignments/{id}` - Get assignment details
- `PUT /api/assignments/{id}` - Update assignment
- `DELETE /api/assignments/{id}` - Delete assignment
- `POST /api/assignments/{id}/upload/statement` - Upload PDF
- `POST /api/assignments/{id}/extract-exercises` - AI extraction

#### 📄 Submissions
- `GET /api/submissions` - List submissions
- `POST /api/submissions` - Create submission
- `GET /api/submissions/{id}` - Get submission details
- `POST /api/submissions/{id}/grade` - Grade submission (AI)

#### 🏫 Courses & Classrooms
- `GET /api/courses` - List courses
- `POST /api/courses` - Create course
- `GET /api/classrooms` - List classrooms
- `POST /api/classrooms` - Create classroom
- `GET /api/groups` - List student groups

#### ⚙️ Admin
- `GET /api/admin/ai-settings` - AI configuration
- `PUT /api/admin/ai-settings` - Update AI settings
- `GET /api/admin/section-configs` - PDF extraction configs

### API Response Format

All endpoints follow consistent response patterns:

```json
// Success Response
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}

// Error Response
{
  "detail": "Error description",
  "status_code": 400
}
```

### Authentication

Protected endpoints require JWT token:

```bash
curl -H "Authorization: Bearer <your-token>" \
     http://localhost:8000/api/assignments
```

**See Swagger UI for complete request/response schemas and examples.**

## 🚀 Deployment

### Frontend (Vercel)
```bash
npm run build
# Deploy to Vercel or your preferred platform
```

### Backend (Docker)
```bash
docker build -t smart-grade-ai-backend .
docker run -p 8000:8000 smart-grade-ai-backend
```

## 🤝 Contributing

1. Follow the coding standards in `.cursor/rules/`
2. Write tests for new features
3. Update documentation
4. Follow semantic commit messages

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions and support, please contact the development team or create an issue in the repository.

