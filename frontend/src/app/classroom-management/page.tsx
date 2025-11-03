"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
import { Plus, Pencil, Trash2, Users, BookOpen, Globe, UserPlus, UserMinus, Edit, Trash, ChevronDown, ChevronRight, Upload } from "lucide-react"
import { apiClient } from "@/lib/api"

interface GroupMember {
  name: string
  email_address: string
  student_id: string
}

interface Group {
  id: number
  name: string
  description?: string
  classroom_id: number
  members: GroupMember[]
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

interface Classroom {
  id: number
  name: string
  teacher_name: string
  language: string
  course_id: number
  semester_id: number
  description?: string
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
  course?: {
    id: number
    name: string
    code: string
  }
  semester?: {
    id: number
    name: string
    code: string
  }
  groups?: Group[]
}

interface Course {
  id: number
  name: string
  code: string
  description?: string
}

interface Semester {
  id: number
  name: string
  code: string
  year: number
  season: string
  course_id: number
}

interface ClassroomFormData {
  name: string
  teacher_name: string
  language: string
  course_id: number
  semester_id: number
  description: string
  room_number?: string
  schedule?: string
  max_students?: number
  created_by: number
}

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish / Español" },
  { value: "ca", label: "Catalan / Català" },
  { value: "fr", label: "French / Français" },
  { value: "de", label: "German / Deutsch" },
]

