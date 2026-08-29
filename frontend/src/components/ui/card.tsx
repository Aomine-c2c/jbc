import * as React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.ComponentProps<"div"> {
  variant?: "default" | "accent" | "warning" | "success" | "danger" | "info"
}

function Card({
  className,
  variant = "default",
  ...props
}: CardProps) {
  const variantStyles = {
    default: "border-border",
    accent: "border-primary/40 border-l-4 border-l-primary",
    warning: "border-amber-500/40 border-l-4 border-l-amber-500",
    success: "border-emerald-500/40 border-l-4 border-l-emerald-500",
    danger: "border-red-500/40 border-l-4 border-l-red-500",
    info: "border-blue-500/40 border-l-4 border-l-blue-500",
  }

  return (
    <div
      data-slot="card"
      className={cn(
        "flex flex-col rounded border bg-card text-xs text-card-foreground shadow-2xs transition-all overflow-hidden",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "flex items-center justify-between gap-2 border-b border-border bg-muted/40 px-4 py-2.5",
        className
      )}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn(
        "text-sm font-semibold tracking-tight text-foreground flex items-center gap-2",
        className
      )}
      {...props}
    />
  )
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-xs text-muted-foreground", className)}
      {...props}
    />
  )
}

function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-action"
      className={cn("flex items-center gap-1.5 shrink-0", className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("p-4", className)}
      {...props}
    />
  )
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center justify-between border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground",
        className
      )}
      {...props}
    />
  )
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}
