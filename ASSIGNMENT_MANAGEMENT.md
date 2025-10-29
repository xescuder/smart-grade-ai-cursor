# Assignment Management System

## 🎯 Overview

A comprehensive CRUD (Create, Read, Update, Delete) system for managing assignments with exercises in a master-detail relationship. Each assignment contains multiple exercises that must total exactly 100 points.

## ✨ Features

### 📝 **Assignment Management**
- **Create**: Add new assignments with multiple exercises
- **Read**: View detailed assignment information and exercises
- **Update**: Edit existing assignments and modify exercises
- **Delete**: Remove assignments with confirmation

### 🧩 **Exercise Management** 
- **Master-Detail Relationship**: Each assignment contains multiple exercises
- **Point Validation**: Exercises must total exactly 100 points
- **Reordering**: Drag and drop exercises to change order
- **Individual Control**: Add, edit, and remove exercises independently

### 🔒 **Security & Validation**
- **Teacher-Only Access**: Only teachers can create, edit, and delete assignments
- **Form Validation**: Comprehensive client and server-side validation
- **Point Constraints**: Automatic validation that total points = 100

## 🗂️ Data Structure

### Assignment Model
```typescript
interface Assignment {
  id: number
  name: string                    // Assignment title
  description: string            // Brief description
  instructions: string           // Detailed instructions for students
  due_date: string              // ISO datetime string
  exercises: Exercise[]          // Array of exercises
  total_points: number          // Always 100
  created_by: number            // Teacher ID
  is_active: boolean            // Assignment status
  created_at: string            // Creation timestamp
  updated_at?: string           // Last update timestamp
}
```

### Exercise Model  
```typescript
interface Exercise {
  id?: number                   // Auto-generated ID
  name: string                  // Exercise title
  description: string           // What students need to do
  points: number               // Points for this exercise (1-100)
  order: number                // Display order
}
```

## 🚀 How to Access

### Navigation
1. **Header Menu**: Click "Teacher Tools" → "Assignment Management"
2. **Direct URL**: `/assignment-management` (teachers only)

### Quick Actions
- **Create**: Click "Create Assignment" button
- **View**: Click the eye icon in the actions column
- **Edit**: Click the edit icon in the actions column  
- **Delete**: Click the trash icon in the actions column

## 📋 Usage Guide

### Creating an Assignment

1. **Click "Create Assignment"**
2. **Fill Basic Information**:
   - Assignment Name (required)
   - Description (required)
   - Instructions (optional but recommended)
   - Due Date (required)

3. **Add Exercises**:
   - Click "Add Exercise" to create new exercises
   - Fill exercise name, description, and points
   - Ensure total points = 100
   - Reorder exercises using up/down arrows

4. **Submit**: Click "Create Assignment" when form is valid

### Editing an Assignment

1. **Click the edit icon** next to an assignment
2. **Modify any fields** as needed
3. **Update exercises**:
   - Edit existing exercises
   - Add new exercises with "Add Exercise"
   - Remove exercises with trash icon
   - Reorder using up/down arrows
4. **Save changes** with "Update Assignment"

### Viewing Assignment Details

1. **Click the eye icon** to view read-only assignment details
2. **See comprehensive information**:
   - Assignment metadata (created date, due date, etc.)
   - All exercises with descriptions and points
   - Total points validation status

## 🔧 API Endpoints

### Backend Routes (`/api/assignments`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|---------|
| `GET` | `/` | List all assignments | Teachers & Students |
| `POST` | `/` | Create new assignment | Teachers Only |
| `GET` | `/{id}` | Get assignment by ID | Teachers & Students |
| `PUT` | `/{id}` | Update assignment | Teachers Only |
| `DELETE` | `/{id}` | Delete assignment | Teachers Only |

### Request/Response Examples

**Create Assignment:**
```json
POST /api/assignments
{
  "name": "Essay on Climate Change",
  "description": "Write a comprehensive essay about climate change",
  "instructions": "Include introduction, body, and conclusion...",
  "due_date": "2024-12-01T23:59:59",
  "exercises": [
    {
      "name": "Introduction",
      "description": "Write compelling introduction with thesis",
      "points": 20,
      "order": 1
    },
    {
      "name": "Body Paragraphs", 
      "description": "Present evidence and analysis",
      "points": 60,
      "order": 2
    },
    {
      "name": "Conclusion",
      "description": "Summarize and call to action", 
      "points": 20,
      "order": 3
    }
  ]
}
```

## ⚡ Frontend Components

### Main Page: `assignment-management/page.tsx`
- Assignment list with actions
- Create/Edit/View dialogs
- Responsive table layout
- Real-time validation feedback

### Form Component: `assignment-form.tsx`
- Dynamic exercise management
- Point total validation
- Drag-and-drop reordering
- Real-time form validation

### Details Component: `assignment-details.tsx`
- Read-only assignment view
- Formatted exercise display
- Metadata information
- Professional layout

## 🎨 UI/UX Features

### 📱 **Responsive Design**
- Mobile-friendly forms and tables
- Adaptive layout for all screen sizes
- Touch-friendly controls

### 🎯 **Intuitive Interface**
- Clear visual hierarchy
- Consistent button placement
- Color-coded validation states
- Loading states and feedback

### ✅ **Real-time Validation**
- Points total indicator (must equal 100)
- Required field validation
- Duplicate name checking
- Form submission state management

### 🎨 **Visual Indicators**
- Green/red badges for point totals
- Status indicators for active/inactive assignments
- Exercise count badges
- Due date formatting with icons

## 🔍 Example Assignments

### Sample 1: Essay Assignment
- **Name**: "Climate Change Essay"
- **Exercises**: Introduction (15pts), Analysis (35pts), Evidence (35pts), Conclusion (15pts)
- **Total**: 100 points

### Sample 2: Math Problem Set  
- **Name**: "Calculus Integration"
- **Exercises**: Basic Integration (20pts), By Parts (30pts), Substitution (30pts), Applications (20pts)
- **Total**: 100 points

## 🚀 Getting Started

1. **Start the backend**: `uvicorn main:app --reload` (port 8000)
2. **Start the frontend**: `npm run dev` (port 3000)
3. **Login as teacher**: Use teacher@example.com
4. **Navigate to Assignment Management**: Header → Teacher Tools → Assignment Management
5. **Create your first assignment** with exercises totaling 100 points!

## 🎉 Success!

You now have a fully functional Assignment Management system with:
- ✅ Complete CRUD operations
- ✅ Master-detail exercise management
- ✅ Point validation (100 total)
- ✅ Professional UI with responsive design
- ✅ Teacher-only security controls
- ✅ Real-time form validation

