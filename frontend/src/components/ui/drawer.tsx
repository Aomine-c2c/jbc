'use client';

import * as React from "react"
import { X } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

export interface DrawerProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: "sm" | "md" | "lg" | "xl"
  side?: "right" | "left"
}

export function Drawer({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  size = "md",
  side = "right",
}: DrawerProps) {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-xl",
    xl: "max-w-3xl",
  }

  return (
    <div className="fixed inset-0 isolate z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/50 backdrop-blur-2xs transition-opacity animate-in fade-in duration-150"
      />

      {/* Drawer Panel */}
      <div
        className={cn(
          "fixed inset-y-0 flex w-full flex-col bg-card shadow-2xl border-border transition-transform animate-in duration-200",
          side === "right" ? "right-0 border-l slide-in-from-right" : "left-0 border-r slide-in-from-left",
          sizeClasses[size]
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border bg-muted/40 px-5 py-3.5">
          <div>
            <h2 className="text-sm font-semibold text-foreground tracking-tight flex items-center gap-2">
              {title}
            </h2>
            {description && (
              <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onClose}
            aria-label="Close drawer"
          >
            <X className="size-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 text-xs">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-border bg-muted/30 px-5 py-3 flex items-center justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
