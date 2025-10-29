/**
 * Assignment Management Page
 * CRUD interface for managing assignments and exercises
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card"
import { Plus, Edit, Trash2, Calendar, BookOpen, Upload, FileText, Download, Globe } from "lucide-react"
import { toast } from "sonner"
import { Assignment } from "@/types/assignment"
import { Badge } from "@/components/ui/badge"
import { AssignmentCreateDialog } from "@/components/assignment-create-dialog"
import { AssignmentPdfUploadDialog } from "@/components/assignment-pdf-upload-dialog"
import { AssignmentExerciseManagementDialog } from "@/components/assignment-exercise-management-dialog"
import { AssignmentEditDialog } from "@/components/assignment-edit-dialog"
import { PdfViewerDialog } from "@/components/pdf-viewer-dialog"
import { apiClient } from "@/lib/api"

export default function AssignmentManagementPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isPdfUploadDialogOpen, setIsPdfUploadDialogOpen] = useState(false)
  const [isExerciseManagementDialogOpen, setIsExerciseManagementDialogOpen] = useState(false)
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Fetch assignments from API
  const fetchAssignments = async () => {
    try {
      setIsLoading(true)
      const data: Assignment[] = await apiClient.getAssignments()
      
      // Transform API response to match frontend expectations
      const transformedData: Assignment[] = data.map((assignment: Assignment) => ({
        id: assignment.id,
        name: assignment.name,
        description: assignment.description,
        due_date: assignment.due_date,
        language: assignment.language || 'en',
        course_id: assignment.course_id,
        semester_id: assignment.semester_id,
        exercises: assignment.exercises || [],
        pdf_file_path: assignment.pdf_file_path,
        pdf_file_name: assignment.pdf_file_name,
        created_by: assignment.created_by ?? 1,
        is_active: assignment.is_active ?? true,
        created_at: assignment.created_at,
        updated_at: assignment.updated_at,
        course: assignment.course,
        semester: assignment.semester
      }))
      setAssignments(transformedData)
    } catch (error) {
      console.error("Error fetching assignments:", error)
      toast.error("Failed to load assignments. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  // Delete assignment
  const handleDelete = async (assignmentId: number) => {
    if (!confirm("Are you sure you want to delete this assignment?")) {
      return
    }

    try {
      await apiClient.deleteAssignment(assignmentId)
      setAssignments(assignments.filter(a => a.id !== assignmentId))
      toast.success("Assignment deleted successfully")
    } catch (error) {
      console.error("Error deleting assignment:", error)
      toast.error("Failed to delete assignment. Please try again.")
    }
  }

  const handleExportSubmissions = async (assignmentId: number) => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${API_BASE_URL}/api/v1/assignments/${assignmentId}/export`, {
        method: "GET",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        // Get the filename from the Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = 'submissions.csv'
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }

        // Create blob and download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        toast.success("Submissions exported successfully")
      } else {
        console.error("Failed to export submissions")
        toast.error("Failed to export submissions. Please try again.")
      }
    } catch (error) {
      console.error("Error exporting submissions:", error)
      toast.error("Error exporting submissions. Please try again.")
    }
  }


  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // Calculate exercises count
  const getAssignmentStats = (assignment: Assignment) => {
    const exerciseCount = assignment.exercises.length
    return { exerciseCount }
  }

  
  const handlePdfUploadSuccess = () => {
    setIsPdfUploadDialogOpen(false)
    setSelectedAssignment(null)
    fetchAssignments()
  }

  const handleExerciseManagementSave = () => {
    setIsExerciseManagementDialogOpen(false)
    setSelectedAssignment(null)
    fetchAssignments()
  }

  // PDF Viewer handlers
  const handleViewPdf = (assignment: Assignment) => {
    setSelectedAssignment(assignment)
    setIsPdfViewerOpen(true)
  }

  const handlePdfViewerUpload = () => {
    setIsPdfViewerOpen(false)
    setIsPdfUploadDialogOpen(true)
  }

  const handlePdfViewerClose = () => {
    setIsPdfViewerOpen(false)
    setSelectedAssignment(null)
  }



  useEffect(() => {
    fetchAssignments()
  }, [])

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
            <p>Loading assignments...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assignment Management</h1>
          <p className="text-gray-600 mt-2">Create and manage assignments with exercises</p>
        </div>
        
        <Button 
          className="flex items-center gap-2"
          onClick={() => {
            setSelectedAssignment(null)
            setIsCreateDialogOpen(true)
          }}
        >
          <Plus className="h-4 w-4" />
          Create Assignment
        </Button>
      </div>

      {assignments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No assignments yet</h3>
            <p className="text-gray-600 text-center mb-6">
              Create your first assignment to get started with AI-powered grading.
            </p>
            <Button onClick={() => {
              setSelectedAssignment(null)
              setIsCreateDialogOpen(true)
            }}>
              <Plus className="h-4 w-4 mr-2" />
              Create Assignment
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {assignments.map((assignment) => {
            const { exerciseCount } = getAssignmentStats(assignment)
            
            return (
              <Card key={assignment.id} className="overflow-hidden">
                {/* Assignment Header */}
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {/* Assignment Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-lg truncate">{assignment.name}</h3>
                          {assignment.language && (
                            <Badge variant="outline" className="shrink-0">
                              <Globe className="h-3 w-3 mr-1" />
                              {assignment.language.toUpperCase()}
                            </Badge>
                          )}
                          {assignment.course && (
                            <Badge variant="secondary" className="shrink-0">
                              {assignment.course.name}
                            </Badge>
                          )}
                          {assignment.semester && (
                            <Badge variant="outline" className="shrink-0">
                              {assignment.semester.name}
                            </Badge>
                          )}
                          {(!assignment.course || !assignment.semester) && (
                            <Badge variant="destructive" className="shrink-0">
                              Missing Course/Semester
                            </Badge>
                          )}
                          <span className={`text-xs px-2 py-1 rounded ${
                            assignment.is_active 
                              ? "bg-green-100 text-green-800" 
                              : "bg-gray-100 text-gray-800"
                          }`}>
                            {assignment.is_active ? "Active" : "Inactive"}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm truncate">{assignment.description}</p>
                        
                        {/* Stats */}
                        <div className="flex items-center gap-4 mt-2">
                          <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Calendar className="h-3 w-3" />
                            <span>Due: {formatDate(assignment.due_date)}</span>
                          </div>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {exerciseCount} exercises • 100 pts
                          </span>
                          {assignment.pdf_file_name && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded flex items-center gap-1">
                              📎 {assignment.pdf_file_name}
                              <button
                                onClick={() => handleViewPdf(assignment)}
                                className="ml-1 text-blue-600 hover:text-blue-800 underline"
                                title="View PDF"
                              >
                                View
                              </button>
                            </span>
                          )}
                        </div>


                        {/* Assignment Metadata */}
                        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                          <span>Created: {formatDate(assignment.created_at)}</span>
                          {assignment.updated_at && (
                            <span>Updated: {formatDate(assignment.updated_at)}</span>
                          )}
                          <span>ID: #{assignment.id}</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-1 shrink-0">
                      
                      {/* Edit */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedAssignment(assignment)
                          setIsEditDialogOpen(true)
                        }}
                        title="Edit Assignment"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      
                      {/* Manage Exercises */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedAssignment(assignment)
                          setIsExerciseManagementDialogOpen(true)
                        }}
                        title="Manage Exercises"
                        className="text-green-600"
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                      
                      {/* Upload PDF */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedAssignment(assignment)
                          setIsPdfUploadDialogOpen(true)
                        }}
                        title={assignment.pdf_file_name ? "Replace PDF" : "Upload PDF"}
                        className={assignment.pdf_file_name ? "text-blue-600" : ""}
                      >
                        <Upload className="h-4 w-4" />
                      </Button>
                      
                      
                      {/* Export Submissions */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleExportSubmissions(assignment.id)}
                        className="text-green-600 hover:text-green-800"
                        title="Export Submissions as CSV"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      
                      {/* Delete */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(assignment.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete Assignment"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Assignment Dialog */}
      <AssignmentCreateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSave={handleAssignmentSave}
      />

      {/* Edit Assignment Dialog */}
      <AssignmentEditDialog
        assignment={selectedAssignment}
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        onSave={handleAssignmentSave}
      />

      {/* PDF Upload Dialog */}
      {selectedAssignment && (
        <AssignmentPdfUploadDialog
          assignment={selectedAssignment}
          open={isPdfUploadDialogOpen}
          onOpenChange={setIsPdfUploadDialogOpen}
          onSuccess={handlePdfUploadSuccess}
        />
      )}

      {/* Exercise Management Dialog */}
      <AssignmentExerciseManagementDialog
        assignment={selectedAssignment}
        open={isExerciseManagementDialogOpen}
        onOpenChange={setIsExerciseManagementDialogOpen}
        onSave={handleExerciseManagementSave}
        onUploadPdf={handlePdfViewerUpload}
      />

      {/* PDF Viewer Dialog */}
      {selectedAssignment && (
        <PdfViewerDialog
          assignment={selectedAssignment}
          open={isPdfViewerOpen}
          onOpenChange={handlePdfViewerClose}
          onUpload={handlePdfViewerUpload}
        />
      )}

    </div>
  )
}
