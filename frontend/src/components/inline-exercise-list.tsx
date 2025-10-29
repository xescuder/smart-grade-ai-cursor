/**
 * Inline Exercise List Component
 * Manages exercises for an assignment with inline editing
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Plus, AlertCircle } from "lucide-react"
import { Assignment, Exercise } from "@/types/assignment"
import { InlineExerciseCard } from "./inline-exercise-card"
import { Card, CardContent } from "@/components/ui/card"

interface InlineExerciseListProps {
  assignment: Assignment
  onAssignmentUpdate: () => void
}

export function InlineExerciseList({ assignment, onAssignmentUpdate }: InlineExerciseListProps) {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  // Load exercises
  useEffect(() => {
    setExercises(assignment.exercises || [])
    setHasChanges(false)
  }, [assignment])

  // Calculate total points
  const totalPoints = exercises.reduce((sum, ex) => sum + (ex.points || 0), 0)

  // Add new exercise
  const addExercise = () => {
    const newExercise: Exercise = {
      description: "",
      evaluation_criteria: "",
      points: Math.max(0, 100 - totalPoints),
      order: exercises.length + 1
    }
    setExercises([...exercises, newExercise])
    setHasChanges(true)
  }

  // Update exercise
  const updateExercise = (index: number, updatedExercise: Exercise) => {
    const newExercises = [...exercises]
    newExercises[index] = { ...updatedExercise, order: index + 1 }
    setExercises(newExercises)
    setHasChanges(true)
  }

  // Delete exercise
  const deleteExercise = (index: number) => {
    if (confirm("Are you sure you want to delete this exercise?")) {
      const newExercises = exercises.filter((_, i) => i !== index)
      // Update order
      newExercises.forEach((exercise, i) => {
        exercise.order = i + 1
      })
      setExercises(newExercises)
      setHasChanges(true)
    }
  }

  // Move exercise up
  const moveExerciseUp = (index: number) => {
    if (index > 0) {
      const newExercises = [...exercises]
      ;[newExercises[index - 1], newExercises[index]] = [newExercises[index], newExercises[index - 1]]
      // Update order
      newExercises.forEach((exercise, i) => {
        exercise.order = i + 1
      })
      setExercises(newExercises)
      setHasChanges(true)
    }
  }

  // Move exercise down
  const moveExerciseDown = (index: number) => {
    if (index < exercises.length - 1) {
      const newExercises = [...exercises]
      ;[newExercises[index], newExercises[index + 1]] = [newExercises[index + 1], newExercises[index]]
      // Update order
      newExercises.forEach((exercise, i) => {
        exercise.order = i + 1
      })
      setExercises(newExercises)
      setHasChanges(true)
    }
  }

  // Save exercises
  const saveExercises = async () => {
    if (totalPoints !== 100) {
      alert(`Total points must equal 100. Current total: ${totalPoints}`)
      return
    }

    setIsSaving(true)
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
        setHasChanges(false)
        onAssignmentUpdate()
      } else {
        const errorData = await response.json()
        alert(errorData.error || "Failed to save exercises")
      }
    } catch (error) {
      alert("An error occurred while saving exercises")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-4 pt-4">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold">
            Exercises ({exercises.length})
          </h3>
          
          {/* Points Summary */}
          <div className={`flex items-center gap-2 px-3 py-1 rounded-lg ${
            totalPoints === 100 
              ? "bg-green-100 text-green-800" 
              : "bg-yellow-100 text-yellow-800"
          }`}>
            {totalPoints !== 100 && <AlertCircle className="h-4 w-4" />}
            <span className="text-sm font-medium">
              {totalPoints} / 100 points
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <Button
              onClick={saveExercises}
              disabled={isSaving || totalPoints !== 100}
              size="sm"
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={addExercise}
            disabled={isSaving}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Exercise
          </Button>
        </div>
      </div>

      {/* Exercise Cards */}
      {exercises.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-gray-500 text-center mb-4">
              No exercises added yet. Click "Add Exercise" to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-0">
          {exercises.map((exercise, index) => (
            <InlineExerciseCard
              key={`${assignment.id}-${index}`}
              exercise={exercise}
              index={index}
              onUpdate={updateExercise}
              onDelete={deleteExercise}
              onMoveUp={moveExerciseUp}
              onMoveDown={moveExerciseDown}
              canMoveUp={index > 0}
              canMoveDown={index < exercises.length - 1}
            />
          ))}
        </div>
      )}

      {/* Save Button for mobile */}
      {hasChanges && (
        <div className="flex justify-end pt-4 border-t md:hidden">
          <Button
            onClick={saveExercises}
            disabled={isSaving || totalPoints !== 100}
          >
            {isSaving ? "Saving..." : "Save All Changes"}
          </Button>
        </div>
      )}
    </div>
  )
}
