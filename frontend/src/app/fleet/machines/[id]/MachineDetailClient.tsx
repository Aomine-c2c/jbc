'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { OperatorPreStartModal } from '@/components/work/OperatorPreStartModal';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { TelemetrySpinner } from '@/components/ui/loading-state';
import {
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Gauge,
  RefreshCw,
  Plus,
  AlertOctagon,
  Calendar,
  Layers,
  MapPin,
  ArrowLeft,
  ArrowRight,
  Wrench,
  Truck,
  Activity,
  ExternalLink,
  Info,
} from 'lucide-react';

interface MachineDetail {
  id: string;
  machine_type_id: string;
  identifier: string;
  serial_number?: string | null;
  status: string;
  location?: string | null;
  location_id?: string | null;
  location_breadcrumb?: string | null;
  capacity_rating?: string | null;
  current_hour_meter: number;
  last_maintenance_date?: string | null;
  asset_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  machine_type?: {
    id: string;
    name: string;
    category?: string | null;
    description?: string | null;
    hourly_rate?: number;
  } | null;
}

interface PreStartRow {
  id: string;
  reference_number: string;
  machine_id: string;
  machine_name: string;
  machine_status: string;
  hour_meter_reading: number;
  overall_status: string;
  is_grounded: boolean;
  spawned_job_card_id?: string;
  spawned_job_card_number?: string;
  created_at: string;
  operator_name?: string;
  operator_notes?: string;
}

interface JobCardItem {
  id: string;
  job_number?: string;
  title: string;
  status: string;
  priority: number | string;
  reported_issue?: string;
  created_at?: string;
  required_date?: string;
  workshop_code?: string;
  estimated_hours?: number;
}

interface RequisitionItem {
  id: string;
  requisition_number?: string;
  purpose: string;
  status: string;
  start_time: string;
  end_time: string;
  department_id?: string;
  department?: { name: string };
  requester?: { first_name: string; last_name: string };
}

