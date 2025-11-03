/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Submission Review Dialog Component
 * Displays PDF contents with exercise grading form side by side
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect, useMemo, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

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
import { X, ZoomIn, ZoomOut, RotateCw, FileText, Brain, Bot, Loader2 } from "lucide-react"
import { toast } from "sonner"

type GroupMember = string | { name?: string; email?: string }

type ExerciseLite = { id?: number; description?: string; points?: number; order?: number; name?: string; evaluation_criteria?: string }
interface AssignmentLite { id?: number; name?: string; exercises?: ExerciseLite[] }
interface GradeLite { exercise_id?: number; score?: number; points?: number | string; feedback?: string; comments?: string }
interface CoordinatorEval { name: string; points?: string | number; comments?: string }
interface MemberEval { name: string; points?: string | number; comments?: string }
interface PrivateEval { coordinators?: CoordinatorEval[]; members?: MemberEval[] }
interface SubmissionLite {
  id?: number
  assignment?: { name?: string } | AssignmentLite
  assignment_id?: number
  classroom?: { name?: string; course?: { name?: string; id?: number }; semester?: { name?: string; id?: number } }
  classroom_id?: number
  group?: { name?: string; members?: GroupMember[] }
  group_id?: number
  has_submission_pdf?: boolean
  has_public_pdf?: boolean
  has_private_pdf?: boolean
  private_pdf_filename?: string
  public_pdf_filename?: string
  coordinators?: string
  public_pdf_responsible_students?: string
  grade_breakdown?: GradeLite[]
  private_report_evaluation?: PrivateEval
  meeting_notes?: boolean
}

interface SubmissionReviewDialogProps {
  submission: SubmissionLite // Submission object with PDF and exercise data
  assignment: AssignmentLite // Assignment object with exercises
  open: boolean
  onOpenChange: (open: boolean) => void
  onGradeSubmit?: (grades: GradeLite[], totalScore: number) => void
  onViewPdf?: () => void // Optional callback to open dedicated PDF viewer
  onSubmissionUpdate?: (updatedSubmission: SubmissionLite) => void // Callback when submission is updated
}

