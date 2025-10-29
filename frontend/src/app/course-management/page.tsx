"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Plus, Pencil, Trash2, BookOpen, GraduationCap, Users, ChevronDown, ChevronRight, Calendar, Clock } from "lucide-react"
import { apiClient } from "@/lib/api"

interface Semester {
  id: number
  year: number
  season: string
  start_date: string
  end_date: string
  course_id: number
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

interface Course {
  id: number
  name: string
  code: string
  credits?: number
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
  semesters?: Semester[]
}

interface CourseFormData {
  name: string
  code: string
  credits: number
  created_by: number
}

export default function CourseManagementPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [courseToDelete, setCourseToDelete] = useState<Course | null>(null)
  const [expandedCourses, setExpandedCourses] = useState<Set<number>>(new Set())
  const [semesterDialogOpen, setSemesterDialogOpen] = useState(false)
  const [editingSemester, setEditingSemester] = useState<Semester | null>(null)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [formData, setFormData] = useState<CourseFormData>({
    name: "",
    code: "",
    credits: 3,
    // created_by will be set by backend based on authenticated user
  })
  const [semesterFormData, setSemesterFormData] = useState({
    year: new Date().getFullYear(),
    season: "Fall",
    start_date: "",
    end_date: "",
    course_id: 0,
    created_by: 1
  })

  // Fetch courses with semesters
  const fetchCourses = async () => {
    try {
      const data = await apiClient.request('/api/v1/courses?created_by=1&include_semesters=true')
      setCourses(data)
    } catch (error) {
      console.error('Error fetching courses:', error)
      toast.error('Failed to fetch courses')
    } finally {
      setLoading(false)
    }
  }

  // Load courses on component mount
  useEffect(() => {
    fetchCourses()
  }, [])

