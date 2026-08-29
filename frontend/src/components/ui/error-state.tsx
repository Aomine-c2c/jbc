'use client';

import * as React from "react"
import { AlertOctagon, RotateCcw, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

export interface ErrorStateProps {
  title?: string
  message: string
  code?: string
  details?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = "Operational System Error",
  message,
  code = "ERR: DIAGNOSTIC_FAULT_500",
  details,
  onRetry,
  className,
}: ErrorStateProps) {
  const [showDetails, setShowDetails] = React.useState(false)

  return (
    <div
      className={cn(
        "rounded border border-destructive/40 bg-destructive/5 p-6 text-center space-y-3 shadow-2xs max-w-lg mx-auto",
        className
      )}
    >
      <div className="flex size-10 items-center justify-center rounded-full bg-destructive/15 text-destructive mx-auto">
        <AlertOctagon className="size-5" />
      </div>

      <div>
        <span className="font-mono text-[10px] uppercase tracking-widest text-destructive/80 font-bold block mb-1">
          {code}
        </span>
        <h4 className="text-sm font-semibold text-foreground tracking-tight">
          {title}
        </h4>
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
          {message}
        </p>
      </div>

      {details && (
        <div className="text-left pt-2">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground hover:text-foreground mx-auto mb-2"
          >
            <span>{showDetails ? "Hide Diagnostic Trace" : "Show Diagnostic Trace"}</span>
            {showDetails ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
          </button>
          {showDetails && (
            <pre className="rounded bg-black/70 p-3 text-[10px] font-mono text-red-300 overflow-x-auto border border-destructive/30 max-h-40">
              {details}
            </pre>
          )}
        </div>
      )}

      {onRetry && (
        <div className="pt-2">
          <Button size="sm" variant="destructive" onClick={onRetry}>
            <RotateCcw className="size-3.5 mr-1" />
            Retry Operation
          </Button>
        </div>
      )}
    </div>
  )
}
