import * as React from "react"
import { cn } from "@/lib/utils"

export type JobStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "PENDING_APPROVAL"
  | "RETURNED"
  | "REJECTED"
  | "APPROVED"
  | "PLANNING"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "PENDING_REVIEW"
  | "VERIFIED"
  | "CLOSED"
  | "CANCELLED"
  | string

export type PriorityLevel = "LOW" | "NORMAL" | "HIGH" | "EMERGENCY" | string

interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: JobStatus
  size?: "sm" | "default" | "lg"
  showDot?: boolean
}

interface PriorityBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  priority: PriorityLevel | number
  size?: "sm" | "default" | "lg"
  showDot?: boolean
}

const statusConfig: Record<
  string,
  { label: string; bg: string; text: string; border: string; dot: string; pulse?: boolean }
> = {
  DRAFT: {
    label: "Draft",
    bg: "bg-slate-500/10 dark:bg-slate-500/15",
    text: "text-slate-700 dark:text-slate-300",
    border: "border-slate-500/30",
    dot: "bg-slate-400",
  },
  SUBMITTED: {
    label: "Submitted",
    bg: "bg-blue-500/10 dark:bg-blue-500/15",
    text: "text-blue-700 dark:text-blue-300",
    border: "border-blue-500/30",
    dot: "bg-blue-500",
  },
  PENDING_APPROVAL: {
    label: "Pending Approval",
    bg: "bg-amber-500/10 dark:bg-amber-500/15",
    text: "text-amber-700 dark:text-amber-300",
    border: "border-amber-500/30",
    dot: "bg-amber-500",
    pulse: true,
  },
  RETURNED: {
    label: "Returned for Correction",
    bg: "bg-orange-500/15 dark:bg-orange-500/20",
    text: "text-orange-800 dark:text-orange-200",
    border: "border-orange-500/40",
    dot: "bg-orange-500",
    pulse: true,
  },
  REJECTED: {
    label: "Rejected",
    bg: "bg-rose-500/10 dark:bg-rose-500/15",
    text: "text-rose-700 dark:text-rose-300",
    border: "border-rose-500/30",
    dot: "bg-rose-500",
  },
  APPROVED: {
    label: "Approved",
    bg: "bg-emerald-500/10 dark:bg-emerald-500/15",
    text: "text-emerald-700 dark:text-emerald-300",
    border: "border-emerald-500/30",
    dot: "bg-emerald-500",
  },
  PLANNING: {
    label: "In Planning",
    bg: "bg-cyan-500/10 dark:bg-cyan-500/15",
    text: "text-cyan-700 dark:text-cyan-300",
    border: "border-cyan-500/30",
    dot: "bg-cyan-500",
  },
  ASSIGNED: {
    label: "Crew Assigned",
    bg: "bg-indigo-500/10 dark:bg-indigo-500/15",
    text: "text-indigo-700 dark:text-indigo-300",
    border: "border-indigo-500/30",
    dot: "bg-indigo-500",
  },
  IN_PROGRESS: {
    label: "In Progress",
    bg: "bg-cyan-500/15 dark:bg-cyan-500/20",
    text: "text-cyan-800 dark:text-cyan-200",
    border: "border-cyan-500/40",
    dot: "bg-cyan-500",
    pulse: true,
  },
  ON_HOLD: {
    label: "On Hold",
    bg: "bg-amber-500/15 dark:bg-amber-500/20",
    text: "text-amber-800 dark:text-amber-200",
    border: "border-amber-500/40",
    dot: "bg-amber-500",
    pulse: true,
  },
  COMPLETED: {
    label: "Work Completed",
    bg: "bg-teal-500/10 dark:bg-teal-500/15",
    text: "text-teal-700 dark:text-teal-300",
    border: "border-teal-500/30",
    dot: "bg-teal-500",
  },
  PENDING_REVIEW: {
    label: "Pending QA Review",
    bg: "bg-violet-500/10 dark:bg-violet-500/15",
    text: "text-violet-700 dark:text-violet-300",
    border: "border-violet-500/30",
    dot: "bg-violet-500",
    pulse: true,
  },
  VERIFIED: {
    label: "Verified / QA Passed",
    bg: "bg-emerald-600/15 dark:bg-emerald-500/20",
    text: "text-emerald-800 dark:text-emerald-200",
    border: "border-emerald-600/40",
    dot: "bg-emerald-500",
  },
  CLOSED: {
    label: "Closed & Archived",
    bg: "bg-zinc-500/10 dark:bg-zinc-500/15",
    text: "text-zinc-700 dark:text-zinc-300",
    border: "border-zinc-500/30",
    dot: "bg-zinc-400",
  },
  CANCELLED: {
    label: "Cancelled",
    bg: "bg-red-500/10 dark:bg-red-500/15",
    text: "text-red-700 dark:text-red-300",
    border: "border-red-500/30",
    dot: "bg-red-500",
  },
}

