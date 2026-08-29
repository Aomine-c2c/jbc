'use client';

import * as React from "react"
import { Check, AlertCircle, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"

export type WorkflowStageKey =
  | "identity"
  | "request"
  | "approval"
  | "planning"
  | "assignment"
  | "execution"
  | "report"
  | "review"
  | "closure"

export interface WorkflowStage {
  key: WorkflowStageKey
  title: string
  subtitle?: string
  status: "complete" | "current" | "upcoming" | "rejected" | "returned"
  timestamp?: string
  actor?: string
}

export interface WorkflowTimelineProps {
  currentStatus: string
  createdAt?: string
  startTime?: string
  endTime?: string
  onSelectStage?: (stageKey: WorkflowStageKey) => void
  activeStageKey?: WorkflowStageKey
  className?: string
}

export function getWorkflowStages(currentStatus: string, timestamps?: {
  created_at?: string
  actual_start_time?: string
  actual_end_time?: string
}): WorkflowStage[] {
  const norm = (currentStatus || "DRAFT").toUpperCase()

  const stageOrder: WorkflowStageKey[] = [
    "identity",
    "request",
    "approval",
    "planning",
    "assignment",
    "execution",
    "report",
    "review",
    "closure",
  ]

  let activeIndex = 1 // default request
  if (norm === "DRAFT" || norm === "SUBMITTED") activeIndex = 1
  else if (norm === "PENDING_APPROVAL" || norm === "RETURNED" || norm === "REJECTED") activeIndex = 2
  else if (norm === "APPROVED" || norm === "PLANNING") activeIndex = 3
  else if (norm === "ASSIGNED") activeIndex = 4
  else if (norm === "IN_PROGRESS" || norm === "ON_HOLD") activeIndex = 5
  else if (norm === "COMPLETED") activeIndex = 6
  else if (norm === "PENDING_REVIEW" || norm === "VERIFIED") activeIndex = 7
  else if (norm === "CLOSED") activeIndex = 8

  const stageTitles: Record<WorkflowStageKey, { title: string; subtitle: string }> = {
    identity: { title: "1. Identity", subtitle: "Asset Tag & #JC" },
    request: { title: "2. Request", subtitle: "Problem & Scope" },
    approval: { title: "3. Approval", subtitle: "Management Sign-off" },
    planning: { title: "4. Planning", subtitle: "Hours & Window" },
    assignment: { title: "5. Assignment", subtitle: "Supervisor & Crew" },
    execution: { title: "6. Execution", subtitle: "Active Maintenance" },
    report: { title: "7. Report", subtitle: "Work & Spares" },
    review: { title: "8. Review", subtitle: "QA & Requester" },
    closure: { title: "9. Closure", subtitle: "Formal Handover" },
  }

  return stageOrder.map((key, idx) => {
    let status: "complete" | "current" | "upcoming" | "rejected" | "returned" = "upcoming"

    if (norm === "REJECTED" && (key === "approval" || key === "review")) {
      status = "rejected"
    } else if (norm === "RETURNED" && key === "approval") {
      status = "returned"
    } else if (norm === "CLOSED") {
      status = "complete"
    } else if (idx < activeIndex) {
      status = "complete"
    } else if (idx === activeIndex) {
      status = "current"
    } else {
      status = "upcoming"
    }

    let timestamp: string | undefined = undefined
    if (key === "request" && timestamps?.created_at) timestamp = timestamps.created_at
    if (key === "execution" && timestamps?.actual_start_time) timestamp = timestamps.actual_start_time
    if (key === "report" && timestamps?.actual_end_time) timestamp = timestamps.actual_end_time

    return {
      key,
      title: stageTitles[key].title,
      subtitle: stageTitles[key].subtitle,
      status,
      timestamp,
    }
  })
}

export function WorkflowTimeline({
  currentStatus,
  createdAt,
  startTime,
  endTime,
  onSelectStage,
  activeStageKey,
  className,
}: WorkflowTimelineProps) {
  const stages = getWorkflowStages(currentStatus, {
    created_at: createdAt,
    actual_start_time: startTime,
    actual_end_time: endTime,
  })

  return (
    <div className={cn("w-full bg-card rounded border border-border p-3 shadow-2xs", className)}>
      <div className="flex items-center justify-between overflow-x-auto pb-1 text-xs font-mono scrollbar-thin">
        {stages.map((stage, idx) => {
          const isSelected = activeStageKey === stage.key
          const isLast = idx === stages.length - 1

          return (
            <React.Fragment key={stage.key}>
              {/* STAGE ITEM */}
              <div
                onClick={() => onSelectStage?.(stage.key)}
                className={cn(
                  "flex items-center gap-2 shrink-0 px-2 py-1 rounded transition-all cursor-pointer select-none",
                  isSelected && "bg-primary/10 border border-primary/40",
                  !isSelected && "hover:bg-muted/50"
                )}
              >
                {/* ICON INDICATOR */}
                <div
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold transition-all",
                    stage.status === "complete" && "bg-emerald-500 text-white",
                    stage.status === "current" && "bg-primary text-primary-foreground animate-pulse",
                    stage.status === "rejected" && "bg-destructive text-white",
                    stage.status === "returned" && "bg-orange-500 text-white",
                    stage.status === "upcoming" && "bg-muted text-muted-foreground border border-border"
                  )}
                >
                  {stage.status === "complete" ? (
                    <Check className="size-3" />
                  ) : stage.status === "rejected" ? (
                    <XCircle className="size-3" />
                  ) : stage.status === "returned" ? (
                    <AlertCircle className="size-3" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>

                {/* LABELS */}
                <div className="text-left leading-tight">
                  <div
                    className={cn(
                      "text-xs font-semibold whitespace-nowrap",
                      stage.status === "current" && "text-primary font-bold",
                      stage.status === "complete" && "text-foreground",
                      stage.status === "upcoming" && "text-muted-foreground",
                      stage.status === "rejected" && "text-destructive font-bold",
                      stage.status === "returned" && "text-orange-600 font-bold"
                    )}
                  >
                    {stage.title}
                  </div>
                  {stage.subtitle && (
                    <div className="text-[10px] text-muted-foreground hidden sm:block">
                      {stage.subtitle}
                    </div>
                  )}
                </div>
              </div>

              {/* CONNECTOR LINE */}
              {!isLast && (
                <div
                  className={cn(
                    "h-0.5 flex-1 min-w-4 mx-1 transition-colors",
                    stage.status === "complete" ? "bg-emerald-500/60" : "bg-border"
                  )}
                />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
