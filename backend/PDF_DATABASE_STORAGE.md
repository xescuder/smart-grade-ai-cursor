# PDF Database Storage Implementation

## Overview

Smart Grade AI now **prioritizes database storage** for PDFs over filesystem storage. This provides better reliability, easier backups, and simplified deployment.

## Updated Functions

### ✅ Both PDF Viewing Endpoints Now Use Database First

#### 1. `/api/v1/assignments/{assignment_id}/pdf`
**Function**: `view_assignment_pdf`

```python
@app.get("/api/v1/assignments/{assignment_id}/pdf")
async def view_assignment_pdf(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """View/download PDF file for assignment (DB bytes preferred)."""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

    # ✅ FIRST: Serve from DB if bytes available
    if getattr(assignment, "pdf_file_data", None):
        return StreamingResponse(
            io.BytesIO(assignment.pdf_file_data),
            media_type=(assignment.pdf_mime_type or "application/pdf"),
            headers={"Content-Disposition": f"inline; filename={assignment.pdf_file_name or 'assignment.pdf'}"},
        )

    # Fallback to filesystem or Google Drive
    ...
```

#### 2. `/api/assignments/{assignment_id}/download/statement`
**Function**: `view_assignment_pdf_inline`

```python
@app.get("/api/assignments/{assignment_id}/download/statement")
async def view_assignment_pdf_inline(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """View PDF file inline for assignment (DB bytes preferred)"""
    assignment = await get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
    
    # ✅ FIRST: Serve from DB if bytes available (preferred method)
    if getattr(assignment, "pdf_file_data", None):
        return StreamingResponse(
            io.BytesIO(assignment.pdf_file_data),
            media_type=(assignment.pdf_mime_type or "application/pdf"),
            headers={"Content-Disposition": "inline"}
        )
    
    # Fallback to filesystem or Google Drive
    ...
```

## Storage Priority Order

Both functions follow this priority order:

1. **🥇 Database Storage** (`pdf_file_data`) - PREFERRED
   - Stored in `assignments.pdf_file_data` (bytea column)
   - Includes `pdf_mime_type` and `pdf_file_name`
   - Fast, reliable, backed up with database

2. **🥈 Filesystem Storage** (`pdf_file_path`)
   - Falls back if no database bytes
   - Looks for file at specified path
   - Searches uploads directory if needed

3. **🥉 Google Drive Reference** (`gdrive:...`)
   - Redirects to Google Drive if path starts with `gdrive:`
   - Useful for shared external files

## Upload Function

PDFs are uploaded using the database-first approach:

```python
@app.post("/api/v1/assignments/{assignment_id}/upload/statement")
async def upload_assignment_pdf(
    assignment_id: int, 
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    content = await file.read()
    
    # ✅ Store directly in database
    updated_assignment = await update_assignment_pdf_bytes(
        db=db,
        assignment_id=assignment_id,
        file_bytes=content,
        file_name=file.filename,
        mime_type="application/pdf",
    )
    
    return {
        "success": True,
        "message": "PDF uploaded successfully",
        "file_name": updated_assignment.pdf_file_name,
        "stored_in": "database",  # ✅ Database storage confirmed
    }
```

## Database Schema

The `assignments` table includes these PDF-related columns:

```sql
-- Legacy filesystem path (now fallback)
pdf_file_path VARCHAR(500),
pdf_file_name VARCHAR(255),

-- ✅ Preferred database storage
pdf_file_data BYTEA,          -- Binary PDF data
pdf_mime_type VARCHAR(100),   -- MIME type (application/pdf)
pdf_file_size INTEGER         -- File size in bytes
```

## Benefits of Database Storage

### ✅ Reliability
- PDFs backed up with regular database backups
- No risk of filesystem/database sync issues
- Atomic operations with transactions

### ✅ Simplicity
- No filesystem permissions to manage
- No file path complications
- Easier container/cloud deployment

### ✅ Performance
- Database caching can be used
- No filesystem I/O overhead
- Faster for small to medium files

### ✅ Portability
- Works in any environment
- No volume mounting needed for Docker
- Easier horizontal scaling

## CRUD Functions

### Upload to Database

```python
from crud import update_assignment_pdf_bytes

updated_assignment = await update_assignment_pdf_bytes(
    db=db,
    assignment_id=assignment_id,
    file_bytes=pdf_content_bytes,
    file_name="assignment.pdf",
    mime_type="application/pdf",
)
```

