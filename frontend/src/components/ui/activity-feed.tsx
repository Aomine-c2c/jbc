'use client';

import * as React from "react"
import {
  Activity,
  User,
  PlusCircle,
  FileCheck,
  Play,
  CheckCircle,
  Shield,
  XCircle,
  MessageSquare,
  Wrench
} from "lucide-react"
import { cn } from "@/lib/utils"

export interface ActivityEvent {
  id: string
  action: string
  userId?: string
  userName?: string
  userRole?: string
  timestamp: string
  details?: string
  category?: "lifecycle" | "parts" | "comment" | "approval"
}

export interface ActivityFeedProps {
  events: ActivityEvent[]
  className?: string
  onAddComment?: (comment: string) => void
}

const actionIcons: Record<string, { icon: React.ElementType; color: string }> = {
  create: { icon: PlusCircle, color: "text-blue-500" },
  submit: { icon: FileCheck, color: "text-amber-500" },
  approve: { icon: Shield, color: "text-emerald-500" },
  reject: { icon: XCircle, color: "text-red-500" },
  assign: { icon: User, color: "text-indigo-500" },
  start: { icon: Play, color: "text-cyan-500" },
  pause: { icon: Activity, color: "text-orange-500" },
  complete: { icon: Wrench, color: "text-teal-500" },
  verify: { icon: CheckCircle, color: "text-emerald-600" },
  close: { icon: CheckCircle, color: "text-slate-500" },
  comment: { icon: MessageSquare, color: "text-muted-foreground" },
}

export function ActivityFeed({
  events,
  className,
  onAddComment,
}: ActivityFeedProps) {
  const [newComment, setNewComment] = React.useState("")

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newComment.trim() || !onAddComment) return
    onAddComment(newComment.trim())
    setNewComment("")
  }

  return (
    <div className={cn("space-y-4 text-xs", className)}>
      <div className="flex items-center justify-between border-b border-border pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-foreground">
          <Activity className="size-4 text-primary" />
          <span>Operational Audit Trail & Activity</span>
        </div>
        <span className="text-[11px] font-mono text-muted-foreground">
          {events.length} Events
        </span>
      </div>

      {/* Add comment quick bar */}
      {onAddComment && (
        <form onSubmit={handleSubmitComment} className="flex gap-2">
          <input
            type="text"
            placeholder="Add operational log comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="h-8 flex-1 rounded border border-input bg-card px-2.5 text-xs text-foreground outline-none focus:border-ring"
          />
          <button
            type="submit"
            disabled={!newComment.trim()}
            className="h-8 px-3 rounded bg-primary text-primary-foreground font-medium text-xs disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            Log
          </button>
        </form>
      )}

      {/* Event Timeline List */}
      <div className="relative pl-4 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-[2px] before:bg-border">
        {events.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground font-mono text-xs">
            No activity logged yet.
          </div>
        ) : (
          events.map((evt) => {
            const key = evt.action.toLowerCase()
            const cfg = actionIcons[key] || { icon: Activity, color: "text-muted-foreground" }
            const Icon = cfg.icon

            return (
              <div key={evt.id} className="relative group">
                {/* Event Dot */}
                <div className="absolute -left-4 top-1 size-3 rounded-full bg-card border-2 border-border group-hover:border-primary transition-colors flex items-center justify-center">
                  <span className="size-1 rounded-full bg-muted-foreground" />
                </div>

                <div className="rounded border border-border/70 bg-card p-2.5 shadow-2xs space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-medium text-foreground">
                      <Icon className={cn("size-3.5", cfg.color)} />
                      <span className="uppercase font-mono text-[11px] font-bold">
                        {evt.action.replace(/_/g, " ")}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground">
                      {new Date(evt.timestamp).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-mono">
                    <User className="size-2.5" />
                    <span>{evt.userName || evt.userId || "System"}</span>
                    {evt.userRole && (
                      <span className="text-[9px] bg-muted px-1 py-0.2 rounded text-foreground">
                        {evt.userRole}
                      </span>
                    )}
                  </div>

                  {evt.details && (
                    <p className="text-xs text-foreground/90 pt-1 font-mono text-[11px] whitespace-pre-wrap bg-muted/30 p-1.5 rounded border border-border/40">
                      {evt.details}
                    </p>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
