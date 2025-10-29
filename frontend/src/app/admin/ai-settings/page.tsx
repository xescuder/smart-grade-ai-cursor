"use client"

import { getAuthHeaders } from "@/lib/utils"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"

export default function AiSettingsPage() {
  const [extractPrompt, setExtractPrompt] = useState("")
  const [evaluatePrompt, setEvaluatePrompt] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const loadSettings = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/admin/ai-settings`, {
        headers: {
          ...getAuthHeaders(),
        },
      })
      if (!res.ok) throw new Error("Failed to load settings")
      const data = await res.json()
      setExtractPrompt(data.extract_system_prompt || "")
      setEvaluatePrompt(data.evaluate_system_prompt || "")
    } catch {
      toast.error("Failed to load AI settings")
    } finally {
      setLoading(false)
    }
  }

  const saveSettings = async () => {
    setSaving(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/admin/ai-settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          extract_system_prompt: extractPrompt,
          evaluate_system_prompt: evaluatePrompt,
        }),
      })
      if (!res.ok) throw new Error("Failed to save settings")
      toast.success("AI settings saved")
    } catch {
      toast.error("Failed to save AI settings")
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-6">Configuration</h1>
      <p className="text-gray-600 mb-6">Set the system prompts used for AI extraction and evaluation.</p>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>System Prompt: Create Exercises from Assignment</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={extractPrompt}
              onChange={(e) => setExtractPrompt(e.target.value)}
              rows={10}
              placeholder="Write the system prompt the AI should use to extract exercises from the assignment PDF..."
              disabled={loading || saving}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Prompt: Evaluate Submission Exercises</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={evaluatePrompt}
              onChange={(e) => setEvaluatePrompt(e.target.value)}
              rows={10}
              placeholder="Write the system prompt the AI should use to evaluate a submission against exercises..."
              disabled={loading || saving}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={saveSettings} disabled={loading || saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>
    </div>
  )
}



