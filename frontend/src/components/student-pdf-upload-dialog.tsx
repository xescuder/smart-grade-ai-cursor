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
  const [selectedCoordinators, setSelectedCoordinators] = useState<string[]>([])
  const [meetingNotes, setMeetingNotes] = useState<boolean>(false)
  const [mainFile, setMainFile] = useState<File | null>(null)
  const [privateFile, setPrivateFile] = useState<File | null>(null)
  const [publicFile, setPublicFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  // Get group members for student selection
  const groupMembers = submission?.group?.members || []
  const studentOptions = groupMembers.map((member: any) => ({
    value: member.name || member.email || 'Unknown',
    label: member.name || member.email || 'Unknown'
  }))
  
  // If no group members, provide default options
  const defaultStudentOptions = [
    { value: 'Coordinator 1', label: 'Coordinator 1' },
    { value: 'Coordinator 2', label: 'Coordinator 2' }
  ]
  
  const finalStudentOptions = studentOptions.length > 0 ? studentOptions : defaultStudentOptions

  const handleCoordinatorToggle = (coordinatorName: string) => {
    if (selectedCoordinators.includes(coordinatorName)) {
      setSelectedCoordinators(selectedCoordinators.filter(name => name !== coordinatorName))
    } else {
      setSelectedCoordinators([...selectedCoordinators, coordinatorName])
    }
  }

  const handleMainFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Only PDF files are allowed')
        return
      }
      setMainFile(file)
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
      
      // Auto-select first coordinator if none selected and coordinators are required
      if (selectedCoordinators.length === 0 && finalStudentOptions.length > 0) {
        setSelectedCoordinators([finalStudentOptions[0].value])
      }
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
      
      // Auto-select first coordinator if none selected and coordinators are required
      if (selectedCoordinators.length === 0 && finalStudentOptions.length > 0) {
        setSelectedCoordinators([finalStudentOptions[0].value])
      }
    }
  }

  const handleUpload = async () => {
    // Only require coordinators if uploading private or public reports
    if ((privateFile || publicFile) && selectedCoordinators.length === 0) {
      toast.error('Please select at least one coordinator for private/public reports')
      return
    }

    if (!mainFile && !privateFile && !publicFile) {
      toast.error('Please upload at least one PDF file')
      return
    }

    setIsUploading(true)

    try {
      const uploadPromises = []

      // Upload main submission PDF if provided
      if (mainFile) {
        const mainFormData = new FormData()
        mainFormData.append('pdf_file', mainFile)
        mainFormData.append('meeting_notes', meetingNotes.toString())

        const mainUpload = fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${submission.id}/pdf`, {
          method: 'PUT',
          headers: getAuthHeadersForFileUpload(),
          body: mainFormData
        })
        uploadPromises.push(mainUpload)
      }

          // Upload private PDF if provided
          if (privateFile) {
            const privateFormData = new FormData()
            privateFormData.append('pdf_file', privateFile)
            privateFormData.append('coordinators', JSON.stringify(selectedCoordinators))

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
            publicFormData.append('coordinators', JSON.stringify(selectedCoordinators))

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
        if (mainFile) uploadedFiles.push('Main PDF')
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
    setSelectedCoordinators([])
    setMeetingNotes(false)
    setMainFile(null)
    setPrivateFile(null)
    setPublicFile(null)
  }

  const handleClose = () => {
    onOpenChange(false)
    resetForm()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Submission Reports</DialogTitle>
              <DialogDescription>
                Select coordinators and upload PDF reports for submission: {submission?.assignment?.name}
              </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Coordinator Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">
              Coordinators (for Private/Public Reports)
              <span className="text-xs text-gray-500 ml-1">(optional)</span>
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {finalStudentOptions.map((option) => (
                <Button
                  key={option.value}
                  variant={selectedCoordinators.includes(option.value) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleCoordinatorToggle(option.value)}
                  className="justify-start"
                >
                  {selectedCoordinators.includes(option.value) ? (
                    <Users className="h-4 w-4 mr-2" />
                  ) : (
                    <User className="h-4 w-4 mr-2" />
                  )}
                  {option.label}
                </Button>
              ))}
            </div>
            {selectedCoordinators.length > 0 && (
              <div className="text-sm text-gray-600">
                Selected: {selectedCoordinators.join(', ')}
              </div>
            )}
            {studentOptions.length === 0 && (
              <div className="text-xs text-gray-500">
                No group members found. Using default coordinator options.
              </div>
            )}
          </div>

          {/* Meeting Notes Checkbox */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="meeting-notes"
                checked={meetingNotes}
                onChange={(e) => setMeetingNotes(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <Label htmlFor="meeting-notes" className="text-sm font-medium">
                Meeting notes
              </Label>
            </div>
          </div>

          {/* Main Submission PDF Upload */}
          <div className="space-y-2">
            <Label htmlFor="main-file" className="text-sm font-medium">Main Submission PDF</Label>
            <div className="flex items-center space-x-2">
              <Input
                id="main-file"
                type="file"
                accept=".pdf"
                onChange={handleMainFileSelect}
                className="flex-1"
              />
              {mainFile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMainFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            {mainFile && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="h-4 w-4" />
                <span>{mainFile.name}</span>
                <span>({(mainFile.size / 1024 / 1024).toFixed(2)} MB)</span>
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
                  disabled={((privateFile || publicFile) && selectedCoordinators.length === 0) || (!mainFile && !privateFile && !publicFile) || isUploading}
                  className="flex items-center space-x-2"
                >
                  <Upload className="h-4 w-4" />
                  <span>{isUploading ? 'Uploading...' : 'Upload All Reports'}</span>
                </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
