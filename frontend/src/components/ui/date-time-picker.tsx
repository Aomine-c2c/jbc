'use client';

import * as React from "react"
import { Calendar as CalendarIcon, Clock } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

export interface DateTimePickerProps {
  value?: string
  onChange: (val: string) => void
  disabled?: boolean
  label?: string
  className?: string
}

export function DateTimePicker({
  value = "",
  onChange,
  disabled = false,
  className,
}: DateTimePickerProps) {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }

  const setNow = () => {
    const now = new Date()
    const offset = now.getTimezoneOffset()
    const local = new Date(now.getTime() - offset * 60 * 1000)
    const isoString = local.toISOString().slice(0, 16)
    onChange(isoString)
  }

  const setShiftStart = () => {
    const now = new Date()
    now.setHours(7, 0, 0, 0)
    const offset = now.getTimezoneOffset()
    const local = new Date(now.getTime() - offset * 60 * 1000)
    const isoString = local.toISOString().slice(0, 16)
    onChange(isoString)
  }

  const setShiftEnd = () => {
    const now = new Date()
    now.setHours(19, 0, 0, 0)
    const offset = now.getTimezoneOffset()
    const local = new Date(now.getTime() - offset * 60 * 1000)
    const isoString = local.toISOString().slice(0, 16)
    onChange(isoString)
  }

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2.5 text-muted-foreground">
            <CalendarIcon className="size-3.5" />
          </div>
          <input
            type="datetime-local"
            disabled={disabled}
            value={value}
            onChange={handleInputChange}
            className={cn(
              "h-8 w-full rounded border border-input bg-card pl-8 pr-2.5 py-1 text-xs font-mono text-foreground transition-all outline-none",
              "focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring/50",
              "disabled:pointer-events-none disabled:bg-muted/60 disabled:opacity-60"
            )}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          size="xs"
          disabled={disabled}
          onClick={setNow}
          className="font-mono text-[10px]"
        >
          <Clock className="size-3 mr-1" />
          Now
        </Button>
      </div>

      <div className="flex gap-1.5 text-[10px]">
        <button
          type="button"
          disabled={disabled}
          onClick={setShiftStart}
          className="text-muted-foreground hover:text-foreground font-mono underline-offset-2 hover:underline cursor-pointer"
        >
          Shift Start (07:00)
        </button>
        <span className="text-border">|</span>
        <button
          type="button"
          disabled={disabled}
          onClick={setShiftEnd}
          className="text-muted-foreground hover:text-foreground font-mono underline-offset-2 hover:underline cursor-pointer"
        >
          Shift End (19:00)
        </button>
      </div>
    </div>
  )
}
