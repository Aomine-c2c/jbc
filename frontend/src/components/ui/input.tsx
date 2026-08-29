import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface InputProps extends React.ComponentProps<"input"> {
  prefixText?: string
  suffixText?: string
  prefixIcon?: React.ReactNode
  suffixIcon?: React.ReactNode
  mono?: boolean
  onClear?: () => void
}

function Input({
  className,
  type,
  prefixText,
  suffixText,
  prefixIcon,
  suffixIcon,
  mono = false,
  onClear,
  value,
  ...props
}: InputProps) {
  const hasWrapper = prefixText || suffixText || prefixIcon || suffixIcon || onClear

  const inputElement = (
    <InputPrimitive
      type={type}
      data-slot="input"
      value={value}
      className={cn(
        "h-8 w-full min-w-0 rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground transition-all outline-none",
        "file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-xs file:font-medium file:text-foreground",
        "placeholder:text-muted-foreground/70 focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring/50",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-muted/60 disabled:opacity-60",
        mono && "font-mono tracking-tight",
        hasWrapper && "border-0 focus-visible:ring-0 focus-visible:border-transparent bg-transparent h-full px-2 shadow-none",
        className
      )}
      {...props}
    />
  )

  if (!hasWrapper) {
    return inputElement
  }

  return (
    <div className={cn(
      "relative flex h-8 w-full items-center rounded border border-input bg-card transition-all focus-within:border-ring focus-within:ring-1 focus-within:ring-ring/50",
      props.disabled && "bg-muted/60 opacity-60 cursor-not-allowed",
      className
    )}>
      {prefixIcon && (
        <span className="flex items-center pl-2.5 text-muted-foreground [&_svg]:size-3.5">
          {prefixIcon}
        </span>
      )}
      {prefixText && (
        <span className="flex items-center pl-2.5 text-[11px] font-mono font-medium text-muted-foreground uppercase select-none">
          {prefixText}
        </span>
      )}

      {inputElement}

      {onClear && value && (
        <button
          type="button"
          onClick={onClear}
          tabIndex={-1}
          className="flex items-center pr-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="size-3" />
        </button>
      )}

      {suffixIcon && (
        <span className="flex items-center pr-2.5 text-muted-foreground [&_svg]:size-3.5">
          {suffixIcon}
        </span>
      )}
      {suffixText && (
        <span className="flex items-center pr-2.5 text-[11px] font-mono font-medium text-muted-foreground uppercase select-none">
          {suffixText}
        </span>
      )}
    </div>
  )
}

export { Input }
