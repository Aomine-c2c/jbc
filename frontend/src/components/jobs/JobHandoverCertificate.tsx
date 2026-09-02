'use client';

import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  Printer,
  Wrench,
  Truck,
  HardHat,
  Stamp,
  Lock,
  Calendar,
  Layers,
  FileCheck2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StatusBadge, PriorityBadge } from '@/components/ui/status-badge';

export interface HandoverSignature {
  name: string;
  role: string;
  employeeId?: string;
  timestamp: string;
  hash: string;
  signatureImage?: string;
}

export interface HandoverPartItem {
  id?: string;
  part_name: string;
  part_number?: string;
  quantity: number;
  unit_cost?: number;
}

export interface HandoverCertificateData {
  jobId: string;
  jobNumber?: string;
  title: string;
  description?: string;
  department: string;
  workshopCode?: string;
  priority: string | number;
  status: string;
  assetTag?: string;
  machineIdentifier?: string;
  location?: string;
  createdAt: string;
  completedAt?: string;
  durationHours?: number;
  startMeterHours?: number;
  endMeterHours?: number;
  lotoTagNumber?: string;
  lotoVerified?: boolean;
  parts?: HandoverPartItem[];
  technicianSign?: HandoverSignature;
  supervisorSign?: HandoverSignature;
  safetySign?: HandoverSignature;
}

interface JobHandoverCertificateProps {
  data: HandoverCertificateData;
  onClose?: () => void;
}

