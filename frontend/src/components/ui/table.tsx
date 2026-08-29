"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

function Table({
  className,
  dense = false,
  zebra = false,
  ...props
}: React.ComponentProps<"table"> & { dense?: boolean; zebra?: boolean }) {
  return (
    <div
      data-slot="table-container"
      className="relative w-full overflow-x-auto rounded border border-border bg-card shadow-2xs"
    >
      <table
        data-slot="table"
        data-dense={dense}
        data-zebra={zebra}
        className={cn(
          "w-full caption-bottom text-xs text-foreground text-left",
          zebra && "[&_tbody_tr:nth-child(even)]:bg-muted/30",
          className
        )}
        {...props}
      />
    </div>
  )
}

function TableHeader({ className, ...props }: React.ComponentProps<"thead">) {
  return (
    <thead
      data-slot="table-header"
      className={cn(
        "bg-muted/70 text-muted-foreground border-b border-border font-mono uppercase tracking-wider text-[11px]",
        className
      )}
      {...props}
    />
  )
}

function TableBody({ className, ...props }: React.ComponentProps<"tbody">) {
  return (
    <tbody
      data-slot="table-body"
      className={cn("[&_tr:last-child]:border-0 divide-y divide-border/60", className)}
      {...props}
    />
  )
}

function TableFooter({ className, ...props }: React.ComponentProps<"tfoot">) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn(
        "border-t border-border bg-muted/80 font-medium text-foreground text-xs [&>tr]:last:border-b-0",
        className
      )}
      {...props}
    />
  )
}

function TableRow({ className, ...props }: React.ComponentProps<"tr">) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "border-b border-border/60 transition-colors hover:bg-muted/40 data-[state=selected]:bg-muted/60",
        className
      )}
      {...props}
    />
  )
}

function TableHead({ className, ...props }: React.ComponentProps<"th">) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "h-8 px-3 py-1.5 text-left align-middle font-semibold whitespace-nowrap text-muted-foreground",
        className
      )}
      {...props}
    />
  )
}

function TableCell({
  className,
  mono = false,
  ...props
}: React.ComponentProps<"td"> & { mono?: boolean }) {
  return (
    <td
      data-slot="table-cell"
      className={cn(
        "px-3 py-2 align-middle whitespace-nowrap text-foreground",
        mono && "font-mono text-xs",
        className
      )}
      {...props}
    />
  )
}

function TableCaption({
  className,
  ...props
}: React.ComponentProps<"caption">) {
  return (
    <caption
      data-slot="table-caption"
      className={cn("mt-4 text-xs text-muted-foreground", className)}
      {...props}
    />
  )
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
}
