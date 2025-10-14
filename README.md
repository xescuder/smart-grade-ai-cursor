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
    ↓ POST /api/v1/assignments
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
    ↓ POST /api/v1/assignments/{id}/upload/statement
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
    ↓ POST /api/v1/assignments/{id}/extract-exercises
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
- `GET /api/v1/assignments` - List all
- `POST /api/v1/assignments` - Create new
- `GET /api/v1/assignments/{id}` - Get details
- `PUT /api/v1/assignments/{id}` - Update
- `DELETE /api/v1/assignments/{id}` - Delete

**PDF Management**
- `POST /api/v1/assignments/{id}/upload/statement` - Upload PDF
- `GET /api/v1/assignments/{id}/pdf` - View PDF (from DB)
- `POST /api/v1/assignments/{id}/extract-exercises` - AI extraction

**Exercises**
- `GET /api/v1/assignments/{id}/exercises` - List exercises
- `PUT /api/v1/assignments/{id}/exercises` - Bulk update

**Submissions**
- `POST /api/v1/submissions` - Submit assignment
- `GET /api/v1/submissions` - List submissions
- `POST /api/v1/submissions/{id}/grade` - Grade submission

**Admin**
- `GET /api/v1/admin/section-configs` - PDF extraction rules
- `GET /api/v1/admin/ai-settings` - AI configuration

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

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL (optional, SQLite works for development)
- Redis (optional, for caching)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Environment Variables

Copy `.env.example` to `.env` in the backend directory and configure:

```bash
# Backend/.env
DATABASE_URL=postgresql://user:password@localhost/smartgrade_db
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
SECRET_KEY=your-secret-key
```

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

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

### Assignments
- `GET /api/v1/assignments` - List assignments
- `POST /api/v1/assignments` - Create assignment (teachers)
- `GET /api/v1/assignments/{id}` - Get assignment details

### Submissions
- `POST /api/v1/submissions` - Submit assignment
- `GET /api/v1/submissions` - List submissions
- `POST /api/v1/submissions/upload` - Upload file

### Grading
- `POST /api/v1/grading/grade` - Grade single submission
- `POST /api/v1/grading/batch-grade` - Batch grade submissions
- `GET /api/v1/grading/jobs` - Get grading jobs status

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

