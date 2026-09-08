'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';
import { OperatorPreStartModal } from '@/components/work/OperatorPreStartModal';
import {
  Truck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldCheck,
  ShieldAlert,
  Gauge,
  Clock,
  RefreshCw,
  Plus,
  FileText,
  AlertOctagon,
  Calendar,
  Layers,
  ChevronRight,
} from 'lucide-react';
import Link from 'next/link';

interface PreStartRow {
  id: string;
  reference_number: string;
  machine_id: string;
  machine_name: string;
  machine_status: string;
  hour_meter_reading: number;
  overall_status: string; // PASSED, DEFECTS_NOTED, CRITICAL_RED_TAG
  is_grounded: boolean;
  spawned_job_card_id?: string;
  spawned_job_card_number?: string;
  created_at: string;
  operator_name?: string;
  operator_notes?: string;
}

interface RequisitionItem {
  id: string;
  requisition_number?: string;
  purpose: string;
  status: string;
  required_start_time?: string;
  estimated_duration_hours?: number;
  created_at?: string;
}

interface MachineSummary {
  id: string;
  identifier: string;
  status: string;
  current_hour_meter?: number;
  location?: string;
  machine_type?: {
    name: string;
    category?: string;
  };
}

export function OperatorMyWorkView() {
  const [preStarts, setPreStarts] = useState<PreStartRow[]>([]);
  const [requisitions, setRequisitions] = useState<RequisitionItem[]>([]);
  const [fleetMachines, setFleetMachines] = useState<MachineSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isPreStartModalOpen, setIsPreStartModalOpen] = useState(false);
  const [feedbackBanner, setFeedbackBanner] = useState<{
    type: 'success' | 'warning' | 'critical';
    title: string;
    message: string;
  } | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [preStartsRes, reqsRes, fleetRes] = await Promise.allSettled([
        apiFetch<PreStartRow[]>('/api/v1/work/pre-starts'),
        apiFetch<RequisitionItem[]>('/api/v1/fleet/requisitions'),
        apiFetch<MachineSummary[]>('/api/v1/fleet/machines'),
      ]);

      if (preStartsRes.status === 'fulfilled' && Array.isArray(preStartsRes.value)) {
        setPreStarts(preStartsRes.value);
      } else {
        setPreStarts([]);
      }

      if (reqsRes.status === 'fulfilled' && Array.isArray(reqsRes.value)) {
        setRequisitions(reqsRes.value);
      } else {
        setRequisitions([]);
      }

      if (fleetRes.status === 'fulfilled' && Array.isArray(fleetRes.value)) {
        setFleetMachines(fleetRes.value);
      } else {
        setFleetMachines([]);
      }
    } catch (err) {
      console.error('Failed to load operator workspace data', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handlePreStartSuccess = (result: {
    referenceNumber: string;
    isGrounded: boolean;
    machineName: string;
    overallStatus: string;
  }) => {
    if (result.isGrounded) {
      setFeedbackBanner({
        type: 'critical',
        title: `CRITICAL RED-TAG ISSUED: ${result.machineName}`,
        message: `Inspection ${result.referenceNumber} grounded this machine (OUT_OF_SERVICE). An urgent maintenance job card has been generated.`,
      });
    } else if (result.overallStatus === 'DEFECTS_NOTED') {
      setFeedbackBanner({
        type: 'warning',
        title: `Pre-Start Completed with Minor Defects: ${result.machineName}`,
        message: `Inspection ${result.referenceNumber} recorded minor maintenance items. The unit remains available for standard operation.`,
      });
    } else {
      setFeedbackBanner({
        type: 'success',
        title: `Pre-Start Certified: ${result.machineName}`,
        message: `Inspection ${result.referenceNumber} passed all 5 safety domains. Equipment verified shift-ready.`,
      });
    }
    loadData();
  };

  // Metrics
  const totalLoggedToday = preStarts.length;
  const recentInspection = preStarts[0];
  const activeGrounded = preStarts.filter((p) => p.is_grounded).length;

  return (
    <div className="space-y-6">
      {/* FEEDBACK BANNER */}
      {feedbackBanner && (
        <div
          className={`p-4 rounded-xl border flex items-start justify-between gap-3 transition-all ${
            feedbackBanner.type === 'critical'
              ? 'bg-rose-500/15 border-rose-500/30 text-rose-400'
              : feedbackBanner.type === 'warning'
              ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
              : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
          }`}
        >
          <div className="flex items-start gap-3">
            {feedbackBanner.type === 'critical' ? (
              <Flame className="size-5 shrink-0 mt-0.5 text-rose-500" />
            ) : feedbackBanner.type === 'warning' ? (
              <AlertTriangle className="size-5 shrink-0 mt-0.5 text-amber-500" />
            ) : (
              <CheckCircle2 className="size-5 shrink-0 mt-0.5 text-emerald-500" />
            )}
            <div>
              <p className="text-xs font-bold">{feedbackBanner.title}</p>
              <p className="text-xs opacity-90 mt-0.5">{feedbackBanner.message}</p>
            </div>
          </div>
          <button
            onClick={() => setFeedbackBanner(null)}
            className="text-xs opacity-60 hover:opacity-100 px-2 py-1"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* HERO COMMAND BANNER */}
      <div className="relative overflow-hidden rounded-2xl bg-linear-to-r from-zinc-900 via-zinc-800 to-zinc-900 border border-zinc-800 p-6 text-white shadow-lg">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider bg-primary/20 text-primary border border-primary/30">
                Shift Alpha Operations
              </span>
              <span className="text-xs text-zinc-400 flex items-center gap-1 font-mono">
                <Clock className="size-3" />
                Bikita Open Cast Main Pit
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              Operator Field & Equipment Console
            </h1>
            <p className="text-xs text-zinc-300 leading-relaxed">
              Complete mandatory pre-start safety walkarounds, log hour-meter readings, flag machine defects, and review vehicle bookings.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => setIsPreStartModalOpen(true)}
              size="lg"
              className="bg-primary text-primary-foreground font-bold hover:bg-primary/90 shadow-md gap-2 text-xs"
            >
              <Truck className="size-4" />
              Start Pre-Start Inspection
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                setRefreshing(true);
                loadData();
              }}
              disabled={refreshing}
              className="border-zinc-700 bg-zinc-800/80 text-zinc-200 hover:bg-zinc-700 text-xs gap-1.5"
            >
              <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* TELEMETRY KPI METRICS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Inspections Logged</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">
                {totalLoggedToday}
              </p>
            </div>
            <div className="p-2.5 rounded-md bg-primary/10 text-primary">
              <ShieldCheck className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Last Pre-Start Status</p>
              <div className="mt-1">
                {recentInspection ? (
                  recentInspection.is_grounded ? (
                    <span className="text-xs font-bold text-rose-500 flex items-center gap-1">
                      <Flame className="size-3.5" /> GROUNDED
                    </span>
                  ) : recentInspection.overall_status === 'DEFECTS_NOTED' ? (
                    <span className="text-xs font-bold text-amber-500 flex items-center gap-1">
                      <AlertTriangle className="size-3.5" /> DEFECTS NOTED
                    </span>
                  ) : (
                    <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="size-3.5" /> READY TO RUN
                    </span>
                  )
                ) : (
                  <span className="text-xs text-muted-foreground">None Logged</span>
                )}
              </div>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Gauge className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Grounded Units</p>
              <p className="text-2xl font-mono font-bold text-rose-500 mt-1">
                {activeGrounded}
              </p>
            </div>
            <div className="p-2.5 rounded-md bg-rose-500/10 text-rose-500">
              <AlertOctagon className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Machine Bookings</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">
                {requisitions.length}
              </p>
            </div>
            <div className="p-2.5 rounded-md bg-blue-500/10 text-blue-400">
              <FileText className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* RECENT PRE-START INSPECTION SUBMISSIONS */}
      <Card className="bg-card border-border">
        <CardHeader className="p-5 border-b border-border flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <ShieldCheck className="size-4 text-primary" />
              <span>Shift Pre-Start Walkaround Log</span>
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Verified daily safety walkarounds, hour meter readings, and defect tickets.
            </p>
          </div>
          <Button
            size="sm"
            onClick={() => setIsPreStartModalOpen(true)}
            className="text-xs gap-1.5 bg-primary text-primary-foreground"
          >
            <Plus className="size-3.5" />
            New Pre-Start
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <RefreshCw className="size-4 animate-spin text-primary" />
              Loading inspection records...
            </div>
          ) : preStarts.length === 0 ? (
            <div className="p-10 text-center space-y-3">
              <div className="size-12 rounded-full bg-muted flex items-center justify-center mx-auto text-muted-foreground">
                <Truck className="size-6" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-foreground">No pre-start checklists completed yet</p>
                <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                  Before operating any haul truck, excavator, loader, or plant vehicle, complete the digital safety walkaround.
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => setIsPreStartModalOpen(true)}
                className="text-xs gap-1.5 bg-primary text-primary-foreground"
              >
                <Truck className="size-3.5" />
                Initiate First Pre-Start
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/40 text-muted-foreground font-mono text-[11px] uppercase border-b border-border">
                  <tr>
                    <th className="px-4 py-3">Inspection Ref</th>
                    <th className="px-4 py-3">Machine Unit</th>
                    <th className="px-4 py-3">Hour Meter</th>
                    <th className="px-4 py-3">Result / Health</th>
                    <th className="px-4 py-3">Defect Action</th>
                    <th className="px-4 py-3">Logged At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {preStarts.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-foreground">
                        {p.reference_number}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Truck className="size-3.5 text-muted-foreground" />
                          <span className="font-semibold text-foreground">{p.machine_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-muted-foreground">
                        {p.hour_meter_reading} hrs
                      </td>
                      <td className="px-4 py-3">
                        {p.is_grounded ? (
                          <Badge className="bg-rose-500/15 text-rose-400 border-rose-500/30 gap-1 px-2 py-0.5">
                            <Flame className="size-3" />
                            CRITICAL RED-TAG
                          </Badge>
                        ) : p.overall_status === 'DEFECTS_NOTED' ? (
                          <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/30 gap-1 px-2 py-0.5">
                            <AlertTriangle className="size-3" />
                            DEFECTS NOTED
                          </Badge>
                        ) : (
                          <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 gap-1 px-2 py-0.5">
                            <CheckCircle2 className="size-3" />
                            PASSED
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {p.spawned_job_card_number ? (
                          <span className="font-mono text-xs text-rose-400 font-semibold flex items-center gap-1">
                            <AlertTriangle className="size-3" />
                            {p.spawned_job_card_number}
                          </span>
                        ) : p.overall_status === 'DEFECTS_NOTED' ? (
                          <span className="text-amber-400 text-xs font-mono">Follow-up Dispatched</span>
                        ) : (
                          <span className="text-muted-foreground text-xs font-mono">None (Safe)</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground font-mono text-[11px]">
                        {p.created_at ? new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* MY MACHINE BOOKINGS & REQUISITIONS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card border-border">
          <CardHeader className="p-4 border-b border-border flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <FileText className="size-4 text-blue-400" />
              <span>My Machine Bookings</span>
            </CardTitle>
            <Link href="/fleet/requisitions/new">
              <Button size="sm" variant="outline" className="text-xs gap-1">
                <Plus className="size-3" />
                Book Machine
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {requisitions.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                No active machine booking requests.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {requisitions.slice(0, 5).map((req) => (
                  <div key={req.id} className="p-3.5 flex items-center justify-between hover:bg-muted/20 transition-colors">
                    <div className="space-y-0.5">
                      <p className="text-xs font-semibold text-foreground">
                        {req.requisition_number || 'REQ-MACHINE'}
                      </p>
                      <p className="text-[11px] text-muted-foreground truncate max-w-xs">
                        {req.purpose}
                      </p>
                    </div>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {req.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="p-4 border-b border-border">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <Truck className="size-4 text-emerald-400" />
              <span>Available Mine Heavy Fleet</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {fleetMachines.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                No fleet units registered.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {fleetMachines.slice(0, 5).map((m) => (
                  <div key={m.id} className="p-3.5 flex items-center justify-between hover:bg-muted/20 transition-colors">
                    <div>
                      <p className="text-xs font-semibold text-foreground">{m.identifier}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {m.machine_type?.name || 'Equipment'} • {m.current_hour_meter || 0} hrs
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                          m.status === 'AVAILABLE'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : m.status === 'OUT_OF_SERVICE'
                            ? 'bg-rose-500/15 text-rose-500 border border-rose-500/30'
                            : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {m.status}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setIsPreStartModalOpen(true)}
                        className="text-xs h-7 px-2 text-primary hover:bg-primary/10"
                      >
                        Checklist
                        <ChevronRight className="size-3 ml-1" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* PRE-START MODAL */}
      <OperatorPreStartModal
        isOpen={isPreStartModalOpen}
        onClose={() => setIsPreStartModalOpen(false)}
        onSuccess={handlePreStartSuccess}
      />
    </div>
  );
}
