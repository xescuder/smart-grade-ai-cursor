/**
 * Inline Exercise Card Component
 * Allows direct editing of exercises without dialogs
 */

"use client"

import * as React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import { Trash2, GripVertical, Check, X, Edit } from "lucide-react"
import { Exercise } from "@/types/assignment"

interface InlineExerciseCardProps {
  exercise: Exercise
  index: number
  onUpdate: (index: number, updatedExercise: Exercise) => void
  onDelete: (index: number) => void
  onMoveUp?: (index: number) => void
  onMoveDown?: (index: number) => void
  canMoveUp: boolean
  canMoveDown: boolean
}

export function InlineExerciseCard({
  exercise,
  index,
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown
}: InlineExerciseCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState<Exercise>(exercise)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Start editing
  const startEditing = () => {
    setEditData({ ...exercise })
    setIsEditing(true)
    setErrors({})
  }

  // Cancel editing
  const cancelEditing = () => {
    setEditData({ ...exercise })
    setIsEditing(false)
    setErrors({})
  }

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!editData.description?.trim()) {
      newErrors.description = "Description is required"
    }
    
    if (!editData.points || editData.points <= 0) {
      newErrors.points = "Points must be greater than 0"
    }
    
    if (editData.points > 100) {
      newErrors.points = "Points cannot exceed 100"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Save changes
  const saveChanges = () => {
    if (validateForm()) {
      onUpdate(index, editData)
      setIsEditing(false)
    }
  }

  // Handle field changes
  const handleChange = (field: keyof Exercise, value: string | number) => {
    setEditData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <Card className="mb-3">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Drag Handle */}
          <div className="flex flex-col items-center gap-1 mt-2">
            <GripVertical className="h-4 w-4 text-gray-400 cursor-move" />
            {/* Move buttons */}
            <div className="flex flex-col gap-1">
              {canMoveUp && onMoveUp && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0"
                  onClick={() => onMoveUp(index)}
                  title="Move Up"
                >
                  ↑
                </Button>
              )}
              {canMoveDown && onMoveDown && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0"
                  onClick={() => onMoveDown(index)}
                  title="Move Down"
                >
                  ↓
                </Button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 space-y-3">
            {isEditing ? (
              // Editing Mode
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="md:col-span-1">
                    <Input
                      type="number"
                      placeholder="Points"
                      value={editData.points || ''}
                      onChange={(e) => handleChange('points', parseInt(e.target.value) || 0)}
                      className={errors.points ? "border-red-500" : ""}
                      min="1"
                      max="100"
                    />
                    {errors.points && (
                      <p className="text-red-500 text-xs mt-1">{errors.points}</p>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={saveChanges}
                      className="flex-1"
                    >
                      <Check className="h-3 w-3 mr-1" />
                      Save
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={cancelEditing}
                      className="flex-1"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Cancel
                    </Button>
                  </div>
                </div>
                
                <div>
                  <Textarea
                    placeholder="Exercise description"
                    value={editData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    className={errors.description ? "border-red-500" : ""}
                    rows={2}
                  />
                  {errors.description && (
                    <p className="text-red-500 text-xs mt-1">{errors.description}</p>
                  )}
                </div>
                
                <div>
                  <Textarea
                    placeholder="Evaluation criteria (optional)"
                    value={editData.evaluation_criteria || ''}
                    onChange={(e) => handleChange('evaluation_criteria', e.target.value)}
                    rows={2}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Define how this exercise should be evaluated and graded
                  </p>
                </div>
              </>
            ) : (
              // View Mode
              <>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">Exercise {index + 1}</h4>
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        {exercise.points} pts
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{exercise.description}</p>
                    {exercise.evaluation_criteria && (
                      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-2 rounded">
                        <p className="text-xs font-medium text-yellow-800 mb-1">Evaluation Criteria:</p>
                        <pre className="text-xs text-yellow-700 whitespace-pre-wrap font-sans">{exercise.evaluation_criteria}</pre>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={startEditing}
                      title="Edit Exercise"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(index)}
                      title="Delete Exercise"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
