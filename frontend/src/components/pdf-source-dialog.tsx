/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { getAuthHeaders } from "@/lib/utils"

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Link as LinkIcon } from "lucide-react";
import { Assignment } from "@/types/assignment";
import { toast } from "sonner";

interface PdfSourceDialogProps {
  assignment: Assignment | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void; // call after successful upload/reference
}

function extractDriveFileId(input: string): string | null {
  if (!input) return null;
  // Accept raw fileId
  if (/^[A-Za-z0-9_-]{20,}$/.test(input)) return input;
  try {
    const url = new URL(input);
    // Patterns: /file/d/{id}/, ?id={id}
    const pathMatch = url.pathname.match(/\/file\/d\/([A-Za-z0-9_-]{20,})/);
    if (pathMatch && pathMatch[1]) return pathMatch[1];
    const idParam = url.searchParams.get("id");
    if (idParam && /^[A-Za-z0-9_-]{20,}$/.test(idParam)) return idParam;
  } catch {
    // not a URL
  }
  return null;
}

export function PdfSourceDialog({ assignment, open, onOpenChange, onUpdated }: PdfSourceDialogProps) {
  const [mode, setMode] = useState<"local" | "gdrive">("local");
  const [isBusy, setIsBusy] = useState(false);
  const [localFile, setLocalFile] = useState<File | null>(null);
  const [driveInput, setDriveInput] = useState("");

  const handleLocalUpload = async () => {
    if (!assignment?.id) return;
    if (!localFile) {
      toast.error("Please choose a PDF file");
      return;
    }
    if (localFile.type !== "application/pdf") {
      toast.error("Only PDF files are allowed");
      return;
    }
    if (localFile.size > 10 * 1024 * 1024) {
      toast.error("File size must be less than 10MB");
      return;
    }

    try {
      setIsBusy(true);
      const formData = new FormData();
      formData.append("file", localFile);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/upload/statement`, {
        method: "POST",
        headers: { 
          'Authorization': getAuthHeaders()['Authorization'] || '',
        },
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to upload PDF");
      }
      toast.success("PDF uploaded successfully");
      onUpdated();
      onOpenChange(false);
    } catch (e: any) {
      toast.error(e?.message || "Failed to upload PDF");
    } finally {
      setIsBusy(false);
    }
  };

  const handleDriveAttach = async () => {
    if (!assignment?.id) return;
    const fileId = extractDriveFileId(driveInput.trim());
    if (!fileId) {
      toast.error("Please paste a valid Google Drive URL or File ID");
      return;
    }
    try {
      setIsBusy(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/assignments/${assignment.id}/pdf-ref`, {
        method: "PATCH",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ drive_file_id: fileId, file_name: assignment.pdf_file_name || "assignment.pdf" }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to attach Drive file");
      }
      toast.success("Google Drive file attached");
      onUpdated();
      onOpenChange(false);
    } catch (e: any) {
      toast.error(e?.message || "Failed to attach Drive file");
    } finally {
      setIsBusy(false);
    }
  };

  if (!assignment) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Choose PDF for {assignment.name}</DialogTitle>
          <DialogDescription>Select from your computer or attach a Google Drive file.</DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 mb-4">
          <Button variant={mode === "local" ? "default" : "outline"} size="sm" onClick={() => setMode("local")}>Local file</Button>
          <Button variant={mode === "gdrive" ? "default" : "outline"} size="sm" onClick={() => setMode("gdrive")}>Google Drive</Button>
        </div>

        {mode === "local" ? (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="pdf">PDF file</Label>
              <Input id="pdf" type="file" accept="application/pdf" onChange={(e) => setLocalFile(e.target.files?.[0] || null)} />
            </div>
            <Button onClick={handleLocalUpload} disabled={isBusy}>
              <Upload className="h-4 w-4 mr-2" /> Upload
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="drive">Google Drive link or File ID</Label>
              <Input id="drive" placeholder="Paste Drive link or fileId" value={driveInput} onChange={(e) => setDriveInput(e.target.value)} />
            </div>
            <Button onClick={handleDriveAttach} disabled={isBusy}>
              <LinkIcon className="h-4 w-4 mr-2" /> Attach from Drive
            </Button>
            <p className="text-xs text-muted-foreground">Tip: share the file appropriately or use a private backend proxy later.</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}



