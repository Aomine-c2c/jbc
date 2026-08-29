'use client';

import * as React from "react"
import { LucideIcon, FolderSearch, Plus } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

export interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  code?: string
  actionLabel?: string
  onAction?: () => void
  secondaryActionLabel?: string
  onSecondaryAction?: () => void
  className?: string
}

export function EmptyState({
  icon: Icon = FolderSearch,
  title,
  description,
  code = "STATUS: NO_DATA",
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded border border-dashed border-border bg-card/60 p-8 text-center",
        className
      )}
    >
      <div className="flex size-11 items-center justify-center rounded-full border border-border bg-muted/60 text-muted-foreground mb-3">
        <Icon className="size-5" />
      </div>

      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70 mb-1">
        {code}
      </span>

      <h3 className="text-sm font-semibold text-foreground tracking-tight max-w-sm">
        {title}
      </h3>

      {description && (
        <p className="mt-1 text-xs text-muted-foreground max-w-md leading-relaxed">
          {description}
        </p>
      )}

      {(actionLabel || secondaryActionLabel) && (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          {actionLabel && onAction && (
            <Button size="sm" variant="default" onClick={onAction}>
              <Plus className="size-3.5 mr-1" />
              {actionLabel}
            </Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button size="sm" variant="outline" onClick={onSecondaryAction}>
              {secondaryActionLabel}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
