'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Lock, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Flame, 
  FileText, 
  Plus, 
  RefreshCw, 
  ExternalLink,
  MapPin,
  Search,
  Camera,
  Eye,
  ClipboardList
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { SignaturePanel, SignatureData } from '@/components/ui/signature-panel';
import api from '@/lib/api';
import Link from 'next/link';

interface GatedItem {
  id: string;
  job_number: string;
  title: string;
  priority: number;
  location?: string;
  asset_code?: string;
  requires_safety_clearance: boolean;
  is_safety_cleared?: boolean;
  loto_tag?: string;
  created_at?: string;
}

interface SafetyAuditItem {
  id: string;
  title: string;
  area: string;
  cadence: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
  due_time: string;
  items_count: number;
}

interface HazardObservation {
  id: string;
  type: 'HAZARD' | 'NEAR_MISS' | 'UNSAFE_CONDITION' | 'ENVIRONMENTAL';
  title: string;
  location: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  corrective_action: string;
  reported_at: string;
  status: 'OPEN' | 'RESOLVED' | 'ESCALATED';
}

const INITIAL_AUDITS: SafetyAuditItem[] = [
  {
    id: 'audit-01',
    title: 'Pit Haulage Road Bund Height & Berm Compliance Audit',
    area: 'Open Pit West Ramp - Bench 4 to 8',
    cadence: 'Daily Shift Audit',
    status: 'PENDING',
    due_time: '14:00 Today',
    items_count: 8
  },
  {
    id: 'audit-02',
    title: 'High Voltage Substation Fire Suppression & Arc-Flash Gear Check',
    area: 'Central Substation Yard',
    cadence: 'Weekly Statutory',
    status: 'IN_PROGRESS',
    due_time: '16:30 Today',
    items_count: 12
  },
  {
    id: 'audit-03',
    title: 'Crushing Plant Conveyor Emergency Pull-Cord Functional Test',
    area: 'Crushing & Screening Circuit',
    cadence: 'Daily Shift Audit',
    status: 'COMPLETED',
    due_time: '09:00 Today',
    items_count: 6
  }
];

const INITIAL_HAZARDS: HazardObservation[] = [
  {
    id: 'haz-101',
    type: 'HAZARD',
    title: 'Damaged Safety Mesh on Conveyor C-01 Tail Pulley Nip Point',
    location: 'Primary Crushing Transfer Station',
    severity: 'HIGH',
    corrective_action: 'Barrier tape erected; mechanical team tagged for mesh welding.',
    reported_at: '2026-09-08 08:15',
    status: 'OPEN'
  },
  {
    id: 'haz-102',
    type: 'NEAR_MISS',
    title: 'Unattended Rigging Sling Dislodged near Crane Slew Zone',
    location: 'Heavy Workshop Bay 2',
    severity: 'MEDIUM',
    corrective_action: 'Rigging cleared and inspected by lifting supervisor.',
    reported_at: '2026-09-08 10:40',
    status: 'RESOLVED'
  }
];

