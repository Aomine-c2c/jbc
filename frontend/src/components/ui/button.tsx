import * as React from "react"
import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded border border-transparent font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs border-primary/20",
        outline:
          "border-border bg-background hover:bg-muted hover:text-foreground shadow-xs text-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 border-border/50",
        ghost:
          "hover:bg-muted hover:text-foreground text-muted-foreground",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90 shadow-xs border-destructive/30",
        warning:
          "bg-amber-600 dark:bg-amber-500 text-white hover:bg-amber-700 dark:hover:bg-amber-600 shadow-xs",
        success:
          "bg-emerald-600 dark:bg-emerald-500 text-white hover:bg-emerald-700 dark:hover:bg-emerald-600 shadow-xs",
        link:
          "text-primary underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-8 gap-1.5 px-3 text-xs",
        xs: "h-6 gap-1 rounded px-2 text-[11px] [&_svg]:size-3",
        sm: "h-7 gap-1.5 rounded px-2.5 text-xs [&_svg]:size-3.5",
        lg: "h-9 gap-2 px-4 text-sm [&_svg]:size-4",
        icon: "size-8 p-0 [&_svg]:size-4",
        "icon-xs": "size-6 p-0 [&_svg]:size-3",
        "icon-sm": "size-7 p-0 [&_svg]:size-3.5",
        "icon-lg": "size-9 p-0 [&_svg]:size-4",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends ButtonPrimitive.Props,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  hotkey?: string
}

function Button({
  className,
  variant = "default",
  size = "default",
  loading = false,
  hotkey,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <ButtonPrimitive
      data-slot="button"
      disabled={disabled || loading}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {loading && <Loader2 className="animate-spin size-3.5 mr-1" />}
      {children}
      {hotkey && (
        <kbd className="ml-1.5 rounded border border-current/20 bg-background/20 px-1 py-0.2 text-[9px] font-mono uppercase tracking-tighter opacity-80 group-hover/button:opacity-100">
          {hotkey}
        </kbd>
      )}
    </ButtonPrimitive>
  )
}

export { Button, buttonVariants }
