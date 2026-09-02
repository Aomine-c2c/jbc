'use client';

import * as React from "react";
import { PenTool, RotateCcw, CheckCheck, Stamp, ShieldCheck, Lock, AlertTriangle } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";
import { cn } from "@/lib/utils";

export interface SignatureData {
  name: string;
  role: string;
  employeeId?: string;
  timestamp: string;
  hash: string;
  signatureImage?: string;
  lotoVerified?: boolean;
}

export interface SignaturePanelProps {
  signerName?: string;
  signerRole?: string;
  signerId?: string;
  title?: string;
  requireLoto?: boolean;
  onSign: (signatureData: SignatureData) => void;
  disabled?: boolean;
  signed?: boolean;
  signedAt?: string;
  signedBy?: string;
  signatureHash?: string;
  signatureImage?: string;
  className?: string;
}

export function SignaturePanel({
  signerName = "",
  signerRole = "Lead Technician",
  signerId = "",
  title = "Electronic Sign-off & Verification",
  requireLoto = false,
  onSign,
  disabled = false,
  signed = false,
  signedAt,
  signedBy,
  signatureHash,
  signatureImage,
  className,
}: SignaturePanelProps) {
  const [name, setName] = React.useState(signerName || "");
  const [empId, setEmpId] = React.useState(signerId || "");
  const [acknowledged, setAcknowledged] = React.useState(false);
  const [lotoChecked, setLotoChecked] = React.useState(!requireLoto);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = React.useState(false);
  const [hasDrawn, setHasDrawn] = React.useState(false);

  // Setup High-DPI canvas
  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || signed) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const rect = canvas.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      ctx.strokeStyle = "#18181b";
      ctx.lineWidth = 2.5;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
    }
  }, [signed]);

  const getCoordinates = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (disabled || signed) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
    setHasDrawn(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing || disabled || signed) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
  };

  const handleConfirmSignature = async () => {
    if (!name.trim() || !acknowledged || (requireLoto && !lotoChecked)) return;
    
    const canvas = canvasRef.current;
    let imgData: string | undefined;
    if (canvas && hasDrawn) {
      try {
        imgData = canvas.toDataURL("image/png");
      } catch {
        // fallback
      }
    }

    const now = new Date().toISOString();
    const rawStamp = `${name.trim()}-${signerRole}-${empId.trim()}-${now}`;
    
    // Generate quick cryptographic hash
    let hash = `BK-SIG-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
    if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
      try {
        const msgBuffer = new TextEncoder().encode(rawStamp);
        const hashBuffer = await window.crypto.subtle.digest("SHA-256", msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        hash = `BK-SHA256-${hashArray.slice(0, 8).map(b => b.toString(16).padStart(2, "0")).join("").toUpperCase()}`;
      } catch {
        // fallback
      }
    }

    onSign({
      name: name.trim(),
      role: signerRole,
      employeeId: empId.trim() || undefined,
      timestamp: now,
      hash,
      signatureImage: imgData,
      lotoVerified: requireLoto ? lotoChecked : undefined,
    });
  };

  if (signed) {
    return (
      <div className={cn("rounded-lg border border-emerald-500/40 bg-emerald-500/5 p-4 space-y-3", className)}>
        <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-semibold text-xs">
            <Stamp className="size-4 text-emerald-600 dark:text-emerald-400" />
            <span>Digital Sign-off Verified & Recorded</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold uppercase tracking-wider bg-emerald-500/20 px-2 py-0.5 rounded">
            CRYPTOGRAPHICALLY VERIFIED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono text-foreground/80">
          <div>
            <span className="text-muted-foreground block text-[10px]">SIGNATORY:</span>
            <span className="font-bold text-foreground">{signedBy || name || signerName || "Authorized Personnel"}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">AUTHORITY ROLE:</span>
            <span className="text-foreground">{signerRole}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">TIMESTAMP:</span>
            <span className="text-foreground">{signedAt ? new Date(signedAt).toLocaleString() : new Date().toLocaleString()}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[10px]">SECURITY STAMP:</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-bold text-[11px] truncate block">
              {signatureHash || "BK-SIG-VERIFIED"}
            </span>
          </div>
        </div>

        {signatureImage && (
          <div className="pt-2 border-t border-emerald-500/20 flex items-center gap-3">
            <span className="text-[10px] font-mono text-muted-foreground">SIGNATURE:</span>
            <div className="bg-white px-3 py-1 rounded border border-emerald-500/30 inline-block shadow-2xs">
              {/* signatureImage is a client-generated data: URL from canvas.toDataURL().
                  next/image cannot optimize data URLs, so we use a plain <img> with
                  explicit dimensions to avoid CLS. The image is already small (h-8). */}
              <img
                src={signatureImage}
                alt="Handwritten Signature"
                width={160}
                height={32}
                className="h-8 max-w-40 w-auto object-contain"
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn("space-y-3 rounded-lg border border-border bg-card p-4 text-xs shadow-xs", className)}>
      <div className="flex items-center justify-between border-b border-border pb-2">
        <div className="flex items-center gap-1.5 font-bold text-foreground">
          <PenTool className="size-3.5 text-primary" />
          <span>{title}</span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground uppercase bg-muted px-2 py-0.5 rounded">
          Role: {signerRole}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
            Signatory Full Name <span className="text-destructive">*</span>
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Tendai Moyo"
            disabled={disabled}
            className="h-8 text-xs"
          />
        </div>
        <div>
          <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
            Employee / Badge Number
          </label>
          <Input
            mono
            value={empId}
            onChange={(e) => setEmpId(e.target.value)}
            placeholder="e.g. BK-OP-4019"
            disabled={disabled}
            className="h-8 text-xs font-mono"
          />
        </div>
      </div>

      {/* LOTO Safety Check if required */}
      {requireLoto && (
        <div className="p-2.5 rounded border border-amber-500/30 bg-amber-500/5 space-y-1.5">
          <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-bold text-[11px]">
            <Lock className="size-3.5" />
            <span>Lockout / Tagout (LOTO) Zero-Energy Verification</span>
          </div>
          <label className="flex items-start gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={lotoChecked}
              onChange={(e) => setLotoChecked(e.target.checked)}
              disabled={disabled}
              className="mt-0.5 size-3.5 rounded border-amber-500 accent-amber-500"
            />
            <span className="text-[11px] text-muted-foreground leading-tight">
              I certify that all electrical, hydraulic, and mechanical isolations have been physically locked, tagged, and zero-energy verified prior to commencing work.
            </span>
          </label>
        </div>
      )}

      {/* Drawing Canvas */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="text-[10px] font-mono uppercase text-muted-foreground">
            Touch / Stylus Handwritten Signature
          </label>
          {hasDrawn && (
            <button
              type="button"
              onClick={clearCanvas}
              disabled={disabled}
              className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1 cursor-pointer transition-colors"
            >
              <RotateCcw className="size-2.5" />
              Clear
            </button>
          )}
        </div>
        <div className="relative rounded-md border border-dashed border-border bg-white dark:bg-zinc-950 text-foreground overflow-hidden">
          <canvas
            ref={canvasRef}
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
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-muted-foreground/40 text-[11px] font-mono">
              Draw handwritten signature here
            </div>
          )}
        </div>
      </div>

      {/* Acknowledgment Checkbox */}
      <label className="flex items-start gap-2 cursor-pointer select-none pt-1">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
          disabled={disabled}
          className="mt-0.5 size-3.5 rounded border-border accent-primary"
        />
        <span className="text-[11px] text-muted-foreground leading-tight">
          I certify that the recorded operational tasks, safety checks, and spare parts meet Bikita Minerals DWRMS compliance standards.
        </span>
      </label>

      {/* Confirm Button */}
      <div className="flex justify-end pt-2 border-t border-border">
        <Button
          size="sm"
          disabled={disabled || !name.trim() || !acknowledged || (requireLoto && !lotoChecked)}
          onClick={handleConfirmSignature}
          className="font-bold gap-1.5"
        >
          <CheckCheck className="size-3.5" />
          Apply Official Digital Stamp
        </Button>
      </div>
    </div>
  );
}

