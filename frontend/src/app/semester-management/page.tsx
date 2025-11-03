"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
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
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { Plus, Pencil, Trash2, Calendar, Clock, CheckCircle } from "lucide-react"
import { OptionalDatePicker } from "@/components/optional-date-picker"

interface Semester {
  id: number
  name: string
  code: string
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
  description?: string
  department?: string
  credits?: number
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

interface SemesterFormData {
  year: number
  season: string
  start_date: string
  end_date: string
  course_id: number
  created_by: number
}

const SEASONS = [
  { value: "Spring", label: "Spring" },
  { value: "Summer", label: "Summer" },
  { value: "Fall", label: "Fall" },
  { value: "Winter", label: "Winter" }
]

export default function SemesterManagementPage() {
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editingSemester, setEditingSemester] = useState<Semester | null>(null)
  const [semesterToDelete, setSemesterToDelete] = useState<Semester | null>(null)
  const [formData, setFormData] = useState<SemesterFormData>({
    year: new Date().getFullYear(),
    season: "Fall",
    start_date: "",
    end_date: "",
    course_id: 0,
    created_by: 1
  })

  // Fetch courses
  const fetchCourses = async () => {
    try {
      const response = await fetch('/api/v1/courses?created_by=1')
      if (!response.ok) {
        throw new Error('Failed to fetch courses')
      }
      const data = await response.json()
      setCourses(data)
    } catch (error) {
      console.error('Error fetching courses:', error)
      toast.error('Failed to fetch courses')
    }
  }