export function StatusBadge({
  status,
  size = "default",
  showDot = true,
  className,
  ...props
}: StatusBadgeProps) {
  const normStatus = (status || "DRAFT").toUpperCase()
  const config = statusConfig[normStatus] || {
    label: normStatus.replace(/_/g, " "),
    bg: "bg-muted/40",
    text: "text-muted-foreground",
    border: "border-border",
    dot: "bg-muted-foreground",
  }

  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-[10px]",
    default: "px-2.5 py-0.5 text-xs",
    lg: "px-3 py-1 text-sm font-semibold",
  }

  const dotSizes = {
    sm: "size-1.5",
    default: "size-2",
    lg: "size-2.5",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded font-mono font-medium border uppercase tracking-wider transition-colors",
        config.bg,
        config.text,
        config.border,
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {showDot && (
        <span className="relative flex items-center justify-center">
          {config.pulse && (
            <span
              className={cn(
                "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                config.dot
              )}
            />
          )}
          <span className={cn("relative inline-flex rounded-full", config.dot, dotSizes[size])} />
        </span>
      )}
      <span>{config.label}</span>
    </span>
  )
}

export function PriorityBadge({
  priority,
  size = "default",
  showDot = true,
  className,
  ...props
}: PriorityBadgeProps) {
  let pStr = "NORMAL"
  if (typeof priority === "number") {
    if (priority <= 0) pStr = "LOW"
    else if (priority === 1) pStr = "NORMAL"
    else if (priority === 2) pStr = "HIGH"
    else pStr = "EMERGENCY"
  } else if (typeof priority === "string") {
    pStr = priority.toUpperCase()
  }

  const configs: Record<string, { label: string; bg: string; text: string; border: string; dot: string; pulse?: boolean }> = {
    LOW: {
      label: "Low Priority",
      bg: "bg-slate-500/10",
      text: "text-slate-600 dark:text-slate-400",
      border: "border-slate-500/30",
      dot: "bg-slate-400",
    },
    NORMAL: {
      label: "Normal",
      bg: "bg-blue-500/10",
      text: "text-blue-700 dark:text-blue-300",
      border: "border-blue-500/30",
      dot: "bg-blue-500",
    },
    HIGH: {
      label: "High Priority",
      bg: "bg-amber-500/15",
      text: "text-amber-800 dark:text-amber-200",
      border: "border-amber-500/40",
      dot: "bg-amber-500",
      pulse: true,
    },
    EMERGENCY: {
      label: "EMERGENCY",
      bg: "bg-red-500/20",
      text: "text-red-700 dark:text-red-300 font-bold",
      border: "border-red-500/50",
      dot: "bg-red-500",
      pulse: true,
    },
  }

  const c = configs[pStr] || configs.NORMAL

  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-[10px]",
    default: "px-2 py-0.5 text-xs",
    lg: "px-3 py-1 text-sm font-semibold",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded font-mono border uppercase tracking-wider",
        c.bg,
        c.text,
        c.border,
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {showDot && (
        <span className="relative flex items-center justify-center">
          {c.pulse && (
            <span
              className={cn(
                "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                c.dot
              )}
            />
          )}
          <span className={cn("relative inline-flex rounded-full size-1.5", c.dot)} />
        </span>
      )}
      <span>{c.label}</span>
    </span>
  )
}
