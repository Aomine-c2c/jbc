'use client';

import * as React from "react"
import { PenTool, RotateCcw, CheckCheck, Stamp } from "lucide-react"
import { Button } from "./button"
import { Input } from "./input"
import { cn } from "@/lib/utils"

export interface SignaturePanelProps {
  signerName?: string
  signerRole?: string
  signerId?: string
  onSign: (signatureData: { name: string; role: string; timestamp: string; hash?: string }) => void
  disabled?: boolean
  signed?: boolean
  signedAt?: string
  className?: string
}

export function SignaturePanel({
  signerName = "",
  signerRole = "Lead Technician",
  signerId = "",
  onSign,
  disabled = false,
  signed = false,
  signedAt,
  className,
}: SignaturePanelProps) {
  const [name, setName] = React.useState(signerName)
  const [empId, setEmpId] = React.useState(signerId)
  const [acknowledged, setAcknowledged] = React.useState(false)
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null)
  const [isDrawing, setIsDrawing] = React.useState(false)
  const [hasDrawn, setHasDrawn] = React.useState(false)

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (disabled || signed) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const x = ("touches" in e ? e.touches[0].clientX : e.clientX) - rect.left
    const y = ("touches" in e ? e.touches[0].clientY : e.clientY) - rect.top

    ctx.strokeStyle = "currentColor"
    ctx.lineWidth = 2
    ctx.lineCap = "round"
    ctx.beginPath()
    ctx.moveTo(x, y)
    setIsDrawing(true)
    setHasDrawn(true)
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing || disabled || signed) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const x = ("touches" in e ? e.touches[0].clientX : e.clientX) - rect.left
    const y = ("touches" in e ? e.touches[0].clientY : e.clientY) - rect.top

    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const stopDrawing = () => {
    setIsDrawing(false)
  }

  const clearCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    setHasDrawn(false)
  }

  const handleConfirmSignature = () => {
    if (!name.trim() || !acknowledged) return
    const now = new Date().toISOString()
    onSign({
      name: name.trim(),
      role: signerRole,
      timestamp: now,
      hash: `SIG-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
    })
  }

  if (signed) {
    return (
      <div className={cn("rounded border border-emerald-500/40 bg-emerald-500/10 p-4 space-y-2", className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-semibold text-xs">
            <Stamp className="size-4 text-emerald-500" />
            <span>Digital Handover Sign-off Verified</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 uppercase tracking-widest bg-emerald-500/20 px-2 py-0.5 rounded">
            STAMPED & VERIFIED
          </span>
        </div>
        <div className="grid grid-cols-2 gap-4 text-xs font-mono pt-1 text-foreground/80">
          <div>
            <span className="text-muted-foreground block text-[10px]">SIGNER NAME:</span>
            <span className="font-semibold">{name || signerName || "Authorized Personnel"}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">ROLE:</span>
            <span>{signerRole}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">TIMESTAMP:</span>
            <span>{signedAt ? new Date(signedAt).toLocaleString() : new Date().toLocaleString()}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">AUTHENTICITY:</span>
            <span className="text-emerald-600 dark:text-emerald-400">Cryptographically Recorded</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-3 rounded border border-border bg-card p-4 text-xs", className)}>
      <div className="flex items-center justify-between border-b border-border pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-foreground">
          <PenTool className="size-3.5 text-primary" />
          <span>Electronic Sign-off & Verification</span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground uppercase">Role: {signerRole}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
            Signatory Full Name *
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Tendai Moyo"
            disabled={disabled}
          />
        </div>
        <div>
          <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
            Employee / Operator ID
          </label>
          <Input
            mono
            value={empId}
            onChange={(e) => setEmpId(e.target.value)}
            placeholder="e.g. BK-ENG-4401"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Drawing Surface */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="text-[10px] font-mono uppercase text-muted-foreground">
            Signature Gesture Canvas
          </label>
          {hasDrawn && (
            <button
              type="button"
              onClick={clearCanvas}
              disabled={disabled}
              className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw className="size-2.5" />
              Clear Canvas
            </button>
          )}
        </div>
        <div className="relative rounded border border-dashed border-border bg-muted/20 text-foreground overflow-hidden">
          <canvas
            ref={canvasRef}
            width={480}
            height={90}
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            onTouchStart={startDrawing}
            onTouchMove={draw}
            onTouchEnd={stopDrawing}
            className="w-full h-[90px] cursor-crosshair touch-none"
          />
          {!hasDrawn && (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-muted-foreground/50 text-[11px]">
              Draw signature here or sign with pointer
            </div>
          )}
        </div>
      </div>

      {/* Acknowledgment checkbox */}
      <label className="flex items-start gap-2 cursor-pointer select-none pt-1">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
          disabled={disabled}
          className="mt-0.5 size-3.5 rounded border-border accent-primary"
        />
        <span className="text-[11px] text-muted-foreground leading-tight">
          I certify that the maintenance work and spare parts documented on this digital job card have been performed according to Bikita Minerals safety and operational standards.
        </span>
      </label>

      {/* Confirm Button */}
      <div className="flex justify-end pt-2 border-t border-border">
        <Button
          size="sm"
          variant="success"
          disabled={disabled || !name.trim() || !acknowledged}
          onClick={handleConfirmSignature}
        >
          <CheckCheck className="size-3.5 mr-1" />
          Apply Official Sign-off Stamp
        </Button>
      </div>
    </div>
  )
}