export default function ClassroomManagementPage() {
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [filteredSemesters, setFilteredSemesters] = useState<Semester[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [selectedSemesterId, setSelectedSemesterId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editingClassroom, setEditingClassroom] = useState<Classroom | null>(null)
  const [classroomToDelete, setClassroomToDelete] = useState<Classroom | null>(null)
  const [classroomGroupsCount, setClassroomGroupsCount] = useState<Record<number, number>>({})
  
  // Group management state
  const [selectedClassroom, setSelectedClassroom] = useState<Classroom | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [groupsLoading, setGroupsLoading] = useState(false)
  const [groupDialogOpen, setGroupDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<Group | null>(null)
  const [groupDeleteDialogOpen, setGroupDeleteDialogOpen] = useState(false)
  const [groupToDelete, setGroupToDelete] = useState<Group | null>(null)
  // Track the classroom currently expected to display groups to avoid stale assignments
  const currentGroupsClassroomIdRef = React.useRef<number | null>(null)
  const [formData, setFormData] = useState<ClassroomFormData>({
    name: "",
    teacher_name: "",
    language: "en",
    course_id: 0,
    semester_id: 0,
    description: "",
    room_number: "",
    schedule: "",
    max_students: undefined,
    created_by: 1
  })

  // Prevent duplicate fetches in React StrictMode and redundant param calls
  const lastClassroomQueryRef = React.useRef<string | null>(null)

  // Group form data
  const [groupFormData, setGroupFormData] = useState<{
    name: string
    description: string
    members: GroupMember[]
  }>({
    name: '',
    description: '',
    members: []
  })

  // Fetch courses
  const fetchCourses = async () => {
    try {
      const data = await apiClient.request<Course[]>('/api/v1/courses?created_by=1')
      setCourses(data)
    } catch (error) {
      console.error('Error fetching courses:', error)
      toast.error('Failed to fetch courses')
    }
  }

  // Fetch semesters
  const fetchSemesters = async () => {
    try {
      const data = await apiClient.request<Semester[]>('/api/v1/semesters?created_by=1')
      setSemesters(data)
    } catch (error) {
      console.error('Error fetching semesters:', error)
      toast.error('Failed to fetch semesters')
    }
  }

  // Fetch classrooms
  const fetchClassrooms = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (selectedCourseId) params.append('course_id', selectedCourseId.toString())
      if (selectedSemesterId) params.append('semester_id', selectedSemesterId.toString())
      const queryKey = params.toString()

      // Skip if same query as last time (guards StrictMode double invoke)
      if (lastClassroomQueryRef.current === queryKey && classrooms.length > 0) {
        return
      }
      lastClassroomQueryRef.current = queryKey
      
      const suffix = params.toString() ? `?${params.toString()}` : ''
      const data = await apiClient.request<Classroom[]>(`/api/v1/classrooms/${suffix}`.replace(/\/?\?/, '?'))
      console.log('Fetched classrooms:', data) // Debug log
      setClassrooms(data)
      
      // Fetch groups count for all classrooms
      const classroomIds = data.map((c: Classroom) => c.id)
      if (classroomIds.length > 0) {
        fetchGroupsCountForClassrooms(classroomIds)
      }
    } catch (error) {
      console.error('Error fetching classrooms:', error)
      toast.error('Failed to fetch classrooms')
    } finally {
      setLoading(false)
    }
  }

  // Fetch groups count for all classrooms
  const fetchGroupsCountForClassrooms = async (classroomIds: number[]) => {
    try {
      const counts: Record<number, number> = {}
      await Promise.all(
        classroomIds.map(async (id) => {
          try {
            const groups = await apiClient.request<any[]>(`/api/v1/groups?classroom_id=${id}`)
            const safeGroups = Array.isArray(groups)
              ? groups.filter((g) => Number(g?.classroom_id ?? g?.classroom?.id) === id)
              : []
            counts[id] = safeGroups.length
          } catch {
            counts[id] = 0
          }
        })
      )
      setClassroomGroupsCount(counts)
    } catch (error) {
      console.error('Error fetching groups count:', error)
    }
  }
  const fetchGroupsForClassroom = async (classroomId: number) => {
    try {
      setGroupsLoading(true)
      const data = await apiClient.request<any[]>(`/api/v1/groups?classroom_id=${classroomId}`)
      // Strictly filter to this classroom id only
      const onlyThisClassroom = Array.isArray(data)
        ? data.filter(g => Number(g?.classroom_id ?? g?.classroom?.id) === classroomId)
        : []
      // Sort groups by name (case-insensitive)
      const sorted = onlyThisClassroom.length > 0
        ? [...onlyThisClassroom].sort((a, b) => {
            const an = (a?.name || '').toString().toLowerCase()
            const bn = (b?.name || '').toString().toLowerCase()
            if (an < bn) return -1
            if (an > bn) return 1
            return 0
          })
        : []
      // Concurrency guard: only apply if still viewing the same classroom
      if (currentGroupsClassroomIdRef.current === classroomId) {
        setGroups(sorted)
      }
    } catch (error) {
      console.error('Error fetching groups:', error)
      toast.error('Failed to fetch groups')
      setGroups([])
    } finally {
      setGroupsLoading(false)
    }
  }

  // Load initial data once (classrooms will be fetched by the filter effect)
  useEffect(() => {
    fetchCourses()
    fetchSemesters()
  }, [])

  // Refetch classrooms when filters change
  useEffect(() => {
    fetchClassrooms()
  }, [selectedCourseId, selectedSemesterId])

  // Filter semesters by selected course
  useEffect(() => {
    if (selectedCourseId) {
      const filtered = semesters.filter(s => s.course_id === selectedCourseId)
      setFilteredSemesters(filtered)
    } else {
      setFilteredSemesters(semesters)
    }
  }, [selectedCourseId, semesters])

  // Update filtered semesters when form course changes
  useEffect(() => {
    if (formData.course_id) {
      const filtered = semesters.filter(s => s.course_id === formData.course_id)
      setFilteredSemesters(filtered)
      // Reset semester selection if current semester doesn't belong to new course
      if (formData.semester_id) {
        const semesterBelongsToCourse = filtered.some(s => s.id === formData.semester_id)
        if (!semesterBelongsToCourse) {
          setFormData(prev => ({ ...prev, semester_id: 0 }))
        }
      }
    } else {
      setFilteredSemesters(semesters)
    }
  }, [formData.course_id, formData.semester_id, semesters])

  // Handle form input changes
  type ClassroomFormValue = ClassroomFormData[keyof ClassroomFormData]
  const handleInputChange = (field: keyof ClassroomFormData, value: ClassroomFormValue) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  // Open dialog for creating new classroom
  const handleCreateClick = () => {
    setEditingClassroom(null)
    setFormData({
      name: "",
      teacher_name: "",
      language: "en",
      course_id: selectedCourseId || 0,
      semester_id: 0,
      description: "",
      created_by: 1
    })
    setDialogOpen(true)
  }

  // Open dialog for editing classroom
  const handleEditClick = (classroom: Classroom) => {
    setEditingClassroom(classroom)
    setFormData({
      name: classroom.name,
      teacher_name: classroom.teacher_name,
      language: classroom.language,
      course_id: classroom.course_id,
      semester_id: classroom.semester_id,
      description: classroom.description || "",
      created_by: classroom.created_by
    })
    setDialogOpen(true)
  }

  // Handle classroom save (create or update)
  const handleSave = async () => {
    // Validation
    if (!formData.name || !formData.teacher_name || !formData.language || !formData.course_id || !formData.semester_id) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      if (editingClassroom) {
        const updated = await apiClient.updateClassroom(editingClassroom.id, formData)
        // Optimistically update in list
        setClassrooms(prev => prev.map(c => c.id === editingClassroom.id ? { ...c, ...updated } : c))
      } else {
        const created = await apiClient.createClassroom(formData)
        // Optimistically add to top of list
        setClassrooms(prev => [created as any, ...prev])
        // Ensure groups count starts at 0 for the new classroom
        if ((created as any)?.id) {
          setClassroomGroupsCount(prev => ({ ...prev, [(created as any).id]: 0 }))
        }
      }

      toast.success(editingClassroom ? 'Classroom updated successfully' : 'Classroom created successfully')
      setDialogOpen(false)
      currentGroupsClassroomIdRef.current = null
      // Collapse any open classroom and clear groups to avoid stale carry-over
      setSelectedClassroom(null)
      setGroups([])
      // Force refetch to ensure server state is reflected
      lastClassroomQueryRef.current = null
      fetchClassrooms()
    } catch (error) {
      console.error('Error saving classroom:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save classroom')
    }
  }

  // Handle classroom delete
  const handleDelete = async () => {
    if (!classroomToDelete) return

    try {
      await apiClient.deleteClassroom(classroomToDelete.id)

      toast.success('Classroom deleted successfully')
      setDeleteDialogOpen(false)
      setClassroomToDelete(null)
      // Optimistically update UI
      setClassrooms(prev => prev.filter(c => c.id !== classroomToDelete.id))
      setClassroomGroupsCount(prev => {
        const { [classroomToDelete.id]: _removed, ...rest } = prev
        return rest
      })
      // Force refetch to avoid memoized query skip
      lastClassroomQueryRef.current = null
      fetchClassrooms()
    } catch (error) {
      console.error('Error deleting classroom:', error)
    toast.error(error instanceof Error ? error.message : 'Failed to delete classroom')
    }
  }

  // Get course label for a classroom using semester -> course linkage
  const getCourseLabelForClassroom = (classroom: Classroom) => {
    const semester = semesters.find(s => s.id === classroom.semester_id)
    const course = semester ? courses.find(c => c.id === semester.course_id) : undefined
    return course ? `${course.code} - ${course.name}` : 'Unknown'
  }

  // Get semester label by ID
  const getSemesterLabel = (semesterId: number) => {
    const semester = semesters.find(s => s.id === semesterId)
    return semester ? `${semester.season} ${semester.year}` : 'Unknown'
  }

  // Get language label
  const getLanguageLabel = (code: string) => {
    const lang = LANGUAGES.find(l => l.value === code)
    return lang ? lang.label : code.toUpperCase()
  }

  // Group management functions
  const handleSelectClassroom = (classroom: Classroom) => {
    // If clicking on the same classroom, toggle (collapse)
    if (selectedClassroom?.id === classroom.id) {
      setSelectedClassroom(null)
      setGroups([])
    } else {
      // If clicking on a different classroom, expand it
      setSelectedClassroom(classroom)
      currentGroupsClassroomIdRef.current = classroom.id
      setGroups([])
      setGroupsLoading(true)
      fetchGroupsForClassroom(classroom.id)
    }
  }

  const handleCreateGroup = () => {
    if (!selectedClassroom) return
    setEditingGroup(null)
    setGroupFormData({
      name: '',
      description: '',
      members: []
    })
    setGroupDialogOpen(true)
  }

  const handleEditGroup = (group: Group) => {
    setEditingGroup(group)
    setGroupFormData({
      name: group.name,
      description: group.description || '',
      members: group.members.length > 0 ? group.members : []
    })
    setGroupDialogOpen(true)
  }

  const handleSaveGroup = async () => {
    if (!selectedClassroom || !groupFormData.name) {
      toast.error('Please fill in the group name')
      return
    }

    try {
      const groupData = {
        name: groupFormData.name,
        description: groupFormData.description || null,
        classroom_id: selectedClassroom.id,
        members: groupFormData.members.filter(m => m.name && m.name.trim() !== '').map(member => ({
          name: member.name,
          email_address: member.email_address || '',
          student_id: member.student_id || ''
        })),
        created_by: 1  // Default teacher ID
      }

      console.log('Sending group data:', groupData) // Debug log

      if (editingGroup) {
        await apiClient.updateGroup(editingGroup.id, groupData)
      } else {
        await apiClient.createGroup(groupData)
      }

      toast.success(editingGroup ? 'Group updated successfully' : 'Group created successfully')
      setGroupDialogOpen(false)
      fetchGroupsForClassroom(selectedClassroom.id)
      
      // Update groups count for the classroom
      if (selectedClassroom) {
        const groups = await apiClient.request<any[]>(`/api/v1/groups?classroom_id=${selectedClassroom.id}`)
        setClassroomGroupsCount(prev => ({
          ...prev,
          [selectedClassroom.id]: Array.isArray(groups) ? groups.length : 0
        }))
      }
    } catch (error) {
      console.error('Error saving group:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save group')
    }
  }

  const handleDeleteGroup = async () => {
    if (!groupToDelete) return

    try {
      await apiClient.deleteGroup(groupToDelete.id)

      toast.success('Group deleted successfully')
      setGroupDeleteDialogOpen(false)
      setGroupToDelete(null)
      if (selectedClassroom) {
        fetchGroupsForClassroom(selectedClassroom.id)
        
        // Update groups count for the classroom
        const groups = await apiClient.request<any[]>(`/api/v1/groups?classroom_id=${selectedClassroom.id}`)
        setClassroomGroupsCount(prev => ({
          ...prev,
          [selectedClassroom.id]: Array.isArray(groups) ? groups.length : 0
        }))
      }
    } catch (error) {
      console.error('Error deleting group:', error)
      toast.error('Failed to delete group')
    }
  }

  const addGroupMember = () => {
    setGroupFormData(prev => ({
      ...prev,
      members: [...prev.members, { name: '', email_address: '', student_id: '' }]
    }))
  }

  const removeGroupMember = (index: number) => {
    if (groupFormData.members.length > 1) {
      setGroupFormData(prev => ({
        ...prev,
        members: prev.members.filter((_, i) => i !== index)
      }))
    }
  }

  // Handle CSV import
  const handleImportCSV = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedClassroom) {
      toast.error('Please select a classroom first')
      return
    }

    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      toast.error('Please select a CSV file')
      return
    }

    try {
      const response = await apiClient.importGroupsFromCSV(selectedClassroom.id, file)
      
      toast.success(
        `Successfully imported ${response.groups_created || 0} groups with ${response.students_imported || 0} students`
      )
      
      // Refresh groups list
      if (selectedClassroom) {
        fetchGroupsForClassroom(selectedClassroom.id)
        
        // Update groups count
        const groups = await apiClient.request<any[]>(`/api/v1/groups?classroom_id=${selectedClassroom.id}`)
        setClassroomGroupsCount(prev => ({
          ...prev,
          [selectedClassroom.id]: Array.isArray(groups) ? groups.length : 0
        }))
      }
      
      // Reset file input
      event.target.value = ''
    } catch (error) {
      console.error('Error importing CSV:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to import CSV file')
      // Reset file input
      event.target.value = ''
    }
  }

  const updateGroupMember = (index: number, field: keyof GroupMember, value: string) => {
    setGroupFormData(prev => ({
      ...prev,
      members: prev.members.map((member, i) => 
        i === index ? { ...member, [field]: value } : member
      )
    }))
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Classroom Management</h1>
        <p className="text-gray-600">Manage classrooms for courses and semesters with teacher and language settings</p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Course</Label>
              <Select 
                value={selectedCourseId?.toString() || "all"} 
                onValueChange={(value) => setSelectedCourseId(value === "all" ? null : parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Courses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Courses</SelectItem>
                  {courses.map((course) => (
                    <SelectItem key={course.id} value={course.id.toString()}>
                      {course.code} - {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Semester</Label>
              <Select 
                value={selectedSemesterId?.toString() || "all"} 
                onValueChange={(value) => setSelectedSemesterId(value === "all" ? null : parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Semesters" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Semesters</SelectItem>
                  {filteredSemesters.map((semester) => (
                    <SelectItem key={semester.id} value={semester.id.toString()}>
                      {`${semester.season} ${semester.year}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button onClick={handleCreateClick} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Create Classroom
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Classrooms Table */}
      <Card>
        <CardHeader>
          <CardTitle>Classrooms ({classrooms.length})</CardTitle>
          <p className="text-sm text-gray-600">Click on any classroom row to expand/collapse and manage its groups</p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading classrooms...</div>
          ) : classrooms.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No classrooms found. Create your first classroom to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"></TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Teacher</TableHead>
                  <TableHead>Language</TableHead>
                  <TableHead>Course</TableHead>
                  <TableHead>Semester</TableHead>
                  <TableHead>Groups</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {classrooms.map((classroom) => (
                  <React.Fragment key={classroom.id}>
                    {/* Classroom Row */}
                    <TableRow 
                      className={`cursor-pointer hover:bg-gray-50 transition-colors ${selectedClassroom?.id === classroom.id ? 'bg-blue-50 border-l-4 border-blue-500' : 'hover:border-l-2 hover:border-gray-300'}`}
                      onClick={() => handleSelectClassroom(classroom)}
                    >
                      <TableCell className="w-12">
                        <div className="flex items-center justify-center">
                          {selectedClassroom?.id === classroom.id ? (
                            <ChevronDown className="h-4 w-4 text-blue-600 transition-colors" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-gray-400 hover:text-gray-600 transition-colors" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          {classroom.name}
                          {selectedClassroom?.id === classroom.id && (
                            <Badge variant="default" className="text-xs">Open</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{classroom.teacher_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          <Globe className="h-3 w-3 mr-1" />
                          {getLanguageLabel(classroom.language)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <BookOpen className="h-3 w-3" />
                          {getCourseLabelForClassroom(classroom)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getSemesterLabel(classroom.semester_id)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          <Users className="h-3 w-3 mr-1" />
                          {classroomGroupsCount[classroom.id] ?? 0}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleEditClick(classroom)
                            }}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              setClassroomToDelete(classroom)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>

                    {/* Groups Row - Only show when this classroom is selected */}
                    {selectedClassroom?.id === classroom.id && (
                      <TableRow>
                        <TableCell colSpan={8} className="p-0 bg-gray-50">
                          <div className="p-6 border-t border-gray-200">
                            <div className="flex justify-between items-start mb-6">
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-1">
                                  <Users className="h-5 w-5 text-blue-600" />
                                  Student Groups
                                </h3>
                                <p className="text-sm text-gray-600">
                                  Manage groups for {classroom.name}
                                </p>
                              </div>
                              <div className="flex gap-2">
                                <input
                                  type="file"
                                  accept=".csv"
                                  onChange={handleImportCSV}
                                  className="hidden"
                                  id="csv-import-input"
                                />
                                <Button
                                  variant="outline"
                                  onClick={() => document.getElementById('csv-import-input')?.click()}
                                  className="shadow-sm"
                                >
                                  <Upload className="h-4 w-4 mr-2" />
                                  Import CSV
                                </Button>
                                <Button onClick={handleCreateGroup} className="shadow-sm">
                                  <Plus className="h-4 w-4 mr-2" />
                                  Add Group
                                </Button>
                              </div>
                            </div>
                            
                            {groups.length === 0 ? (
                              <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
                                <div className="flex flex-col items-center">
                                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                                    <Users className="h-8 w-8 text-gray-400" />
                                  </div>
                                  <h4 className="text-lg font-medium text-gray-900 mb-2">No groups yet</h4>
                                  <p className="text-gray-600 mb-4 max-w-sm">
                                    Create your first student group to organize students for assignments and projects.
                                  </p>
                                  <Button onClick={handleCreateGroup} variant="outline">
                                    <Plus className="h-4 w-4 mr-2" />
                                    Create First Group
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="grid gap-4">
                                {groups.map((group) => (
                                  <div key={group.id} className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                    <div className="p-4">
                                      <div className="flex justify-between items-start mb-3">
                                        <div className="flex-1">
                                          <div className="flex items-center gap-3 mb-2">
                                            <h4 className="text-base font-semibold text-gray-900">{group.name}</h4>
                                            <div className="flex gap-2">
                                              <Badge variant="secondary" className="text-xs">
                                                {group.members.length} member{group.members.length !== 1 ? 's' : ''}
                                              </Badge>
                                            </div>
                                          </div>
                                          {group.description && (
                                            <p className="text-sm text-gray-600 mb-2">{group.description}</p>
                                          )}
                                        </div>
                                        <div className="flex gap-1 ml-4">
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleEditGroup(group)}
                                            className="h-8 w-8 p-0"
                                          >
                                            <Edit className="h-4 w-4" />
                                          </Button>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => {
                                              setGroupToDelete(group)
                                              setGroupDeleteDialogOpen(true)
                                            }}
                                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                                          >
                                            <Trash className="h-4 w-4" />
                                          </Button>
                                        </div>
                                      </div>
                                      
                                      {group.members.length > 0 && (
                                        <div className="border-t border-gray-100 pt-3">
                                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                                            Members
                                          </p>
                                          <div className="flex flex-wrap gap-2">
                                            {group.members.map((member, index) => (
                                              <Badge key={index} variant="secondary" className="text-xs">
                                                {typeof member === 'string' ? member : member.name || 'Unknown'}
                                              </Badge>
                                            ))}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingClassroom ? 'Edit Classroom' : 'Create New Classroom'}
            </DialogTitle>
            <DialogDescription>
              {editingClassroom 
                ? 'Update the classroom information below' 
                : 'Fill in the information to create a new classroom'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="e.g., CS101 - Fall 2024 - Morning Section"
              />
            </div>

            {/* Teacher Name */}
            <div className="grid gap-2">
              <Label htmlFor="teacher_name">Teacher Name *</Label>
              <Input
                id="teacher_name"
                value={formData.teacher_name}
                onChange={(e) => handleInputChange('teacher_name', e.target.value)}
                placeholder="e.g., Dr. John Smith"
              />
            </div>

            {/* Language */}
            <div className="grid gap-2">
              <Label htmlFor="language">Language *</Label>
              <Select value={formData.language} onValueChange={(value) => handleInputChange('language', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.value} value={lang.value}>
                      {lang.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Course */}
            <div className="grid gap-2">
              <Label htmlFor="course_id">Course *</Label>
              <Select 
                value={formData.course_id?.toString() || ""} 
                onValueChange={(value) => handleInputChange('course_id', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a course" />
                </SelectTrigger>
                <SelectContent>
                  {courses.map((course) => (
                    <SelectItem key={course.id} value={course.id.toString()}>
                      {course.code} - {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Semester */}
            <div className="grid gap-2">
              <Label htmlFor="semester_id">Semester *</Label>
              <Select 
                value={formData.semester_id?.toString() || ""} 
                onValueChange={(value) => handleInputChange('semester_id', parseInt(value))}
                disabled={!formData.course_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder={formData.course_id ? "Select a semester" : "Select a course first"} />
                </SelectTrigger>
                <SelectContent>
                  {filteredSemesters.map((semester) => (
                    <SelectItem key={semester.id} value={semester.id.toString()}>
                      {`${semester.season} ${semester.year}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Additional information about this classroom..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>
              {editingClassroom ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Classroom</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{classroomToDelete?.name}"? This action cannot be undone.
              {classroomToDelete?.groups && classroomToDelete.groups.length > 0 && (
                <div className="mt-2 text-amber-600 font-semibold">
                  Warning: This classroom has {classroomToDelete.groups.length} group(s) associated with it.
                </div>
              )}
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

      {/* Group Create/Edit Dialog */}
      <Dialog open={groupDialogOpen} onOpenChange={setGroupDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingGroup ? 'Edit Group' : 'Create New Group'}
            </DialogTitle>
            <DialogDescription>
              {editingGroup 
                ? 'Update the group information below' 
                : 'Fill in the information to create a new group'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Group Name */}
            <div className="grid gap-2">
              <Label htmlFor="group_name">Group Name *</Label>
              <Input
                id="group_name"
                value={groupFormData.name}
                onChange={(e) => setGroupFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Group A, Team Alpha"
              />
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="group_description">Description</Label>
              <Textarea
                id="group_description"
                value={groupFormData.description}
                onChange={(e) => setGroupFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Optional description for this group..."
                rows={2}
              />
            </div>


            {/* Group Members */}
            <div className="grid gap-2">
              <Label>Group Members</Label>
              {groupFormData.members.length === 0 ? (
                <p className="text-sm text-muted-foreground mb-2">No members added yet. Click "Add Member" to add students to this group.</p>
              ) : null}
              {groupFormData.members.map((member, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input
                    placeholder="Student name"
                    value={member.name}
                    onChange={(e) => updateGroupMember(index, 'name', e.target.value)}
                  />
                  <Input
                    placeholder="Email"
                    value={member.email_address}
                    onChange={(e) => updateGroupMember(index, 'email_address', e.target.value)}
                  />
                  <Input
                    placeholder="Student ID"
                    value={member.student_id}
                    onChange={(e) => updateGroupMember(index, 'student_id', e.target.value)}
                  />
                  {groupFormData.members.length > 1 && (
                    <Button 
                      type="button" 
                      variant="outline" 
                      size="sm" 
                      onClick={() => removeGroupMember(index)}
                    >
                      <UserMinus className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button type="button" variant="outline" onClick={addGroupMember}>
                <UserPlus className="mr-2 h-4 w-4" />
                Add Member
              </Button>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setGroupDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveGroup}>
              {editingGroup ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Group Delete Confirmation Dialog */}
      <Dialog open={groupDeleteDialogOpen} onOpenChange={setGroupDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Group</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{groupToDelete?.name}"? This action cannot be undone.
              {groupToDelete?.members && groupToDelete.members.length > 0 && (
                <div className="mt-2 text-amber-600 font-semibold">
                  Warning: This group has {groupToDelete.members.length} member(s).
                </div>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGroupDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteGroup}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

