"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Separator } from "@/components/ui/separator"
import { AlertCircle, Calendar, Download, Edit, Eye, FileText, GraduationCap, Plus, Trash2, Upload, Users, ArrowUpDown, ArrowUp, ArrowDown, Filter, Wand2 } from "lucide-react"
import { toast } from "sonner"
import { SubmissionReviewDialog } from "@/components/submission-review-dialog"
import { StudentPdfUploadDialog } from "@/components/student-pdf-upload-dialog"
import { apiClient } from "@/lib/api"
import { getAuthHeaders, getAuthHeadersForFileUpload } from "@/lib/utils"

interface Course {
  id: number
  name: string
  code: string
  description?: string
  department?: string
  credits?: number
  is_active: boolean
}

interface Semester {
  id: number
  name: string
  code: string
  year: number
  season: string
  start_date: string
  end_date: string
  course_id: number
  is_active: boolean
}

interface Classroom {
  id: number
  name: string
  teacher_name: string
  language: string
  course_id: number
  semester_id: number
  description?: string
  is_active: boolean
}

interface Group {
  id: number
  name: string
  description?: string
  classroom_id: number
  course_id?: number
  semester_id?: number
  course?: Course
  semester?: Semester
  members: any[]
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

interface Assignment {
  id: number
  name: string
  description?: string
  due_date: string
  created_at: string
  updated_at: string
  exercises?: Array<{
    id: number
    name: string
    points: number
    description?: string
    evaluation_criteria?: string
  }>
}

interface Submission {
  id: number
  assignment_id: number
  classroom_id?: number
  group_id?: number
  comments?: string
  pdf_file_path?: string
  pdf_file_name?: string
  coordinators?: string  // JSON string of coordinator names
  private_pdf_filename?: string
  public_pdf_filename?: string
  // PDF presence flags (provided by /grading endpoint)
  has_submission_pdf?: boolean
  has_private_pdf?: boolean
  has_public_pdf?: boolean
  status: string
  total_score?: number
  max_score?: number
  percentage_score?: number
  teacher_feedback?: string
  ai_feedback?: string
  submitted_at: string
  graded_at?: string
  graded_by?: number
  is_late: boolean
  created_at: string
  updated_at: string
  // Relationship data
  assignment?: Assignment
  classroom?: Classroom
  group?: Group
}

interface AssignmentSubmissionsProps {
  assignmentId: number
  assignment?: Assignment
  selectedCourse?: number | null
  selectedSemester?: number | null
  selectedClassroom?: number | null
  hideHeader?: boolean // New prop to hide the header when used in grouped view
}

export function AssignmentSubmissions({ assignmentId, assignment: propAssignment, selectedCourse, selectedSemester, selectedClassroom, hideHeader = false }: AssignmentSubmissionsProps) {
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [assignment, setAssignment] = useState<Assignment | null>(propAssignment || null)
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)
  const [isGradeDialogOpen, setIsGradeDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null)
  const [loading, setLoading] = useState(true)
  
  const [editForm, setEditForm] = useState({
    classroom_id: '',
    group_id: '',
    comments: '',
    status: '',
    coordinators: [] as string[]
  })

  // Form states
  const [newSubmission, setNewSubmission] = useState({
    classroom_id: 'none',
    group_id: 'none',
    comments: '',
    pdf_file: null as File | null,
    private_file: null as File | null,
    public_file: null as File | null,
    coordinators: [] as string[]
  })

  const [generateForm, setGenerateForm] = useState({
    classroom_id: ''
  })

  const [isStudentPdfDialogOpen, setIsStudentPdfDialogOpen] = useState(false)
  const [submissionForStudentPdf, setSubmissionForStudentPdf] = useState<Submission | null>(null)

  // Filter and sort states
  const [sortField, setSortField] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Fetch data on component mount
  useEffect(() => {
    fetchAssignment()
    fetchSubmissions()
    fetchClassrooms()
    fetchGroups()
  }, [assignmentId])

  // Fetch submissions when classroom filter changes
  useEffect(() => {
    fetchSubmissions()
  }, [selectedClassroom])

  // Fetch data when course or semester filters change
  useEffect(() => {
    fetchSubmissions()
    fetchClassrooms()
  }, [selectedCourse, selectedSemester])

