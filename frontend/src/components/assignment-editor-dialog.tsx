/**
 * Assignment Editor Dialog Component
 * Displays assignment PDF with exercise management side by side
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { X, Download, ZoomIn, ZoomOut, RotateCw, FileText, Plus, Trash2, Edit, Grip } from "lucide-react"
import { toast } from "sonner"
import { Assignment, Exercise } from "@/types/assignment"

interface AssignmentEditorDialogProps {
  assignment?: Assignment
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave?: (assignment: Assignment) => void
}

export function AssignmentEditorDialog({ 
  assignment,
  open, 
  onOpenChange, 
  onSave 
}: AssignmentEditorDialogProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [pdfUrl, setPdfUrl] = useState("")
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  
  // Form data
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    due_date: "",
  })
  
  // Exercise management
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [editingExercise, setEditingExercise] = useState<Exercise | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Initialize form data and exercises when dialog opens
  useEffect(() => {
    if (open) {
      if (assignment) {
        setFormData({
          name: assignment.name,
          description: assignment.description,
          due_date: new Date(assignment.due_date).toISOString().slice(0, 16),
        })
        setExercises(assignment.exercises || [])
      } else {
        // Reset for new assignment
        setFormData({
          name: "",
          description: "",
          due_date: "",
        })
        setExercises([])
      }
    }
  }, [open, assignment])

  // Load PDF when dialog opens
  useEffect(() => {
    console.log("PDF useEffect triggered - open:", open, "assignment:", assignment?.id, "pdf_file_name:", assignment?.pdf_file_name)
    if (open && assignment?.pdf_file_name) {
      loadPdf()
    } else if (open && !assignment) {
      setPdfUrl("")
    }
  }, [open, assignment?.pdf_file_name])

  const loadPdf = async () => {
    if (!assignment?.id) return

    console.log("Loading PDF for assignment:", assignment.id, "PDF file name:", assignment.pdf_file_name, "PDF file path:", assignment.pdf_file_path)
    
    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/pdf`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      console.log("PDF response status:", response.status)

      if (response.ok) {
        const blob = await response.blob()
        console.log("PDF blob size:", blob.size)
        const url = URL.createObjectURL(blob)
        setPdfUrl(url)
      } else {
        setError("Failed to load PDF")
      }
    } catch (err) {
      console.error("Error loading PDF:", err)
      setError("Failed to load PDF")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (pdfUrl) {
      const link = document.createElement('a')
      link.href = pdfUrl
      link.download = `${assignment?.name || 'assignment'}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    const pdfFile = files.find(file => file.type === 'application/pdf')

    if (!pdfFile) {
      toast.error("Please drop a PDF file")
      return
    }

    if (files.length > 1) {
      toast.error("Please drop only one PDF file at a time")
      return
    }

    await uploadPdf(pdfFile)
  }

  const uploadPdf = async (file: File) => {
    if (!assignment?.id) {
      toast.error("Please save the assignment first before uploading a PDF")
      return
    }

    setIsUploading(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/upload/statement`, {
        method: 'POST',
        headers: {
          'Authorization': getAuthHeaders()['Authorization'] || '',
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Update the assignment with new PDF info
      if (assignment) {
        // Update the assignment object with new PDF info
        assignment.pdf_file_path = result.pdf_file_path
        assignment.pdf_file_name = result.pdf_file_name
        
        // Clear current PDF URL first
        setPdfUrl("")
        setError("")
        
        // Wait a moment to ensure the file is fully saved
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // Create a proper PDF URL for viewing with timestamp to force reload
        const timestamp = Date.now()
        const pdfViewerUrl = `http://localhost:8001/api/v1/assignments/${assignment.id}/pdf?t=${timestamp}`
        
        // Set the PDF URL directly
        setPdfUrl(pdfViewerUrl)
        
        toast.success("PDF uploaded successfully!")
      }
    } catch (error) {
      console.error("Error uploading PDF:", error)
      setError("Failed to upload PDF")
      toast.error("Failed to upload PDF. Please try again.")
    } finally {
      setIsUploading(false)
    }
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 300))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50))
  const handleRotate = () => setRotation(prev => (prev + 90) % 360)

  // Exercise management functions
  const addExercise = () => {
    const newExercise: Exercise = {
      id: Date.now(), // Temporary ID
      name: "",
      description: "",
      points: 0,
      evaluation_criteria: "",
      assignment_id: assignment?.id || 0
    }
    setExercises([...exercises, newExercise])
    setEditingExercise(newExercise)
  }

  const updateExercise = (exerciseId: number, updates: Partial<Exercise>) => {
    setExercises(exercises.map(ex => 
      ex.id === exerciseId ? { ...ex, ...updates } : ex
    ))
  }

  const removeExercise = (exerciseId: number) => {
    setExercises(exercises.filter(ex => ex.id !== exerciseId))
    if (editingExercise?.id === exerciseId) {
      setEditingExercise(null)
    }
  }

  const startEditingExercise = (exercise: Exercise) => {
    setEditingExercise(exercise)
  }

  const finishEditingExercise = () => {
    setEditingExercise(null)
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    try {
      // Validate form
      if (!formData.name.trim()) {
        toast.error("Assignment name is required")
        return
      }

      if (exercises.length === 0) {
        toast.error("At least one exercise is required")
        return
      }

      // Validate exercises
      for (const exercise of exercises) {
        // No name validation needed since we removed the name field
        if (exercise.points <= 0) {
          toast.error("All exercises must have points greater than 0")
          return
        }
      }

      // Calculate total points
      const totalPoints = exercises.reduce((sum, ex) => sum + ex.points, 0)
      if (totalPoints !== 100) {
        toast.error(`Total points must equal 100 (currently ${totalPoints})`)
        return
      }

      // Prepare assignment data
      const assignmentData = {
        ...formData,
        exercises: exercises.map(ex => ({
          ...ex,
          id: ex.id > 1000000 ? undefined : ex.id // Remove temporary IDs
        }))
      }

      // Call onSave with the assignment data
      if (onSave) {
        await onSave(assignmentData as Assignment)
      }

      toast.success(assignment ? "Assignment updated successfully!" : "Assignment created successfully!")
      onOpenChange(false)
    } catch (error) {
      console.error("Error saving assignment:", error)
      toast.error("Failed to save assignment")
    } finally {
      setIsSubmitting(false)
    }
  }

  const totalPoints = exercises.reduce((sum, ex) => sum + ex.points, 0)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="max-w-[95vw] w-[95vw] h-[90vh] flex flex-col p-0"
        style={{
          width: '95vw',
          height: '90vh',
          maxWidth: '95vw',
          maxHeight: '90vh',
          minWidth: '800px',
          minHeight: '600px',
          resize: 'both',
          overflow: 'hidden'
        }}
      >
        <DialogHeader className="flex-shrink-0 p-6 pb-4">
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {assignment ? "Edit Assignment" : "Create Assignment"}
          </DialogTitle>
          <DialogDescription>
            {assignment 
              ? `Edit assignment: ${assignment.name}` 
              : "Create a new assignment with exercises"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex gap-6 overflow-hidden px-6">
          {/* Left side - PDF Viewer */}
          <div className="w-1/2 flex flex-col">
            <Card className="flex-1 flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-lg">Assignment PDF</CardTitle>
                <CardDescription>
                  {assignment?.pdf_file_path ? "View and navigate the assignment PDF" : "Upload a PDF to view it here"}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col overflow-hidden">
                {assignment?.pdf_file_path ? (
                  <>
                    {/* PDF Controls */}
                    <div className="flex items-center gap-2 mb-4 flex-shrink-0">
                      <Button variant="outline" size="sm" onClick={handleZoomOut}>
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                      <span className="text-sm font-medium">{zoom}%</span>
                      <Button variant="outline" size="sm" onClick={handleZoomIn}>
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleRotate}>
                        <RotateCw className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleDownload}>
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* PDF Viewer */}
                    <div 
                      className={`flex-1 border rounded-lg overflow-hidden transition-colors ${
                        isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                      }`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      {isLoading || isUploading ? (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-2"></div>
                            <p className="text-sm text-gray-600">
                              {isUploading ? "Uploading PDF..." : "Loading PDF..."}
                            </p>
                          </div>
                        </div>
                      ) : error ? (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                            <p className="text-sm text-red-600">{error}</p>
                          </div>
                        </div>
                      ) : pdfUrl ? (
                        <iframe
                          key={pdfUrl} // Force reload when URL changes
                          src={pdfUrl}
                          className="w-full h-full"
                          style={{
                            transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                            transformOrigin: 'top left',
                            width: `${100 / (zoom / 100)}%`,
                            height: `${100 / (zoom / 100)}%`,
                          }}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                            <p className="text-sm text-gray-600">No PDF uploaded</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {assignment?.id ? "Drag & drop a PDF file here" : "Save assignment first to upload PDF"}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div 
                    className={`flex items-center justify-center h-full transition-colors ${
                      isDragOver ? 'bg-blue-50' : ''
                    }`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <div className="text-center">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">No PDF uploaded</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {assignment?.id ? "Drag & drop a PDF file here" : "Save assignment first to upload PDF"}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right side - Assignment Form and Exercise Management */}
          <div className="w-1/2 flex flex-col gap-4 overflow-hidden">
            {/* Assignment Basic Info */}
            <Card className="flex-shrink-0">
              <CardHeader>
                <CardTitle className="text-lg">Assignment Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Assignment Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Enter assignment name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Enter assignment description"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="due_date">Due Date</Label>
                  <Input
                    id="due_date"
                    type="datetime-local"
                    value={formData.due_date}
                    onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Exercise Management */}
            <Card className="flex-1 flex flex-col">
              <CardHeader className="flex-shrink-0">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">Exercises ({exercises.length})</CardTitle>
                    <CardDescription>
                      Total points: {totalPoints}/100
                      {totalPoints !== 100 && (
                        <span className="text-red-600 ml-2">
                          (Must equal 100)
                        </span>
                      )}
                    </CardDescription>
                  </div>
                  <Button onClick={addExercise} size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add Exercise
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4">
                {exercises.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 mb-4">No exercises added yet</p>
                    <Button onClick={addExercise} variant="outline">
                      <Plus className="h-4 w-4 mr-1" />
                      Add First Exercise
                    </Button>
                  </div>
                ) : (
                  exercises.map((exercise, index) => (
                    <Card key={exercise.id} className="border-l-4 border-l-blue-500">
                      <CardContent className="pt-4">
                        {editingExercise?.id === exercise.id ? (
                          // Edit mode
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium">Exercise {index + 1}</h4>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={finishEditingExercise}
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => removeExercise(exercise.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                  <div className="text-sm text-gray-600 py-2">
                                    Exercise {exercise.order || index + 1}
                                  </div>
                                </div>
                                <div className="space-y-1">
                                  <Label htmlFor={`ex-points-${exercise.id}`}>Points *</Label>
                                  <Input
                                    id={`ex-points-${exercise.id}`}
                                    type="number"
                                    min="1"
                                    max="100"
                                    value={exercise.points}
                                    onChange={(e) => updateExercise(exercise.id, { points: parseInt(e.target.value) || 0 })}
                                    placeholder="Points"
                                  />
                                </div>
                              </div>
                              <div className="space-y-1">
                                <Label htmlFor={`ex-desc-${exercise.id}`}>Description</Label>
                                <Textarea
                                  id={`ex-desc-${exercise.id}`}
                                  value={exercise.description}
                                  onChange={(e) => updateExercise(exercise.id, { description: e.target.value })}
                                  placeholder="Exercise description"
                                  rows={2}
                                />
                              </div>
                              <div className="space-y-1">
                                <Label htmlFor={`ex-criteria-${exercise.id}`}>Evaluation Criteria</Label>
                                <Textarea
                                  id={`ex-criteria-${exercise.id}`}
                                  value={exercise.evaluation_criteria}
                                  onChange={(e) => updateExercise(exercise.id, { evaluation_criteria: e.target.value })}
                                  placeholder="How to evaluate this exercise"
                                  rows={2}
                                />
                              </div>
                            </div>
                          </div>
                        ) : (
                          // View mode
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div>
                                <h4 className="font-medium">Exercise {exercise.order}</h4>
                                <p className="text-sm text-gray-600">{exercise.points} points</p>
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => startEditingExercise(exercise)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                            </div>
                            {exercise.description && (
                              <p className="text-sm text-gray-700">{exercise.description}</p>
                            )}
                            {exercise.evaluation_criteria && (
                              <div className="text-sm">
                                <span className="font-medium text-gray-600">Evaluation:</span>
                                <pre className="text-gray-700 whitespace-pre-wrap font-sans">{exercise.evaluation_criteria}</pre>
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer with Save button */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t flex-shrink-0 px-6 pb-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : assignment ? "Update Assignment" : "Create Assignment"}
          </Button>
        </div>

        {/* Resize handle */}
        <div className="absolute bottom-0 right-0 w-4 h-4 bg-gray-300 hover:bg-gray-400 cursor-se-resize flex items-center justify-center">
          <Grip className="h-3 w-3 text-gray-600" />
        </div>
      </DialogContent>
    </Dialog>
  )
}
