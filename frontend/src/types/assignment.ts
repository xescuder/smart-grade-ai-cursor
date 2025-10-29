/**
 * Assignment and Exercise type definitions
 */

export interface Exercise {
  id?: number
  description: string
  evaluation_criteria?: string
  points: number
  order: number
}

export interface Classroom {
  id: number
  name: string
  teacher_name: string
  language: string
}

export interface Assignment {
  id: number
  name: string
  description: string
  due_date: string
  language: string  // Language code: en, es, ca, etc.
  course_id?: number  // Course assignment belongs to (optional for backward compatibility)
  semester_id?: number  // Semester assignment belongs to (optional for backward compatibility)
  exercises: Exercise[]
  pdf_file_path?: string
  pdf_file_name?: string
  created_by: number
  is_active: boolean
  created_at: string
  updated_at?: string
  course?: {
    id: number
    name: string
    code: string
  }
  semester?: {
    id: number
    name: string
    code: string
    year: number
    season: string
  }
}

export interface AssignmentCreate {
  name: string
  description: string
  due_date: string
  language: string
  course_id: number  // Required for new assignments
  semester_id: number  // Required for new assignments
  exercises: Exercise[]
}

export interface AssignmentUpdate {
  name?: string
  description?: string
  due_date?: string
  exercises?: Exercise[]
  is_active?: boolean
}

export interface ApiResponse<T> {
  success?: boolean
  data?: T
  error?: string
  message?: string
}
