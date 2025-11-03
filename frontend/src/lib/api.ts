import type { Assignment } from "@/types/assignment"
/**
 * API utilities for frontend-backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Export API_BASE_URL for components that need direct fetch access
export { API_BASE_URL }

interface ApiError {
  detail: string
}

export class ApiClient {
  private baseURL: string
  
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
    }
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    // Don't add Content-Type header for FormData - browser sets it with boundary
    const isFormData = options.body instanceof FormData
    const defaultHeaders = isFormData ? {} : this.getHeaders()
    
    // Merge headers properly - options.headers can override or extend defaults
    const headers: Record<string, string> = {
      ...defaultHeaders,
      ...(options.headers as Record<string, string> || {})
    }
    
    const config: RequestInit = {
      ...options,
      headers: Object.keys(headers).length > 0 ? headers : undefined,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        try {
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json()
            // Handle FastAPI validation errors - detail can be a string or array of error objects
            if (errorData.detail) {
              if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail
              } else if (Array.isArray(errorData.detail)) {
                // Pydantic validation errors are arrays of {type, loc, msg, input}
                errorMessage = errorData.detail
                  .map((err: any) => err.msg || JSON.stringify(err))
                  .join(', ')
              } else if (typeof errorData.detail === 'object') {
                errorMessage = JSON.stringify(errorData.detail)
              }
            }
          } else {
            // Try to get text response if not JSON
            const text = await response.text()
            errorMessage = text || response.statusText || `HTTP ${response.status}`
          }
        } catch (parseError) {
          // If response is not valid JSON, use status text
          errorMessage = response.statusText || `HTTP ${response.status}`
        }
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      // Handle network errors (e.g., CORS, connection refused, etc.)
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw new Error('Failed to connect to the server. Please check if the backend is running and CORS is configured correctly.')
      }
      if (error instanceof Error) {
        throw error
      }
      throw new Error('An unexpected error occurred')
    }
  }

  // Assignment API methods
  async getAssignments(): Promise<Assignment[]> {
    return this.request<Assignment[]>('/api/v1/assignments/')
  }

  async getAssignment(id: number): Promise<Assignment> {
    return this.request<Assignment>(`/api/v1/assignments/${id}`)
  }

  async createAssignment(data: Partial<Assignment>) {
    return this.request<Assignment>('/api/v1/assignments/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async updateAssignment(id: number, data: Partial<Assignment>) {
    return this.request<Assignment>(`/api/v1/assignments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteAssignment(id: number) {
    return this.request<void>(`/api/v1/assignments/${id}`, {
      method: 'DELETE'
    })
  }

  // Exercise API methods
  async getAssignmentExercises(assignmentId: number) {
    return this.request(`/api/v1/assignments/${assignmentId}/exercises`)
  }

  async updateAssignmentExercises(assignmentId: number, exercises: unknown[]) {
    return this.request(`/api/v1/assignments/${assignmentId}/exercises`, {
      method: 'PUT',
      body: JSON.stringify(exercises)
    })
  }

  // PDF upload methods
  async uploadAssignmentPDF(assignmentId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request(`/api/v1/assignments/${assignmentId}/upload/statement`, {
      method: 'POST',
      body: formData,
      headers: {} // Remove Content-Type header to let browser set it with boundary
    })
  }

  async getAssignmentPDF(assignmentId: number) {
    return this.request(`/api/v1/assignments/${assignmentId}/pdf`)
  }

  // AI extraction methods
  async extractExercisesAI(assignmentId: number) {
    return this.request(`/api/v1/assignments/${assignmentId}/extract-exercises-ai`, {
      method: 'POST'
    })
  }

  // Classroom API methods
  async getClassrooms() {
    return this.request('/api/v1/classrooms/')
  }

  async getClassroom(id: number) {
    return this.request(`/api/v1/classrooms/${id}`)
  }

  async createClassroom(data: unknown) {
    return this.request('/api/v1/classrooms', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async updateClassroom(id: number, data: unknown) {
    return this.request(`/api/v1/classrooms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteClassroom(id: number) {
    return this.request(`/api/v1/classrooms/${id}`, {
      method: 'DELETE'
    })
  }

  // Course API methods
  async getCourses(): Promise<CourseListItem[]> {
    return this.request<CourseListItem[]>('/api/v1/courses/')
  }

  async getCourse(id: number) {
    return this.request(`/api/v1/courses/${id}`)
  }

  async createCourse(data: unknown) {
    return this.request('/api/v1/courses/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async updateCourse(id: number, data: unknown) {
    return this.request(`/api/v1/courses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteCourse(id: number) {
    return this.request(`/api/v1/courses/${id}`, {
      method: 'DELETE'
    })
  }

  // Semester API methods
  async getSemesters(): Promise<SemesterListItem[]> {
    return this.request<SemesterListItem[]>('/api/v1/semesters/')
  }

  async getSemester(id: number) {
    return this.request(`/api/v1/semesters/${id}`)
  }

  async createSemester(data: unknown) {
    return this.request('/api/v1/semesters', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async updateSemester(id: number, data: unknown) {
    return this.request(`/api/v1/semesters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteSemester(id: number) {
    return this.request(`/api/v1/semesters/${id}`, {
      method: 'DELETE'
    })
  }

  // Group API methods
  async getGroups(params?: { created_by?: number; classroom_id?: number; course_id?: number; semester_id?: number }) {
    const qs = new URLSearchParams()
    if (params?.created_by) qs.append('created_by', String(params.created_by))
    if (params?.classroom_id) qs.append('classroom_id', String(params.classroom_id))
    if (params?.course_id) qs.append('course_id', String(params.course_id))
    if (params?.semester_id) qs.append('semester_id', String(params.semester_id))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return this.request(`/api/v1/groups${suffix}`)
  }

  async createGroup(data: unknown) {
    return this.request('/api/v1/groups', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async updateGroup(id: number, data: unknown) {
    return this.request(`/api/v1/groups/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteGroup(id: number) {
    return this.request(`/api/v1/groups/${id}`, {
      method: 'DELETE'
    })
  }

  // CSV import method
  async importGroupsFromCSV(classroomId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request(`/api/v1/groups/import-csv/${classroomId}`, {
      method: 'POST',
      body: formData,
      headers: {} // Remove Content-Type header to let browser set it with boundary
    })
  }

  // Submission API methods
  async getSubmissions(params?: { assignment_id?: number; classroom_id?: number; group_id?: number }) {
    const qs = new URLSearchParams()
    if (params?.assignment_id) qs.append('assignment_id', String(params.assignment_id))
    if (params?.classroom_id) qs.append('classroom_id', String(params.classroom_id))
    if (params?.group_id) qs.append('group_id', String(params.group_id))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return this.request(`/api/v1/submissions/grading${suffix}`)
  }

  async createSubmission(formData: FormData) {
    return this.request('/api/v1/submissions', {
      method: 'POST',
      body: formData,
      headers: {} // Remove Content-Type header to let browser set it with boundary
    })
  }

  async getSubmissionGradingData(id: number) {
    return this.request(`/api/v1/submissions/${id}/grading`)
  }

  async updateSubmission(id: number, data: unknown) {
    return this.request(`/api/v1/submissions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteSubmission(id: number) {
    return this.request(`/api/v1/submissions/${id}`, {
      method: 'DELETE'
    })
  }

  async gradeSubmission(id: number, data: unknown) {
    return this.request(`/api/v1/submissions/${id}/grade`, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async uploadSubmissionPDF(id: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request(`/api/v1/submissions/${id}/pdf`, {
      method: 'PUT',
      body: formData,
      headers: {} // Remove Content-Type header to let browser set it with boundary
    })
  }

  async getSubmissionPDF(id: number): Promise<string> {
    // Return the URL for the PDF endpoint
    return `${this.baseURL}/api/v1/submissions/${id}/pdf`
  }
}

export const apiClient = new ApiClient()
