/**
 * PDF Viewer Dialog Component
 * Displays PDF contents in a modal popup
 */

"use client"

import { getAuthHeaders } from "@/lib/utils"

import * as React from "react"
import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { X, Download, ZoomIn, ZoomOut, RotateCw, Upload } from "lucide-react"
import { Assignment } from "@/types/assignment"

interface PdfViewerDialogProps {
  assignment: Assignment
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpload: () => void
}

export function PdfViewerDialog({ assignment, open, onOpenChange, onUpload }: PdfViewerDialogProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [pdfUrl, setPdfUrl] = useState("")
  const [zoom, setZoom] = useState(100)

  const loadPdf = useCallback(async () => {
    if (!assignment?.id) return

    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/pdf`, {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        setPdfUrl(url)
      } else {
        setError("Failed to load PDF")
      }
    } catch {
      setError("An error occurred while loading the PDF")
    } finally {
      setIsLoading(false)
    }
  }, [assignment?.id])

  // Load PDF when dialog opens (prefer name/id; DB bytes may not have a path)
  useEffect(() => {
    if (open && assignment?.id) {
      loadPdf()
    }
  }, [open, assignment?.id, loadPdf])

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
      link.download = assignment.pdf_file_name || `${assignment.name}.pdf`
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
            <span>PDF: {assignment.pdf_file_name}</span>
            <div className="flex items-center gap-2">
              {/* Upload Button */}
              <Button variant="outline" size="sm" onClick={onUpload} title="Upload PDF">
                <Upload className="h-3 w-3 mr-1" />
                Upload
              </Button>
              
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
            Assignment PDF for "{assignment.name}"
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

          {!pdfUrl && !isLoading && !error && (
            <div className="flex flex-col items-center gap-3 p-8">
              <p className="text-gray-500">No PDF attached to this assignment</p>
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
