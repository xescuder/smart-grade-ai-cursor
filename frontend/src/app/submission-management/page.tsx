/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-hooks/exhaustive-deps */
"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FileText, Calendar, Search, ChevronDown, ChevronRight, Download, Wand2 } from "lucide-react"
import { toast } from "sonner"
import { AssignmentSubmissions } from "@/components/assignment-submissions"
import { apiClient } from "@/lib/api"
import { getAuthHeaders } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface Assignment {
  id: number
  name: string
  description?: string
  due_date: string
  created_at: string
  updated_at: string
  course_id?: number
  semester_id?: number
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
  coordinators?: string
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
  assignment?: Assignment
  classroom?: Classroom
  group?: {
    id: number
    name: string
    classroom_id: number
    members: any[]
  }
}

interface AssignmentGroup {
  assignment: Assignment
  submissions: Submission[]
  isExpanded: boolean
}

interface Classroom {
  id: number
  name: string
  teacher_name?: string
  language?: string
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
    course?: {
      id: number
      name: string
      code: string
    }
  }
}

export default function SubmissionManagementPage() {
  const [, setSubmissions] = useState<Submission[]>([])
  const [assignmentGroups, setAssignmentGroups] = useState<AssignmentGroup[]>([])
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState(true)
  
  // Dialog states
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)
  
  // Form state for generate submissions
  const [courses, setCourses] = useState<any[]>([])
  const [semesters, setSemesters] = useState<any[]>([])
  const [classrooms, setClassrooms] = useState<any[]>([])
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [generateForm, setGenerateForm] = useState({
    course_id: '',
    semester_id: '',
    classroom_id: '',
    assignment_id: ''
  })

  // Fetch data on component mount
  useEffect(() => {
    fetchSubmissions()
  }, [])
  
  // Fetch data when dialog opens
  useEffect(() => {
    if (isGenerateDialogOpen) {
      fetchCourses()
      fetchSemesters()
    }
  }, [isGenerateDialogOpen])
  
  // Fetch semesters when course is selected
  useEffect(() => {
    if (isGenerateDialogOpen && generateForm.course_id) {
      fetchSemesters()
    }
  }, [isGenerateDialogOpen, generateForm.course_id])
  
  // Fetch classrooms when semester is selected
  useEffect(() => {
    if (isGenerateDialogOpen && generateForm.semester_id) {
      fetchClassroomsForDialog(generateForm.semester_id)
    } else {
      setClassrooms([])
    }
  }, [isGenerateDialogOpen, generateForm.semester_id])
  
  // Fetch assignments when semester is selected
  useEffect(() => {
    if (isGenerateDialogOpen && generateForm.semester_id) {
      fetchAssignmentsForDialog()
    } else {
      setAssignments([])
    }
  }, [isGenerateDialogOpen, generateForm.semester_id])

  const fetchSubmissions = async () => {
    try {
      setLoading(true)
      
      // Fetch all assignments first
      const assignmentsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/`)
      const allAssignments = assignmentsResponse.ok ? await assignmentsResponse.json() : []
      
      // Fetch all submissions
      const submissions = await apiClient.getSubmissions({})
      
      console.log('Raw submissions from API:', submissions)
      
      let filteredSubmissions = Array.isArray(submissions) ? submissions : []
      
      // Filter by search query if provided
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        filteredSubmissions = filteredSubmissions.filter(submission => {
          const assignment = submission.assignment
          const classroom = submission.classroom
          
          // Search in assignment name
          if (assignment?.name?.toLowerCase().includes(query)) return true
          
          // Search in course name or code
          if (classroom?.semester?.course?.name?.toLowerCase().includes(query)) return true
          if (classroom?.semester?.course?.code?.toLowerCase().includes(query)) return true
          
          // Search in classroom name
          if (classroom?.name?.toLowerCase().includes(query)) return true
          
          return false
        })
      }
      
      console.log('Filtered submissions:', filteredSubmissions)
      setSubmissions(filteredSubmissions)
      
      // Group submissions by assignment and include all assignments
      await groupSubmissionsByAssignment(filteredSubmissions, Array.isArray(allAssignments) ? allAssignments : [])
    } catch (error) {
      console.error('Error fetching submissions:', error)
      toast.error('Failed to fetch submissions')
      setSubmissions([])
      setAssignmentGroups([])
    } finally {
      setLoading(false)
    }
  }

  const groupSubmissionsByAssignment = async (submissions: Submission[], allAssignments: Assignment[]) => {
    const assignmentMap = new Map<number, AssignmentGroup>()
    
    // Create a map of course/semester data from submissions
    const courseSemesterMap = new Map<number, { course?: any, semester?: any }>()
    submissions.forEach(submission => {
      if (submission.classroom?.semester?.course && submission.classroom?.semester) {
        courseSemesterMap.set(submission.assignment_id, {
          course: submission.classroom.semester.course,
          semester: submission.classroom.semester
        })
      }
    })
    
    // First, add all assignments (even if they have no submissions)
    allAssignments.forEach(assignment => {
      // Try to enrich assignment with course/semester data from submissions
      const enrichData = courseSemesterMap.get(assignment.id)
      const enrichedAssignment = enrichData 
        ? { ...assignment, course: enrichData.course, semester: enrichData.semester }
        : assignment
      
      assignmentMap.set(assignment.id, {
        assignment: enrichedAssignment,
        submissions: [],
        isExpanded: true // Default to expanded
      })
    })
    
    // Then, group submissions by assignment
    submissions.forEach(submission => {
      const assignmentId = submission.assignment_id
      
      if (!assignmentMap.has(assignmentId)) {
        // Use assignment data from submission if available, otherwise create placeholder
        const assignment = submission.assignment || {
          id: assignmentId,
          name: `Assignment ${assignmentId}`,
          description: '',
          due_date: '',
          created_at: '',
          updated_at: '',
          exercises: []
        }
        
        assignmentMap.set(assignmentId, {
          assignment,
          submissions: [],
          isExpanded: true // Default to expanded
        })
      }
      
      assignmentMap.get(assignmentId)!.submissions.push(submission)
    })
    
    // Convert map to array and sort by assignment name
    const sortedGroups = Array.from(assignmentMap.values()).sort((a, b) => 
      a.assignment.name.localeCompare(b.assignment.name)
    )
    
    setAssignmentGroups(sortedGroups)
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

  const toggleAssignmentGroup = (assignmentId: number) => {
    setAssignmentGroups(prev => 
      prev.map(group => 
        group.assignment.id === assignmentId 
          ? { ...group, isExpanded: !group.isExpanded }
          : group
      )
    )
  }


  const getAssignmentStats = (submissions: Submission[]) => {
    const total = submissions.length
    const graded = submissions.filter(s => s.status === 'graded').length
    const pending = submissions.filter(s => s.status === 'submitted').length
    const late = submissions.filter(s => s.is_late).length
    
    return { total, graded, pending, late }
  }

  const handleExportAssignment = async (assignmentId: number) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignmentId}/export-excel`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `assignment_${assignmentId}_grades.xlsx`
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


  const fetchCourses = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/courses/?created_by=1&include_semesters=true`)
      if (response.ok) {
        const data = await response.json()
        console.log('Courses data:', data)
        setCourses(Array.isArray(data) ? data : [])
      } else {
        console.error('Failed to fetch courses:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching courses:', error)
    }
  }
  
  const fetchSemesters = async () => {
    try {
      // If a course is selected, fetch semesters for that course
      if (generateForm.course_id) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/semesters/by-course/${generateForm.course_id}`)
        if (response.ok) {
          const data = await response.json()
          setSemesters(Array.isArray(data) ? data : [])
        }
      } else {
        // If no course selected, fetch all semesters
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/semesters/`)
        if (response.ok) {
          const data = await response.json()
          setSemesters(Array.isArray(data) ? data : [])
        }
      }
    } catch (error) {
      console.error('Error fetching semesters:', error)
    }
  }
  
  const fetchClassroomsForDialog = async (semesterId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/classrooms/by-semester/${semesterId}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Classrooms fetched:', data)
        setClassrooms(Array.isArray(data) ? data : [])
      } else {
        console.error('Failed to fetch classrooms:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching classrooms:', error)
    }
  }
  
  const fetchAssignmentsForDialog = async () => {
    try {
      // Use semester_id to fetch assignments
      if (generateForm.semester_id) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/by-semester/${generateForm.semester_id}`)
        if (response.ok) {
          const data = await response.json()
          setAssignments(Array.isArray(data) ? data : [])
        }
      } else {
        setAssignments([])
      }
    } catch (error) {
      console.error('Error fetching assignments:', error)
    }
  }
  
  const handleGenerateSubmissions = async () => {
    if (!generateForm.course_id || !generateForm.semester_id || !generateForm.classroom_id || !generateForm.assignment_id) {
      toast.error('Please fill all fields')
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
          assignment_id: parseInt(generateForm.assignment_id),
          classroom_id: parseInt(generateForm.classroom_id)
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate submissions')
      }
      
      const result = await response.json()
      toast.success(result.message || `Generated ${result.count} submissions successfully`)
      setIsGenerateDialogOpen(false)
      fetchSubmissions()
      
      // Reset form
      setGenerateForm({
        course_id: '',
        semester_id: '',
        classroom_id: '',
        assignment_id: ''
      })
    } catch (error: any) {
      console.error('Error generating submissions:', error)
      toast.error(error.message || 'Failed to generate submissions')
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="text-center py-8">Loading assignments...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Submission Management</h1>
          <p className="text-muted-foreground">Manage student group submissions by assignment</p>
        </div>
        
        <Button 
          className="flex items-center gap-2"
          onClick={() => setIsGenerateDialogOpen(true)}
        >
          <Wand2 className="h-4 w-4" />
          Generate Submissions
        </Button>
      </div>

      {/* Search Filter */}
      <div className="mb-8">
        <div className="flex gap-3 items-center">
          <div className="flex-1">
            <Label className="text-xs text-muted-foreground mb-1">Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search by assignment name, course name, or classroom name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    fetchSubmissions()
                  }
                }}
                className="pl-10 w-full"
              />
            </div>
          </div>
          <Button
            onClick={fetchSubmissions}
            variant="outline"
            size="sm"
            className="mt-auto"
          >
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>
      </div>


      {/* Assignment Groups */}
      <div className="space-y-4">
        {assignmentGroups.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No submissions found</h3>
                <p>No submissions match your current filters.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          assignmentGroups.map(group => {
            const stats = getAssignmentStats(group.submissions)
            return (
              <Card key={group.assignment.id} className="overflow-hidden">
                <Collapsible 
                  open={group.isExpanded} 
                  onOpenChange={() => toggleAssignmentGroup(group.assignment.id)}
                >
                  <CardHeader className="p-0">
                    <div className="flex items-center justify-between p-6">
                      <CollapsibleTrigger asChild>
                        <div className="flex items-center gap-3 cursor-pointer hover:bg-muted/50 transition-colors rounded-md p-2 -m-2 flex-1">
                          {group.isExpanded ? (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-5 w-5 text-muted-foreground" />
                          )}
                          <div>
                            <CardTitle className="text-xl">{group.assignment.name}</CardTitle>
                            {group.assignment.description && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {group.assignment.description}
                              </p>
                            )}
                            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                              {/* Show course and semester if available */}
                              {(() => {
                                const firstSubmission = group.submissions[0]
                                if (firstSubmission?.classroom?.semester?.course && firstSubmission?.classroom?.semester) {
                                  return (
                                    <>
                                      <div className="flex items-center gap-1">
                                        <FileText className="h-3 w-3" />
                                        {firstSubmission.classroom.semester.course.code} - {firstSubmission.classroom.semester.season} {firstSubmission.classroom.semester.year}
                                      </div>
                                      <div className="text-muted-foreground">•</div>
                                    </>
                                  )
                                }
                                // If no submissions, try to get from assignment
                                if (group.assignment.course && group.assignment.semester) {
                                  return (
                                    <>
                                      <div className="flex items-center gap-1">
                                        <FileText className="h-3 w-3" />
                                        {group.assignment.course.code} - {group.assignment.semester.season} {group.assignment.semester.year}
                                      </div>
                                      <div className="text-muted-foreground">•</div>
                                    </>
                                  )
                                }
                                return null
                              })()}
                              <div className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                Due: {formatDate(group.assignment.due_date)}
                              </div>
                              <div className="text-muted-foreground">•</div>
                              <div className="flex items-center gap-1">
                                <FileText className="h-4 w-4" />
                                {group.assignment.exercises?.length || 0} exercises
                              </div>
                            </div>
                          </div>
                        </div>
                      </CollapsibleTrigger>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{stats.total} total</Badge>
                          <Badge variant="secondary">{stats.graded} graded</Badge>
                          <Badge variant="default">{stats.pending} pending</Badge>
                          {stats.late > 0 && (
                            <Badge variant="destructive">{stats.late} late</Badge>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleExportAssignment(group.assignment.id)
                            }}
                          >
                            <Download className="mr-2 h-4 w-4" />
                            Export
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CollapsibleContent>
                    <CardContent className="pt-0">
                      <AssignmentSubmissions 
                        assignmentId={group.assignment.id}
                        assignment={group.assignment}
                        hideHeader={true}
                      />
                    </CardContent>
                  </CollapsibleContent>
                </Collapsible>
              </Card>
            )
          })
        )}
      </div>
      
      {/* Generate Submissions Dialog */}
      <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Generate Submissions</DialogTitle>
            <DialogDescription>
              Create submissions for all groups in a classroom for a specific assignment.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="generate-course">Course *</Label>
              <Select 
                value={generateForm.course_id} 
                onValueChange={(value) => {
                  setGenerateForm(prev => ({ 
                    ...prev, 
                    course_id: value,
                    semester_id: '',
                    classroom_id: '',
                    assignment_id: ''
                  }))
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select course" />
                </SelectTrigger>
                <SelectContent>
                  {courses.map(course => (
                    <SelectItem key={course.id} value={course.id.toString()}>
                      {course.name} ({course.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="generate-semester">Semester *</Label>
              <Select 
                value={generateForm.semester_id} 
                onValueChange={(value) => {
                  setGenerateForm(prev => ({ 
                    ...prev, 
                    semester_id: value,
                    classroom_id: '',
                    assignment_id: ''
                  }))
                }}
                disabled={!generateForm.course_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select semester" />
                </SelectTrigger>
                <SelectContent>
                  {semesters
                    .filter(semester => !generateForm.course_id || semester.course_id === parseInt(generateForm.course_id))
                    .map(semester => (
                      <SelectItem key={semester.id} value={semester.id.toString()}>
                        {semester.season} {semester.year}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="generate-classroom">Classroom *</Label>
              <Select 
                value={generateForm.classroom_id} 
                onValueChange={(value) => {
                  setGenerateForm(prev => ({ 
                    ...prev, 
                    classroom_id: value,
                    assignment_id: ''
                  }))
                }}
                disabled={!generateForm.semester_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select classroom" />
                </SelectTrigger>
                <SelectContent>
                  {classrooms
                    .filter(classroom => {
                      if (!generateForm.semester_id) return false
                      // Check both direct semester_id and nested semester.id
                      return (classroom.semester_id === parseInt(generateForm.semester_id)) || 
                             (classroom.semester?.id === parseInt(generateForm.semester_id))
                    })
                    .map(classroom => (
                      <SelectItem key={classroom.id} value={classroom.id.toString()}>
                        {classroom.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="generate-assignment">Assignment *</Label>
              <Select 
                value={generateForm.assignment_id} 
                onValueChange={(value) => {
                  setGenerateForm(prev => ({ 
                    ...prev, 
                    assignment_id: value
                  }))
                }}
                disabled={!generateForm.classroom_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select assignment" />
                </SelectTrigger>
                <SelectContent>
                  {assignments.map(assignment => (
                    <SelectItem key={assignment.id} value={assignment.id.toString()}>
                      {assignment.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setIsGenerateDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button 
                type="button"
                onClick={handleGenerateSubmissions}
                disabled={!generateForm.course_id || !generateForm.semester_id || !generateForm.classroom_id || !generateForm.assignment_id}
              >
                Generate Submissions
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
