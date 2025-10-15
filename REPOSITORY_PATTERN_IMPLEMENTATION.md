# Repository Pattern Implementation

## Summary

Refactored the AI service to use the **Repository Pattern** instead of direct CRUD functions with database sessions. This provides better separation of concerns and cleaner architecture.

## Changes Made

### 1. Created AssignmentRepository (`backend/repositories/assignment_repository.py`)

A dedicated repository class that encapsulates all database operations for assignments:

```python
class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Core CRUD operations
    async def get_by_id(assignment_id: int) -> Optional[Assignment]
    async def get_all() -> List[Assignment]
    async def create(assignment: Assignment) -> Assignment
    async def update(assignment: Assignment) -> Assignment
    async def delete(assignment: Assignment) -> None
    
    # Specialized operations
    async def replace_exercises(assignment_id: int, exercises_data: List[dict]) -> List[Exercise]
    async def get_pdf_data(assignment_id: int) -> tuple[Optional[bytes], Optional[str]]
```

### 2. Updated AIExtractionService

**Before (using direct CRUD):**
```python
from crud import get_assignment
from database import Exercise

assignment = await get_assignment(db, assignment_id)

# Manual exercise deletion
for exercise in assignment.exercises:
    await db.delete(exercise)
await db.commit()

# Manual exercise creation
for exercise_data in exercises_data:
    new_exercise = Exercise(...)
    db.add(new_exercise)
await db.commit()
```

**After (using Repository):**
```python
from repositories.assignment_repository import AssignmentRepository

assignment_repo = AssignmentRepository(db)
assignment = await assignment_repo.get_by_id(assignment_id)

# Single repository method handles everything
created_exercises = await assignment_repo.replace_exercises(
    assignment_id=assignment_id,
    exercises_data=exercises_data
)
```

## Benefits

### 1. **Separation of Concerns**
- Services focus on business logic
- Repositories handle data access
- No direct database operations in services

### 2. **Cleaner Code**
- `assignment_repo.get_by_id(17)` is more readable than `await db.execute(select(Assignment).where(...))`
- No need to import database models in services
- Consistent interface across the application

### 3. **Testability**
- Easy to mock repositories in unit tests
- Can test business logic without database
- Repository tests can focus on data access only

### 4. **Reusability**
- Same repository methods used across different services
- Encapsulates complex queries (with eager loading)
- Single source of truth for database operations

### 5. **Maintainability**
- Database changes only affect repository layer
- Easy to add caching, logging, or validation
- Clear boundaries between layers

## Architecture Layers

```
┌─────────────────────────────────────┐
│   API Layer (FastAPI Routes)       │
│   - Handle HTTP requests            │
│   - Validate input                  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Service Layer (Business Logic)   │
│   - AIExtractionService             │
│   - GoogleAIService                 │
│   - Business rules & orchestration  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Repository Layer (Data Access)   │
│   - AssignmentRepository            │
│   - Encapsulates database queries   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Database Layer (SQLAlchemy ORM)  │
│   - Assignment, Exercise models     │
│   - Database connection             │
└─────────────────────────────────────┘
```

## Example Usage

### In AI Service
```python
async def extract_exercises_from_pdf(self, assignment_id: int, db: AsyncSession):
    # Create repository
    assignment_repo = AssignmentRepository(db)
    
    # Use repository methods
    assignment = await assignment_repo.get_by_id(assignment_id)
    
    # ... AI extraction logic ...
    
    # Replace exercises using repository
    created_exercises = await assignment_repo.replace_exercises(
        assignment_id=assignment_id,
        exercises_data=exercises_data
    )
```

### In API Routes
```python
@router.get("/assignments/{assignment_id}")
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    repo = AssignmentRepository(db)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment
```

## Repository Methods

### `get_by_id(assignment_id: int)`
- Loads assignment with exercises and classrooms (eager loading)
- Returns `Optional[Assignment]`
- No N+1 query problems

### `replace_exercises(assignment_id: int, exercises_data: List[dict])`
- Deletes all existing exercises
- Creates new exercises from data
- Returns list of created Exercise objects
- All in one atomic operation

### `get_pdf_data(assignment_id: int)`
- Returns tuple of (pdf_file_data, pdf_file_path)
- Useful for PDF processing
- One of them will be set if PDF exists

## Migration Notes

If you have other services using `crud.py`, you can gradually migrate them:

1. Keep `crud.py` for backward compatibility
2. Create repositories for each domain entity
3. Update services one by one
4. Eventually deprecate direct CRUD functions

## Best Practices

✅ **Do:**
- Use repositories for all database operations
- Keep business logic in services
- Use type hints for better IDE support
- Handle errors in service layer

❌ **Don't:**
- Import database models in services
- Use `db.execute()` directly in services
- Mix business logic with data access
- Bypass repositories for "quick" queries

The code is now cleaner, more maintainable, and follows solid architectural principles!

