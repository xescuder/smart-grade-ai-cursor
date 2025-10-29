/**
 * Exercise Management Component
 * Manage exercises for a specific assignment
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
import { Plus, Trash2, GripVertical, AlertCircle, BookOpen } from "lucide-react"
import { Assignment, Exercise } from "@/types/assignment"

interface ExerciseManagementProps {
  assignment: Assignment
  onSuccess: () => void
  onCancel: () => void
}

export function ExerciseManagement({ assignment, onSuccess, onCancel }: ExerciseManagementProps) {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(true)

  // Load exercises for the assignment
  useEffect(() => {
    const loadExercises = async () => {
      try {
        setIsLoading(true)
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/exercises`, {
          headers: {
            ...getAuthHeaders(),
          },
        })
        
        if (response.ok) {
          const data = await response.json()
          setExercises(data.length > 0 ? data : [{
            name: "",
            description: "",
            points: 100,
            order: 1
          }])
        } else {
          // Start with one empty exercise if none exist
          setExercises([{
            name: "",
            description: "",
            points: 100,
            order: 1
          }])
        }
      } catch (error) {
        console.error("Error loading exercises:", error)
        setExercises([{
          name: "",
          description: "",
          points: 100,
          order: 1
        }])
      } finally {
        setIsLoading(false)
      }
    }

    loadExercises()
  }, [assignment.id])

  // Calculate total points (always aiming for 100)
  const totalPoints = exercises.reduce((sum, ex) => sum + (ex.points || 0), 0)

  // Add new exercise
  const addExercise = () => {
    const newExercise: Exercise = {
      name: "",
      description: "",
      points: Math.max(0, 100 - totalPoints),
      order: exercises.length + 1
    }
    setExercises([...exercises, newExercise])
  }

  // Remove exercise
  const removeExercise = (index: number) => {
    setExercises(exercises.filter((_, i) => i !== index))
  }

  // Update exercise
  const updateExercise = (index: number, field: keyof Exercise, value: string | number) => {
    const updatedExercises = [...exercises]
    updatedExercises[index] = {
      ...updatedExercises[index],
      [field]: field === 'points' ? parseInt(value as string) || 0 : value
    }
    setExercises(updatedExercises)
  }

  // Move exercise up/down
  const moveExercise = (index: number, direction: 'up' | 'down') => {
    const newExercises = [...exercises]
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    
    if (targetIndex >= 0 && targetIndex < exercises.length) {
      [newExercises[index], newExercises[targetIndex]] = [newExercises[targetIndex], newExercises[index]]
      
      // Update order numbers
      newExercises.forEach((exercise, i) => {
        exercise.order = i + 1
      })
      
      setExercises(newExercises)
    }
  }

  // Validate form
  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (exercises.length === 0) {
      newErrors.exercises = "At least one exercise is required"
    }

    exercises.forEach((exercise, index) => {
      // No name validation needed since we removed the name field
      if (!exercise.description.trim()) {
        newErrors[`exercise_${index}_description`] = "Exercise description is required"
      }
      if (exercise.points <= 0) {
        newErrors[`exercise_${index}_points`] = "Points must be greater than 0"
      }
    })

    if (totalPoints !== 100) {
      newErrors.totalPoints = `Total points must equal 100 (currently ${totalPoints})`
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
      const exercisesData = exercises.map((exercise, index) => ({
        ...exercise,
        order: index + 1
      }))

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/exercises`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(exercisesData),
      })

      if (response.ok) {
        onSuccess()
      } else {
        const errorData = await response.json()
        setErrors({ submit: errorData.detail || "Failed to save exercises" })
      }
    } catch {
      setErrors({ submit: "An error occurred while saving the exercises" })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p>Loading exercises...</p>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Assignment Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            {assignment.name}
          </CardTitle>
          <CardDescription>
            Managing exercises for this assignment
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Exercises Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>Exercises ({exercises.length})</CardTitle>
            <CardDescription>
              Define individual exercises for this assignment. Exercises should total 100 points.
            </CardDescription>
          </div>
          <Button type="button" variant="outline" onClick={addExercise}>
            <Plus className="h-4 w-4 mr-2" />
            Add Exercise
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Total Points Summary */}
          <div className={`flex items-center gap-2 p-3 rounded-lg ${
            totalPoints === 100 
              ? "bg-green-50 border border-green-200" 
              : "bg-red-50 border border-red-200"
          }`}>
            {totalPoints !== 100 && <AlertCircle className="h-4 w-4 text-red-500" />}
            <span className={`font-medium ${
              totalPoints === 100 ? "text-green-800" : "text-red-800"
            }`}>
              Total Points: {totalPoints}/100
            </span>
            {errors.totalPoints && (
              <span className="text-red-500 text-sm ml-2">({errors.totalPoints})</span>
            )}
          </div>

          {/* Exercise List */}
          {exercises.map((exercise, index) => (
            <Card key={index} className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GripVertical className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">Exercise {index + 1}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {index > 0 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => moveExercise(index, 'up')}
                      >
                        ↑
                      </Button>
                    )}
                    {index < exercises.length - 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => moveExercise(index, 'down')}
                      >
                        ↓
                      </Button>
                    )}
                    {exercises.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeExercise(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <div className="text-sm font-medium text-gray-700">
                      Exercise {exercise.order || index + 1}
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor={`exercise_${index}_points`}>Points</Label>
                    <Input
                      id={`exercise_${index}_points`}
                      type="number"
                      min="1"
                      max="100"
                      value={exercise.points}
                      onChange={(e) => updateExercise(index, 'points', e.target.value)}
                      className={errors[`exercise_${index}_points`] ? "border-red-500" : ""}
                    />
                    {errors[`exercise_${index}_points`] && (
                      <p className="text-red-500 text-sm mt-1">{errors[`exercise_${index}_points`]}</p>
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor={`exercise_${index}_description`}>Description</Label>
                  <Textarea
                    id={`exercise_${index}_description`}
                    value={exercise.description}
                    onChange={(e) => updateExercise(index, 'description', e.target.value)}
                    className={errors[`exercise_${index}_description`] ? "border-red-500" : ""}
                    rows={2}
                    placeholder="Describe what students need to do for this exercise..."
                  />
                  {errors[`exercise_${index}_description`] && (
                    <p className="text-red-500 text-sm mt-1">{errors[`exercise_${index}_description`]}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {exercises.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No exercises added yet. Click "Add Exercise" to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Submit Section */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{errors.submit}</p>
        </div>
      )}

      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button 
          type="submit" 
          disabled={isSubmitting || totalPoints !== 100}
          className="min-w-[140px]"
        >
          {isSubmitting ? "Saving..." : "Save Exercises"}
        </Button>
      </div>
    </form>
  )
}
