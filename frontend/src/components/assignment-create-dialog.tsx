"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { Assignment } from "@/types/assignment"
import { apiClient } from "@/lib/api"

interface AssignmentCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (assignment: Assignment) => void
}

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish / Español" },
  { value: "ca", label: "Catalan / Català" },
  { value: "fr", label: "French / Français" },
  { value: "de", label: "German / Deutsch" },
]

interface Course {
  id: number
  name: string
  code: string
}

interface Semester {
  id: number
  year: number
  season: string
  course_id: number
  start_date?: string | null
  end_date?: string | null
}

export function AssignmentCreateDialog({ open, onOpenChange, onSave }: AssignmentCreateDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    due_date: "",
    language: "en",
    course_id: 0,
    semester_id: 0
  })
  const [courses, setCourses] = useState<Course[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Fetch courses and semesters on component mount
  useEffect(() => {
    if (open) {
      fetchCourses()
      fetchSemesters()
    }
  }, [open])

  const fetchCourses = async () => {
    try {
      const data = await apiClient.getCourses()
      setCourses(data)
    } catch (error) {
      console.error("Error fetching courses:", error)
      toast.error("Failed to load courses")
    }
  }

  const fetchSemesters = async () => {
    try {
      const data = await apiClient.getSemesters()
      setSemesters(data)
    } catch (error) {
      console.error("Error fetching semesters:", error)
      toast.error("Failed to load semesters")
    }
  }

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error("Assignment name is required")
      return
    }
    
    if (!formData.language) {
      toast.error("Please select a language")
      return
    }

    if (!formData.semester_id) {
      toast.error("Please select a semester")
      return
    }

    setIsLoading(true)
    try {
      // Only send semester_id - backend will derive course_id from semester_id
      const newAssignment = await apiClient.createAssignment({
        name: formData.name.trim(),
        due_date: formData.due_date || new Date().toISOString(),
        language: formData.language,
        semester_id: formData.semester_id,
        is_active: true,
        exercises: []
      })
      toast.success("Assignment created successfully!")
      onSave(newAssignment)
      handleClose()
    } catch (error) {
      console.error("Error creating assignment:", error)
      toast.error(error instanceof Error ? error.message : "Failed to create assignment")
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({ name: "", due_date: "", language: "en", course_id: 0, semester_id: 0 })
    onOpenChange(false)
  }

  // Filter semesters based on selected course
  const filteredSemesters = semesters.filter(semester => 
    !formData.course_id || semester.course_id === formData.course_id
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create New Assignment</DialogTitle>
          <DialogDescription>
            Create a new assignment with basic information.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="course">Course (optional - helps filter semesters)</Label>
            <Select 
              value={formData.course_id ? formData.course_id.toString() : ""} 
              onValueChange={(value) => {
                const courseId = parseInt(value)
                setFormData({
                  ...formData, 
                  course_id: courseId,
                  semester_id: 0 // Reset semester when course changes
                })
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a course to filter semesters (optional)" />
              </SelectTrigger>
              <SelectContent>
                {courses.map((course) => (
                  <SelectItem key={course.id} value={course.id.toString()}>
                    {course.name} ({course.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="semester">Semester *</Label>
            <Select 
              value={formData.semester_id ? formData.semester_id.toString() : ""} 
              onValueChange={(value) => setFormData({...formData, semester_id: parseInt(value)})}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a semester" />
              </SelectTrigger>
              <SelectContent>
                {filteredSemesters.map((semester) => (
                  <SelectItem key={semester.id} value={semester.id.toString()}>
                    {semester.season} {semester.year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language *</Label>
            <Select 
              value={formData.language} 
              onValueChange={(value) => setFormData({...formData, language: value})}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a language" />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((language) => (
                  <SelectItem key={language.value} value={language.value}>
                    {language.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

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
            <Label htmlFor="due_date">Due Date</Label>
            <Input
              id="due_date"
              type="datetime-local"
              value={formData.due_date}
              onChange={(e) => setFormData({...formData, due_date: e.target.value})}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? "Creating..." : "Create Assignment"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
