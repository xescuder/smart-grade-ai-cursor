/**
 * Submission PDF Viewer Dialog Component
 * Dedicated dialog for viewing submission PDFs with full-screen experience
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { X, Download, ZoomIn, ZoomOut, RotateCw, FileText } from "lucide-react"

interface SubmissionPdfViewerDialogProps {
  submission: any // Submission object with PDF data
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SubmissionPdfViewerDialog({ 
  submission, 
  open, 
  onOpenChange 
}: SubmissionPdfViewerDialogProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [pdfUrl, setPdfUrl] = useState("")
  const [zoom, setZoom] = useState(100)

  // Load PDF when dialog opens
  useEffect(() => {
    if (open && submission?.id) {
      loadPdf()
    }
  }, [open, submission?.id])

  const loadPdf = async () => {
    if (!submission?.id) return

    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/submissions/${submission.id}/pdf`, {
        headers: {
          ...getAuthHeaders(),
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        setPdfUrl(url)
      } else {
        setError("Failed to load PDF")
      }
    } catch (error) {
      setError("An error occurred while loading the PDF")
    } finally {
      setIsLoading(false)
    }
  }

  // Clean up blob URL when dialog closes
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl)
      }
    }
  }, [pdfUrl])

  // Clean up when dialog closes
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && pdfUrl) {
      URL.revokeObjectURL(pdfUrl)
      setPdfUrl("")
    }
    onOpenChange(newOpen)
  }

  // Download PDF
  const handleDownload = () => {
    if (pdfUrl) {
      const link = document.createElement('a')
      link.href = pdfUrl
      link.download = `${submission?.assignment?.name || 'submission'}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50))
  const handleResetZoom = () => setZoom(100)

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent 
        className="overflow-hidden flex flex-col"
        style={{
          maxWidth: '95vw',
          width: '95vw',
          height: '95vh',
          maxHeight: '95vh'
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center justify-between">
            <span>Submission PDF: {submission?.pdf_file_name || 'Submission'}</span>
            <div className="flex items-center gap-2">
              {/* Zoom Controls */}
              <div className="flex items-center gap-1 text-sm">
                <Button variant="ghost" size="sm" onClick={handleZoomOut} disabled={zoom <= 50}>
                  <ZoomOut className="h-3 w-3" />
                </Button>
                <span className="min-w-[3rem] text-center">{zoom}%</span>
                <Button variant="ghost" size="sm" onClick={handleZoomIn} disabled={zoom >= 200}>
                  <ZoomIn className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" onClick={handleResetZoom}>
                  <RotateCw className="h-3 w-3" />
                </Button>
              </div>
              
              {/* Download Button */}
              <Button variant="outline" size="sm" onClick={handleDownload} disabled={!pdfUrl}>
                <Download className="h-3 w-3 mr-1" />
                Download
              </Button>
            </div>
          </DialogTitle>
          <DialogDescription>
            Assignment: {submission?.assignment?.name || `Assignment ${submission?.assignment_id}`} / 
            Group: {submission?.group?.name || `Group ${submission?.group_id}`}
          </DialogDescription>
        </DialogHeader>

        {/* PDF Content */}
        <div className="flex-1 flex items-center justify-center overflow-auto bg-gray-100 rounded-lg">
          {isLoading && (
            <div className="flex flex-col items-center gap-3 p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              <p className="text-gray-600">Loading PDF...</p>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center gap-3 p-8">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <p className="text-red-800 font-medium">Failed to load PDF</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={loadPdf}
                  className="mt-3"
                >
                  Try Again
                </Button>
              </div>
            </div>
          )}

          {pdfUrl && !isLoading && !error && (
            <div className="w-full h-full flex justify-center p-4">
              <iframe
                src={pdfUrl}
                className="w-full h-full border-0 rounded"
                style={{ 
                  transform: `scale(${zoom / 100})`,
                  transformOrigin: 'top center',
                  width: `${100 / (zoom / 100)}%`,
                  height: `${100 / (zoom / 100)}%`
                }}
                title="PDF Viewer"
              />
            </div>
          )}

          {!submission?.pdf_file_name && !isLoading && !error && (
            <div className="flex flex-col items-center gap-3 p-8">
              <FileText className="h-12 w-12 text-gray-400" />
              <p className="text-gray-500">No PDF attached to this submission</p>
            </div>
          )}
        </div>

        {/* Close Button */}
        <div className="flex justify-end pt-3 border-t flex-shrink-0">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            <X className="h-3 w-3 mr-2" />
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
