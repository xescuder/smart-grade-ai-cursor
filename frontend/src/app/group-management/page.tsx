"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Edit, Plus, Trash2, Users, UserPlus, UserMinus, BookOpen, Calendar } from "lucide-react"
import { toast } from "sonner"

interface GroupMember {
  name: string
  email_address: string
  student_id: string
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
}

interface Group {
  id: number
  name: string
  nickname?: string  // Optional nickname like "Mandalorian"
  description?: string
  classroom_id?: number
  course_id?: number
  semester_id?: number
  classroom?: Classroom
  course?: Course
  semester?: Semester
  members: GroupMember[]
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

export default function GroupManagementPage() {
  const [groups, setGroups] = useState<Group[]>([])
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
  const [loading, setLoading] = useState(true)

  // Form states
  const [newGroup, setNewGroup] = useState<{
    name: string
    nickname: string
    description: string
    classroom_id: string
    members: GroupMember[]
  }>({
    name: '',
    nickname: '',
    description: '',
    classroom_id: 'none',
    members: []
  })

  const [editGroup, setEditGroup] = useState<{
    name: string
    nickname: string
    description: string
    classroom_id: string
    members: GroupMember[]
  }>({
    name: '',
    nickname: '',
    description: '',
    classroom_id: 'none',
    members: []
  })

  // Fetch data on component mount
  useEffect(() => {
    fetchGroups()
    fetchClassrooms()
  }, [])

  const fetchGroups = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/groups?created_by=1')  // Default teacher ID
      if (response.ok) {
        const data = await response.json()
        // Ensure data is an array before setting
        setGroups(Array.isArray(data) ? data : [])
      } else {
        console.error('Error response from API:', response.status)
        toast.error('Failed to fetch groups')
        setGroups([])
      }
    } catch (error) {
      console.error('Error fetching groups:', error)
      toast.error('Failed to fetch groups')
      setGroups([])
    } finally {
      setLoading(false)
    }
  }

  const fetchClassrooms = async () => {
    try {
      const response = await fetch('/api/v1/classrooms')
      if (response.ok) {
        const data = await response.json()
        setClassrooms(Array.isArray(data) ? data : [])
      } else {
        console.error('Failed to fetch classrooms')
        setClassrooms([])
      }
    } catch (error) {
      console.error('Error fetching classrooms:', error)
      setClassrooms([])
    }
  }

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newGroup.name) {
      toast.error('Please fill in the group name')
      return
    }

    try {
      const groupData = {
        name: newGroup.name,
        nickname: newGroup.nickname || null,
        description: newGroup.description || null,
        classroom_id: newGroup.classroom_id && newGroup.classroom_id !== 'none' ? parseInt(newGroup.classroom_id) : null,
        members: newGroup.members.filter(m => m.name).length > 0 ? newGroup.members.filter(m => m.name) : [],
        created_by: 1  // Default teacher ID
      }

      const response = await fetch('/api/v1/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(groupData)
      })

      if (response.ok) {
        toast.success('Group created successfully')
        setIsCreateDialogOpen(false)
        fetchGroups()
        // Reset form
        setNewGroup({
          name: '',
          nickname: '',
          description: '',
          classroom_id: 'none',
          members: []
        })
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to create group')
      }
    } catch (error) {
      console.error('Error creating group:', error)
      toast.error('Failed to create group')
    }
  }

  const handleEditGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedGroup || !editGroup.name) {
      toast.error('Please fill in required fields')
      return
    }

    try {
      const groupData = {
        name: editGroup.name,
        nickname: editGroup.nickname || null,
        description: editGroup.description || null,
        classroom_id: editGroup.classroom_id && editGroup.classroom_id !== 'none' ? parseInt(editGroup.classroom_id) : null,
        members: editGroup.members.filter(m => m.name).length > 0 ? editGroup.members.filter(m => m.name) : []
      }

      const response = await fetch(`/api/v1/groups/${selectedGroup.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(groupData)
      })

      if (response.ok) {
        toast.success('Group updated successfully')
        setIsEditDialogOpen(false)
        fetchGroups()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to update group')
      }
    } catch (error) {
      console.error('Error updating group:', error)
      toast.error('Failed to update group')
    }
  }

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('Are you sure you want to delete this group?')) return

    try {
      const response = await fetch(`/api/v1/groups/${groupId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Group deleted successfully')
        fetchGroups()
      } else {
        toast.error('Failed to delete group')
      }
    } catch (error) {
      console.error('Error deleting group:', error)
      toast.error('Failed to delete group')
    }
  }

  const openEditDialog = (group: Group) => {
    setSelectedGroup(group)
    setEditGroup({
      name: group.name,
      nickname: group.nickname || '',
      description: group.description || '',
      classroom_id: group.classroom_id?.toString() || 'none',
      members: group.members.length > 0 ? group.members : []
    })
    setIsEditDialogOpen(true)
  }

  const addGroupMember = (isEdit = false) => {
    if (isEdit) {
      setEditGroup(prev => ({
        ...prev,
        members: [...prev.members, { name: '', email_address: '', student_id: '' }]
      }))
    } else {
      setNewGroup(prev => ({
        ...prev,
        members: [...prev.members, { name: '', email_address: '', student_id: '' }]
      }))
    }
  }

  const removeGroupMember = (index: number, isEdit = false) => {
    if (isEdit) {
      if (editGroup.members.length > 1) {
        setEditGroup(prev => ({
          ...prev,
          members: prev.members.filter((_, i) => i !== index)
        }))
      }
    } else {
      if (newGroup.members.length > 1) {
        setNewGroup(prev => ({
          ...prev,
          members: prev.members.filter((_, i) => i !== index)
        }))
      }
    }
  }

  const updateGroupMember = (index: number, field: keyof GroupMember, value: string, isEdit = false) => {
    if (isEdit) {
      setEditGroup(prev => ({
        ...prev,
        members: prev.members.map((member, i) => 
          i === index ? { ...member, [field]: value } : member
        )
      }))
    } else {
      setNewGroup(prev => ({
        ...prev,
        members: prev.members.map((member, i) => 
          i === index ? { ...member, [field]: value } : member
        )
      }))
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const renderMemberForm = (members: GroupMember[], isEdit = false) => (
    <div>
      <Label>Group Members</Label>
      {members.length === 0 ? (
        <p className="text-sm text-muted-foreground mb-2">No members added yet. Click "Add Member" to add students to this group.</p>
      ) : null}
      {members.map((member, index) => (
        <div key={index} className="flex gap-2 mb-2">
          <Input
            placeholder="Student name"
            value={member.name}
            onChange={(e) => updateGroupMember(index, 'name', e.target.value, isEdit)}
          />
          <Input
            placeholder="Email"
            value={member.email_address}
            onChange={(e) => updateGroupMember(index, 'email_address', e.target.value, isEdit)}
          />
          <Input
            placeholder="Student ID"
            value={member.student_id}
            onChange={(e) => updateGroupMember(index, 'student_id', e.target.value, isEdit)}
          />
          {members.length > 1 && (
            <Button 
              type="button" 
              variant="outline" 
              size="sm" 
              onClick={() => removeGroupMember(index, isEdit)}
            >
              <UserMinus className="h-4 w-4" />
            </Button>
          )}
        </div>
      ))}
      <Button type="button" variant="outline" onClick={() => addGroupMember(isEdit)}>
        <UserPlus className="mr-2 h-4 w-4" />
        Add Member
      </Button>
    </div>
  )

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Group Management</h1>
          <p className="text-muted-foreground">Manage student groups for assignments and projects</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Group
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Group</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Group Name *</Label>
                  <Input
                    id="name"
                    value={newGroup.name}
                    onChange={(e) => setNewGroup(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter group name"
                  />
                </div>
                <div>
                  <Label htmlFor="nickname">Nickname</Label>
                  <Input
                    id="nickname"
                    value={newGroup.nickname || ''}
                    onChange={(e) => setNewGroup(prev => ({ ...prev, nickname: e.target.value }))}
                    placeholder="e.g., Mandalorian"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="classroom_id">Classroom *</Label>
                <Select value={newGroup.classroom_id} onValueChange={(value) => setNewGroup(prev => ({ ...prev, classroom_id: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a classroom" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No classroom</SelectItem>
                    {classrooms.map(classroom => (
                      <SelectItem key={classroom.id} value={classroom.id.toString()}>
                        {classroom.name} - {classroom.teacher_name} ({classroom.language.toUpperCase()})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Course and Semester are now managed through Classroom selection */}

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newGroup.description}
                  onChange={(e) => setNewGroup(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Optional description"
                />
              </div>

              {renderMemberForm(newGroup.members, false)}

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Group</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Groups Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Groups ({groups.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading groups...</div>
          ) : groups.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No groups found
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Course</TableHead>
                  <TableHead>Members</TableHead>
                  <TableHead>Semester</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.map(group => (
                  <TableRow key={group.id}>
                    <TableCell className="font-medium">
                      <div>
                        <div className="font-semibold">
                          {group.name}
                          {group.nickname && (
                            <span className="ml-2 text-sm font-normal text-blue-600">
                              "{group.nickname}"
                            </span>
                          )}
                        </div>
                        {group.description && (
                          <div className="text-sm text-muted-foreground">{group.description}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {group.course ? (
                        <div className="flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          {group.course.name} ({group.course.code})
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">
                          {group.members.length}
                        </Badge>
                        <div className="text-sm text-muted-foreground">
                          {group.members.length === 0 ? (
                            'No members'
                          ) : (
                            <>
                              {group.members.slice(0, 2).map(m => m.name).join(', ')}
                              {group.members.length > 2 && ` +${group.members.length - 2} more`}
                            </>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {group.semester ? (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {group.semester.name} ({group.semester.code})
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(group.created_at)}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openEditDialog(group)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteGroup(group.id)}
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

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Group</DialogTitle>
          </DialogHeader>
          {selectedGroup && (
            <form onSubmit={handleEditGroup} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit_name">Group Name *</Label>
                  <Input
                    id="edit_name"
                    value={editGroup.name}
                    onChange={(e) => setEditGroup(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter group name"
                  />
                </div>
                <div>
                  <Label htmlFor="edit_nickname">Nickname</Label>
                  <Input
                    id="edit_nickname"
                    value={editGroup.nickname || ''}
                    onChange={(e) => setEditGroup(prev => ({ ...prev, nickname: e.target.value }))}
                    placeholder="e.g., Mandalorian"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="edit_classroom_id">Classroom *</Label>
                <Select value={editGroup.classroom_id} onValueChange={(value) => setEditGroup(prev => ({ ...prev, classroom_id: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a classroom" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No classroom</SelectItem>
                    {classrooms.map(classroom => (
                      <SelectItem key={classroom.id} value={classroom.id.toString()}>
                        {classroom.name} - {classroom.teacher_name} ({classroom.language.toUpperCase()})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Course and Semester are now managed through Classroom selection */}

              <div>
                <Label htmlFor="edit_description">Description</Label>
                <Textarea
                  id="edit_description"
                  value={editGroup.description}
                  onChange={(e) => setEditGroup(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Optional description"
                />
              </div>

              {renderMemberForm(editGroup.members, true)}

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">Update Group</Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
