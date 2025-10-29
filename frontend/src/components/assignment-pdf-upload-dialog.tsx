"use client"

import { getAuthHeaders } from "@/lib/utils"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FileText, Upload, X } from "lucide-react"
import { toast } from "sonner"
import { Assignment } from "@/types/assignment"

interface AssignmentPdfUploadDialogProps {
  assignment: Assignment | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function AssignmentPdfUploadDialog({ 
  assignment, 
  open, 
  onOpenChange, 
  onSuccess 
}: AssignmentPdfUploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type !== "application/pdf") {
        toast.error("Please select a PDF file")
        return
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error("File size must be less than 10MB")
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !assignment?.id) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/upload/statement`, {
        method: 'POST',
        headers: {
          'Authorization': getAuthHeaders()['Authorization'] || '',
        },
        body: formData,
      })

      if (response.ok) {
        toast.success("PDF uploaded successfully!")
        onSuccess()
        handleClose()
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to upload PDF")
      }
    } catch (error) {
      console.error("Error uploading PDF:", error)
      toast.error("Failed to upload PDF")
    } finally {
      setIsUploading(false)
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    onOpenChange(false)
  }

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  if (!assignment) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Upload PDF</DialogTitle>
          <DialogDescription>
            Upload a PDF file for assignment "{assignment.name}"
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Current PDF Status */}
          {assignment.pdf_file_name && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">
                  Current PDF: {assignment.pdf_file_name}
                </span>
              </div>
              <p className="text-xs text-blue-600 mt-1">
                Uploading a new PDF will replace the current one.
              </p>
            </div>
          )}

          {/* File Upload Area */}
          <div className="space-y-2">
            <Label htmlFor="pdf-file">Select PDF File</Label>
            <Input
              id="pdf-file"
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
            <p className="text-xs text-gray-500">
              Maximum file size: 10MB. Only PDF files are allowed.
            </p>
          </div>

          {/* Selected File Display */}
          {selectedFile && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-green-800">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-green-600">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFile(null)}
                  className="h-6 w-6 p-0 text-green-600 hover:text-green-800"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpload} 
            disabled={!selectedFile || isUploading}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            {isUploading ? "Uploading..." : "Upload PDF"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