  // Fetch semesters
  const fetchSemesters = async () => {
    try {
      setLoading(true)
      let url = '/api/v1/semesters?created_by=1'
      if (selectedCourseId) {
        url += `&course_id=${selectedCourseId}`
      }
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch semesters')
      }
      const data = await response.json()
      setSemesters(data)
    } catch (error) {
      console.error('Error fetching semesters:', error)
      toast.error('Failed to fetch semesters')
    } finally {
      setLoading(false)
    }
  }

  // Load courses and semesters on component mount
  useEffect(() => {
    fetchCourses()
    fetchSemesters()
  })

  // Refetch semesters when course selection changes
  useEffect(() => {
    if (courses.length > 0) {
      fetchSemesters()
    }
  })

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'year' ? parseInt(value) || new Date().getFullYear() : value
    }))
  }

  // Handle select changes
  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  // No name/code generation; composite key is course_id, year, season

  // Reset form
  const resetForm = () => {
    const currentYear = new Date().getFullYear()
    const defaultSeason = "Fall"
    
    // Auto-generate name and code for new semester
    setFormData({
      year: currentYear,
      season: defaultSeason,
      start_date: "",
      end_date: "",
      course_id: 0,
      created_by: 1
    })
    setEditingSemester(null)
  }

  // Open create dialog
  const openCreateDialog = () => {
    resetForm()
    setDialogOpen(true)
  }

  // Open edit dialog
  const openEditDialog = (semester: Semester) => {
    setFormData({
      year: semester.year,
      season: semester.season,
      start_date: (semester.start_date || '').split('T')[0] || '', // Convert to YYYY-MM-DD safely
      end_date: (semester.end_date || '').split('T')[0] || '',
      course_id: semester.course_id,
      created_by: semester.created_by
    })
    setEditingSemester(semester)
    setDialogOpen(true)
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedCourseId && !editingSemester) {
      toast.error('Please select a course first')
      return
    }
    
    try {
      const toIsoDate = (v: string) => {
        if (!v) return ""
        if (v.includes('/')) {
          const [d, m, y] = v.split('/')
          if (d && m && y) return `${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`
        }
        return v
      }
      // Use simple date format for backend (YYYY-MM-DD) and omit if empty
      const startIso = toIsoDate(formData.start_date)
      const endIso = toIsoDate(formData.end_date)
      const submitData: Record<string, unknown> = {
        year: formData.year,
        season: formData.season,
        course_id: editingSemester ? editingSemester.course_id : selectedCourseId
      }
      if (startIso) submitData.start_date = startIso
      if (endIso) submitData.end_date = endIso

      const url = editingSemester 
        ? `/api/v1/semesters/${editingSemester.id}`
        : '/api/v1/semesters'
      
      const method = editingSemester ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
      })

      if (!response.ok) {
        const errorData = await response.text()
        throw new Error(errorData || `Failed to ${editingSemester ? 'update' : 'create'} semester`)
      }

      toast.success(`Semester ${editingSemester ? 'updated' : 'created'} successfully`)
      setDialogOpen(false)
      resetForm()
      fetchSemesters()
    } catch (error) {
      console.error('Error saving semester:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save semester')
    }
  }

  // Handle delete
  const handleDelete = async () => {
    if (!semesterToDelete) return

    try {
      const response = await fetch(`/api/v1/semesters/${semesterToDelete.id}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        // Try to extract server-provided detail for better UX
        let message = 'Failed to delete semester'
        try {
          const contentType = response.headers.get('content-type') || ''
          if (contentType.includes('application/json')) {
            const data = await response.json()
            if (data?.detail) message = data.detail
          } else {
            const text = await response.text()
            if (text) message = text
          }
        } catch {}
        throw new Error(message)
      }

      toast.success('Semester deleted successfully')
      setDeleteDialogOpen(false)
      setSemesterToDelete(null)
      fetchSemesters()
    } catch (error) {
      console.error('Error deleting semester:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to delete semester')
    }
  }

  const openDeleteDialog = (semester: Semester) => {
    setSemesterToDelete(semester)
    setDeleteDialogOpen(true)
  }

  // Check if semester is current
  const isCurrentSemester = (semester: Semester) => {
    const now = new Date()
    const start = new Date(semester.start_date)
    const end = new Date(semester.end_date)
    return now >= start && now <= end && semester.is_active
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
          <div className="text-lg">Loading semesters...</div>
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
            <Calendar className="h-8 w-8" />
            Semester Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Create and manage academic semesters for your institution
          </p>
        </div>
        <Button 
          onClick={openCreateDialog} 
          className="flex items-center gap-2"
          disabled={!selectedCourseId}
        >
          <Plus className="h-4 w-4" />
          Create Semester
        </Button>
      </div>

      {/* Course Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filter by Course</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Select
                value={selectedCourseId?.toString() || "all"}
                onValueChange={(value) => {
                  if (value === "all") {
                    setSelectedCourseId(null)
                  } else {
                    setSelectedCourseId(parseInt(value))
                  }
                }}
              >
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="Select a course to view its semesters" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Semesters</SelectItem>
                  {courses.map((course) => (
                    <SelectItem key={course.id} value={course.id.toString()}>
                      {course.code} - {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="text-sm text-muted-foreground">
              {selectedCourseId 
                ? `Showing semesters for selected course`
                : `Showing all semesters (${semesters.length})`
              }
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Semesters</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{semesters.length}</div>
            <p className="text-xs text-muted-foreground">
              Semesters in system
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Semester</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {semesters.filter(isCurrentSemester).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Active right now
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Years</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(semesters.map(s => s.year)).size}
            </div>
            <p className="text-xs text-muted-foreground">
              Academic years
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Semesters Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Semesters</CardTitle>
        </CardHeader>
        <CardContent>
          {semesters.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">No semesters found</p>
              <p className="text-muted-foreground mb-4">Create your first semester to get started</p>
              <Button onClick={openCreateDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Create Semester
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Course</TableHead>
                  <TableHead>Season</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {semesters.map((semester) => (
                  <TableRow key={semester.id}>
                    <TableCell className="font-medium">{courses.find(c => c.id === semester.course_id)?.code || semester.course_id}</TableCell>
                    <TableCell>{semester.season}</TableCell>
                    <TableCell>{semester.year}</TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div>{formatDate(semester.start_date)}</div>
                        <div className="text-muted-foreground">to {formatDate(semester.end_date)}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Badge variant={semester.is_active ? "default" : "secondary"}>
                          {semester.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {isCurrentSemester(semester) && (
                          <Badge variant="outline" className="text-green-600">
                            Current
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditDialog(semester)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDeleteDialog(semester)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Semester Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {editingSemester ? 'Edit Semester' : 'Create New Semester'}
            </DialogTitle>
            <DialogDescription>
              {editingSemester 
                ? 'Update the semester information below.'
                : 'Fill in the details to create a new semester.'
              }
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="year">Year *</Label>
                <Input
                  id="year"
                  name="year"
                  type="number"
                  value={formData.year}
                  onChange={handleInputChange}
                  min="2020"
                  max="2030"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="season">Season *</Label>
                <Select 
                  value={formData.season} 
                  onValueChange={(value) => handleSelectChange('season', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select season" />
                  </SelectTrigger>
                  <SelectContent>
                    {SEASONS.map((season) => (
                      <SelectItem key={season.value} value={season.value}>
                        {season.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {/* Name and Code removed: composite key is course_id + year + season */}
              <div className="grid gap-2">
                <Label htmlFor="start_date">Start Date</Label>
                <OptionalDatePicker
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={(v) => setFormData(prev => ({ ...prev, start_date: v }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="end_date">End Date</Label>
                <OptionalDatePicker
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={(v) => setFormData(prev => ({ ...prev, end_date: v }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
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
            <DialogTitle>Delete Semester</DialogTitle>
            <DialogDescription>
              {`Are you sure you want to delete the semester "${semesterToDelete ? `${semesterToDelete.season} ${semesterToDelete.year}` : ''}" (${semesterToDelete ? (courses.find(c => c.id === semesterToDelete.course_id)?.code || semesterToDelete.course_id) : ''})?`}
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