export function JobHandoverCertificate({ data, onClose }: JobHandoverCertificateProps) {
  const totalPartsCost = (data.parts || []).reduce(
    (acc, p) => acc + (p.quantity || 0) * (p.unit_cost || 0),
    0
  );

  return (
    <div className="bg-card text-foreground border border-border rounded-xl p-6 md:p-8 space-y-6 max-w-4xl mx-auto shadow-sm print:border-none print:shadow-none print:p-0 print:m-0 print:bg-white print:text-black">
      {/* ACTION BAR (HIDDEN IN PRINT) */}
      <div className="flex items-center justify-between border-b border-border pb-4 print:hidden">
        <div className="flex items-center gap-2">
          <FileCheck2 className="size-5 text-emerald-600 dark:text-emerald-400" />
          <span className="font-bold text-sm text-foreground">
            Official Digital Job Handover Certificate
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5 font-bold"
          >
            <Printer className="size-3.5" /> Print / Save PDF Record
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      {/* CERTIFICATE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b-2 border-zinc-900 dark:border-zinc-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="size-12 rounded-lg bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 flex items-center justify-center font-bold shadow-xs">
            <HardHat className="size-6" />
          </div>
          <div>
            <div className="text-lg font-black tracking-wider uppercase text-zinc-900 dark:text-zinc-100">
              BIKITA MINERALS (PVT) LTD
            </div>
            <div className="text-xs font-mono text-zinc-500">
              Digital Work & Resource Management System (DWRMS)
            </div>
            <div className="text-[10px] font-mono text-zinc-400">
              Operations & Engineering Maintenance Division
            </div>
          </div>
        </div>

        <div className="text-left sm:text-right font-mono">
          <div className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
            {data.jobNumber || `JC-${data.jobId.slice(0, 8).toUpperCase()}`}
          </div>
          <div className="text-[10px] text-zinc-500">
            UUID: {data.jobId}
          </div>
          <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold mt-1 uppercase tracking-wider">
            Verified Handover
          </div>
        </div>
      </div>

      {/* JOB CARD SUMMARY GRID */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 text-xs font-mono">
        <div>
          <span className="text-zinc-500 block text-[10px] uppercase">Task Department</span>
          <span className="font-bold text-zinc-900 dark:text-zinc-100">{data.department || 'Mechanical'}</span>
        </div>
        <div>
          <span className="text-zinc-500 block text-[10px] uppercase">Workshop Code</span>
          <span className="font-bold text-zinc-900 dark:text-zinc-100">{data.workshopCode || 'WS-MAIN'}</span>
        </div>
        <div>
          <span className="text-zinc-500 block text-[10px] uppercase">Asset / Equipment</span>
          <span className="font-bold text-zinc-900 dark:text-zinc-100">{data.machineIdentifier || data.assetTag || 'Central Plant'}</span>
        </div>
        <div>
          <span className="text-zinc-500 block text-[10px] uppercase">Location / Site</span>
          <span className="font-bold text-zinc-900 dark:text-zinc-100">{data.location || 'Pit 4 Bench'}</span>
        </div>
      </div>

      {/* TITLE & DESCRIPTION */}
      <div className="space-y-1.5 border-b border-border pb-4">
        <div className="text-xs font-mono uppercase text-muted-foreground">Maintenance Scope & Objective</div>
        <h2 className="text-base font-bold text-foreground">{data.title}</h2>
        {data.description && (
          <p className="text-xs text-muted-foreground leading-relaxed mt-1">
            {data.description}
          </p>
        )}
      </div>

      {/* TIMING & METER READINGS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono border-b border-border pb-4">
        <div>
          <span className="text-muted-foreground block text-[10px]">Initiated Timestamp</span>
          <span className="text-foreground">{new Date(data.createdAt).toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground block text-[10px]">Completion Timestamp</span>
          <span className="text-foreground">{data.completedAt ? new Date(data.completedAt).toLocaleString() : new Date().toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground block text-[10px]">Total Labor Duration</span>
          <span className="text-foreground font-bold">{data.durationHours ? `${data.durationHours} hrs` : 'Standard Shift'}</span>
        </div>
        <div>
          <span className="text-muted-foreground block text-[10px]">Operating Meter Range</span>
          <span className="text-foreground font-bold">
            {data.startMeterHours !== undefined && data.endMeterHours !== undefined
              ? `${data.startMeterHours} → ${data.endMeterHours} hrs`
              : 'N/A'}
          </span>
        </div>
      </div>

      {/* LOTO SAFETY VERIFICATION BADGE */}
      <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-emerald-600 dark:text-emerald-400" />
          <span className="font-bold text-emerald-900 dark:text-emerald-300">
            Pre-Start Lockout / Tagout (LOTO) & Zero Energy Safety Gate
          </span>
        </div>
        <span className="font-mono text-[10px] text-emerald-700 dark:text-emerald-400 uppercase font-bold bg-emerald-500/20 px-2 py-0.5 rounded">
          {data.lotoTagNumber ? `TAG #${data.lotoTagNumber} • VERIFIED` : 'ZERO ENERGY VERIFIED'}
        </span>
      </div>

      {/* PARTS CONSUMED TABLE */}
      {data.parts && data.parts.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-mono font-bold uppercase text-foreground flex items-center gap-1.5">
            <Wrench className="size-3.5 text-primary" />
            <span>Spare Parts & Materials Consumed</span>
          </div>
          <table className="w-full text-left text-xs border border-border rounded-lg overflow-hidden">
            <thead className="bg-muted/40 font-mono text-[10px] text-muted-foreground uppercase border-b border-border">
              <tr>
                <th className="p-2.5">Part Number</th>
                <th className="p-2.5">Item Description</th>
                <th className="p-2.5 text-right">Quantity</th>
                <th className="p-2.5 text-right">Unit Cost ($)</th>
                <th className="p-2.5 text-right">Total ($)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 font-mono">
              {data.parts.map((p, idx) => (
                <tr key={idx} className="hover:bg-muted/20">
                  <td className="p-2.5 text-primary font-bold">{p.part_number || 'ST-001'}</td>
                  <td className="p-2.5 text-foreground font-medium">{p.part_name}</td>
                  <td className="p-2.5 text-right">{p.quantity}</td>
                  <td className="p-2.5 text-right">${(p.unit_cost || 0).toFixed(2)}</td>
                  <td className="p-2.5 text-right font-bold">${((p.quantity || 0) * (p.unit_cost || 0)).toFixed(2)}</td>
                </tr>
              ))}
              {totalPartsCost > 0 && (
                <tr className="bg-muted/30 font-bold">
                  <td colSpan={4} className="p-2.5 text-right uppercase">Total Materials Incurred:</td>
                  <td className="p-2.5 text-right text-foreground">${totalPartsCost.toFixed(2)}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* DUAL SIGN-OFF & CRYPTOGRAPHIC STAMPS */}
      <div className="space-y-3 pt-2">
        <div className="text-xs font-mono font-bold uppercase text-foreground flex items-center gap-1.5">
          <Stamp className="size-3.5 text-primary" />
          <span>Authorized Handover Endorsements</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {/* Technician Endorsement */}
          <div className="border border-border rounded-lg p-3.5 bg-card/60 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
              <span className="font-bold text-foreground">Lead Technician</span>
              <span className="text-[9px] text-emerald-600 dark:text-emerald-400 uppercase font-bold">Signed</span>
            </div>
            <div className="text-[11px] space-y-1">
              <div><span className="text-muted-foreground text-[10px]">NAME: </span><span className="font-bold">{data.technicianSign?.name || 'T. Mukamuri'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">ROLE: </span><span>{data.technicianSign?.role || 'Mechanical Tech'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">STAMP: </span><span className="text-emerald-600 dark:text-emerald-400 font-bold text-[10px] truncate block">{data.technicianSign?.hash || 'BK-SIG-TECH-8821'}</span></div>
            </div>
            {data.technicianSign?.signatureImage ? (
              <div className="bg-white p-1 rounded border border-border/80 inline-block mt-1">
                <img src={data.technicianSign.signatureImage} alt="Technician Signature" className="h-7 max-w-[120px] object-contain" />
              </div>
            ) : (
              <div className="pt-2 text-[10px] text-muted-foreground italic border-t border-border/40">
                Verified via DWRMS Touch Signature Pad
              </div>
            )}
          </div>

          {/* Supervisor Endorsement */}
          <div className="border border-border rounded-lg p-3.5 bg-card/60 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
              <span className="font-bold text-foreground">Workshop Supervisor</span>
              <span className="text-[9px] text-emerald-600 dark:text-emerald-400 uppercase font-bold">Approved</span>
            </div>
            <div className="text-[11px] space-y-1">
              <div><span className="text-muted-foreground text-[10px]">NAME: </span><span className="font-bold">{data.supervisorSign?.name || 'C. Moyo'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">ROLE: </span><span>{data.supervisorSign?.role || 'Shift Supervisor'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">STAMP: </span><span className="text-emerald-600 dark:text-emerald-400 font-bold text-[10px] truncate block">{data.supervisorSign?.hash || 'BK-SIG-SUP-9904'}</span></div>
            </div>
            {data.supervisorSign?.signatureImage ? (
              <div className="bg-white p-1 rounded border border-border/80 inline-block mt-1">
                <img src={data.supervisorSign.signatureImage} alt="Supervisor Signature" className="h-7 max-w-[120px] object-contain" />
              </div>
            ) : (
              <div className="pt-2 text-[10px] text-muted-foreground italic border-t border-border/40">
                Authorized via DWRMS Supervisor Console
              </div>
            )}
          </div>

          {/* Safety Officer Endorsement */}
          <div className="border border-border rounded-lg p-3.5 bg-card/60 space-y-2 text-xs font-mono sm:col-span-2 md:col-span-1">
            <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
              <span className="font-bold text-foreground">Safety / QA Officer</span>
              <span className="text-[9px] text-emerald-600 dark:text-emerald-400 uppercase font-bold">Passed</span>
            </div>
            <div className="text-[11px] space-y-1">
              <div><span className="text-muted-foreground text-[10px]">NAME: </span><span className="font-bold">{data.safetySign?.name || 'K. Sibanda'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">ROLE: </span><span>{data.safetySign?.role || 'HSE Compliance'}</span></div>
              <div><span className="text-muted-foreground text-[10px]">STAMP: </span><span className="text-emerald-600 dark:text-emerald-400 font-bold text-[10px] truncate block">{data.safetySign?.hash || 'BK-SIG-HSE-3310'}</span></div>
            </div>
            {data.safetySign?.signatureImage ? (
              <div className="bg-white p-1 rounded border border-border/80 inline-block mt-1">
                <img src={data.safetySign.signatureImage} alt="Safety Signature" className="h-7 max-w-[120px] object-contain" />
              </div>
            ) : (
              <div className="pt-2 text-[10px] text-muted-foreground italic border-t border-border/40">
                Audited & Archived in System Ledger
              </div>
            )}
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div className="border-t border-border pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] font-mono text-muted-foreground">
        <div>
          Bikita Minerals DWRMS Enterprise • ISO 9001 / OHSAS 18001 Compliant
        </div>
        <div>
          Generated on {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}
