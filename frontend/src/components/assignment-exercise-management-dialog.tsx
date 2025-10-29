"use client"

import { getAuthHeaders } from "@/lib/utils"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Plus, Trash2, Brain, ZoomIn, ZoomOut, RotateCw, Upload } from "lucide-react"
import { toast } from "sonner"
import { Assignment, Exercise } from "@/types/assignment"

interface AssignmentExerciseManagementDialogProps {
  assignment: Assignment | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: () => void
  onUploadPdf?: () => void
}

export function AssignmentExerciseManagementDialog({ 
  assignment, 
  open, 
  onOpenChange, 
  onSave,
  onUploadPdf
}: AssignmentExerciseManagementDialogProps) {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [pdfUrl, setPdfUrl] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState("")
  const [isExtractingWithAi, setIsExtractingWithAi] = useState(false)
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)

  // Load exercises when dialog opens
  useEffect(() => {
    if (open && assignment) {
      setExercises(assignment.exercises || [])
      loadPdf()
    }
  }, [open, assignment?.id])

  const loadPdf = async () => {
    if (!assignment?.id) return

    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/pdf`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const blob = await response.blob()
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

  const addExercise = () => {
    const newExercise: Exercise = {
      id: Date.now(), // Temporary ID
      name: "",
      description: "",
      points: 0,
      evaluation_criteria: "",
      assignment_id: assignment?.id || 0,
      order: exercises.length
    }
    setExercises([...exercises, newExercise])
  }

  const updateExercise = (exerciseId: number, updates: Partial<Exercise>) => {
    setExercises(exercises.map(ex => 
      ex.id === exerciseId ? { ...ex, ...updates } : ex
    ))
  }

  const removeExercise = (exerciseId: number) => {
    setExercises(exercises.filter(ex => ex.id !== exerciseId))
  }

  const handleAiExtractExercises = () => {
    // Show confirmation dialog first
    setShowConfirmDialog(true)
  }

  const confirmAiExtractExercises = async () => {
    if (!assignment?.id) {
      toast.error("Assignment not loaded")
      return
    }

    setShowConfirmDialog(false)
    setIsExtractingWithAi(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/extract-exercises-ai`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const result = await response.json()
        if (result.exercises && result.exercises.length > 0) {
          // Replace existing exercises with AI-extracted ones
          setExercises(result.exercises.map((ex: any, index: number) => {
            // Convert percentage points to numeric values
            let points = ex.points
            if (typeof points === 'string' && points.includes('%')) {
              points = parseInt(points.replace('%', ''))
            } else if (typeof points === 'string') {
              points = parseInt(points) || 0
            }
            
            return {
              ...ex,
              id: Date.now() + index, // Temporary ID
              assignment_id: assignment.id,
              order: index,
              points: points,
              evaluation_criteria: ex.criteria ? (Array.isArray(ex.criteria) ? ex.criteria.join('\n') : ex.criteria) : ex.evaluation_criteria
            }
          }))
          toast.success(`Successfully extracted ${result.exercises.length} exercises from PDF`)
        } else {
          toast.error("No exercises could be extracted from the PDF")
        }
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to extract exercises")
      }
    } catch (error) {
      console.error("Error extracting exercises:", error)
      toast.error("Failed to extract exercises")
    } finally {
      setIsExtractingWithAi(false)
    }
  }

  const handleSave = async () => {
    if (!assignment?.id) return

    // Calculate total points
    const totalPoints = exercises.reduce((sum, ex) => sum + ex.points, 0)
    if (totalPoints !== 100) {
      toast.error(`Total points must equal 100. Current total: ${totalPoints}`)
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/exercises`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(exercises.map((ex, index) => ({
          id: ex.id,
          name: ex.name,
          description: ex.description,
          points: ex.points,
          evaluation_criteria: ex.evaluation_criteria,
          order: index
        }))),
      })

      if (response.ok) {
        toast.success("Exercises saved successfully!")
        onSave()
        onOpenChange(false)
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to save exercises")
      }
    } catch (error) {
      console.error("Error saving exercises:", error)
      toast.error("Failed to save exercises")
    }
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 300))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50))
  const handleRotate = () => setRotation(prev => (prev + 90) % 360)
  
  const handleUploadPdf = () => {
    console.log("Upload PDF button clicked!")
    if (onUploadPdf) {
      // Close this dialog and trigger the parent to open the PDF upload dialog
      onOpenChange(false)
      onUploadPdf()
    } else {
      // Fallback message if no callback is provided
      toast.info("Please use the Upload PDF button in the main assignment view to upload a new PDF")
    }
  }

  const totalPoints = exercises.reduce((sum, ex) => sum + ex.points, 0)

  if (!assignment) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-[90vw] !h-[98vh] !max-h-[98vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Manage Exercises - {assignment.name}</DialogTitle>
          <DialogDescription>
            Add and manage exercises for this assignment. Total points must equal 100.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex gap-4 overflow-hidden">
          {/* Left side - PDF Viewer */}
          <div className="w-1/2 flex flex-col gap-4">
            <Card className="flex-1">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">PDF Viewer</CardTitle>
                  <div className="flex items-center gap-2">
                    <Button variant="default" size="sm" onClick={handleUploadPdf} title="Upload PDF" className="bg-blue-600 text-white hover:bg-blue-700">
                      <Upload className="h-4 w-4 mr-1" />
                      Upload
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleZoomOut}>
                      <ZoomOut className="h-4 w-4" />
                    </Button>
                    <span className="text-sm">{zoom}%</span>
                    <Button variant="outline" size="sm" onClick={handleZoomIn}>
                      <ZoomIn className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleRotate}>
                      <RotateCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="h-full p-0">
                {assignment.pdf_file_name ? (
                  <>
                    {isLoading || isUploading ? (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-2"></div>
                          <p className="text-sm text-gray-600">Loading PDF...</p>
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
                        key={pdfUrl}
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
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">No PDF uploaded</p>
                      <p className="text-xs text-gray-500 mt-1">Upload a PDF to view it here</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right side - Exercise Management */}
          <div className="w-1/2 flex flex-col gap-4 overflow-hidden">
            <Card className="flex-1 overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Exercises</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant={totalPoints === 100 ? "default" : "destructive"}>
                      {totalPoints}/100 pts
                    </Badge>
                    {assignment.pdf_file_name && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleAiExtractExercises}
                        disabled={isExtractingWithAi}
                        className="flex items-center gap-1"
                      >
                        <Brain className="h-4 w-4" />
                        {isExtractingWithAi ? "Extracting..." : "AI Extract"}
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="h-full overflow-y-auto">
                <div className="space-y-4">
                  {exercises.map((exercise, index) => (
                    <Card key={exercise.id} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-sm">Exercise {index + 1}</CardTitle>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeExercise(exercise.id)}
                            className="text-red-600 hover:text-red-800 h-6 w-6 p-0"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-gray-700">
                            Exercise {exercise.order || index + 1}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`exercise-description-${exercise.id}`}>Description</Label>
                          <Textarea
                            id={`exercise-description-${exercise.id}`}
                            value={exercise.description}
                            onChange={(e) => updateExercise(exercise.id, { description: e.target.value })}
                            placeholder="Exercise description"
                            rows={2}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`exercise-criteria-${exercise.id}`}>Evaluation Criteria</Label>
                          <Textarea
                            id={`exercise-criteria-${exercise.id}`}
                            value={exercise.evaluation_criteria}
                            onChange={(e) => updateExercise(exercise.id, { evaluation_criteria: e.target.value })}
                            placeholder="How to evaluate this exercise"
                            rows={2}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`exercise-points-${exercise.id}`}>Points</Label>
                          <Input
                            id={`exercise-points-${exercise.id}`}
                            type="number"
                            min="0"
                            max="100"
                            value={exercise.points}
                            onChange={(e) => updateExercise(exercise.id, { points: parseInt(e.target.value) || 0 })}
                            placeholder="Points"
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  <Button
                    onClick={addExercise}
                    variant="outline"
                    className="w-full flex items-center gap-2 border-dashed"
                  >
                    <Plus className="h-4 w-4" />
                    Add Exercise
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Exercises
          </Button>
        </div>
      </DialogContent>

      {/* AI Extract Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-orange-600" />
              AI Extract Confirmation
            </DialogTitle>
            <DialogDescription>
              This action will replace all existing exercises with AI-extracted exercises from the PDF.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="text-orange-600 mt-0.5">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-orange-800">Warning</h4>
                  <p className="text-sm text-orange-700 mt-1">
                    All current exercises ({exercises.length}) will be permanently removed and replaced with AI-extracted exercises from the PDF.
                  </p>
                </div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600">
              The AI will analyze the PDF content and extract exercises automatically. 
              This action cannot be undone.
            </p>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={confirmAiExtractExercises}
              disabled={isExtractingWithAi}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              {isExtractingWithAi ? "Extracting..." : "Yes, Extract Exercises"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Dialog>
  )
}