  // Expand courses with semesters by default
  useEffect(() => {
    if (courses.length > 0) {
      const coursesWithSemesters = courses
        .filter(course => course.semesters && course.semesters.length > 0)
        .map(course => course.id)
      setExpandedCourses(new Set(coursesWithSemesters))
    }
  }, [courses])

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'credits' ? parseInt(value) || 0 : value
    }))
  }

  // Reset form
  const resetForm = () => {
    setFormData({
      name: "",
      code: "",
      credits: 3,
      created_by: 1
    })
    setEditingCourse(null)
  }

  // Open create dialog
  const openCreateDialog = () => {
    resetForm()
    setDialogOpen(true)
  }

  // Open edit dialog
  const openEditDialog = (course: Course) => {
    setFormData({
      name: course.name,
      code: course.code,
      credits: course.credits || 3,
      created_by: course.created_by
    })
    setEditingCourse(course)
    setDialogOpen(true)
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      if (editingCourse) {
        await apiClient.updateCourse(editingCourse.id, formData)
        toast.success('Course updated successfully')
      } else {
        await apiClient.createCourse(formData)
        toast.success('Course created successfully')
      }
      
      setDialogOpen(false)
      resetForm()
      fetchCourses()
    } catch (error) {
      console.error('Error saving course:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save course')
    }
  }

  // Handle delete
  const handleDelete = async () => {
    if (!courseToDelete) return

    try {
      await apiClient.deleteCourse(courseToDelete.id)
      toast.success('Course deleted successfully')
      setDeleteDialogOpen(false)
      setCourseToDelete(null)
      fetchCourses()
    } catch (error) {
      console.error('Error deleting course:', error)
      toast.error('Failed to delete course')
    }
  }

  const openDeleteDialog = (course: Course) => {
    setCourseToDelete(course)
    setDeleteDialogOpen(true)
  }

  // Toggle course expansion
  const toggleCourseExpansion = (courseId: number) => {
    const newExpanded = new Set(expandedCourses)
    if (newExpanded.has(courseId)) {
      newExpanded.delete(courseId)
    } else {
      newExpanded.add(courseId)
    }
    setExpandedCourses(newExpanded)
  }

  // Open semester dialog for a specific course
  const openSemesterDialog = (course: Course) => {
    setSelectedCourse(course)
    const currentYear = new Date().getFullYear()
    const season = "Fall"
    setSemesterFormData({
      year: currentYear,
      season: season,
      start_date: "",
      end_date: "",
      course_id: course.id,
      created_by: 1
    })
    setEditingSemester(null)
    setSemesterDialogOpen(true)
  }

  // Handle semester form submission
  const handleSemesterSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      if (editingSemester) {
        await apiClient.updateSemester(editingSemester.id, semesterFormData)
        toast.success('Semester updated successfully')
      } else {
        await apiClient.createSemester(semesterFormData)
        toast.success('Semester created successfully')
      }
      
      setSemesterDialogOpen(false)
      fetchCourses() // Refresh to get updated semesters
    } catch (error) {
      console.error('Error saving semester:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save semester')
    }
  }

  // Handle semester delete
  const handleDeleteSemester = async (semesterId: number) => {
    try {
      await apiClient.deleteSemester(semesterId)
      toast.success('Semester deleted successfully')
      fetchCourses() // Refresh to get updated semesters
    } catch (error) {
      console.error('Error deleting semester:', error)
      if (error instanceof Error && error.message.includes('404')) {
        toast.info('Semester not found or already deleted')
        fetchCourses() // Refresh to get updated data
      } else {
        toast.error(error instanceof Error ? error.message : 'Failed to delete semester')
      }
    }
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="text-lg">Loading courses...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <BookOpen className="h-8 w-8" />
            Course Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Create and manage academic courses for your institution
          </p>
        </div>
        <Button onClick={openCreateDialog} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create Course
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{courses.length}</div>
            <p className="text-xs text-muted-foreground">
              Active courses in system
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Semesters</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {courses.reduce((sum, c) => sum + (c.semesters?.length || 0), 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Across all courses
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {courses.reduce((sum, c) => sum + (c.credits || 0), 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Across all courses
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Courses Master-Detail Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Courses</CardTitle>
        </CardHeader>
        <CardContent>
          {courses.length === 0 ? (
            <div className="text-center py-8">
              <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">No courses found</p>
              <p className="text-muted-foreground mb-4">Create your first course to get started</p>
              <Button onClick={openCreateDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Create Course
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {courses.map((course) => (
                <div key={course.id} className="border rounded-lg">
                  {/* Course Row */}
                  <div className="p-4 border-b bg-gray-50/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleCourseExpansion(course.id)}
                          className="p-1 h-8 w-8"
                        >
                          {expandedCourses.has(course.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                        <div>
                          <div className="font-medium text-lg">{course.code} - {course.name}</div>
                          <div className="flex items-center gap-4 mt-1">
                            <span className="text-sm">
                              <strong>Credits:</strong> {course.credits || 'N/A'}
                            </span>
                            <span className="text-sm">
                              <strong>Semesters:</strong> {course.semesters?.length || 0}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={course.is_active ? "default" : "secondary"}>
                          {course.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openSemesterDialog(course)}
                          className="flex items-center gap-1"
                        >
                          <Plus className="h-3 w-3" />
                          Add Semester
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditDialog(course)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDeleteDialog(course)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Semesters Detail */}
                  {expandedCourses.has(course.id) && (
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-sm text-muted-foreground">Semesters</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openSemesterDialog(course)}
                          className="flex items-center gap-1"
                        >
                          <Plus className="h-3 w-3" />
                          Add Semester
                        </Button>
                      </div>
                      
                      {course.semesters && course.semesters.length > 0 ? (
                        <div className="space-y-2">
                          {course.semesters.map((semester) => (
                            <div key={semester.id} className="flex items-center justify-between p-3 border rounded-lg bg-white">
                              <div className="flex items-center gap-4">
                                <div>
                                  <div className="font-medium">{course.code} - {semester.season} {semester.year}</div>
                                  <div className="text-sm text-muted-foreground">
                                    {semester.season} {semester.year}
                                  </div>
                                  <div className="text-xs text-muted-foreground flex items-center gap-4">
                                    <span className="flex items-center gap-1">
                                      <Calendar className="h-3 w-3" />
                                      {formatDate(semester.start_date)}
                                    </span>
                                    <span className="flex items-center gap-1">
                                      <Clock className="h-3 w-3" />
                                      {formatDate(semester.end_date)}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge variant={semester.is_active ? "default" : "secondary"}>
                                  {semester.is_active ? "Active" : "Inactive"}
                                </Badge>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setEditingSemester(semester)
                                    setSelectedCourse(course)
                                    setSemesterFormData({
                                      year: semester.year,
                                      season: semester.season,
                                      start_date: (semester.start_date || '').split('T')[0] || '',
                                      end_date: (semester.end_date || '').split('T')[0] || '',
                                      course_id: course.id,
                                      created_by: semester.created_by
                                    })
                                    setSemesterDialogOpen(true)
                                  }}
                                >
                                  <Pencil className="h-3 w-3" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDeleteSemester(semester.id)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-6 text-muted-foreground">
                          <Calendar className="h-8 w-8 mx-auto mb-2" />
                          <p>No semesters for this course yet</p>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openSemesterDialog(course)}
                            className="mt-2"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Add First Semester
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Course Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {editingCourse ? 'Edit Course' : 'Create New Course'}
            </DialogTitle>
            <DialogDescription>
              {editingCourse 
                ? 'Update the course information below.'
                : 'Fill in the details to create a new course.'
              }
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="code">Course Code *</Label>
                <Input
                  id="code"
                  name="code"
                  value={formData.code}
                  onChange={handleInputChange}
                  placeholder="e.g., CS101, MATH201"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="name">Course Name *</Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Introduction to Computer Science"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="credits">Credits</Label>
                <Input
                  id="credits"
                  name="credits"
                  type="number"
                  value={formData.credits}
                  onChange={handleInputChange}
                  min="0"
                  max="15"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">
                {editingCourse ? 'Update' : 'Create'} Course
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create/Edit Semester Dialog */}
      <Dialog open={semesterDialogOpen} onOpenChange={setSemesterDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {editingSemester ? 'Edit Semester' : `Create New Semester for ${selectedCourse?.name}`}
            </DialogTitle>
            <DialogDescription>
              {editingSemester 
                ? 'Update the semester information below.'
                : 'Fill in the details to create a new semester.'
              }
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSemesterSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="year">Year *</Label>
                <Input
                  id="year"
                  name="year"
                  type="number"
                  value={semesterFormData.year}
                  onChange={(e) => {
                    const year = parseInt(e.target.value) || new Date().getFullYear()
                    setSemesterFormData(prev => ({
                      ...prev,
                      year
                    }))
                  }}
                  min="2020"
                  max="2030"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="season">Season *</Label>
                <select
                  id="season"
                  name="season"
                  value={semesterFormData.season}
                  onChange={(e) => {
                    const season = e.target.value
                    setSemesterFormData(prev => ({
                      ...prev,
                      season
                    }))
                  }}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  required
                >
                  <option value="Fall">Fall</option>
                  <option value="Spring">Spring</option>
                  <option value="Summer">Summer</option>
                  <option value="Winter">Winter</option>
                </select>
              </div>
              {/* Name and Code removed: composite key is course_id + year + season */}
              <div className="grid gap-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  name="start_date"
                  type="date"
                  value={semesterFormData.start_date}
                  onChange={(e) => setSemesterFormData(prev => ({ ...prev, start_date: e.target.value }))}
                  required={false}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  name="end_date"
                  type="date"
                  value={semesterFormData.end_date}
                  onChange={(e) => setSemesterFormData(prev => ({ ...prev, end_date: e.target.value }))}
                  required={false}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSemesterDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">
                {editingSemester ? 'Update' : 'Create'} Semester
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Course</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the course "{courseToDelete?.name}" ({courseToDelete?.code})?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