export function SubmissionReviewDialog({ 
  submission, 
  assignment,
  open, 
  onOpenChange, 
  onGradeSubmit,
  onSubmissionUpdate
}: SubmissionReviewDialogProps) {
  const [zoom, setZoom] = useState(100)
  const [grades, setGrades] = useState<any[]>([])
  const [isAiEvaluating, setIsAiEvaluating] = useState(false)
  const [isPublicReportEvaluating, setIsPublicReportEvaluating] = useState(false)
  const [isEvaluatingPrivate, setIsEvaluatingPrivate] = useState(false)
  const [aiResults, setAiResults] = useState<any>(null)
  const [showJsonDialog, setShowJsonDialog] = useState(false)
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
  // Public report grading fields
  const [publicReportPoints, setPublicReportPoints] = useState<string>("")
  const [publicReportComments, setPublicReportComments] = useState<string>("")
  
  // State for presence flags
  const [hasSubmissionPdf, setHasSubmissionPdf] = useState<boolean>(false)
  const [hasPrivatePdf, setHasPrivatePdf] = useState<boolean>(false)
  const [hasPublicPdf, setHasPublicPdf] = useState<boolean>(false)
  const [hasMeetingNotes, setHasMeetingNotes] = useState<boolean>(false)
  
  // State for manual private report evaluation
  const [manualEvaluation, setManualEvaluation] = useState<{
    coordinators: Array<{name: string, points: string, comments: string}>,
    members: Array<{name: string, points: string, comments: string}>
  }>({
    coordinators: [],
    members: []
  })
  
  // Ref to track if manual evaluation has been initialized
  const initializedRef = useRef(false)

  // Parse coordinator names from JSON strings
  const privateCoordinators = useMemo(() => {
    return submission?.coordinators 
      ? JSON.parse(submission.coordinators) 
      : []
  }, [submission?.coordinators])
  
  const publicCoordinators = useMemo(() => {
    return submission?.public_pdf_responsible_students 
      ? JSON.parse(submission.public_pdf_responsible_students) 
      : []
  }, [submission?.public_pdf_responsible_students])

  // Initialize manual evaluation state when dialog opens
  useEffect(() => {
    if (open && submission && !initializedRef.current) {
      
      // Initialize coordinators - try multiple sources
      let coordinators: Array<{name: string, points: string, comments: string}> = []
      
      // First try: use saved evaluation data if available
      if (submission.private_report_evaluation?.coordinators?.length > 0) {
        coordinators = submission.private_report_evaluation.coordinators.map((coord: any) => ({
          name: coord.name,
          points: coord.points?.toString() || '',
          comments: coord.comments || ''
        }))
      }
      // Second try: submission.coordinators field
      else if (privateCoordinators.length > 0) {
        coordinators = privateCoordinators.map((name: string) => {
          // Check if we have saved evaluation data for this coordinator
          const savedCoordinator = submission.private_report_evaluation?.coordinators?.find(
            (c: any) => c.name === name
          )
          
          const result = {
            name,
            points: savedCoordinator?.points?.toString() || '',
            comments: savedCoordinator?.comments || ''
          }
          return result
        })
      }
      // Second try: if no coordinators field, try to get from group members (first 1-2 members as coordinators)
      else if (submission.group?.members && Array.isArray(submission.group.members)) {
        const groupMembers = submission.group.members.slice(0, 2) // Take first 2 members as coordinators
        coordinators = (groupMembers as GroupMember[]).map((member: GroupMember) => ({
          name: typeof member === 'string' ? member : (member.name || member.email || 'Unknown'),
          points: '',
          comments: ''
        }))
      }
      // Third try: create default coordinator entry
      else {
        coordinators = [{
          name: 'No coordinators found',
          points: '',
          comments: ''
        }]
      }
      
      // Initialize members - try multiple sources
      let members: Array<{name: string, points: string, comments: string}> = []
      
      // First try: use saved evaluation data if available
      if (submission.private_report_evaluation?.members?.length > 0) {
        members = submission.private_report_evaluation.members.map((member: any) => ({
          name: member.name,
          points: member.points?.toString() || '',
          comments: member.comments || ''
        }))
      }
      // Second try: submission.group?.members
      else if (submission.group?.members && Array.isArray(submission.group.members)) {
        // Get coordinator names for filtering
        const coordinatorNames = coordinators.map(c => c.name)
        members = (submission.group.members as GroupMember[])
          .filter((member: GroupMember) => {
            const memberName = typeof member === 'string' ? member : (member.name || member.email || 'Unknown')
            return !coordinatorNames.includes(memberName)
          })
          .map((member: GroupMember) => {
            const memberName = typeof member === 'string' ? member : (member.name || member.email || 'Unknown')
            // Check if we have saved evaluation data for this member
            const savedMember = submission.private_report_evaluation?.members?.find(
              (m: any) => m.name === memberName
            )
            const result = {
              name: memberName,
              points: savedMember?.points?.toString() || '',
              comments: savedMember?.comments || ''
            }
            return result
          })
      }
      // Second try: if no group members, use coordinators as fallback
      else if (coordinators.length > 0 && coordinators[0].name !== 'No coordinators found') {
        members = coordinators.map(coord => {
          // Check if we have saved evaluation data for this member
          const savedMember = submission.private_report_evaluation?.members?.find(
            (m: any) => m.name === coord.name
          )
          
          return {
            name: coord.name,
            points: savedMember?.points?.toString() || '',
            comments: savedMember?.comments || ''
          }
        })
      }
      // Third try: if still no members, create a default entry
      else {
        members = [{
          name: 'No members found',
          points: '',
          comments: ''
        }]
      }
      
      
      setManualEvaluation({
        coordinators,
        members
      })
      
      initializedRef.current = true
    }
    
    // Reset initialization flag when dialog closes
    if (!open) {
      initializedRef.current = false
    }
  }, [open, submission, privateCoordinators, submission?.private_report_evaluation])

  // Create PDF URLs using the download endpoints
  useEffect(() => {
    if (submission?.id && submission?.has_submission_pdf) {
      // Use the PDF download endpoint instead of blob data
      const pdfUrl = `/api/v1/submissions/${submission.id}/pdf`
      setPdfBlobUrl(pdfUrl)
    } else {
      setPdfBlobUrl(null)
    }
  }, [submission?.id, submission?.has_submission_pdf])

  // Initialize grades and flags when dialog opens
  useEffect(() => {
    if (open && assignment?.exercises) {
      const initialGrades = assignment.exercises.map((exercise: any, index: number) => {
        // Check if there's existing grade data for this exercise
        const existingGrade = submission?.grade_breakdown?.find(
          (grade: any) => grade.exercise_id === exercise.id
        )
        
        return {
          exercise_id: exercise.id,
          exercise_name: exercise.description || exercise.name || `Exercise ${index + 1}`,
          max_points: exercise.points,
          points: existingGrade?.score || existingGrade?.points || 0,
          comments: existingGrade?.feedback || existingGrade?.comments || ""
        }
      })
      setGrades(initialGrades)
      
      // Initialize presence flags from backend data (now provided directly by the API)
      setHasSubmissionPdf(Boolean(submission?.has_submission_pdf))
      setHasPrivatePdf(Boolean(submission?.has_private_pdf))
      setHasPublicPdf(Boolean(submission?.has_public_pdf))
      setHasMeetingNotes(Boolean(submission?.meeting_notes))
      
      // Initialize public report grade from ai_feedback
      if (submission?.ai_feedback) {
        try {
          const aiFeedback = typeof submission.ai_feedback === 'string' 
            ? JSON.parse(submission.ai_feedback) 
            : submission.ai_feedback
          
          const publicReport = aiFeedback?.public_report
          if (publicReport) {
            setPublicReportPoints(publicReport.points?.toString() || '')
            setPublicReportComments(publicReport.comments || '')
          }
        } catch (e) {
          console.warn('Failed to parse ai_feedback for public report:', e)
        }
      }
    }
  }, [open, assignment, submission?.grade_breakdown, submission?.meeting_notes, submission?.has_submission_pdf, submission?.has_private_pdf, submission?.has_public_pdf, submission?.ai_feedback])



  // Clean up when dialog closes
  const handleOpenChange = (newOpen: boolean) => {
    onOpenChange(newOpen)
  }

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50))
  const handleResetZoom = () => setZoom(100)

  // Handle grade changes
  const handleGradeChange = (index: number, field: string, value: any) => {
    setGrades(prev => prev.map((grade, i) => 
      i === index ? { ...grade, [field]: value } : grade
    ))
  }

  // Handle decimal point input with validation (0-10 range)
  const handlePointsChange = (index: number, value: string) => {
    // Allow empty string, digits, and up to 2 decimal places
    if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
      const numericValue = value === '' ? 0 : parseFloat(value)
      
      // Validate that the value is between 0 and 10
      if (numericValue >= 0 && numericValue <= 10) {
        handleGradeChange(index, "points", value)
      } else if (value === '') {
        // Allow empty for initial state, but will validate on submit
        handleGradeChange(index, "points", value)
      }
    }
  }

  // Handle toggle flag changes (only for meeting notes now)
  const handleToggleFlag = async (flagName: string, checked: boolean) => {
    if (!submission?.id) return
    
    // Only allow meeting notes to be toggled, PDF presence is auto-determined
    if (flagName !== 'meeting_notes') {
      console.warn(`Cannot toggle ${flagName} - this field is auto-determined from PDF data`)
      return
    }
    
    try {
      const response = await fetch(`/api/v1/submissions/${submission.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ [flagName]: checked })
      })
      
      if (response.ok) {
        // Update local state optimistically
        switch (flagName) {
          case 'meeting_notes':
            setHasMeetingNotes(checked)
            break
        }
        
        // Update the parent component's submission object
        if (onSubmissionUpdate) {
          const updatedSubmission = {
            ...submission,
            [flagName]: checked
          }
          onSubmissionUpdate(updatedSubmission)
        }
        
        toast.success(`${flagName.replace(/_/g, ' ')} updated successfully`)
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to update flag')
      }
    } catch (error: any) {
      console.error('Error updating flag:', error)
      toast.error(error.message || 'Failed to update flag')
    }
  }

  // Handle public report points input (0-10 with optional decimals)
  const handlePublicReportPointsChange = (value: string) => {
    if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
      const numericValue = value === '' ? 0 : parseFloat(value)
      if (numericValue >= 0 && numericValue <= 10) {
        setPublicReportPoints(value)
        return
      }
      if (value === '') {
        setPublicReportPoints(value)
      }
    }
  }

  // AI Evaluation function
  const handleAiEvaluation = async () => {
    if (!submission?.has_submission_pdf || !assignment?.exercises) {
      toast.error("No PDF or exercises found for AI evaluation")
      return
    }

    setIsAiEvaluating(true)
    try {
      const response = await fetch(`/api/v1/submissions/${submission.id}/ai-evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        }
      })

      if (response.ok) {
        const results = await response.json()
        
        // Store AI results
        setAiResults(results)
        
        // Update grades with AI suggestions
        const updatedGrades = grades.map((grade, index) => {
          // Find the corresponding exercise
          const exercise = assignment?.exercises?.find(ex => ex.id === grade.exercise_id)
          if (!exercise) return grade
          
          // Try to find AI suggestion by matching exercise description/name
          const aiSuggestion = results.exercises?.find((suggestion: any) => {
            // Try multiple matching strategies
            const suggestionName = suggestion.name?.toLowerCase() || ''
            const exerciseDesc = exercise.description?.toLowerCase() || ''
            const exerciseOrder = exercise.order || 0
            
            // Match by description similarity or by order/index
            return suggestionName.includes(exerciseDesc.substring(0, 20)) ||
                   suggestionName.includes(exerciseDesc.substring(exerciseDesc.length - 20)) ||
                   index === exerciseOrder - 1
          })
          
          if (aiSuggestion) {
            return {
              ...grade,
              points: aiSuggestion.points?.toString() || grade.points,
              comments: aiSuggestion.comments || grade.comments
            }
          }
          return grade
        })
        
        setGrades(updatedGrades)
        
        toast.success("AI evaluation completed and fields populated!")
      } else {
        const errorData = await response.json()
        toast.error(`AI evaluation failed: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error("AI evaluation error:", error)
      toast.error("Failed to perform AI evaluation. Please try again.")
    } finally {
      setIsAiEvaluating(false)
    }
  }

  // AI Public Report Evaluation function
  const handlePublicReportEvaluation = async () => {
    if (!submission?.has_public_pdf) {
      toast.error("No public report PDF found for AI evaluation")
      return
    }

    setIsPublicReportEvaluating(true)
    try {
      const response = await fetch(`/api/v1/submissions/${submission.id}/ai-evaluate-public-report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          language: "catalan",
          use_vision: true
        })
      })

      if (response.ok) {
        const results = await response.json()
        
        // Store public report AI results
        setAiResults({
          type: "public_report",
          ...results
        })
        // Populate public report fields
        if (typeof results.points !== 'undefined') {
          setPublicReportPoints(results.points?.toString?.() || `${results.points}`)
        }
        if (typeof results.comments !== 'undefined') {
          setPublicReportComments(results.comments || '')
        }
        
        // Show AI results dialog - REMOVED
        // setShowAiResultsDialog(true)
        
        toast.success("AI public report evaluation completed successfully!")
      } else {
        const errorData = await response.json()
        toast.error(`AI public report evaluation failed: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error("AI public report evaluation error:", error)
      toast.error("Failed to perform AI public report evaluation. Try again")
    } finally {
      setIsPublicReportEvaluating(false)
    }
  }

  const handleAiEvaluatePrivateReport = async () => {
    if (!submission?.has_private_pdf) {
      toast.error("No private report PDF found for AI evaluation")
      return
    }

    setIsEvaluatingPrivate(true)
    try {
      const response = await fetch(`/api/v1/submissions/${submission.id}/ai-evaluate-private-report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const results = await response.json()
        
        // Store private report AI results
        setAiResults({
          type: "private_report",
          ...results
        })
        
        // Populate manual evaluation fields with AI results
        if (results.coordinators && results.members) {
          setManualEvaluation(prev => {
            // First, populate coordinators with AI coordinator results
            const updatedCoordinators = prev.coordinators.map((coord, _index) => {
              const aiCoord = results.coordinators.find((c: any) => c.name === coord.name)
              if (aiCoord) {
                return {
                  ...coord,
                  points: aiCoord.points?.toString() || coord.points,
                  comments: aiCoord.comments || coord.comments
                }
              }
              return coord
            })
            
            // Calculate max points from non-coordinator members for coordinator-members
            const coordinatorNames = prev.coordinators.map(c => c.name)
            const nonCoordinatorMembers = results.members.filter((m: any) => 
              !coordinatorNames.includes(m.name)
            )
            const maxPoints = nonCoordinatorMembers.length > 0 
              ? Math.max(...nonCoordinatorMembers.map((m: any) => parseFloat(m.points) || 0))
              : 0
            
            // Populate members - use max points for coordinator-members, AI results for others
            const updatedMembers = prev.members.map((member, _index) => {
              const aiMember = results.members.find((m: any) => m.name === member.name)
              const isCoordinator = coordinatorNames.includes(member.name)
              
              if (aiMember) {
                if (isCoordinator) {
                  // For coordinator-members, use max points from other members
                  return {
                    ...member,
                    points: maxPoints.toString(),
                    comments: aiMember.comments || member.comments || `Points assigned based on maximum team member performance (${maxPoints})`
                  }
                } else {
                  // For non-coordinator members, use AI results
                  return {
                    ...member,
                    points: aiMember.points?.toString() || member.points,
                    comments: aiMember.comments || member.comments
                  }
                }
              }
              return member
            })
            
            return {
              coordinators: updatedCoordinators,
              members: updatedMembers
            }
          })
        }
        
        toast.success("AI private report evaluation completed and fields populated!")
      } else {
        const errorData = await response.json()
        toast.error(errorData.detail || "Failed to perform AI private report evaluation")
      }
    } catch (error) {
      console.error("AI private report evaluation error:", error)
      toast.error("Failed to perform AI private report evaluation. Try again")
    } finally {
      setIsEvaluatingPrivate(false)
    }
  }

  const handleManualEvaluationChange = (type: 'coordinators' | 'members', index: number, field: 'points' | 'comments', value: string) => {
    setManualEvaluation(prev => ({
      ...prev,
      [type]: prev[type].map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }))
  }

  const handleSavePrivateReportEvaluation = async () => {
    try {
      // Create a summary of the evaluation for storage
      const evaluationSummary = {
        coordinators: manualEvaluation.coordinators.filter(c => c.points || c.comments),
        members: manualEvaluation.members.filter(m => m.points || m.comments),
        ai_results: aiResults?.type === 'private_report' ? {
          coordinators: aiResults.coordinators || [],
          members: aiResults.members || []
        } : null,
        evaluation_date: new Date().toISOString(),
        ai_model: aiResults?.ai_model || 'manual'
      }

      // Send the evaluation results to the backend
      const response = await fetch(`/api/v1/submissions/${submission.id}/private-report-evaluation`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(evaluationSummary)
      })

      if (response.ok) {
        toast.success("Private report evaluation saved successfully!")
        
        // Update the parent component's submission object
        if (onSubmissionUpdate) {
          const updatedSubmission = {
            ...submission,
            private_report_evaluation: evaluationSummary
          }
          onSubmissionUpdate(updatedSubmission)
        }
        
        // Close the dialog - REMOVED
        // setShowAiResultsDialog(false)
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to save evaluation')
      }
      
    } catch (error: any) {
      console.error("Error saving private report evaluation:", error)
      toast.error(`Failed to save evaluation: ${error.message}`)
    }
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate all grades are between 0-10
    const invalidGrades = grades.filter(grade => {
      const points = parseFloat(grade.points.toString())
      return isNaN(points) || points < 0 || points > 10
    })
    
    if (invalidGrades.length > 0) {
      toast.error("All grades must be between 0 and 10 points")
      return
    }
    
    // Convert string points to numbers and calculate total using sumproduct
    const processedGrades = grades.map(grade => ({
      ...grade,
      points: parseFloat(grade.points.toString()) || 0
    }))
    
    // Calculate total score using sumproduct normalized by sum of (max_score * 10) for each exercise
    const sumproduct = processedGrades.reduce((sum, grade) => {
      return sum + (grade.points * grade.max_points)
    }, 0)
    const maxPossibleScore = processedGrades.reduce((sum, grade) => {
      return sum + (grade.max_points * 10)
    }, 0)
    // Convert percentage to 0-10 scale (90% = 9.0 out of 10)
    const percentageScore = (sumproduct / maxPossibleScore) * 100
    const totalScore = (percentageScore / 100) * 10
    
    console.log(`=== FRONTEND GRADE SUBMISSION ===`)
    console.log(`Submission ID: ${submission.id}`)
    console.log(`Total Score: ${totalScore}`)
    console.log(`Grade Breakdown: ${processedGrades}`)
    
    try {
      // Send grades to backend
      const response = await fetch(`/api/v1/submissions/${submission.id}/grade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          total_score: totalScore,
          teacher_feedback: `Grades submitted on ${new Date().toLocaleString()}`,
          grade_breakdown: processedGrades
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to save grades')
      }
      
      const result = await response.json()
      console.log('Grade submission result:', result)
      
      toast.success("Grades saved successfully!")
      
      // Call the onGradeSubmit callback if provided
      if (onGradeSubmit) {
        onGradeSubmit(processedGrades, totalScore)
      }
      
    } catch (error: any) {
      console.error('Error saving grades:', error)
      toast.error(error.message || 'Failed to save grades')
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent 
        className="overflow-hidden flex flex-col"
        style={{
          maxWidth: '95vw',
          width: '95vw',
          height: '98vh',
          maxHeight: '98vh'
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center justify-between">
            <span>Review Submission: {submission?.assignment?.name || `Assignment ${submission?.assignment_id}`}</span>
            <div className="flex items-center gap-2">
              {/* Zoom Controls */}
              <div className="flex items-center gap-1 text-sm">
                <Button variant="ghost" size="sm" onClick={handleZoomOut} disabled={zoom <= 50}>
                  <ZoomOut className="h-3 w-3" />
                </Button>
                <span className="min-w-[3rem] text-center">{zoom}%</span>
                <Button variant="ghost" size="sm" onClick={handleZoomIn} disabled={zoom >= 200}>
                  <ZoomIn className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" onClick={handleResetZoom}>
                  <RotateCw className="h-3 w-3" />
                </Button>
              </div>
              
              
            </div>
          </DialogTitle>
          <DialogDescription>
            Assignment: {submission?.assignment?.name || `Assignment ${submission?.assignment_id}`} / 
            Classroom: {submission?.classroom?.name || `Classroom ${submission?.classroom_id}`} / 
            Group: {submission?.group?.name || `Group ${submission?.group_id}`} / 
            Course: {submission?.classroom?.course?.name || `Course ${submission?.classroom?.course_id}`} / 
            Semester: {submission?.classroom?.semester?.name || `Semester ${submission?.classroom?.semester_id}`}
            {(submission?.private_pdf_filename || submission?.public_pdf_filename) && (
              <>
                <br />
                <span className="text-sm">
                  {submission?.private_pdf_filename && (
                    <>
                      Private PDF: {submission.private_pdf_filename}
                      {submission?.coordinators && (
                        <span className="text-gray-500 ml-2">
                          (coordinators: {JSON.parse(submission.coordinators).join(', ')})
                        </span>
                      )}
                    </>
                  )}
                  {submission?.private_pdf_filename && submission?.public_pdf_filename && <br />}
                  {submission?.public_pdf_filename && (
                    <>
                      Public PDF: {submission.public_pdf_filename}
                      {submission?.public_pdf_responsible_students && (
                        <span className="text-gray-500 ml-2">
                          (coordinators: {JSON.parse(submission.public_pdf_responsible_students).join(', ')})
                        </span>
                      )}
                    </>
                  )}
                </span>
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        {/* Main Content - Unified Accordion Layout */}
        <div className="flex-1 overflow-auto">
          <Accordion type="multiple" className="w-full" defaultValue={["exercise-grading"]}>
            
            {/* Exercise Grading Section */}
            <AccordionItem value="exercise-grading">
              <AccordionTrigger className="hover:no-underline justify-start">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-900">Exercise Grading</span>
                  {submission?.has_submission_pdf && (
                    <span className="text-xs text-green-600 font-medium">(PDF Available)</span>
                  )}
                </div>
              </AccordionTrigger>
              <AccordionContent className="p-0">
                <div className="flex gap-6 h-[700px]">
                  {/* PDF Viewer (60%) */}
                  <div className="flex-[3] min-w-0">
                    <div className="h-full border border-gray-200 rounded">
                      {submission?.has_submission_pdf ? (
                        pdfBlobUrl ? (
                          <div className="h-full overflow-auto">
                            <object
                              data={pdfBlobUrl}
                              type="application/pdf"
                              width="100%"
                              height="800px"
                              style={{ border: 'none', minHeight: '800px' }}
                              title="Main Submission PDF"
                            >
                              <iframe
                                src={pdfBlobUrl}
                                width="100%"
                                height="800px"
                                style={{ border: 'none', minHeight: '800px' }}
                                title="Main Submission PDF Fallback"
                              />
                            </object>
                          </div>
                        ) : (
                          <div className="p-4 text-center text-gray-500">
                            <p>Loading PDF...</p>
                          </div>
                        )
                      ) : (
                        <div className="p-8 text-center text-gray-500">
                          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                          <p className="text-lg">No PDF uploaded</p>
                          <p className="text-sm text-gray-400 mt-2">Upload a PDF to view it here</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Grading Form (40%) */}
                  <div className="flex-[2] min-w-0 overflow-y-auto">
                    <div className="p-4">
                      {/* Submission PDF Present - Read Only */}
                      <div className="mb-4 rounded-md border p-3 bg-blue-50">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-blue-900">Submission PDF present</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-semibold ${hasSubmissionPdf ? 'text-green-600' : 'text-red-600'}`}>
                              {hasSubmissionPdf ? '✓ Yes' : '✗ No'}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <form onSubmit={handleSubmit} className="space-y-4">
                        {grades.length > 0 ? (
                          grades.map((grade, index) => (
                          <Card key={index}>
                            <CardHeader>
                              <CardTitle className="text-md">
                                {grade.exercise_name} ({grade.max_points} points)
                              </CardTitle>
                              {assignment?.exercises?.[index]?.description && (
                                <CardDescription>
                                  {assignment.exercises[index].description}
                                </CardDescription>
                              )}
                              {assignment?.exercises?.[index]?.evaluation_criteria && (
                                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-2 rounded mt-2">
                                  <p className="text-xs font-medium text-yellow-800 mb-1">
                                    Evaluation Criteria:
                                  </p>
                                  <pre className="text-xs text-yellow-700 whitespace-pre-wrap font-sans">
                                    {assignment.exercises[index].evaluation_criteria}
                                  </pre>
                                </div>
                              )}
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label htmlFor={`points-${index}`}>Points:</Label>
                                <Input
                                  id={`points-${index}`}
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  max="10"
                                  value={grade.points}
                                  onChange={(e) => handlePointsChange(index, e.target.value)}
                                  placeholder="0.00-10.00"
                                  className="w-24"
                                />
                                <span className="text-sm text-gray-500">
                                  (0-10 scale)
                                </span>
                              </div>
                              <div>
                                <Label htmlFor={`comments-${index}`}>Comments:</Label>
                                <Textarea
                                  id={`comments-${index}`}
                                  value={grade.comments || ""}
                                  onChange={(e) =>
                                    handleGradeChange(
                                      index,
                                      "comments",
                                      e.target.value
                                    )
                                  }
                                  rows={2}
                                  placeholder="Add comments for this exercise"
                                />
                              </div>
                            </CardContent>
                          </Card>
                          ))
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            <FileText className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                            <p className="text-lg font-medium mb-2">No Exercises Found</p>
                            <p className="text-sm">
                              This assignment doesn&apos;t have any exercises defined yet.
                            </p>
                            <p className="text-sm mt-1">
                              Please add exercises to the assignment before grading submissions.
                            </p>
                          </div>
                        )}
                        
                        {/* AI Submission Autofill Button */}
                        <Button 
                          type="button"
                          variant="outline" 
                          onClick={handleAiEvaluation} 
                          disabled={!submission?.has_submission_pdf || isAiEvaluating}
                          className="w-full bg-purple-50 hover:bg-purple-100 border-purple-200 mb-2"
                        >
                          <Brain className="h-4 w-4 mr-2" />
                          {isAiEvaluating ? "Evaluating..." : "AI Submission Autofill"}
                        </Button>
                        
                        {grades.length > 0 && (
                          <Button type="submit" className="w-full">
                            Save Grades
                          </Button>
                        )}
                      </form>
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Private Report Grading Section */}
            <AccordionItem value="private-report-grading">
              <AccordionTrigger className="hover:no-underline justify-start">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-semibold text-gray-900">Private Report Grading</span>
                  {submission?.has_private_pdf && (
                    <span className="text-xs text-green-600 font-medium">
                      (Available{submission?.coordinators ? 
                        ` - ${privateCoordinators.join(', ')}` : ''})
                    </span>
                  )}
                </div>
              </AccordionTrigger>
              <AccordionContent className="p-0">
                <div className="flex gap-6 h-[700px]">
                  {/* PDF Viewer (60%) */}
                  <div className="flex-[3] min-w-0">
                    <div className="h-full border border-gray-200 rounded">
                      {submission?.has_private_pdf ? (
                        <div className="h-full overflow-auto">
                          <object
                            data={`/api/v1/submissions/${submission.id}/private-pdf`}
                            type="application/pdf"
                            width="100%"
                            height="800px"
                            style={{ border: 'none', minHeight: '800px' }}
                            title="Private Report PDF"
                          >
                            <iframe
                              src={`/api/v1/submissions/${submission.id}/private-pdf`}
                              width="100%"
                              height="800px"
                              style={{ border: 'none', minHeight: '800px' }}
                              title="Private Report PDF Fallback"
                            />
                          </object>
                        </div>
                      ) : (
                        <div className="p-8 text-center text-gray-500">
                          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                          <p className="text-lg">No private report uploaded</p>
                          <p className="text-sm text-gray-400 mt-2">Upload a private report to view it here</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Grading Form (40%) */}
                  <div className="flex-[2] min-w-0 overflow-y-auto">
                    <div className="p-4">
                      {/* Private Report Present - Read Only */}
                      <div className="mb-4 rounded-md border p-3 bg-purple-50">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-purple-900">Private report present</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-semibold ${hasPrivatePdf ? 'text-green-600' : 'text-red-600'}`}>
                              {hasPrivatePdf ? '✓ Yes' : '✗ No'}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        {/* Manual Evaluation Section */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-md">
                              Manual Private Report Evaluation
                            </CardTitle>
                            <CardDescription>
                              Enter points and comments for coordinators and team members
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {/* Coordinators Manual Entry */}
                            <div className="space-y-3">
                              <h4 className="font-medium text-md text-gray-700">Coordinators</h4>
                              {manualEvaluation.coordinators.length === 0 ? (
                                <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg">
                                  No coordinators found. Check if submission has coordinators data.
                                </div>
                              ) : (
                                manualEvaluation.coordinators.map((coordinator, index) => (
                                  <div key={index} className="border rounded-lg p-4 bg-gray-50">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                      <div>
                                        <Label className="text-sm font-medium text-gray-700">Coordinator Name</Label>
                                        <div className="text-sm italic text-gray-600 mt-1">
                                          {coordinator.name}
                                        </div>
                                      </div>
                                      <div>
                                        <Label htmlFor={`coordinator-points-${index}`} className="text-sm font-medium text-gray-700">Points (0-10)</Label>
                                        <Input
                                          id={`coordinator-points-${index}`}
                                          type="number"
                                          min="0"
                                          max="10"
                                          step="0.1"
                                          placeholder="0.0"
                                          value={coordinator.points}
                                          onChange={(e) => handleManualEvaluationChange('coordinators', index, 'points', e.target.value)}
                                          className="w-full bg-white mt-1"
                                        />
                                      </div>
                                      <div>
                                        <Label htmlFor={`coordinator-comments-${index}`} className="text-sm font-medium text-gray-700">Comments</Label>
                                        <Textarea
                                          id={`coordinator-comments-${index}`}
                                          rows={2}
                                          placeholder="Enter evaluation comments..."
                                          value={coordinator.comments}
                                          onChange={(e) => handleManualEvaluationChange('coordinators', index, 'comments', e.target.value)}
                                          className="w-full bg-white mt-1"
                                        />
                                      </div>
                                    </div>
                                  </div>
                                ))
                              )}
                            </div>

                            {/* Members Manual Entry */}
                            <div className="space-y-3">
                              <h4 className="font-medium text-md text-gray-700">Team Members</h4>
                              {manualEvaluation.members.length === 0 ? (
                                <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg">
                                  No team members found. Check if submission has group data.
                                </div>
                              ) : (
                                manualEvaluation.members.map((member, index) => (
                                  <div key={index} className="border rounded-lg p-4 bg-gray-50">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                      <div>
                                        <Label className="text-sm font-medium text-gray-700">Member Name</Label>
                                        <div className="text-sm italic text-gray-600 mt-1">
                                          {member.name}
                                        </div>
                                      </div>
                                      <div>
                                        <Label htmlFor={`member-points-${index}`} className="text-sm font-medium text-gray-700">Points (0-10)</Label>
                                        <Input
                                          id={`member-points-${index}`}
                                          type="number"
                                          min="0"
                                          max="10"
                                          step="0.1"
                                          placeholder="0.0"
                                          value={member.points}
                                          onChange={(e) => handleManualEvaluationChange('members', index, 'points', e.target.value)}
                                          className="w-full bg-white mt-1"
                                        />
                                      </div>
                                      <div>
                                        <Label htmlFor={`member-comments-${index}`} className="text-sm font-medium text-gray-700">Comments</Label>
                                        <Textarea
                                          id={`member-comments-${index}`}
                                          rows={2}
                                          placeholder="Enter evaluation comments..."
                                          value={member.comments}
                                          onChange={(e) => handleManualEvaluationChange('members', index, 'comments', e.target.value)}
                                          className="w-full bg-white mt-1"
                                        />
                                      </div>
                                    </div>
                                  </div>
                                ))
                              )}
                            </div>
                          </CardContent>
                        </Card>
                        
              <div className="flex gap-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  className="flex-1"
                  onClick={handleAiEvaluatePrivateReport}
                  disabled={!submission?.has_private_pdf || isEvaluatingPrivate}
                >
                  {isEvaluatingPrivate ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Evaluating...
                    </>
                  ) : (
                    <>
                      <Bot className="h-4 w-4 mr-2" />
                      AI Private Report Autofill
                    </>
                  )}
                </Button>
                <Button 
                  type="button" 
                  variant="default" 
                  onClick={handleSavePrivateReportEvaluation}
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                >
                  Save Private Report Evaluation
                </Button>
              </div>
                      </div>
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Public Report Grading Section */}
            <AccordionItem value="public-report-grading">
              <AccordionTrigger className="hover:no-underline justify-start">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-semibold text-gray-900">Public Report Grading</span>
                  {submission?.has_public_pdf && (
                    <span className="text-xs text-green-600 font-medium">
                      (Available{submission?.public_pdf_responsible_students ? 
                        ` - ${publicCoordinators.join(', ')}` : ''})
                    </span>
                  )}
                </div>
              </AccordionTrigger>
              <AccordionContent className="p-0">
                <div className="flex gap-6 h-[700px]">
                  {/* PDF Viewer (60%) */}
                  <div className="flex-[3] min-w-0">
                    <div className="h-full border border-gray-200 rounded">
                      {submission?.has_public_pdf ? (
                        <div className="h-full overflow-auto">
                          <object
                            data={`/api/v1/submissions/${submission.id}/public-pdf`}
                            type="application/pdf"
                            width="100%"
                            height="800px"
                            style={{ border: 'none', minHeight: '800px' }}
                            title="Public Report PDF"
                          >
                            <iframe
                              src={`/api/v1/submissions/${submission.id}/public-pdf`}
                              width="100%"
                              height="800px"
                              style={{ border: 'none', minHeight: '800px' }}
                              title="Public Report PDF Fallback"
                            />
                          </object>
                        </div>
                      ) : (
                        <div className="p-8 text-center text-gray-500">
                          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                          <p className="text-lg">No public report uploaded</p>
                          <p className="text-sm text-gray-400 mt-2">Upload a public report to view it here</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Grading Form (40%) */}
                  <div className="flex-[2] min-w-0 overflow-y-auto">
                    <div className="p-4">
                      {/* Public Report and Meeting Notes Toggles */}
                      <div className="mb-4 space-y-3">
                        <div className="rounded-md border p-3 bg-green-50">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-green-900">Public report present</span>
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-semibold ${hasPublicPdf ? 'text-green-600' : 'text-red-600'}`}>
                                {hasPublicPdf ? '✓ Yes' : '✗ No'}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="rounded-md border p-3 bg-green-50">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-green-900">Meeting notes present</span>
                            <Switch
                              checked={hasMeetingNotes}
                              onCheckedChange={(checked) => handleToggleFlag('meeting_notes', checked)}
                            />
                          </div>
                        </div>
                      </div>
                      
                      <form className="space-y-4" onSubmit={(e) => { e.preventDefault() }}>
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-md">
                              Public Report Evaluation
                            </CardTitle>
                            <CardDescription>
                              Grade the quality and completeness of the public report
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <Label htmlFor="public-report-points">Points:</Label>
                              <Input
                                id="public-report-points"
                            type="text"
                            placeholder="0.0-10.0"
                            className="w-24"
                            value={publicReportPoints}
                            onChange={(e) => handlePublicReportPointsChange(e.target.value)}
                              />
                              <span className="text-sm text-gray-500">
                                (0-10 scale)
                              </span>
                            </div>
                            <div>
                              <Label htmlFor="public-report-comments">Comments:</Label>
                              <Textarea
                                id="public-report-comments"
                                rows={3}
                            placeholder="Add comments about the public report quality, completeness, presentation, etc."
                            value={publicReportComments}
                            onChange={(e) => setPublicReportComments(e.target.value)}
                              />
                            </div>
                          </CardContent>
                        </Card>
                        
                        {/* AI Public Report Autofill Button */}
                        <Button 
                          type="button"
                          variant="outline" 
                          onClick={handlePublicReportEvaluation} 
                          disabled={!submission?.has_public_pdf || isPublicReportEvaluating}
                          className="w-full bg-green-50 hover:bg-green-100 border-green-200 mb-2"
                        >
                          <Brain className="h-4 w-4 mr-2" />
                          {isPublicReportEvaluating ? "Evaluating..." : "AI Public Report Autofill"}
                        </Button>
                        
                        <Button 
                          type="button" 
                          className="w-full"
                          onClick={async () => {
                            if (!submission?.id) return
                            // Convert points to float safely
                            const pointsNum = parseFloat(publicReportPoints || '0')
                            if (isNaN(pointsNum) || pointsNum < 0 || pointsNum > 10) {
                              toast.error('Points must be a number between 0 and 10')
                              return
                            }
                            try {
                              console.log(`=== FRONTEND PUBLIC REPORT GRADE SAVE ===`)
                              console.log(`Submission ID: ${submission.id}`)
                              console.log(`Points: ${pointsNum}`)
                              console.log(`Comments: ${publicReportComments}`)
                              
                              const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                              const res = await fetch(`${API_BASE_URL}/api/v1/submissions/${submission.id}/public-report-grade`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                  ...getAuthHeaders(),
                                },
                                body: JSON.stringify({ points: pointsNum, comments: publicReportComments })
                              })
                              if (!res.ok) {
                                const err = await res.json().catch(() => ({}))
                                throw new Error(err.detail || 'Failed to save')
                              }
                              
                              // Update local submission state with saved data
                              if (onSubmissionUpdate && submission) {
                                try {
                                  // Parse existing ai_feedback or create new object
                                  let aiFeedback = {}
                                  if (submission.ai_feedback) {
                                    aiFeedback = typeof submission.ai_feedback === 'string'
                                      ? JSON.parse(submission.ai_feedback)
                                      : submission.ai_feedback
                                  }
                                  
                                  // Update public_report in ai_feedback
                                  aiFeedback.public_report = {
                                    points: pointsNum,
                                    comments: publicReportComments
                                  }
                                  
                                  // Update the submission prop
                                  const updatedSubmission = {
                                    ...submission,
                                    ai_feedback: typeof submission.ai_feedback === 'string'
                                      ? JSON.stringify(aiFeedback)
                                      : aiFeedback
                                  }
                                  onSubmissionUpdate(updatedSubmission)
                                } catch (e) {
                                  console.warn('Failed to update local submission state:', e)
                                }
                              }
                              
                              toast.success('Public report grade saved')
                            } catch (err: any) {
                              console.error(err)
                              toast.error(err.message || 'Failed to save public report grade')
                            }
                          }}
                        >
                          Save Public Report Grade
                        </Button>
                      </form>
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

          </Accordion>
        </div>

        {/* Close Button */}
        <div className="flex justify-end pt-3 border-t flex-shrink-0">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            <X className="h-3 w-3 mr-2" />
            Close
          </Button>
        </div>
      </DialogContent>

      {/* AI Results Dialog - REMOVED */}

      {/* JSON Response Dialog */}
      <Dialog open={showJsonDialog} onOpenChange={setShowJsonDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="text-2xl">📄</span>
              AI Response - Raw JSON
            </DialogTitle>
            <DialogDescription>
              Complete JSON response from the AI model
            </DialogDescription>
          </DialogHeader>

          {aiResults && (
            <div className="flex-1 overflow-hidden flex flex-col">
              {/* JSON Display */}
              <div className="flex-1 overflow-auto bg-gray-900 rounded-lg p-4">
                <pre className="text-green-400 text-xs font-mono">
                  {JSON.stringify(aiResults, null, 2)}
                </pre>
              </div>

              {/* Copy Button and Stats */}
              <div className="flex justify-between items-center pt-3 border-t mt-3">
                <div className="text-xs text-gray-500">
                  {aiResults.exercise_grades?.length || 0} exercises · 
                  {' '}{JSON.stringify(aiResults).length} characters
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(aiResults, null, 2))
                      toast.success('JSON copied to clipboard!')
                    }}
                  >
                    Copy JSON
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowJsonDialog(false)}
                  >
                    Close
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Dialog>
  )
}
