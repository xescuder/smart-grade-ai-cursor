"use client"

import React from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

type OptionalDatePickerProps = {
  id: string
  name: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function OptionalDatePicker({ id, name, value, onChange, placeholder = "", className }: OptionalDatePickerProps) {
  return (
    <div className={`flex gap-2 ${className || ""}`.trim()}>
      <Input
        id={id}
        name={name}
        type="date"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {value ? (
        <Button type="button" variant="outline" onClick={() => onChange("")}>Clear</Button>
      ) : null}
    </div>
  )
}


