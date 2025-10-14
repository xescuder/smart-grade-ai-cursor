# Assignment Many-to-Many Classrooms - Implementation Progress

## 🎯 **Goal**

Allow the **same assignment** (in one language) to be **assigned to multiple classrooms** that share the same language. This implements a **many-to-many** relationship between Assignments and Classrooms.

## ✅ **Completed Tasks**

### **1. Database Model Updates** ✅

**Created Association Table:**
```python
# backend/database.py
assignment_classroom_association = Table(
    'assignment_classroom',
    Base.metadata,
    Column('assignment_id', Integer, ForeignKey('assignments.id', ondelete='CASCADE'), primary_key=True),
    Column('classroom_id', Integer, ForeignKey('classrooms.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)
```

**Updated Assignment Model:**
```python
class Assignment(Base):
    __tablename__ = "assignments"
    # Removed: classroom_id column
    # Added many-to-many relationship
    classrooms = relationship("Classroom", secondary=assignment_classroom_association, back_populates="assignments")
```

**Updated Classroom Model:**
```python
class Classroom(Base):
    # Updated relationship
    assignments = relationship("Assignment", secondary=assignment_classroom_association, back_populates="classrooms")
```

**Database Init:**
- Created `assignment_classroom` association table
- Kept old `classroom_id` column for backward compatibility (not dropped yet)

### **2. Backend CRUD Operations** ✅

**Updated Pydantic Models:**
```python
class AssignmentBase(BaseModel):
    name: str
    description: str
    due_date: datetime
    language: str  # No more classroom_id here
    is_active: bool = True

class AssignmentCreate(AssignmentBase):
    classroom_ids: List[int] = []  # NEW: List of classrooms
    exercises: List[ExerciseCreate] = []
```

**Updated `create_assignment`:**
```python
async def create_assignment(db: AsyncSession, assignment: AssignmentCreate, created_by: int) -> Assignment:
    db_assignment = Assignment(
        # ... other fields, NO classroom_id
    )
    
    # Associate with multiple classrooms
    if assignment.classroom_ids:
        for classroom_id in assignment.classroom_ids:
            classroom = await get_classroom(db, classroom_id)
            if classroom:
                db_assignment.classrooms.append(classroom)
    
    # Add exercises...
    await db.commit()
    return db_assignment
```

**Updated `get_assignments`:**
- Added `.options(selectinload(Assignment.classrooms))` to eagerly load classrooms

### **3. Backend API Endpoints** ✅

**Updated `POST /api/v1/assignments`:**
```python
# Validates ALL classroom languages match assignment language
if assignment.classroom_ids:
    for classroom_id in assignment.classroom_ids:
        classroom = await get_classroom(db, classroom_id)
        if not classroom:
            raise HTTPException(status_code=404, detail=f"Classroom {classroom_id} not found")
        
        if assignment.language != classroom.language:
            raise HTTPException(
                status_code=400, 
                detail=f"Assignment language must match all classroom languages"
            )
```

**Updated `GET /api/v1/assignments`:**
```python
# Returns assignments with classrooms array
{
    "id": 1,
    "name": "PAC1",
    "language": "es",
    "classrooms": [
        {"id": 1, "name": "CS101-Morning", "teacher_name": "John", "language": "es"},
        {"id": 2, "name": "CS101-Evening", "teacher_name": "Maria", "language": "es"}
    ],
    "exercises": [...]
}
```

### **4. Frontend TypeScript Types** ✅

**Updated Interfaces:**
```typescript
export interface Classroom {
  id: number
  name: string
  teacher_name: string
  language: string
}

export interface Assignment {
  // ... other fields
  classrooms: Classroom[]  // Many-to-many
  // Removed: classroom_id
}

export interface AssignmentCreate {
  // ... other fields
  classroom_ids: number[]  // List instead of single ID
}
```

### **5. Backend Server Restarted** ✅

- Association table created successfully
- Backend running on port 8002
- Ready to accept requests with new structure

---

## 🚧 **Remaining Tasks**

### **6. Frontend Assignment Create Dialog** ⏳