  const fetchAssignment = async () => {
    if (propAssignment) {
      setAssignment(propAssignment)
      return
    }

    if (!assignmentId) {
      setAssignment(null)
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignmentId}/`, {
        headers: {
          ...getAuthHeaders(),
        },
      })
      if (response.ok) {
        const data = await response.json()
        setAssignment(data)
      } else {
        console.error('Error response from API:', response.status)
        toast.error('Failed to fetch assignment')
      }
    } catch (error) {
      console.error('Error fetching assignment:', error)
      toast.error('Failed to fetch assignment')
    }
  }

  const fetchSubmissions = async () => {
    try {
      setLoading(true)
      
      console.log('Fetching submissions with:', { assignmentId, selectedClassroom, selectedCourse, selectedSemester })
      
      // If no specific assignment is selected (assignmentId is 0), fetch all submissions
      const submissions = await apiClient.getSubmissions({ 
        assignment_id: assignmentId && assignmentId > 0 ? assignmentId : undefined,
        classroom_id: selectedClassroom || undefined 
      })
      
      console.log('Raw submissions from API:', submissions)
      
      // Filter submissions by course and semester if specified
      let filteredSubmissions = Array.isArray(submissions) ? submissions : []
      
      if (selectedCourse || selectedSemester) {
        filteredSubmissions = filteredSubmissions.filter(submission => {
          const classroom = submission.classroom
          if (!classroom) return false
          
          // Filter by course if specified
          if (selectedCourse && classroom.course_id !== selectedCourse) {
            return false
          }
          
          // Filter by semester if specified
          if (selectedSemester && classroom.semester_id !== selectedSemester) {
            return false
          }
          
          return true
        })
      }
      
      console.log('Filtered submissions:', filteredSubmissions)
      setSubmissions(filteredSubmissions)
    } catch (error) {
      console.error('Error fetching submissions:', error)
      toast.error('Failed to fetch submissions')
      setSubmissions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchClassrooms = async () => {
    try {
      const data = await apiClient.getClassrooms()
      let classrooms = Array.isArray(data) ? data : []
      
      // Filter classrooms by course and semester if specified
      if (selectedCourse || selectedSemester) {
        classrooms = classrooms.filter(classroom => {
          // Filter by course if specified
          if (selectedCourse && classroom.course_id !== selectedCourse) {
            return false
          }
          
          // Filter by semester if specified
          if (selectedSemester && classroom.semester_id !== selectedSemester) {
            return false
          }
          
          return true
        })
      }
      
      setClassrooms(classrooms)
    } catch (error) {
      console.error('Error fetching classrooms:', error)
      toast.error('Failed to fetch classrooms')
      setClassrooms([])
    }
  }

  const fetchGroups = async () => {
    try {
      const data = await apiClient.getGroups({ created_by: 1 })
      setGroups(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching groups:', error)
      toast.error('Failed to fetch groups')
      setGroups([])
    }
  }

  const handleCreateSubmission = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newSubmission.classroom_id || newSubmission.classroom_id === 'none') {
      toast.error('Please select a classroom')
      return
    }

    try {
      const formData = new FormData()
      formData.append('assignment_id', assignmentId.toString())
      formData.append('classroom_id', newSubmission.classroom_id)
      if (newSubmission.group_id && newSubmission.group_id !== 'none') {
        formData.append('group_id', newSubmission.group_id)
      }
      if (newSubmission.comments) {
        formData.append('comments', newSubmission.comments)
      }
      // Upload main submission PDF
      if (newSubmission.pdf_file) {
        formData.append('files', newSubmission.pdf_file)
      }

      const newSubmissionResponse = await apiClient.createSubmission(formData)
      const createdSubmissionId = newSubmissionResponse.id

      // Upload private report if provided
      if (newSubmission.private_file && createdSubmissionId) {
        const privateFormData = new FormData()
        privateFormData.append('pdf_file', newSubmission.private_file)
        privateFormData.append('coordinators', JSON.stringify(newSubmission.coordinators))
        
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${createdSubmissionId}/private-pdf`, {
          method: 'PUT',
          body: privateFormData,
        })
      }

      // Upload public report if provided
      if (newSubmission.public_file && createdSubmissionId) {
        const publicFormData = new FormData()
        publicFormData.append('pdf_file', newSubmission.public_file)
        publicFormData.append('coordinators', '')
        
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${createdSubmissionId}/public-pdf`, {
          method: 'PUT',
          body: publicFormData,
        })
      }

      toast.success('Submission created successfully')
      setIsCreateDialogOpen(false)
      fetchSubmissions()
      // Reset form
      setNewSubmission({
        classroom_id: 'none',
        group_id: 'none',
        comments: '',
        pdf_file: null,
        private_file: null,
        public_file: null,
        coordinators: []
      })
    } catch (error) {
      console.error('Error creating submission:', error)
      toast.error(`Failed to create submission: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  const handleGenerateSubmissions = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!generateForm.classroom_id) {
      toast.error('Please select a classroom')
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/generate-expected`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          assignment_id: assignmentId,
          classroom_id: parseInt(generateForm.classroom_id)
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate submissions')
      }

      const result = await response.json()
      toast.success(`Generated ${result.count} expected submissions successfully`)
      setIsGenerateDialogOpen(false)
      fetchSubmissions()
      
      // Reset form
      setGenerateForm({
        classroom_id: ''
      })
    } catch (error) {
      console.error('Error generating submissions:', error)
      toast.error(`Failed to generate submissions: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  const handleSubmissionUpdate = (updatedSubmission: any) => {
    setSelectedSubmission(updatedSubmission)
    // Also update the submission in the submissions list
    setSubmissions(prev => 
      prev.map(sub => sub.id === updatedSubmission.id ? updatedSubmission : sub)
    )
  }

  const handleGradeSubmission = async (grades: any[], totalScore: number) => {
    if (!selectedSubmission) {
      toast.error('No submission selected')
      return
    }

    try {
      const response = await fetch(`/api/v1/submissions/${selectedSubmission.id}/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          total_score: totalScore,
          teacher_feedback: 'Graded via review dialog',
          graded_by: 'teacher@example.com',
          grade_breakdown: grades.map(grade => ({
            exercise_id: grade.exercise_id,
            points: grade.points,
            comments: grade.comments || ''
          }))
        })
      })

      if (response.ok) {
        toast.success('Submission graded successfully')
        
        // Update the selected submission with the new grade data instead of refetching all submissions
        const updatedSubmission = {
          ...selectedSubmission,
          total_score: totalScore,
          grade_breakdown: grades,
          graded_at: new Date().toISOString(),
          teacher_feedback: 'Graded via review dialog'
        }
        
        setSelectedSubmission(updatedSubmission)
        
        // Update the submission in the submissions list
        setSubmissions(prev => 
          prev.map(sub => sub.id === selectedSubmission.id ? updatedSubmission : sub)
        )
        
        // Don't call fetchSubmissions() here to prevent dialog flickering
        // The data will be refreshed when the dialog is closed or when navigating away
      } else {
        toast.error('Failed to grade submission')
      }
    } catch (error) {
      console.error('Error grading submission:', error)
      toast.error('Error grading submission')
    }
  }

  const handleDeleteSubmission = async (submissionId: number) => {
    if (!confirm('Are you sure you want to delete this submission?')) return

    try {
      const response = await fetch(`/api/v1/submissions/${submissionId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Submission deleted successfully')
        fetchSubmissions()
      } else {
        toast.error('Failed to delete submission')
      }
    } catch (error) {
      console.error('Error deleting submission:', error)
      toast.error('Failed to delete submission')
    }
  }

  const handleEditSubmission = (submission: Submission) => {
    setSelectedSubmission(submission)
    
    // Parse coordinators from JSON string or array
    let coordinators: string[] = []
    if (submission.coordinators) {
      try {
        coordinators = typeof submission.coordinators === 'string' 
          ? JSON.parse(submission.coordinators) 
          : submission.coordinators
      } catch {
        coordinators = []
      }
    }
    
    setEditForm({
      classroom_id: submission.classroom_id?.toString() || '',
      group_id: submission.group_id?.toString() || '',
      comments: submission.comments || '',
      status: submission.status || 'submitted',
      coordinators
    })
    setIsEditDialogOpen(true)
  }

  const handleSaveSubmission = async () => {
    if (!selectedSubmission) return

    try {
      // Update submission basic fields
      const updatedData = {
        classroom_id: parseInt(editForm.classroom_id) || undefined,
        group_id: parseInt(editForm.group_id) || undefined,
        comments: editForm.comments,
        status: editForm.status
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${selectedSubmission.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(updatedData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update submission')
      }

      // Update coordinators if there's a private PDF
      if (selectedSubmission.has_private_pdf && editForm.coordinators.length > 0) {
        const coordinatorFormData = new FormData()
        coordinatorFormData.append('coordinators', JSON.stringify(editForm.coordinators))
        
        const coordResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${selectedSubmission.id}/private-pdf`, {
          method: 'PUT',
          body: coordinatorFormData,
        })
        
        if (!coordResponse.ok) {
          console.warn('Failed to update coordinators for private PDF')
        }
      }

      toast.success('Submission updated successfully')
      setIsEditDialogOpen(false)
      fetchSubmissions()
    } catch (error) {
      console.error('Error updating submission:', error)
      toast.error(`Failed to update submission: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  const openStudentPdfDialog = (submission: Submission) => {
    setSubmissionForStudentPdf(submission)
    setIsStudentPdfDialogOpen(true)
  }

  const closeStudentPdfDialog = () => {
    setIsStudentPdfDialogOpen(false)
    setSubmissionForStudentPdf(null)
  }

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: "default" | "secondary" | "destructive" | "outline" } = {
      'submitted': 'default',
      'graded': 'secondary',
      'returned': 'outline',
      'late': 'destructive',
      'draft': 'outline'
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Filter and sort functions
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (field: string) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" />
    }
    return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
  }

  const filteredAndSortedSubmissions = () => {
    let filtered = submissions

    // Apply classroom filter if selectedClassroom is provided
    if (selectedClassroom) {
      filtered = filtered.filter(submission => submission.classroom_id === selectedClassroom)
    }

    // Sort by classroom name, then by group name
    return [...filtered].sort((a, b) => {
      const classroomA = a.classroom?.name || ''
      const classroomB = b.classroom?.name || ''
      const cmpClassroom = classroomA.localeCompare(classroomB)
      if (cmpClassroom !== 0) return cmpClassroom

      const groupA = a.group?.name || ''
      const groupB = b.group?.name || ''
      return groupA.localeCompare(groupB)
    })
  }

  const handleExportExcel = async () => {
    if (!assignmentId) {
      toast.error('Please select an assignment to export')
      return
    }
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignmentId}/export-excel`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${assignment?.name || 'assignment'}_grades.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success('Excel file downloaded successfully')
      } else {
        toast.error('Failed to export Excel file')
      }
    } catch (error) {
      console.error('Error exporting Excel:', error)
      toast.error('Failed to export Excel file')
    }
  }

  const handleExportClassroomGrades = async () => {
    if (!assignmentId) {
      toast.error('Please select an assignment to export')
      return
    }
    
    if (!selectedClassroom) {
      toast.error('Please select a classroom to export grades')
      return
    }
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/classroom/${selectedClassroom}/assignment/${assignmentId}/grades.xlsx`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${assignment?.name || 'assignment'}_classroom_grades.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success('Classroom grades Excel file downloaded successfully')
      } else {
        toast.error('Failed to export classroom grades Excel file')
      }
    } catch (error) {
      console.error('Error exporting classroom grades Excel:', error)
      toast.error('Failed to export classroom grades Excel file')
    }
  }

  const handleExportCsv = async () => {
    if (!assignmentId) {
      toast.error('Please select an assignment to export')
      return
    }
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignmentId}/export-csv`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${assignment?.name || 'assignment'}_group_grades.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success('CSV file downloaded successfully')
      } else {
        toast.error('Failed to export CSV file')
      }
    } catch (error) {
      console.error('Error exporting CSV:', error)
      toast.error('Failed to export CSV file')
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="text-center py-8">Loading submissions...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header - only show if not hidden */}
      {!hideHeader && (
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold">
              {assignment ? assignment.name : "All Submissions"}
            </h2>
            <p className="text-muted-foreground">
              {assignment ? "Manage submissions for this assignment" : "Manage all submissions"}
            </p>
            {assignment?.description && (
              <p className="text-sm text-muted-foreground">{assignment.description}</p>
            )}
            {assignment && (
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  Due: {formatDate(assignment?.due_date)}
                </div>
                <div className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  {assignment?.exercises?.length || 0} exercises
                </div>
              </div>
            )}
          </div>
          {assignment && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleExportExcel}>
                <Download className="mr-2 h-4 w-4" />
                Excel
              </Button>
              <Button variant="outline" size="sm" onClick={handleExportCsv}>
                <Download className="mr-2 h-4 w-4" />
                CSV
              </Button>
              {selectedClassroom && (
                <Button variant="default" size="sm" onClick={handleExportClassroomGrades}>
                  <Download className="mr-2 h-4 w-4" />
                  Classroom Grades
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create Submission Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Submission</DialogTitle>
            <DialogDescription>
              Create a submission for {assignment?.name || 'this assignment'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmission} className="space-y-4">
            <div>
              <Label htmlFor="classroom">Classroom *</Label>
              <Select value={newSubmission.classroom_id} onValueChange={(value) => setNewSubmission(prev => ({ ...prev, classroom_id: value, group_id: 'none' }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select classroom" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No classroom</SelectItem>
                  {classrooms.map(classroom => (
                    <SelectItem key={classroom.id} value={classroom.id.toString()}>
                      {classroom.name} ({classroom.teacher_name})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="group">Group</Label>
              <Select value={newSubmission.group_id} onValueChange={(value) => setNewSubmission(prev => ({ ...prev, group_id: value }))} disabled={newSubmission.classroom_id === 'none'}>
                <SelectTrigger>
                  <SelectValue placeholder="Select group" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No group</SelectItem>
                  {groups.filter(g => newSubmission.classroom_id === 'none' || g.classroom_id === parseInt(newSubmission.classroom_id)).map(group => (
                    <SelectItem key={group.id} value={group.id.toString()}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {newSubmission.group_id !== 'none' && (() => {
              const selectedGroup = groups.find(g => g.id === parseInt(newSubmission.group_id))
              const members = selectedGroup?.members || []
              return (
                <div>
                  <Label>Coordinators (for private reports)</Label>
                  <div className="space-y-2 border rounded p-3 max-h-48 overflow-y-auto">
                    {members.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No members in this group</p>
                    ) : (
                      members.map((member: any) => {
                        const memberName = typeof member === 'string' ? member : (member.name || member.email || 'Unknown')
                        return (
                          <div key={memberName} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={`coord-${memberName}`}
                              checked={newSubmission.coordinators.includes(memberName)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setNewSubmission(prev => ({
                                    ...prev,
                                    coordinators: [...prev.coordinators, memberName]
                                  }))
                                } else {
                                  setNewSubmission(prev => ({
                                    ...prev,
                                    coordinators: prev.coordinators.filter(c => c !== memberName)
                                  }))
                                }
                              }}
                              className="h-4 w-4"
                            />
                            <label htmlFor={`coord-${memberName}`} className="text-sm">
                              {memberName}
                            </label>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              )
            })()}

            <div>
              <Label htmlFor="pdf_file">Submission PDF *</Label>
              <Input
                id="pdf_file"
                type="file"
                accept=".pdf"
                onChange={(e) => setNewSubmission(prev => ({ ...prev, pdf_file: e.target.files?.[0] || null }))}
              />
              <p className="text-xs text-muted-foreground mt-1">Main submission document</p>
            </div>

            <div>
              <Label htmlFor="private_file">Private Report (Optional)</Label>
              <Input
                id="private_file"
                type="file"
                accept=".pdf"
                onChange={(e) => setNewSubmission(prev => ({ ...prev, private_file: e.target.files?.[0] || null }))}
              />
              <p className="text-xs text-muted-foreground mt-1">Private report for grading</p>
            </div>

            <div>
              <Label htmlFor="public_file">Public Report (Optional)</Label>
              <Input
                id="public_file"
                type="file"
                accept=".pdf"
                onChange={(e) => setNewSubmission(prev => ({ ...prev, public_file: e.target.files?.[0] || null }))}
              />
              <p className="text-xs text-muted-foreground mt-1">Public report for sharing</p>
            </div>

            <div>
              <Label htmlFor="comments">Comments</Label>
              <Textarea
                id="comments"
                value={newSubmission.comments}
                onChange={(e) => setNewSubmission(prev => ({ ...prev, comments: e.target.value }))}
                placeholder="Optional comments about the submission"
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Create Submission</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Generate Submissions Dialog */}
      <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Generate Expected Submissions</DialogTitle>
            <DialogDescription>
              Create placeholder submissions for all groups in a classroom for {assignment?.name || 'this assignment'}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleGenerateSubmissions} className="space-y-4">
            <div>
              <Label htmlFor="generate-classroom">Classroom *</Label>
              <Select value={generateForm.classroom_id} onValueChange={(value) => setGenerateForm(prev => ({ ...prev, classroom_id: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select classroom" />
                </SelectTrigger>
                <SelectContent>
                  {classrooms.map(classroom => (
                    <SelectItem key={classroom.id} value={classroom.id.toString()}>
                      {classroom.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsGenerateDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!generateForm.classroom_id}>
                Generate Submissions
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Submissions Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Submissions ({filteredAndSortedSubmissions().length})
              {submissions.length !== filteredAndSortedSubmissions().length && (
                <span className="text-sm text-muted-foreground">
                  (filtered from {submissions.length})
                </span>
              )}
            </span>
            <div className="flex gap-2">
              <Button 
                size="sm"
                onClick={() => setIsCreateDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setIsGenerateDialogOpen(true)}
              >
                <Wand2 className="mr-2 h-4 w-4" />
                Generate
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading submissions...</div>
          ) : filteredAndSortedSubmissions().length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No submissions found for this assignment
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead 
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('classroom')}
                  >
                    <div className="flex items-center gap-2">
                      Classroom
                      {getSortIcon('classroom')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('group')}
                  >
                    <div className="flex items-center gap-2">
                      Group
                      {getSortIcon('group')}
                    </div>
                  </TableHead>
                  <TableHead>Coordinators</TableHead>
                  <TableHead>PDF Files</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedSubmissions().map(submission => (
                  <TableRow key={submission.id}>
                    <TableCell>
                      {submission.classroom ? (
                        <div className="flex items-center gap-1">
                          <GraduationCap className="h-4 w-4" />
                          {submission.classroom.name}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {submission.group ? (
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          {submission.group.name}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {submission.coordinators ? (
                        <div className="flex flex-col gap-1">
                          {(() => {
                            try {
                              const coordinators = JSON.parse(submission.coordinators)
                              return Array.isArray(coordinators) ? coordinators.map((coord: string, index: number) => (
                                <div key={index} className="flex items-center gap-1">
                                  <Users className="h-3 w-3 text-blue-600" />
                                  <span className="text-xs text-blue-600">{coord}</span>
                                </div>
                              )) : (
                                <div className="flex items-center gap-1">
                                  <Users className="h-3 w-3 text-blue-600" />
                                  <span className="text-xs text-blue-600">{coordinators}</span>
                                </div>
                              )
                            } catch (e) {
                              return (
                                <div className="flex items-center gap-1">
                                  <Users className="h-3 w-3 text-blue-600" />
                                  <span className="text-xs text-blue-600">{submission.coordinators}</span>
                                </div>
                              )
                            }
                          })()}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        {/* Main PDF */}
                        {submission.pdf_file_name ? (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-blue-600" />
                            <span className="text-xs text-blue-600">Main: {submission.pdf_file_name}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-gray-400" />
                            <span className="text-xs text-gray-400">Main: Not uploaded</span>
                          </div>
                        )}
                        
                        {/* Private PDF */}
                        {submission.private_pdf_filename ? (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-purple-600" />
                            <span className="text-xs text-purple-600">Private: {submission.private_pdf_filename}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-gray-400" />
                            <span className="text-xs text-gray-400">Private: Not uploaded</span>
                          </div>
                        )}
                        
                        {/* Public PDF */}
                        {submission.public_pdf_filename ? (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-green-600" />
                            <span className="text-xs text-green-600">Public: {submission.public_pdf_filename}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-gray-400" />
                            <span className="text-xs text-gray-400">Public: Not uploaded</span>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(submission.status)}
                        {submission.is_late && (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {submission.total_score !== null && submission.max_score ? (
                        <span className="font-medium">{submission.total_score.toFixed(1)}/10</span>
                      ) : (
                        <span className="text-muted-foreground">Not graded</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditSubmission(submission)}
                          title="Edit Submission"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedSubmission(submission)
                            setIsGradeDialogOpen(true)
                          }}
                        >
                          <GraduationCap className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openStudentPdfDialog(submission)}
                          title="Upload Reports"
                        >
                          <Upload className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteSubmission(submission.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Submission Review Dialog */}
      {selectedSubmission && (
        <SubmissionReviewDialog
          submission={selectedSubmission}
          assignment={assignment}
          open={isGradeDialogOpen}
          onOpenChange={(open) => {
            setIsGradeDialogOpen(open)
            // Refresh data when dialog is closed to ensure consistency
            if (!open) {
              fetchSubmissions()
            }
          }}
          onGradeSubmit={handleGradeSubmission}
          onSubmissionUpdate={handleSubmissionUpdate}
        />
      )}

      {/* Student PDF Upload Dialog */}
      {submissionForStudentPdf && (
        <StudentPdfUploadDialog
          submission={submissionForStudentPdf}
          open={isStudentPdfDialogOpen}
          onOpenChange={setIsStudentPdfDialogOpen}
          onSuccess={() => {
            fetchSubmissions()
            closeStudentPdfDialog()
          }}
        />
      )}

      {/* Edit Submission Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Submission</DialogTitle>
            <DialogDescription>
              Update submission details
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-classroom">Classroom</Label>
              <Select 
                value={editForm.classroom_id} 
                onValueChange={(value) => setEditForm(prev => ({ ...prev, classroom_id: value, group_id: '' }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select classroom" />
                </SelectTrigger>
                <SelectContent>
                  {classrooms.map(classroom => (
                    <SelectItem key={classroom.id} value={classroom.id.toString()}>
                      {classroom.name} ({classroom.teacher_name})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="edit-group">Group</Label>
              <Select 
                value={editForm.group_id} 
                onValueChange={(value) => setEditForm(prev => ({ ...prev, group_id: value }))}
                disabled={!editForm.classroom_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select group" />
                </SelectTrigger>
                <SelectContent>
                  {groups.filter(g => !editForm.classroom_id || g.classroom_id === parseInt(editForm.classroom_id)).map(group => (
                    <SelectItem key={group.id} value={group.id.toString()}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {editForm.group_id && (() => {
              const selectedGroup = groups.find(g => g.id === parseInt(editForm.group_id))
              const members = selectedGroup?.members || []
              return (
                <div>
                  <Label>Coordinators (for private reports)</Label>
                  <div className="space-y-2 border rounded p-3 max-h-48 overflow-y-auto">
                    {members.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No members in this group</p>
                    ) : (
                      members.map((member: any) => {
                        const memberName = typeof member === 'string' ? member : (member.name || member.email || 'Unknown')
                        return (
                          <div key={memberName} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={`edit-coord-${memberName}`}
                              checked={editForm.coordinators.includes(memberName)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setEditForm(prev => ({
                                    ...prev,
                                    coordinators: [...prev.coordinators, memberName]
                                  }))
                                } else {
                                  setEditForm(prev => ({
                                    ...prev,
                                    coordinators: prev.coordinators.filter(c => c !== memberName)
                                  }))
                                }
                              }}
                              className="h-4 w-4"
                            />
                            <label htmlFor={`edit-coord-${memberName}`} className="text-sm">
                              {memberName}
                            </label>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              )
            })()}

            <div>
              <Label htmlFor="edit-status">Status</Label>
              <Select value={editForm.status} onValueChange={(value) => setEditForm(prev => ({ ...prev, status: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="submitted">Submitted</SelectItem>
                  <SelectItem value="graded">Graded</SelectItem>
                  <SelectItem value="returned">Returned</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="edit-comments">Comments</Label>
              <Textarea
                id="edit-comments"
                value={editForm.comments}
                onChange={(e) => setEditForm(prev => ({ ...prev, comments: e.target.value }))}
                placeholder="Optional comments about the submission"
                rows={4}
              />
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="button" onClick={handleSaveSubmission}>
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
