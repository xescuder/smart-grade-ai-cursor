/**
 * Assignment Details Component
 * Display assignment information and exercises in read-only format
 */

"use client"

import * as React from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, BookOpen, Target, FileText } from "lucide-react"
import { Assignment } from "@/types/assignment"

interface AssignmentDetailsProps {
  assignment: Assignment
}

export function AssignmentDetails({ assignment }: AssignmentDetailsProps) {
  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // Note: All assignments are always 100 points total

  return (
    <div className="space-y-6">
      {/* Assignment Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">{assignment.name}</CardTitle>
              <CardDescription className="mt-2 text-base">
                {assignment.description}
              </CardDescription>
            </div>
            <Badge variant={assignment.is_active ? "default" : "secondary"}>
              {assignment.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm font-medium">Due Date</p>
                <p className="text-sm text-gray-600">{formatDate(assignment.due_date)}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm font-medium">Exercises</p>
                <p className="text-sm text-gray-600">{assignment.exercises.length} exercises</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm font-medium">Total Points</p>
                <p className="text-sm font-semibold text-blue-600">
                  100 points
                </p>
              </div>
            </div>
          </div>

        </CardContent>
      </Card>

      {/* Exercises List */}
      <Card>
        <CardHeader>
          <CardTitle>Exercises ({assignment.exercises.length})</CardTitle>
          <CardDescription>
            Individual exercises that make up this assignment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {assignment.exercises.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No exercises defined for this assignment.
            </div>
          ) : (
            assignment.exercises
              .sort((a, b) => a.order - b.order)
              .map((exercise, index) => (
                <Card key={exercise.id || index} className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">
                        Exercise {exercise.order}
                      </CardTitle>
                      <Badge variant="outline" className="font-semibold">
                        {exercise.points} pts
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {exercise.description}
                    </p>
                  </CardContent>
                </Card>
              ))
          )}
        </CardContent>
      </Card>

      {/* Assignment Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Assignment Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-gray-700">Created</p>
              <p className="text-gray-600">{formatDate(assignment.created_at)}</p>
            </div>
            
            {assignment.updated_at && (
              <div>
                <p className="font-medium text-gray-700">Last Updated</p>
                <p className="text-gray-600">{formatDate(assignment.updated_at)}</p>
              </div>
            )}
            
            <div>
              <p className="font-medium text-gray-700">Assignment ID</p>
              <p className="text-gray-600">#{assignment.id}</p>
            </div>
            
            <div>
              <p className="font-medium text-gray-700">Created By</p>
              <p className="text-gray-600">Teacher ID #{assignment.created_by}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