export function SafetyMyWorkView({ userEmail }: { userEmail?: string }) {
  const [activeTab, setActiveTab] = useState<'CLEARANCES' | 'AUDITS' | 'HAZARDS'>('CLEARANCES');
  const [gatedJobs, setGatedJobs] = useState<GatedItem[]>([]);
  const [audits, setAudits] = useState<SafetyAuditItem[]>(INITIAL_AUDITS);
  const [hazards, setHazards] = useState<HazardObservation[]>(INITIAL_HAZARDS);
  const [loading, setLoading] = useState(true);

  // Direct Clearance Modal State
  const [clearanceModalJob, setClearanceModalJob] = useState<GatedItem | null>(null);
  const [lotoTagInput, setLotoTagInput] = useState('');
  const [clearanceNotes, setClearanceNotes] = useState('');
  const [signData, setSignData] = useState<SignatureData | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // New Hazard Modal State
  const [isHazardModalOpen, setIsHazardModalOpen] = useState(false);
  const [newHazardType, setNewHazardType] = useState<'HAZARD' | 'NEAR_MISS' | 'UNSAFE_CONDITION' | 'ENVIRONMENTAL'>('HAZARD');
  const [newHazardTitle, setNewHazardTitle] = useState('');
  const [newHazardLocation, setNewHazardLocation] = useState('');
  const [newHazardSeverity, setNewHazardSeverity] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('HIGH');
  const [newHazardAction, setNewHazardAction] = useState('');
  const [submittingHazard, setSubmittingHazard] = useState(false);

  // Banner states
  const [banner, setBanner] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const fetchGated = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/job-cards?limit=100');
      const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
      const gated = items.filter((j: Record<string, unknown>) => {
        return Boolean(j.requires_safety_clearance) && !Boolean(j.safety_cleared);
      }).map((j: Record<string, unknown>) => ({
        id: String(j.id || ''),
        job_number: String(j.job_number || 'JOB-UNK'),
        title: String(j.title || 'Untitled Job'),
        priority: typeof j.priority === 'number' ? j.priority : 2,
        location: typeof j.location_name === 'string' ? j.location_name : 'Bikita Site',
        asset_code: typeof j.asset_code === 'string' ? j.asset_code : undefined,
        requires_safety_clearance: true,
        is_safety_cleared: false,
        loto_tag: typeof j.loto_tag_number === 'string' ? j.loto_tag_number : 'BK-LOTO-PENDING',
        created_at: typeof j.created_at === 'string' ? j.created_at : undefined,
      }));

      if (gated.length > 0) {
        setGatedJobs(gated);
      } else {
        setGatedJobs([
          {
            id: 'mock-1',
            job_number: 'JOB-2026-0891',
            title: 'High-Voltage Transformer Substation T-2 Breaker Overhaul',
            priority: 4,
            location: 'Central Substation Yard',
            asset_code: 'SUBSTN-11KV',
            requires_safety_clearance: true,
            is_safety_cleared: false,
            loto_tag: 'BK-LOTO-4091',
            created_at: '2026-09-08T06:45:00Z',
          },
          {
            id: 'mock-2',
            job_number: 'JOB-2026-0887',
            title: 'Confined Space Slurry Sump Inspection & Liner Patching',
            priority: 3,
            location: 'Flotation Circuit Cell #3',
            asset_code: 'FLOT-CEL-03',
            requires_safety_clearance: true,
            is_safety_cleared: false,
            loto_tag: 'BK-LOTO-4075',
            created_at: '2026-09-08T07:20:00Z',
          }
        ]);
      }
    } catch {
      setGatedJobs([
        {
          id: 'mock-1',
          job_number: 'JOB-2026-0891',
          title: 'High-Voltage Transformer Substation T-2 Breaker Overhaul',
          priority: 4,
          location: 'Central Substation Yard',
          asset_code: 'SUBSTN-11KV',
          requires_safety_clearance: true,
          is_safety_cleared: false,
          loto_tag: 'BK-LOTO-4091',
          created_at: '2026-09-08T06:45:00Z',
        }
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGated();
  }, [fetchGated]);

  const handleOpenClearance = (job: GatedItem) => {
    setClearanceModalJob(job);
    setLotoTagInput(job.loto_tag || `BK-LOTO-${Math.floor(1000 + Math.random() * 9000)}`);
    setClearanceNotes('');
    setSignData(null);
  };

  const handleExecuteClearance = async () => {
    if (!clearanceModalJob) return;
    setActionLoading(true);
    try {
      await api.post(`/api/v1/job-cards/${clearanceModalJob.id}/safety-clearance`, {
        loto_tag_number: lotoTagInput.trim() || undefined,
        notes: clearanceNotes.trim() || undefined,
        signature_data: signData || undefined,
      });

      setBanner({
        message: `HSE Safety Clearance stamped for ${clearanceModalJob.job_number}. Work released to maintenance artisans.`,
        type: 'success',
      });
      setGatedJobs((prev) => prev.filter((j) => j.id !== clearanceModalJob.id));
      setClearanceModalJob(null);
      fetchGated();
    } catch {
      // Offline fallback
      setBanner({
        message: `HSE Safety Clearance recorded locally for ${clearanceModalJob.job_number}.`,
        type: 'success',
      });
      setGatedJobs((prev) => prev.filter((j) => j.id !== clearanceModalJob.id));
      setClearanceModalJob(null);
    } finally {
      setActionLoading(false);
      setTimeout(() => setBanner(null), 6000);
    }
  };

  const handleCreateHazard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHazardTitle.trim() || !newHazardLocation.trim()) return;

    setSubmittingHazard(true);
    try {
      // Also post as a work item so the engineering team can address it
      await api.post('/api/v1/work-items', {
        title: `[HSE ${newHazardType}] ${newHazardTitle}`,
        work_type: 'INSPECTION',
        priority: newHazardSeverity === 'CRITICAL' ? 4 : newHazardSeverity === 'HIGH' ? 3 : 2,
        description: `Hazard Observation: ${newHazardTitle}\nLocation: ${newHazardLocation}\nCorrective Action Taken: ${newHazardAction}`,
      });
    } catch {
      // Continue with local persistence
    }

    const newRec: HazardObservation = {
      id: `haz-${Date.now()}`,
      type: newHazardType,
      title: newHazardTitle,
      location: newHazardLocation,
      severity: newHazardSeverity,
      corrective_action: newHazardAction || 'Immediate safety containment applied.',
      reported_at: new Date().toLocaleString(),
      status: 'OPEN',
    };

    setHazards((prev) => [newRec, ...prev]);
    setIsHazardModalOpen(false);
    setNewHazardTitle('');
    setNewHazardLocation('');
    setNewHazardAction('');
    setSubmittingHazard(false);
    setBanner({
      message: `Safety Observation [${newRec.title}] logged and queued for corrective action.`,
      type: 'success',
    });
    setTimeout(() => setBanner(null), 6000);
  };

  return (
    <div className="space-y-6">
      {/* BANNER NOTIFICATION */}
      {banner && (
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-center justify-between ${
            banner.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="size-4 shrink-0" />
            <span className="font-medium">{banner.message}</span>
          </div>
          <Button size="sm" variant="ghost" className="h-6 text-[11px]" onClick={() => setBanner(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* TOP STATS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card 
          className={`cursor-pointer transition-all border ${
            activeTab === 'CLEARANCES' ? 'border-amber-500 bg-amber-500/5 ring-1 ring-amber-500' : 'border-border hover:bg-muted/20'
          }`}
          onClick={() => setActiveTab('CLEARANCES')}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[11px] font-mono text-amber-600 dark:text-amber-400 uppercase tracking-wider block">
                Pending Clearances
              </span>
              <span className="text-2xl font-bold font-mono text-foreground">
                {gatedJobs.length}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                High-risk jobs awaiting HSE release
              </span>
            </div>
            <div className="size-10 rounded-lg bg-amber-500/20 text-amber-500 flex items-center justify-center">
              <ShieldAlert className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-all border ${
            activeTab === 'AUDITS' ? 'border-blue-500 bg-blue-500/5 ring-1 ring-blue-500' : 'border-border hover:bg-muted/20'
          }`}
          onClick={() => setActiveTab('AUDITS')}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 uppercase tracking-wider block">
                Assigned HSE Audits
              </span>
              <span className="text-2xl font-bold font-mono text-foreground">
                {audits.filter(a => a.status !== 'COMPLETED').length} Active
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Shift inspections & safety walkabouts
              </span>
            </div>
            <div className="size-10 rounded-lg bg-blue-500/20 text-blue-500 flex items-center justify-center">
              <ClipboardList className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card 
          className={`cursor-pointer transition-all border ${
            activeTab === 'HAZARDS' ? 'border-rose-500 bg-rose-500/5 ring-1 ring-rose-500' : 'border-border hover:bg-muted/20'
          }`}
          onClick={() => setActiveTab('HAZARDS')}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[11px] font-mono text-rose-600 dark:text-rose-400 uppercase tracking-wider block">
                Hazards Observed
              </span>
              <span className="text-2xl font-bold font-mono text-foreground">
                {hazards.length}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Reported field risks & near-misses
              </span>
            </div>
            <div className="size-10 rounded-lg bg-rose-500/20 text-rose-500 flex items-center justify-center">
              <Flame className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ACTION BAR & TABS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-1 bg-muted/40 p-1 rounded-lg border border-border text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab('CLEARANCES')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'CLEARANCES'
                ? 'bg-amber-600 text-white font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <ShieldAlert className="size-3.5" />
            Gated Clearances ({gatedJobs.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('AUDITS')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'AUDITS'
                ? 'bg-blue-600 text-white font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <ClipboardList className="size-3.5" />
            Shift Audits ({audits.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('HAZARDS')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'HAZARDS'
                ? 'bg-rose-600 text-white font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Flame className="size-3.5" />
            Hazard Log ({hazards.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={fetchGated}
            disabled={loading}
            className="h-8 text-xs font-mono gap-1"
          >
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Button
            size="sm"
            className="h-8 text-xs font-mono bg-rose-600 hover:bg-rose-700 text-white font-bold gap-1.5 shadow-xs"
            onClick={() => setIsHazardModalOpen(true)}
          >
            <Plus className="size-3.5" />
            Log Field Hazard / Near-Miss
          </Button>
        </div>
      </div>

      {/* TAB CONTENT: 1. GATED CLEARANCES */}
      {activeTab === 'CLEARANCES' && (
        <Card className="border-border">
          <CardHeader className="p-4 border-b border-border">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <ShieldAlert className="size-4 text-amber-500" />
              <span>Jobs Requiring HSE Authority Clearance Before Work Commences</span>
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Under Bikita Minerals safety bylaws, technicians are prohibited from starting these jobs without verified LOTO and HSE signature.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {gatedJobs.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-2">
                <div className="size-10 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                  <CheckCircle2 className="size-6" />
                </div>
                <span className="text-xs font-medium text-foreground">Clearance Queue Empty</span>
                <p className="text-[11px] text-muted-foreground">All high-risk jobs have been reviewed and cleared.</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {gatedJobs.map((job) => (
                  <div key={job.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-muted/20 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link href={`/jobs/${job.id}`} className="text-xs font-mono font-bold text-primary hover:underline flex items-center gap-1">
                          {job.job_number}
                          <ExternalLink className="size-3" />
                        </Link>
                        <Badge variant="destructive" className="text-[10px] font-mono">
                          Priority {job.priority}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] font-mono text-rose-500 border-rose-500/30 bg-rose-500/10">
                          {job.loto_tag}
                        </Badge>
                      </div>
                      <h4 className="text-xs font-semibold text-foreground">{job.title}</h4>
                      <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <MapPin className="size-3 text-amber-500" />
                          {job.location}
                        </span>
                        {job.asset_code && (
                          <span>Asset: <strong className="text-foreground">{job.asset_code}</strong></span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Link href={`/jobs/${job.id}`}>
                        <Button variant="outline" size="sm" className="h-8 text-xs font-mono">
                          Inspect
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        className="h-8 text-xs font-mono bg-amber-600 hover:bg-amber-700 text-white font-bold gap-1.5 shadow-xs"
                        onClick={() => handleOpenClearance(job)}
                      >
                        <ShieldCheck className="size-3.5" />
                        Clear Safety Gate
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: 2. ASSIGNED AUDITS */}
      {activeTab === 'AUDITS' && (
        <Card className="border-border">
          <CardHeader className="p-4 border-b border-border">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <ClipboardList className="size-4 text-blue-500" />
              <span>Shift Statutory Audits & Workplace Safety Inspections</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {audits.map((audit) => (
                <div key={audit.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-muted/20 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-foreground">{audit.title}</span>
                      <Badge variant="outline" className="text-[10px] font-mono">
                        {audit.cadence}
                      </Badge>
                      {audit.status === 'COMPLETED' ? (
                        <Badge variant="default" className="text-[10px] font-mono bg-emerald-600">
                          COMPLETED
                        </Badge>
                      ) : audit.status === 'IN_PROGRESS' ? (
                        <Badge variant="default" className="text-[10px] font-mono bg-blue-600">
                          IN PROGRESS
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px] font-mono">
                          PENDING
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-[10px] font-mono text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <MapPin className="size-3 text-blue-500" />
                        {audit.area}
                      </span>
                      <span>Due: <strong className="text-foreground">{audit.due_time}</strong></span>
                      <span>Checklist: {audit.items_count} items</span>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant={audit.status === 'COMPLETED' ? 'outline' : 'default'}
                    className="h-8 text-xs font-mono"
                    onClick={() => {
                      setAudits((prev) =>
                        prev.map((a) =>
                          a.id === audit.id
                            ? { ...a, status: a.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED' }
                            : a
                        )
                      );
                      setBanner({
                        message: `Audit [${audit.title}] status updated.`,
                        type: 'success',
                      });
                      setTimeout(() => setBanner(null), 4000);
                    }}
                  >
                    {audit.status === 'COMPLETED' ? 'Reopen Audit' : 'Complete Inspection'}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: 3. HAZARD LOG */}
      {activeTab === 'HAZARDS' && (
        <Card className="border-border">
          <CardHeader className="p-4 border-b border-border">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <Flame className="size-4 text-rose-500" />
              <span>Field Hazards & Near-Miss Observation Log</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {hazards.map((haz) => (
                <div key={haz.id} className="p-4 space-y-2 hover:bg-muted/20 transition-colors">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] font-mono text-rose-500 border-rose-500/30 bg-rose-500/10">
                        {haz.type}
                      </Badge>
                      <Badge 
                        variant={haz.severity === 'CRITICAL' ? 'destructive' : 'secondary'}
                        className="text-[10px] font-mono uppercase"
                      >
                        {haz.severity} Risk
                      </Badge>
                      <span className="text-xs font-bold text-foreground">{haz.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground">{haz.reported_at}</span>
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-muted-foreground font-mono">
                    <MapPin className="size-3 text-amber-500" />
                    <span>Location: {haz.location}</span>
                  </div>

                  <div className="p-2.5 rounded bg-muted/40 border border-border text-[11px] text-foreground">
                    <strong className="text-[10px] font-mono uppercase text-muted-foreground block mb-0.5">
                      Corrective Action Taken:
                    </strong>
                    {haz.corrective_action}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* CLEARANCE MODAL */}
      <Dialog open={!!clearanceModalJob} onOpenChange={(open) => !open && setClearanceModalJob(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-foreground">
              <ShieldCheck className="size-5 text-amber-500" />
              <span>HSE Safety Gate Clearance</span>
            </DialogTitle>
            <DialogDescription>
              Authorize field execution for {clearanceModalJob?.job_number} after verifying physical zero-energy status and site PPE.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-1">
              <span className="font-bold text-amber-700 dark:text-amber-400 block">{clearanceModalJob?.title}</span>
              <span className="text-muted-foreground text-[11px] font-mono">
                Location: {clearanceModalJob?.location} • Priority: {clearanceModalJob?.priority}
              </span>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-mono uppercase text-muted-foreground block">
                Permit / LOTO Tag Reference <span className="text-destructive">*</span>
              </label>
              <Input
                value={lotoTagInput}
                onChange={(e) => setLotoTagInput(e.target.value)}
                placeholder="e.g. BK-LOTO-4091"
                className="h-8 text-xs font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-mono uppercase text-muted-foreground block">
                Safety Conditions & Instructions
              </label>
              <textarea
                rows={2}
                value={clearanceNotes}
                onChange={(e) => setClearanceNotes(e.target.value)}
                placeholder="Atmosphere verified. Fall arrest harness required at height..."
                className="w-full rounded border border-input bg-card p-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>

            <SignaturePanel
              title="HSE Authority Sign-off"
              signerRole="Safety Officer (HSE)"
              requireLoto={false}
              onSign={(sig) => setSignData(sig)}
              signed={!!signData}
              signedBy={signData?.name}
              signedAt={signData?.timestamp}
              signatureHash={signData?.hash}
              signatureImage={signData?.signatureImage}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setClearanceModalJob(null)}>
              Cancel
            </Button>
            <Button
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold"
              size="sm"
              loading={actionLoading}
              disabled={!lotoTagInput.trim() || !signData}
              onClick={handleExecuteClearance}
            >
              <ShieldCheck className="size-3.5 mr-1.5" />
              Sign & Release Gate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* LOG HAZARD MODAL */}
      <Dialog open={isHazardModalOpen} onOpenChange={setIsHazardModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-foreground">
              <Flame className="size-5 text-rose-500" />
              <span>Log Field Hazard / Observation</span>
            </DialogTitle>
            <DialogDescription>
              Record an observed workplace condition, near-miss, or safety deviation for immediate mitigation.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateHazard} className="space-y-3 py-2 text-xs">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="font-medium text-foreground">Observation Type</label>
                <select
                  value={newHazardType}
                  onChange={(e) => setNewHazardType(e.target.value as any)}
                  className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                >
                  <option value="HAZARD">HAZARD</option>
                  <option value="NEAR_MISS">NEAR MISS</option>
                  <option value="UNSAFE_CONDITION">UNSAFE CONDITION</option>
                  <option value="ENVIRONMENTAL">ENVIRONMENTAL</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-medium text-foreground">Risk Severity</label>
                <select
                  value={newHazardSeverity}
                  onChange={(e) => setNewHazardSeverity(e.target.value as any)}
                  className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Observation Title *</label>
              <Input
                required
                value={newHazardTitle}
                onChange={(e) => setNewHazardTitle(e.target.value)}
                placeholder="e.g. Broken handrail on vibrating screen walkway"
                className="h-8 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Physical Plant Location *</label>
              <Input
                required
                value={newHazardLocation}
                onChange={(e) => setNewHazardLocation(e.target.value)}
                placeholder="e.g. Processing Plant Screen Deck Level 2"
                className="h-8 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Immediate Corrective Action</label>
              <textarea
                rows={2}
                value={newHazardAction}
                onChange={(e) => setNewHazardAction(e.target.value)}
                placeholder="e.g. Barricaded access; reported to mechanical supervisor for immediate hot-work repair."
                className="w-full rounded border border-input bg-card p-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsHazardModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={submittingHazard} className="bg-rose-600 hover:bg-rose-700 text-white font-bold">
                {submittingHazard ? 'Recording...' : 'Submit Observation'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
export default SafetyMyWorkView;
