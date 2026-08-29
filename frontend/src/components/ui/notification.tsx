'use client';

import * as React from "react"
import { AlertTriangle, CheckCircle2, Info, XCircle, X } from "lucide-react"
import { cn } from "@/lib/utils"

export type NotificationType = "info" | "success" | "warning" | "error"

export interface NotificationBannerProps {
  type?: NotificationType
  title?: string
  message: string
  dismissible?: boolean
  onDismiss?: () => void
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function NotificationBanner({
  type = "info",
  title,
  message,
  dismissible = false,
  onDismiss,
  actionLabel,
  onAction,
  className,
}: NotificationBannerProps) {
  const [visible, setVisible] = React.useState(true)

  if (!visible) return null

  const handleDismiss = () => {
    setVisible(false)
    if (onDismiss) onDismiss()
  }

  const typeConfig = {
    info: {
      border: "border-blue-500/40 bg-blue-500/10 text-blue-800 dark:text-blue-200",
      icon: Info,
      iconColor: "text-blue-500",
    },
    success: {
      border: "border-emerald-500/40 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200",
      icon: CheckCircle2,
      iconColor: "text-emerald-500",
    },
    warning: {
      border: "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-200",
      icon: AlertTriangle,
      iconColor: "text-amber-500",
    },
    error: {
      border: "border-red-500/40 bg-red-500/10 text-red-800 dark:text-red-200",
      icon: XCircle,
      iconColor: "text-red-500",
    },
  }

  const cfg = typeConfig[type]
  const Icon = cfg.icon

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded border p-3 text-xs shadow-2xs transition-all",
        cfg.border,
        className
      )}
    >
      <Icon className={cn("size-4 shrink-0 mt-0.5", cfg.iconColor)} />
      <div className="flex-1 space-y-0.5">
        {title && <h5 className="font-semibold text-xs leading-none">{title}</h5>}
        <p className="text-[11px] leading-relaxed opacity-90">{message}</p>
      </div>

      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="text-xs font-semibold underline underline-offset-2 hover:opacity-80 transition-opacity shrink-0"
        >
          {actionLabel}
        </button>
      )}

      {dismissible && (
        <button
          type="button"
          onClick={handleDismiss}
          className="text-current opacity-70 hover:opacity-100 transition-opacity shrink-0"
          aria-label="Dismiss notification"
        >
          <X className="size-3.5" />
        </button>
      )}
    </div>
  )
}
