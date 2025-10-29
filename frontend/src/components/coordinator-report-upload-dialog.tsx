/* eslint-disable @typescript-eslint/no-explicit-any */
"use client"

import React, { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Upload, FileText, X } from 'lucide-react'
import { toast } from 'sonner'
import { getAuthHeadersForFileUpload } from '@/lib/utils'

interface AdditionalPdfUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  submission: any
  onSuccess: () => void
}

export function AdditionalPdfUploadDialog({
  open,
  onOpenChange,
  submission,
  onSuccess
}: AdditionalPdfUploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadType, setUploadType] = useState<'private' | 'public'>('private')

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Only PDF files are allowed')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file to upload')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('pdf_file', selectedFile)
      
      // Determine coordinators - use existing coordinators or first group member as fallback
      let coordinators = []
      if (submission?.coordinators) {
        try {
          coordinators = JSON.parse(submission.coordinators)
        } catch {
          // If parsing fails, use as string
          coordinators = [submission.coordinators]
        }
      } else if (submission?.group?.members?.length > 0) {
        // Fallback: use first member as coordinator
        coordinators = [submission.group.members[0].name]
      } else {
        // Last fallback: use a generic coordinator name
        coordinators = ['Coordinator']
      }
      
      formData.append('coordinators', JSON.stringify(coordinators))

      const endpoint = uploadType === 'private' 
        ? `/api/v1/submissions/${submission.id}/private-pdf`
        : `/api/v1/submissions/${submission.id}/public-pdf`

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${endpoint}`, {
        method: 'PUT',
        headers: getAuthHeadersForFileUpload(),
        body: formData
      })

      if (response.ok) {
        // Await and ignore unused result for lint compliance
        await response.json()
        toast.success(`${uploadType === 'private' ? 'Private' : 'Public'} PDF uploaded successfully`)
        onSuccess()
        onOpenChange(false)
        resetForm()
      } else {
        const errorText = await response.text()
        console.error('Upload error response:', errorText)
        try {
          const error = JSON.parse(errorText)
          toast.error(error.detail || 'Failed to upload PDF')
        } catch {
          toast.error('Failed to upload PDF')
        }
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload PDF')
    } finally {
      setIsUploading(false)
    }
  }

  const resetForm = () => {
    setSelectedFile(null)
    setUploadType('private')
  }

  const handleClose = () => {
    onOpenChange(false)
    resetForm()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Additional PDF</DialogTitle>
          <DialogDescription>
            Upload an additional PDF file for submission: {submission?.assignment?.name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Upload Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="upload-type">PDF Type</Label>
            <Select value={uploadType} onValueChange={(value: 'private' | 'public') => setUploadType(value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select PDF type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="private">Private PDF</SelectItem>
                <SelectItem value="public">Public PDF</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="file">Upload PDF</Label>
            <div className="flex items-center space-x-2">
              <Input
                id="file"
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="flex-1"
              />
              {selectedFile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            {selectedFile && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="h-4 w-4" />
                <span>{selectedFile.name}</span>
                <span>({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
            )}
          </div>

          {/* Upload Button */}
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpload} 
              disabled={!selectedFile || isUploading}
              className="flex items-center space-x-2"
            >
              <Upload className="h-4 w-4" />
              <span>{isUploading ? 'Uploading...' : 'Upload PDF'}</span>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