**Need to Update:**
```typescript
// frontend/src/components/assignment-create-dialog.tsx

// Change from single select to multi-select
const [formData, setFormData] = useState({
  name: '',
  description: '',
  due_date: '',
  classroom_ids: [],  // Array instead of single ID
  language: ''
})

// Use multi-select component (checkboxes or multi-select dropdown)
<Label>Classrooms * (Select one or more with same language)</Label>
{classrooms
  .filter(c => !formData.language || c.language === formData.language)
  .map(classroom => (
    <div key={classroom.id}>
      <input
        type="checkbox"
        checked={formData.classroom_ids.includes(classroom.id)}
        onChange={(e) => handleClassroomToggle(classroom.id)}
      />
      <label>{classroom.name} - {classroom.teacher_name} ({classroom.language})</label>
    </div>
  ))
}

// Update API call
body: JSON.stringify({
  ...formData,
  classroom_ids: formData.classroom_ids,  // Send array
  exercises: []
})
```

### **7. Frontend Assignment List** ⏳

**Need to Display Multiple Classrooms:**
```typescript
// frontend/src/app/assignment-management/page.tsx

// Show all classrooms for each assignment
{assignment.classrooms && assignment.classrooms.length > 0 && (
  <div className="flex flex-wrap gap-1 mt-1">
    {assignment.classrooms.map(classroom => (
      <Badge key={classroom.id} variant="secondary" className="text-xs">
        {classroom.name}
      </Badge>
    ))}
  </div>
)}
```

### **8. Testing** ⏳

**Test Scenarios:**
1. Create assignment with 2 classrooms (same language)
2. Verify assignment appears in both classrooms
3. Try to assign to classrooms with different languages (should fail)
4. Edit assignment to add/remove classrooms
5. Delete assignment → association entries deleted (CASCADE)
6. Delete classroom → assignment remains, association removed

---

## 📊 **Data Model**

### **Before (One-to-Many):**
```
Assignment (classroom_id) → Classroom
```
- One assignment belonged to ONE classroom only
- To use in multiple classrooms, had to duplicate assignment

### **After (Many-to-Many):**
```
Assignment ←→ assignment_classroom ←→ Classroom
```
- One assignment can be used in MULTIPLE classrooms
- One classroom can have MULTIPLE assignments
- Association table tracks which assignments are in which classrooms

---

## 🎯 **Benefits**

1. **No Duplication**: Create assignment once, use in multiple classrooms
2. **Centralized Updates**: Update assignment content once, affects all classrooms
3. **Same Language Enforcement**: All classrooms must have same language as assignment
4. **Flexibility**: Teachers can reuse assignments across sections/groups

---

## 🔄 **Migration Strategy**

### **For Existing Assignments:**

1. **Keep `classroom_id` column temporarily** for backward compatibility
2. **Migration Script** (to run later):
   ```sql
   -- Copy existing assignments to association table
   INSERT INTO assignment_classroom (assignment_id, classroom_id)
   SELECT id, classroom_id 
   FROM assignments 
   WHERE classroom_id IS NOT NULL;
   
   -- Then drop old column
   ALTER TABLE assignments DROP COLUMN classroom_id;
   ```

---

## 📁 **Files Modified**

### **Backend:**
1. ✅ `backend/database.py` - Association table, updated models
2. ✅ `backend/crud.py` - Updated Pydantic models and CRUD operations
3. ✅ `backend/db_server.py` - Updated API endpoints and validation
4. ✅ Backend restarted successfully

### **Frontend:**
5. ✅ `frontend/src/types/assignment.ts` - Updated TypeScript interfaces
6. ⏳ `frontend/src/components/assignment-create-dialog.tsx` - NEEDS UPDATE (multi-select)
7. ⏳ `frontend/src/app/assignment-management/page.tsx` - NEEDS UPDATE (display classrooms)

---

## 🚀 **Next Steps**

1. **Update Assignment Create Dialog:**
   - Replace single select with multi-select (checkboxes)
   - Filter classrooms by language
   - Update form submission to send `classroom_ids` array

2. **Update Assignment List:**
   - Display all classrooms as badges
   - Show classroom count
   - Add filtering by classroom

3. **Test the Implementation:**
   - Create assignment with multiple classrooms
   - Verify associations in database
   - Test edit/delete operations

4. **Data Migration:**
   - Run migration script to convert existing assignments
   - Drop old `classroom_id` column

---

## 🎉 **Status**

**Backend**: ✅ Complete (80%)
**Frontend**: ⏳ In Progress (20%)
**Testing**: ⏳ Pending

**Backend Server**: Running on port 8002
**Database**: Association table created
**API**: Ready to handle multiple classrooms

---

**Implementation Date**: October 13, 2025
**Status**: 🚧 In Progress - Frontend updates needed