export default function MachineDetailClient() {
  const params = useParams();
  const router = useRouter();
  const machineId = params?.id as string;

  const [machine, setMachine] = useState<MachineDetail | null>(null);
  const [preStarts, setPreStarts] = useState<PreStartRow[]>([]);
  const [jobCards, setJobCards] = useState<JobCardItem[]>([]);
  const [requisitions, setRequisitions] = useState<RequisitionItem[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [isPreStartModalOpen, setIsPreStartModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'PRESTARTS' | 'JOBCARDS' | 'REQUISITIONS'>('OVERVIEW');
  const [feedbackBanner, setFeedbackBanner] = useState<{
    type: 'success' | 'warning' | 'critical';
    title: string;
    message: string;
  } | null>(null);

  const loadData = useCallback(async () => {
    if (!machineId) return;
    try {
      const [mRes, psRes, jcRes, reqRes] = await Promise.allSettled([
        apiFetch<MachineDetail>(`/api/v1/fleet/machines/${machineId}`),
        apiFetch<PreStartRow[]>(`/api/v1/work/pre-starts?machine_id=${machineId}`),
        apiFetch<JobCardItem[]>(`/api/v1/job-cards?machine_id=${machineId}`),
        apiFetch<RequisitionItem[]>(`/api/v1/fleet/requisitions?machine_id=${machineId}`),
      ]);

      if (mRes.status === 'fulfilled' && mRes.value) {
        setMachine(mRes.value);
      }
      if (psRes.status === 'fulfilled' && Array.isArray(psRes.value)) {
        setPreStarts(psRes.value);
      } else {
        setPreStarts([]);
      }
      if (jcRes.status === 'fulfilled' && Array.isArray(jcRes.value)) {
        setJobCards(jcRes.value);
      } else {
        setJobCards([]);
      }
      if (reqRes.status === 'fulfilled' && Array.isArray(reqRes.value)) {
        setRequisitions(reqRes.value);
      } else {
        setRequisitions([]);
      }
    } catch (err) {
      console.error('Failed to load machine profile', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [machineId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStatusChange = async (newStatus: string) => {
    if (!machine) return;
    setUpdatingStatus(true);
    try {
      await apiFetch(`/api/v1/fleet/machines/${machine.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      setFeedbackBanner({
        type: newStatus === 'OUT_OF_SERVICE' ? 'critical' : 'success',
        title: 'Status Updated',
        message: `Machine status transitioned to ${newStatus.replace('_', ' ')}.`,
      });
      await loadData();
    } catch (err) {
      setFeedbackBanner({
        type: 'warning',
        title: 'Status Change Failed',
        message: err instanceof Error ? err.message : 'Failed to update machine state.',
      });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return <Badge className="bg-emerald-600 text-white font-mono text-[10px] py-0 px-2">AVAILABLE</Badge>;
      case 'IN_USE':
        return <Badge className="bg-blue-600 text-white font-mono text-[10px] py-0 px-2">IN USE</Badge>;
      case 'UNDER_MAINTENANCE':
        return <Badge className="bg-amber-600 text-white font-mono text-[10px] py-0 px-2">UNDER MAINTENANCE</Badge>;
      case 'OUT_OF_SERVICE':
        return <Badge className="bg-red-600 text-white font-mono text-[10px] py-0 px-2 animate-pulse">OUT OF SERVICE</Badge>;
      default:
        return <Badge variant="outline" className="font-mono text-[10px] py-0 px-2">{status.replace('_', ' ')}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <TelemetrySpinner message="Retrieving vehicle profile, telemetry, and service history..." />
      </div>
    );
  }

  if (!machine) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-3">
        <Button variant="ghost" size="sm" onClick={() => router.push('/fleet')} className="gap-1.5 text-xs">
          <ArrowLeft className="size-3.5" /> Back to Fleet Inventory
        </Button>
        <Card className="p-6 text-center border-dashed">
          <AlertOctagon className="size-10 text-destructive mx-auto mb-2" />
          <h2 className="text-lg font-bold">Vehicle Not Found</h2>
          <p className="text-xs text-muted-foreground mt-1">
            No equipment record matching ID <span className="font-mono">{machineId}</span> was found in the fleet register.
          </p>
          <Button size="sm" className="mt-3 text-xs" onClick={() => router.push('/fleet')}>
            Return to Fleet Inventory
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <Protect capability="fleet:view" isPageGuard moduleName="Vehicle Profile">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-3.5">
        
        {/* ── BREADCRUMB & BACK LINK ─────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-mono text-muted-foreground">
            <Link href="/fleet" className="hover:text-primary flex items-center gap-1 transition-colors">
              <ArrowLeft className="size-3" /> Fleet & Equipment
            </Link>
            <span>/</span>
            <span className="text-foreground font-semibold">{machine.identifier}</span>
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={() => { setRefreshing(true); loadData(); }}
            disabled={refreshing}
            className="flex items-center gap-1 text-xs h-7 px-2.5"
          >
            <RefreshCw className={`size-3 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* ── FEEDBACK BANNER ────────────────────────────────────────── */}
        {feedbackBanner && (
          <div
            className={`p-3 rounded-xl border flex items-start gap-2.5 text-xs transition-all ${
              feedbackBanner.type === 'critical'
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : feedbackBanner.type === 'warning'
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}
          >
            {feedbackBanner.type === 'critical' ? (
              <AlertOctagon className="size-4 shrink-0 mt-0.5 text-red-500" />
            ) : feedbackBanner.type === 'warning' ? (
              <AlertTriangle className="size-4 shrink-0 mt-0.5 text-amber-500" />
            ) : (
              <CheckCircle2 className="size-4 shrink-0 mt-0.5 text-emerald-500" />
            )}
            <div className="flex-1">
              <h4 className="font-bold">{feedbackBanner.title}</h4>
              <p className="text-[11px] text-muted-foreground mt-0.5">{feedbackBanner.message}</p>
            </div>
            <button
              onClick={() => setFeedbackBanner(null)}
              className="text-muted-foreground hover:text-foreground text-xs"
            >
              &times;
            </button>
          </div>
        )}

        {/* ── COMPACT HERO COMMAND HEADER ────────────────────────────── */}
        <div className="p-4 md:p-5 rounded-xl bg-linear-to-br from-card via-card to-muted/30 border border-border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="p-2.5 bg-primary/10 text-primary rounded-xl shrink-0">
                <Truck className="size-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl md:text-2xl font-bold font-mono text-foreground tracking-tight">
                    {machine.identifier}
                  </h1>
                  {getStatusBadge(machine.status)}
                </div>
                <p className="text-xs font-medium text-muted-foreground flex items-center gap-1.5 mt-0.5">
                  <span className="text-foreground/90 font-semibold">{machine.machine_type?.name || 'Heavy Equipment'}</span>
                  <span>•</span>
                  <span className="font-mono text-[11px]">{machine.machine_type?.category || 'Mining Fleet'}</span>
                  {machine.serial_number && (
                    <>
                      <span>•</span>
                      <span className="font-mono text-[11px] text-muted-foreground">SN: {machine.serial_number}</span>
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* ── PRIMARY OPERATIONAL ACTIONS ──────────────────────────── */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <Button
              size="sm"
              onClick={() => setIsPreStartModalOpen(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1 h-8 shadow-xs"
            >
              <CheckCircle2 className="size-3.5" />
              Start Walkaround
            </Button>

            <Link href={`/jobs/new?machine_id=${machine.id}`}>
              <Button size="sm" variant="outline" className="text-xs flex items-center gap-1 h-8 border-border">
                <Wrench className="size-3.5 text-amber-500" />
                Report Defect
              </Button>
            </Link>

            <Link href={`/fleet/requisitions/new?machine_id=${machine.id}`}>
              <Button size="sm" variant="outline" className="text-xs flex items-center gap-1 h-8 border-border">
                <Calendar className="size-3.5 text-primary" />
                Book Machine
              </Button>
            </Link>

            {/* Quick Status Toggle (Gated by fleet:allocate) */}
            <Protect capability="fleet:allocate">
              {machine.status === 'AVAILABLE' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleStatusChange('UNDER_MAINTENANCE')}
                  disabled={updatingStatus}
                  className="h-8 text-xs text-amber-500 border-amber-500/30 hover:bg-amber-500/10"
                >
                  Send to Maintenance
                </Button>
              )}
              {machine.status === 'UNDER_MAINTENANCE' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleStatusChange('AVAILABLE')}
                  disabled={updatingStatus}
                  className="h-8 text-xs text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10"
                >
                  Mark Available
                </Button>
              )}
              {machine.status === 'OUT_OF_SERVICE' && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleStatusChange('UNDER_MAINTENANCE')}
                  disabled={updatingStatus}
                  className="h-8 text-xs"
                >
                  Send to Maintenance
                </Button>
              )}
            </Protect>
          </div>
        </div>

        {/* ── COMPACT KEY TELEMETRY STRIP ────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="p-3 bg-card border border-border space-y-0.5">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Current Meter</span>
              <Gauge className="size-3.5 text-emerald-500" />
            </div>
            <div className="text-xl font-mono font-bold text-foreground">
              {machine.current_hour_meter != null ? machine.current_hour_meter.toLocaleString() : '0.0'}
              <span className="text-xs font-normal text-muted-foreground ml-1">hrs</span>
            </div>
            <div className="text-[10px] text-muted-foreground">Operating runtime</div>
          </Card>

          <Card className="p-3 bg-card border border-border space-y-0.5">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Operational Status</span>
              <Activity className="size-3.5 text-blue-500" />
            </div>
            <div className="text-base font-mono font-bold text-foreground truncate">
              {machine.status.replace('_', ' ')}
            </div>
            <div className="text-[10px] text-muted-foreground">Dispatch availability</div>
          </Card>

          <Card className="p-3 bg-card border border-border space-y-0.5">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Location</span>
              <MapPin className="size-3.5 text-amber-500" />
            </div>
            <div className="text-base font-bold text-foreground truncate" title={machine.location || 'Central Yard'}>
              {machine.location || 'Central Yard'}
            </div>
            <div className="text-[10px] text-muted-foreground font-mono truncate">
              {machine.location_breadcrumb || 'Bikita Mine Site'}
            </div>
          </Card>

          <Card className="p-3 bg-card border border-border space-y-0.5">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Rating & Rate</span>
              <Layers className="size-3.5 text-cyan-500" />
            </div>
            <div className="text-base font-bold text-foreground truncate">
              {machine.capacity_rating || 'Heavy Duty'}
            </div>
            <div className="text-[10px] text-muted-foreground">
              ${machine.machine_type?.hourly_rate || 50}/hr rate
            </div>
          </Card>
        </div>

        {/* ── 4-TAB NAVIGATION BAR ────────────────────────────────────── */}
        <div className="border-b border-border">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
            <button
              onClick={() => setActiveTab('OVERVIEW')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md font-semibold transition-colors ${
                activeTab === 'OVERVIEW'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              }`}
            >
              <Info className="size-3.5" />
              Overview & Specs
            </button>

            <button
              onClick={() => setActiveTab('PRESTARTS')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md font-semibold transition-colors ${
                activeTab === 'PRESTARTS'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              }`}
            >
              <ShieldCheck className="size-3.5 text-emerald-400" />
              Pre-Starts ({preStarts.length})
            </button>

            <button
              onClick={() => setActiveTab('JOBCARDS')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md font-semibold transition-colors ${
                activeTab === 'JOBCARDS'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              }`}
            >
              <Wrench className="size-3.5 text-amber-400" />
              Job Cards ({jobCards.length})
            </button>

            <button
              onClick={() => setActiveTab('REQUISITIONS')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md font-semibold transition-colors ${
                activeTab === 'REQUISITIONS'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              }`}
            >
              <Calendar className="size-3.5 text-blue-400" />
              Bookings ({requisitions.length})
            </button>
          </div>
        </div>

        {/* ── TAB 1: OVERVIEW & SPECIFICATIONS ───────────────────────── */}
        {activeTab === 'OVERVIEW' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            <Card>
              <CardHeader className="border-b border-border/50 py-2.5 px-4">
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Truck className="size-4 text-primary" />
                  Technical Specifications
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/50 text-xs">
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Machine Identifier</span>
                    <span className="font-mono font-bold text-foreground">{machine.identifier}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Model / Type</span>
                    <span className="font-semibold text-foreground">{machine.machine_type?.name || 'Heavy Equipment'}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Equipment Category</span>
                    <span className="text-foreground">{machine.machine_type?.category || 'Mining Plant'}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Serial Number / VIN</span>
                    <span className="font-mono font-medium text-foreground">{machine.serial_number || 'N/A'}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Capacity Rating</span>
                    <span className="font-medium text-foreground">{machine.capacity_rating || 'Standard'}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Hourly Rate</span>
                    <span className="font-mono font-medium text-foreground">${machine.machine_type?.hourly_rate || 50.0}/hr</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Description</span>
                    <span className="text-foreground text-right max-w-xs">{machine.machine_type?.description || 'Heavy earthmoving mobile equipment.'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-border/50 py-2.5 px-4">
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Activity className="size-4 text-emerald-500" />
                  Operating Telemetry & Compliance
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/50 text-xs">
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Current Operating Hours</span>
                    <span className="font-mono font-bold text-emerald-500">
                      {machine.current_hour_meter != null ? machine.current_hour_meter.toLocaleString() : '0.0'} hrs
                    </span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Last Service Date</span>
                    <span className="font-mono text-foreground">
                      {machine.last_maintenance_date ? new Date(machine.last_maintenance_date).toLocaleDateString() : 'No historical service logged'}
                    </span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Yard / Site Location</span>
                    <span className="font-medium text-foreground">{machine.location || 'Central Yard'}</span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Asset Register Link</span>
                    {machine.asset_id ? (
                      <Link href="/assets" className="text-primary hover:underline font-mono flex items-center gap-1">
                        <span>AST-{machine.asset_id.slice(0, 8).toUpperCase()}</span>
                        <ExternalLink className="size-3" />
                      </Link>
                    ) : (
                      <span className="text-muted-foreground font-mono">Unlinked Fixed Asset</span>
                    )}
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Record Created</span>
                    <span className="font-mono text-muted-foreground">
                      {machine.created_at ? new Date(machine.created_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div className="p-2.5 flex justify-between">
                    <span className="text-muted-foreground">Last Status Update</span>
                    <span className="font-mono text-muted-foreground">
                      {machine.updated_at ? new Date(machine.updated_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── TAB 2: PRE-START WALKAROUNDS ───────────────────────────── */}
        {activeTab === 'PRESTARTS' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 py-2.5 px-4">
              <div>
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <ShieldCheck className="size-4 text-emerald-500" />
                  Pre-Start Equipment Inspections
                </CardTitle>
                <p className="text-[11px] text-muted-foreground">
                  Shift walkarounds and safety gating logs for {machine.identifier}.
                </p>
              </div>

              <Button
                size="sm"
                onClick={() => setIsPreStartModalOpen(true)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs flex items-center gap-1 h-7"
              >
                <Plus className="size-3" />
                Start Walkaround
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead className="py-2 text-xs">Inspection #</TableHead>
                    <TableHead className="py-2 text-xs">Date / Time</TableHead>
                    <TableHead className="py-2 text-xs">Hour-Meter</TableHead>
                    <TableHead className="py-2 text-xs">Safety Status</TableHead>
                    <TableHead className="py-2 text-xs">Defect Remarks</TableHead>
                    <TableHead className="py-2 text-xs">Linked Job Card</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {preStarts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground h-16 text-xs">
                        No pre-start inspections logged for this machine yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    preStarts.map((ps) => (
                      <TableRow key={ps.id}>
                        <TableCell className="py-2 font-mono text-xs font-bold text-foreground">
                          {ps.reference_number}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {new Date(ps.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="py-2 font-mono text-xs font-semibold">
                          {ps.hour_meter_reading?.toLocaleString() || 'N/A'} hrs
                        </TableCell>
                        <TableCell className="py-2">
                          {ps.overall_status === 'CRITICAL_RED_TAG' ? (
                            <Badge className="bg-red-600 text-white font-mono text-[9px] py-0 px-1.5">
                              RED-TAG LOCKED
                            </Badge>
                          ) : ps.overall_status === 'DEFECTS_NOTED' ? (
                            <Badge className="bg-amber-500 text-white font-mono text-[9px] py-0 px-1.5">
                              DEFECTS NOTED
                            </Badge>
                          ) : (
                            <Badge className="bg-emerald-600 text-white font-mono text-[9px] py-0 px-1.5">
                              ALL CLEAR
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground max-w-xs truncate" title={ps.operator_notes || 'No remarks'}>
                          {ps.operator_notes || 'Clean walkaround'}
                        </TableCell>
                        <TableCell className="py-2">
                          {ps.spawned_job_card_id ? (
                            <Link
                              href={`/jobs/${ps.spawned_job_card_id}`}
                              className="text-xs font-mono font-bold text-red-400 hover:underline flex items-center gap-1"
                            >
                              <span>{ps.spawned_job_card_number || 'JC-URGENT'}</span>
                              <ExternalLink className="size-3" />
                            </Link>
                          ) : (
                            <span className="text-xs text-muted-foreground font-mono">None</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* ── TAB 3: MAINTENANCE JOB CARDS ───────────────────────────── */}
        {activeTab === 'JOBCARDS' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 py-2.5 px-4">
              <div>
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Wrench className="size-4 text-amber-500" />
                  Maintenance & Service Job Cards
                </CardTitle>
                <p className="text-[11px] text-muted-foreground">
                  Work orders and scheduled services for {machine.identifier}.
                </p>
              </div>

              <Link href={`/jobs/new?machine_id=${machine.id}`}>
                <Button size="sm" variant="default" className="text-xs flex items-center gap-1 h-7">
                  <Plus className="size-3" />
                  New Job Card
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead className="py-2 text-xs">Job Card #</TableHead>
                    <TableHead className="py-2 text-xs">Title / Description</TableHead>
                    <TableHead className="py-2 text-xs">Priority</TableHead>
                    <TableHead className="py-2 text-xs">Status</TableHead>
                    <TableHead className="py-2 text-xs">Est. Hours</TableHead>
                    <TableHead className="py-2 text-xs">Created Date</TableHead>
                    <TableHead className="py-2 text-xs">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobCards.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground h-16 text-xs">
                        No maintenance job cards logged for this machine.
                      </TableCell>
                    </TableRow>
                  ) : (
                    jobCards.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell className="py-2 font-mono text-xs font-bold text-foreground">
                          {job.job_number || `JC-${job.id.slice(0, 6)}`}
                        </TableCell>
                        <TableCell className="py-2">
                          <div className="text-xs font-semibold text-foreground">{job.title}</div>
                          {job.reported_issue && (
                            <div className="text-[11px] text-muted-foreground truncate max-w-xs" title={job.reported_issue}>
                              {job.reported_issue}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="py-2">
                          <Badge variant={job.priority === 3 || job.priority === 'CRITICAL' ? 'destructive' : 'outline'} className="text-[9px] font-mono py-0 px-1.5">
                            {job.priority === 3 ? 'CRITICAL' : job.priority === 2 ? 'HIGH' : 'NORMAL'}
                          </Badge>
                        </TableCell>
                        <TableCell className="py-2">
                          <Badge variant="outline" className="text-[9px] font-mono py-0 px-1.5">
                            {job.status.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="py-2 font-mono text-xs">
                          {job.estimated_hours ? `${job.estimated_hours}h` : '0h'}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'N/A'}
                        </TableCell>
                        <TableCell className="py-2">
                          <Link href={`/jobs/${job.id}`} className="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5">
                            <span>Open</span>
                            <ArrowRight className="size-3" />
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* ── TAB 4: REQUISITIONS & BOOKINGS ─────────────────────────── */}
        {activeTab === 'REQUISITIONS' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 py-2.5 px-4">
              <div>
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Calendar className="size-4 text-blue-500" />
                  Shift Requisitions & Dispatch Bookings
                </CardTitle>
                <p className="text-[11px] text-muted-foreground">
                  Historical and scheduled shift allocations for {machine.identifier}.
                </p>
              </div>

              <Link href={`/fleet/requisitions/new?machine_id=${machine.id}`}>
                <Button size="sm" variant="default" className="text-xs flex items-center gap-1 h-7">
                  <Plus className="size-3" />
                  Book Machine
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead className="py-2 text-xs">Requisition #</TableHead>
                    <TableHead className="py-2 text-xs">Purpose / Scope</TableHead>
                    <TableHead className="py-2 text-xs">Department</TableHead>
                    <TableHead className="py-2 text-xs">Start Time</TableHead>
                    <TableHead className="py-2 text-xs">End Time</TableHead>
                    <TableHead className="py-2 text-xs">Status</TableHead>
                    <TableHead className="py-2 text-xs">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requisitions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground h-16 text-xs">
                        No shift requisitions allocated to this machine.
                      </TableCell>
                    </TableRow>
                  ) : (
                    requisitions.map((req) => (
                      <TableRow key={req.id}>
                        <TableCell className="py-2 font-mono text-xs font-bold text-foreground">
                          {req.requisition_number || `REQ-${req.id.slice(0, 8).toUpperCase()}`}
                        </TableCell>
                        <TableCell className="py-2 text-xs font-semibold text-foreground max-w-xs truncate" title={req.purpose}>
                          {req.purpose}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {req.department?.name || req.department_id || 'Mining Operations'}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {new Date(req.start_time).toLocaleString()}
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          {new Date(req.end_time).toLocaleString()}
                        </TableCell>
                        <TableCell className="py-2">
                          <Badge variant="outline" className="text-[9px] font-mono py-0 px-1.5">
                            {req.status.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="py-2">
                          <Link href={`/fleet/requisitions/${req.id}`} className="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5">
                            <span>Details</span>
                            <ArrowRight className="size-3" />
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* ── PRE-START WALK-AROUND MODAL ────────────────────────────── */}
        {isPreStartModalOpen && (
          <OperatorPreStartModal
            isOpen={isPreStartModalOpen}
            onClose={() => setIsPreStartModalOpen(false)}
            initialMachineId={machine.id}
            onSuccess={(res) => {
              setIsPreStartModalOpen(false);
              setFeedbackBanner({
                type: res.isGrounded ? 'critical' : 'success',
                title: res.isGrounded ? 'Machine Red-Tagged & Grounded' : 'Pre-Start Walkaround Passed',
                message: res.isGrounded
                  ? `Critical defect logged on ${res.machineName}. Machine locked to OUT_OF_SERVICE. Ref: ${res.referenceNumber}`
                  : `Pre-start inspection ${res.referenceNumber} recorded successfully for ${res.machineName}.`,
              });
              loadData();
            }}
          />
        )}

      </div>
    </Protect>
  );
}
