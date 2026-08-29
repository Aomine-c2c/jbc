'use client';

import * as React from "react"
import { CheckCircle2, XCircle, Clock, ShieldCheck, UserCheck, ArrowRightLeft, AlertTriangle } from "lucide-react"
import { StatusBadge } from "./status-badge"
import { Button } from "./button"
import { cn } from "@/lib/utils"
import { ApprovalStep } from "@/lib/approvals"

export interface ApprovalPanelProps {
  steps: ApprovalStep[]
  canApprove?: boolean
  onAction?: (stepId: string, action: 'approve' | 'reject' | 'return' | 'delegate' | 'escalate', comments: string) => void
  loading?: boolean
  className?: string
}

export function ApprovalPanel({
  steps,
  canApprove = false,
  onAction,
  loading = false,
  className,
}: ApprovalPanelProps) {
  const [commentInput, setCommentInput] = React.useState<Record<string, string>>({})
  const [activeStepId, setActiveStepId] = React.useState<string | null>(null)

  const handleAction = (stepId: string, action: 'approve' | 'reject' | 'return' | 'delegate' | 'escalate') => {
    if (onAction) {
      onAction(stepId, action, commentInput[stepId] || "")
      setActiveStepId(null)
    }
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between border-b border-border/80 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
          <ShieldCheck className="size-4 text-primary" />
          <span>Operational Authorization & Sign-off</span>
        </div>
        <span className="text-[11px] font-mono text-muted-foreground">
          {steps.filter(s => s.status === "APPROVED").length}/{steps.length} Approved
        </span>
      </div>

      <div className="divide-y divide-border/60 rounded border border-border bg-card">
        {steps.map((step) => {
          const isPending = step.status === "PENDING"
          const isApproved = step.status === "APPROVED"
          const isRejected = step.status === "REJECTED" || step.status === "RETURNED"

          return (
            <div key={step.id} className="p-3.5 space-y-2.5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <div className="mt-0.5 shrink-0">
                    {isApproved ? (
                      <CheckCircle2 className="size-4 text-emerald-500" />
                    ) : isRejected ? (
                      <XCircle className="size-4 text-red-500" />
                    ) : step.status === "DELEGATED" ? (
                      <ArrowRightLeft className="size-4 text-blue-500" />
                    ) : step.status === "ESCALATED" ? (
                      <AlertTriangle className="size-4 text-amber-500" />
                    ) : (
                      <Clock className="size-4 text-amber-500" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground">
                        {step.authority_role}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5">
                      <UserCheck className="size-3" />
                      <span>{step.approver_name || "Pending Assignment"}</span>
                      {step.timestamp && (
                        <>
                          <span>•</span>
                          <span className="font-mono">{new Date(step.timestamp).toLocaleString()}</span>
                        </>
                      )}
                    </div>
                    {step.signature_token && (
                      <div className="text-[9px] font-mono text-muted-foreground/60 mt-1 uppercase">
                        {step.signature_token}
                      </div>
                    )}
                  </div>
                </div>

                <StatusBadge
                  status={step.status}
                  size="sm"
                  showDot={false}
                />
              </div>

              {step.comment && (
                <div className="rounded bg-muted/40 p-2 text-xs text-foreground border border-border/50 font-mono">
                  <span className="text-muted-foreground select-none">Notes: </span>
                  {step.comment}
                </div>
              )}

              {isPending && canApprove && (
                <div className="pt-2 border-t border-border/40 space-y-2">
                  <input
                    type="text"
                    placeholder="Enter approval/rejection remarks..."
                    value={commentInput[step.id] || ""}
                    onChange={(e) => setCommentInput({ ...commentInput, [step.id]: e.target.value })}
                    className="h-7 w-full rounded border border-input bg-background px-2 text-xs text-foreground outline-none focus:border-ring"
                  />
                  <div className="flex flex-wrap gap-2 justify-end">
                    <Button
                      size="xs"
                      variant="destructive"
                      loading={loading && activeStepId === step.id}
                      onClick={() => {
                        setActiveStepId(step.id)
                        handleAction(step.id, 'reject')
                      }}
                    >
                      Reject
                    </Button>
                    <Button
                      size="xs"
                      variant="secondary"
                      loading={loading && activeStepId === step.id}
                      onClick={() => {
                        setActiveStepId(step.id)
                        handleAction(step.id, 'return')
                      }}
                    >
                      Return
                    </Button>
                    <Button
                      size="xs"
                      variant="success"
                      loading={loading && activeStepId === step.id}
                      onClick={() => {
                        setActiveStepId(step.id)
                        handleAction(step.id, 'approve')
                      }}
                    >
                      Approve & Sign
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
