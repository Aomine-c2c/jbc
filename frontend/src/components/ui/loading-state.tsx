'use client';

import * as React from "react"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded bg-muted/70", className)}
      {...props}
    />
  )
}

export function TableSkeleton({
  rows = 5,
  columns = 5,
  className,
}: {
  rows?: number
  columns?: number
  className?: string
}) {
  return (
    <div className={cn("rounded border border-border bg-card overflow-hidden shadow-2xs", className)}>
      <div className="flex h-9 items-center gap-4 border-b border-border bg-muted/60 px-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-3.5 flex-1" />
        ))}
      </div>
      <div className="divide-y divide-border/60 p-0">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex h-10 items-center gap-4 px-4">
            {Array.from({ length: columns }).map((_, c) => (
              <Skeleton key={c} className="h-3 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export function MetricCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded border border-border bg-card p-4 space-y-2 shadow-2xs", className)}>
      <Skeleton className="h-3 w-1/3" />
      <Skeleton className="h-7 w-1/2" />
      <Skeleton className="h-2.5 w-3/4" />
    </div>
  )
}

export function TelemetrySpinner({
  message = "Acquiring telemetry data...",
  code = "SYS: FETCH_RECORD",
  className,
}: {
  message?: string
  code?: string
  className?: string
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-12 text-center", className)}>
      <Loader2 className="size-6 text-primary animate-spin mb-3" />
      <span className="font-mono text-[10px] uppercase text-muted-foreground tracking-widest mb-1">
        {code}
      </span>
      <p className="text-xs font-medium text-foreground">{message}</p>
    </div>
  )
}