### Retrieve from Database

```python
from database import get_assignment

assignment = await get_assignment(db, assignment_id)

if assignment.pdf_file_data:
    # PDF is in database
    pdf_bytes = assignment.pdf_file_data
    mime_type = assignment.pdf_mime_type or "application/pdf"
    filename = assignment.pdf_file_name or "document.pdf"
    
    # Serve as streaming response
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type=mime_type,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
```

## Migration Path

### For Existing Filesystem PDFs

If you have existing PDFs in the filesystem, they will still work as fallback. To migrate them to database:

```python
# Example migration script
async def migrate_pdf_to_database(db: AsyncSession, assignment_id: int):
    assignment = await get_assignment(db, assignment_id)
    
    if assignment.pdf_file_path and not assignment.pdf_file_data:
        # Read from filesystem
        file_path = assignment.pdf_file_path.lstrip('/')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Store in database
            await update_assignment_pdf_bytes(
                db=db,
                assignment_id=assignment_id,
                file_bytes=pdf_bytes,
                file_name=assignment.pdf_file_name or "assignment.pdf",
                mime_type="application/pdf"
            )
            
            print(f"✅ Migrated assignment {assignment_id} PDF to database")
```

## Testing

### Test Database Storage

```python
# Upload a PDF
response = requests.post(
    "http://localhost:8000/api/v1/assignments/1/upload/statement",
    files={"file": ("test.pdf", pdf_content, "application/pdf")}
)

# Verify it's in database
response = requests.get("http://localhost:8000/api/v1/assignments/1/pdf")
assert response.status_code == 200
assert response.headers["content-type"] == "application/pdf"
```

### Verify Database Storage

```sql
-- Check if PDF is in database
SELECT 
    id,
    name,
    pdf_file_name,
    pdf_mime_type,
    pdf_file_size,
    CASE 
        WHEN pdf_file_data IS NOT NULL THEN 'DATABASE'
        WHEN pdf_file_path IS NOT NULL THEN 'FILESYSTEM'
        ELSE 'NONE'
    END as storage_location
FROM assignments
WHERE pdf_file_data IS NOT NULL OR pdf_file_path IS NOT NULL;
```

## Endpoints Summary

| Endpoint | Method | Storage Priority | Headers |
|----------|--------|------------------|---------|
| `/api/v1/assignments/{id}/upload/statement` | POST | Database only | - |
| `/api/v1/assignments/{id}/pdf` | GET | Database → Filesystem → GDrive | `inline; filename=...` |
| `/api/assignments/{id}/download/statement` | GET | Database → Filesystem → GDrive | `inline` |

## Configuration

Database storage uses centralized configuration:

```env
# .env file
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/smartgrade_db
MAX_FILE_SIZE=10485760  # 10MB default

# Optional: Configure pool for better performance with large files
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Best Practices

### ✅ DO
- Use database storage for new PDFs
- Set appropriate `MAX_FILE_SIZE` limit
- Monitor database size growth
- Include PDFs in database backups

### ❌ DON'T
- Store extremely large PDFs (>10MB) in database
- Forget to set file size limits
- Skip database backup verification
- Use filesystem without fallback logic

## Performance Considerations

### Database Storage is Best For:
- ✅ Small to medium PDFs (<10MB)
- ✅ High reliability requirements
- ✅ Cloud/container deployments
- ✅ Simplified backup requirements

### Filesystem Storage is Better For:
- ⚠️ Very large PDFs (>50MB)
- ⚠️ Extremely high volume
- ⚠️ CDN integration needed
- ⚠️ Static file serving optimization

## Monitoring

Track PDF storage usage:

```sql
-- Total PDFs in database
SELECT COUNT(*) as pdf_count,
       SUM(pdf_file_size) as total_size_bytes,
       AVG(pdf_file_size) as avg_size_bytes
FROM assignments
WHERE pdf_file_data IS NOT NULL;

-- Largest PDFs
SELECT id, name, pdf_file_name, pdf_file_size
FROM assignments
WHERE pdf_file_data IS NOT NULL
ORDER BY pdf_file_size DESC
LIMIT 10;
```

---

**Implementation Status**: ✅ COMPLETE
**Storage Method**: Database-First with Filesystem Fallback
**Endpoints Updated**: 2
**Date**: October 14, 2025

