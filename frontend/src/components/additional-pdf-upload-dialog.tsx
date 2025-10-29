/* eslint-disable @typescript-eslint/no-explicit-any */
"use client"

import React, { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Upload, FileText, X, User, Users } from 'lucide-react'
import { toast } from 'sonner'
import { getAuthHeadersForFileUpload } from '@/lib/utils'

interface StudentPdfUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  submission: any
  onSuccess: () => void
}

export function StudentPdfUploadDialog({
  open,
  onOpenChange,
  submission,
  onSuccess
}: StudentPdfUploadDialogProps) {
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])
  const [privateFile, setPrivateFile] = useState<File | null>(null)
  const [publicFile, setPublicFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  // Get group members for student selection
  const groupMembers = submission?.group?.members || []
  const studentOptions = groupMembers.map((member: any) => ({
    value: member.name,
    label: member.name
  }))

  const handleStudentSelect = (studentName: string) => {
    if (selectedStudents.includes(studentName)) {
      setSelectedStudents(selectedStudents.filter(name => name !== studentName))
    } else if (selectedStudents.length < 2) {
      setSelectedStudents([...selectedStudents, studentName])
    } else {
      toast.error('You can select maximum 2 students')
    }
  }

  const handlePrivateFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Only PDF files are allowed')
        return
      }
      setPrivateFile(file)
    }
  }

  const handlePublicFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Only PDF files are allowed')
        return
      }
      setPublicFile(file)
    }
  }

  const handleUpload = async () => {
    if (selectedStudents.length === 0) {
      toast.error('Please select at least one student')
      return
    }

    if (!privateFile && !publicFile) {
      toast.error('Please upload at least one PDF file')
      return
    }

    setIsUploading(true)

    try {
      const uploadPromises = []

      // Upload private PDF if provided
      if (privateFile) {
        const privateFormData = new FormData()
        privateFormData.append('pdf_file', privateFile)
        privateFormData.append('coordinators', JSON.stringify(selectedStudents))

        const privateUpload = fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${submission.id}/private-pdf`, {
          method: 'PUT',
          headers: getAuthHeadersForFileUpload(),
          body: privateFormData
        })
        uploadPromises.push(privateUpload)
      }

      // Upload public PDF if provided
      if (publicFile) {
        const publicFormData = new FormData()
        publicFormData.append('pdf_file', publicFile)
        publicFormData.append('coordinators', JSON.stringify(selectedStudents))

        const publicUpload = fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${submission.id}/public-pdf`, {
          method: 'PUT',
          headers: getAuthHeadersForFileUpload(),
          body: publicFormData
        })
        uploadPromises.push(publicUpload)
      }

      // Wait for all uploads to complete
      const responses = await Promise.all(uploadPromises)
      
      // Check if all uploads were successful
      const allSuccessful = responses.every(response => response.ok)
      
      if (allSuccessful) {
        const uploadedFiles = []
        if (privateFile) uploadedFiles.push('Private PDF')
        if (publicFile) uploadedFiles.push('Public PDF')
        
        toast.success(`Successfully uploaded: ${uploadedFiles.join(', ')}`)
        onSuccess()
        onOpenChange(false)
        resetForm()
      } else {
        const errorTexts = await Promise.all(
          responses.map(async (response) => {
            if (!response.ok) {
              return await response.text()
            }
            return null
          })
        )
        
        const errors = errorTexts.filter(text => text !== null)
        console.error('Upload errors:', errors)
        toast.error('Some files failed to upload. Please try again.')
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload files')
    } finally {
      setIsUploading(false)
    }
  }

  const resetForm = () => {
    setSelectedStudents([])
    setPrivateFile(null)
    setPublicFile(null)
  }

  const handleClose = () => {
    onOpenChange(false)
    resetForm()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Student Reports</DialogTitle>
          <DialogDescription>
            Select responsible students and upload private/public PDF reports for submission: {submission?.assignment?.name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Student Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Responsible Students (max 2)</Label>
            <div className="grid grid-cols-2 gap-2">
              {studentOptions.map((option: { value: string; label: string }) => (
                <Button
                  key={option.value}
                  variant={selectedStudents.includes(option.value) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleStudentSelect(option.value)}
                  className="justify-start"
                  disabled={!selectedStudents.includes(option.value) && selectedStudents.length >= 2}
                >
                  {selectedStudents.includes(option.value) ? (
                    <Users className="h-4 w-4 mr-2" />
                  ) : (
                    <User className="h-4 w-4 mr-2" />
                  )}
                  {option.label}
                </Button>
              ))}
            </div>
            {selectedStudents.length > 0 && (
              <div className="text-sm text-gray-600">
                Selected: {selectedStudents.join(', ')}
              </div>
            )}
          </div>

          {/* Private PDF Upload */}
          <div className="space-y-2">
            <Label htmlFor="private-file" className="text-sm font-medium">Private Report (PDF)</Label>
            <div className="flex items-center space-x-2">
              <Input
                id="private-file"
                type="file"
                accept=".pdf"
                onChange={handlePrivateFileSelect}
                className="flex-1"
              />
              {privateFile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPrivateFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            {privateFile && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="h-4 w-4" />
                <span>{privateFile.name}</span>
                <span>({(privateFile.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
            )}
          </div>

          {/* Public PDF Upload */}
          <div className="space-y-2">
            <Label htmlFor="public-file" className="text-sm font-medium">Public Report (PDF)</Label>
            <div className="flex items-center space-x-2">
              <Input
                id="public-file"
                type="file"
                accept=".pdf"
                onChange={handlePublicFileSelect}
                className="flex-1"
              />
              {publicFile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPublicFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            {publicFile && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="h-4 w-4" />
                <span>{publicFile.name}</span>
                <span>({(publicFile.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
            )}
          </div>

          {/* Upload Button */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpload} 
              disabled={selectedStudents.length === 0 || (!privateFile && !publicFile) || isUploading}
              className="flex items-center space-x-2"
            >
              <Upload className="h-4 w-4" />
              <span>{isUploading ? 'Uploading...' : 'Upload Reports'}</span>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
