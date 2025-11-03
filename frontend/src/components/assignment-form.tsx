/**
 * Assignment Form Component
 * Create and edit basic assignment information (without exercises)
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Assignment, AssignmentCreate } from "@/types/assignment"

interface AssignmentFormProps {
  assignment?: Assignment
  onSuccess: () => void
}

export function AssignmentForm({ assignment, onSuccess }: AssignmentFormProps) {
  const isEditing = !!assignment
  
  const [formData, setFormData] = useState({
    name: "",
    due_date: "",
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Initialize form data
  useEffect(() => {
    if (assignment) {
      setFormData({
        name: assignment.name,
        due_date: new Date(assignment.due_date).toISOString().slice(0, 16),
      })
    }
  }, [assignment])


  // Validate form
  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = "Assignment name is required"
    }

    if (!formData.due_date) {
      newErrors.due_date = "Due date is required"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    
    try {
      const assignmentData: AssignmentCreate = {
        ...formData,
        exercises: [], // Exercises will be managed separately
        language: assignment?.language ?? "",
        course_id: typeof assignment?.course_id === "number"
          ? assignment.course_id
          : Number(assignment?.course_id ?? 0),
        semester_id: typeof assignment?.semester_id === "number"
          ? assignment.semester_id
          : Number(assignment?.semester_id ?? 0),
      }

      // Determine API endpoint and method
      // Safely determine if editing an assignment
      const isEdit = assignment && typeof assignment.id === "number"
      const url = isEdit
        ? `/api/assignments/${assignment.id}`
        : "/api/assignments"
      const method = isEdit ? "PUT" : "POST"

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(assignmentData),
      })

      if (response.ok) {
        onSuccess()
      } else {
        const errorData = await response.json()
        // Handle different error formats from FastAPI
        let errorMessage = "Failed to save assignment"
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((err: { msg?: string }) => err.msg ?? "Unknown error").join(', ')
          }
        }
        setErrors({ submit: errorMessage })
        return
      }
    } catch {
      setErrors({ submit: "An error occurred while saving the assignment" })
      return
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Assignment Information */}
      <Card>
        <CardHeader>
          <CardTitle>Assignment Information</CardTitle>
          <CardDescription>
            Basic details about the assignment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name" className="mb-2 block">Assignment Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={errors.name ? "border-red-500" : ""}
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          <div>
            <Label htmlFor="due_date" className="mb-2 block">Due Date</Label>
            <Input
              id="due_date"
              type="datetime-local"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              className={errors.due_date ? "border-red-500" : ""}
            />
            {errors.due_date && (
              <p className="text-red-500 text-sm mt-1">{errors.due_date}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              📝 <strong>Next Step:</strong> After creating the assignment, you can add and manage exercises 
              using the &quot;Manage Exercises&quot; button in the assignment list.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Submit Section */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{String(errors.submit)}</p>
        </div>
      )}

      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline" onClick={onSuccess}>
          Cancel
        </Button>
        <Button 
          type="submit" 
          disabled={isSubmitting}
          className="min-w-[120px]"
        >
          {isSubmitting ? "Saving..." : (isEditing ? "Update" : "Create")} Assignment
        </Button>
      </div>
    </form>
  )
}
