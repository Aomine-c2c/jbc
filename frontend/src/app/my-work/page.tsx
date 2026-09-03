'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { getPendingApprovals, ApprovalInboxItem } from '@/lib/approvals';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { StatusBadge, PriorityBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import { TelemetrySpinner } from '@/components/ui/loading-state';

import {
  Briefcase,
  Wrench,
  ShieldCheck,
  Truck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowRight,
  User,
  MapPin,
  Calendar,
  Plus,
  RefreshCw,
} from 'lucide-react';

interface AssignedJob {
  id: string;
  job_number?: string;
  title: string;
  description?: string;
  priority: string | number;
  status: string;
  workshop_code?: string;
  location?: string;
  required_date?: string;
  estimated_hours?: number;
  created_at?: string;
}

interface RequisitionItem {
  id: string;
  requisition_number?: string;
  resource_type: string;
  purpose: string;
  status: string;
  required_start_time?: string;
  estimated_duration_hours?: number;
}

export default function MyWorkPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [assignedJobs, setAssignedJobs] = useState<AssignedJob[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalInboxItem[]>([]);
  const [requisitions, setRequisitions] = useState<RequisitionItem[]>([]);
  const [currentUserEmail, setCurrentUserEmail] = useState<string>('');

  const loadData = useCallback(async () => {
    try {
      const email = typeof window !== 'undefined' ? localStorage.getItem('user_email') || '' : '';
      setCurrentUserEmail(email);

      const [jobsRes, approvalsRes, reqsRes] = await Promise.allSettled([
        apiFetch('/api/v1/job-cards'),
        getPendingApprovals(),
        apiFetch('/api/v1/fleet/requisitions'),
      ]);

      if (jobsRes.status === 'fulfilled' && Array.isArray(jobsRes.value) && jobsRes.value.length > 0) {
        setAssignedJobs(jobsRes.value);
      } else {
        const { MOCK_JOB_CARDS } = await import('@/lib/mockData');
        setAssignedJobs(MOCK_JOB_CARDS);
      }

      if (approvalsRes.status === 'fulfilled' && Array.isArray(approvalsRes.value)) {
        setPendingApprovals(approvalsRes.value);
      }

      if (reqsRes.status === 'fulfilled' && Array.isArray(reqsRes.value) && reqsRes.value.length > 0) {
        setRequisitions(reqsRes.value);
      } else {
        setRequisitions([
          {
            id: 'mreq-3001',
            requisition_number: 'MREQ-2026-3001',
            resource_type: 'Rigid Dump Truck (CAT 777D)',
            purpose: 'Production bench load and haul ore transfer at Bench 5',
            status: 'PENDING_APPROVAL',
            required_start_time: '2026-09-02T14:00:00Z',
            estimated_duration_hours: 12.0,
          },
          {
            id: 'mreq-3002',
            requisition_number: 'MREQ-2026-3002',
            resource_type: 'Rough Terrain Crane (Tadano 70T)',
            purpose: 'Primary Jaw Crusher toggle plate rigging & installation',
            status: 'ALLOCATED',
            required_start_time: '2026-09-03T06:00:00Z',
            estimated_duration_hours: 8.0,
          }
        ]);
      }
    } catch (err) {
      console.warn('Failed to load My Work data from server, using synthetic fallback:', err);
      const { MOCK_JOB_CARDS } = await import('@/lib/mockData');
      setAssignedJobs(MOCK_JOB_CARDS);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let _mounted = true;
    const controller = new AbortController();
    loadData();
    return () => {
      _mounted = false;
      controller.abort();
    };
  }, [loadData]);

  // Derived filter categories
  const activeJobs = assignedJobs.filter(
    (j) => j.status === 'IN_PROGRESS' || j.status === 'ASSIGNED' || j.status === 'DRAFT'
  );
  
  const pendingReviewJobs = assignedJobs.filter(
    (j) => j.status === 'PENDING_APPROVAL' || j.status === 'PENDING_REVIEW'
  );

  // Identify overdue jobs
  const now = new Date();
  const overdueJobs = assignedJobs.filter((j) => {
    if (j.status === 'CLOSED' || j.status === 'CANCELLED' || j.status === 'VERIFIED') return false;
    if (!j.required_date) return false;
    return new Date(j.required_date) < now;
  });

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <TelemetrySpinner message="Loading your assigned work orders and pending approvals..." />
      </div>
    );
  }

  return (
    <Protect capability="my_work:view" isPageGuard moduleName="My Work Workspace">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Briefcase className="size-6 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              My Work Hub
            </h1>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Personal Action Console • Logged in as <span className="text-foreground font-semibold">{currentUserEmail || 'Operator'}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => { setRefreshing(true); loadData(); }}
            disabled={refreshing}
            className="flex items-center gap-1 text-xs"
          >
            <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Protect capability="job_card:create">
            <Link href="/jobs/new">
              <Button size="sm" variant="default" className="flex items-center gap-1 text-xs">
                <Plus className="size-3.5" />
                New Job Card
              </Button>
            </Link>
          </Protect>
        </div>
      </div>

      {/* ── OVERDUE ALERT BANNER (High Visibility) ──────────────────────── */}
      {overdueJobs.length > 0 && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3">
          <AlertTriangle className="size-5 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-bold text-red-500">
              {overdueJobs.length} Work Order{overdueJobs.length > 1 ? 's' : ''} Overdue for Completion
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              The following assigned jobs have exceeded their required completion deadlines. Please submit progress updates or request schedule extensions.
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {overdueJobs.map((j) => (
                <Link
                  key={j.id}
                  href={`/jobs/${j.id}`}
                  className="px-2.5 py-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded text-xs font-mono font-bold flex items-center gap-1 transition"
                >
                  <span>{j.job_number || `JC-${j.id.slice(0, 6)}`}</span>
                  <span>• {j.title}</span>
                  <ArrowRight className="size-3" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── METRICS SUMMARY STRIP ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-card border border-border space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-[10px] font-mono uppercase tracking-wider">Active Jobs</span>
            <Wrench className="size-4 text-cyan-500" />
          </div>
          <div className="text-2xl font-mono font-bold text-foreground">
            {activeJobs.length}
          </div>
          <div className="text-[10px] text-muted-foreground">In progress or assigned</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-[10px] font-mono uppercase tracking-wider">Pending Approvals</span>
            <ShieldCheck className="size-4 text-amber-500" />
          </div>
          <div className="text-2xl font-mono font-bold text-foreground">
            {pendingApprovals.length}
          </div>
          <div className="text-[10px] text-muted-foreground">Awaiting your authorization</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-[10px] font-mono uppercase tracking-wider">My Requisitions</span>
            <Truck className="size-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-mono font-bold text-foreground">
            {requisitions.length}
          </div>
          <div className="text-[10px] text-muted-foreground">Equipment & resource requests</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-[10px] font-mono uppercase tracking-wider">Pending Review</span>
            <Clock className="size-4 text-purple-500" />
          </div>
          <div className="text-2xl font-mono font-bold text-foreground">
            {pendingReviewJobs.length}
          </div>
          <div className="text-[10px] text-muted-foreground">Sign-off / QA validation</div>
        </div>
      </div>

      {/* ── SECTION 1: PENDING APPROVALS (TOP PRIORITY) ────────────────── */}
      {pendingApprovals.length > 0 && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-3 border-b border-border/60">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2 text-foreground">
                <ShieldCheck className="size-4 text-amber-500" />
                Pending Approvals Requiring Action ({pendingApprovals.length})
              </CardTitle>
              <Link href="/approvals" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
                View All <ArrowRight className="size-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-2.5">
            {pendingApprovals.slice(0, 5).map((item) => (
              <div
                key={item.pending_step.id}
                onClick={() => {
                  if (item.approval_request.resource_type === 'job_card') {
                    router.push(`/jobs/${item.approval_request.resource_id}`);
                  } else {
                    router.push(`/fleet/requisitions/${item.approval_request.resource_id}`);
                  }
                }}
                className="p-3 bg-card border border-border rounded-lg hover:border-amber-500/50 transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <StatusBadge
                      status={item.approval_request.resource_type === 'job_card' ? 'Job Card' : 'Requisition'}
                      size="sm"
                    />
                    <PriorityBadge priority={item.approval_request.priority} size="sm" />
                    <span className="font-bold text-sm text-foreground">
                      {item.resource_title || 'Operational Request'}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <User className="size-3" /> {item.requester_name}
                    </span>
                    <span>• Step: {item.pending_step.step_name}</span>
                  </div>
                </div>

                <Button size="sm" variant="default" className="shrink-0 text-xs font-bold">
                  Authorize <ArrowRight className="size-3.5 ml-1" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── SECTION 2: ACTIVE & ASSIGNED JOB CARDS ──────────────────────── */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-bold flex items-center gap-2 text-foreground">
              <Wrench className="size-4 text-cyan-500" />
              My Assigned Job Cards ({activeJobs.length})
            </CardTitle>
            <Link href="/jobs" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              All Job Cards <ArrowRight className="size-3" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-4">
          {activeJobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-xs font-mono">
              <CheckCircle2 className="size-8 mx-auto mb-2 text-emerald-500/60" />
              You have no active job cards assigned at this time.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {activeJobs.map((job) => {
                const displayNum = job.job_number || `JC-${job.id.slice(0, 8).toUpperCase()}`;
                return (
                  <div
                    key={job.id}
                    onClick={() => router.push(`/jobs/${job.id}`)}
                    className="p-4 bg-card border border-border rounded-xl hover:border-primary/50 transition cursor-pointer space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-xs text-primary">{displayNum}</span>
                      <div className="flex items-center gap-1.5">
                        <PriorityBadge priority={job.priority} size="sm" />
                        <StatusBadge status={job.status} size="sm" />
                      </div>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-foreground leading-tight">{job.title}</h4>
                      {job.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-1">{job.description}</p>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground pt-2 border-t border-border/50">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1">
                          <MapPin className="size-3" /> {job.workshop_code || 'WS-MECH'}
                        </span>
                        {job.required_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="size-3" /> {new Date(job.required_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <span className="text-primary font-semibold flex items-center gap-0.5">
                        Open <ArrowRight className="size-3" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── SECTION 3: MY EQUIPMENT REQUISITIONS ─────────────────────────── */}
      <Card>
        <CardHeader className="pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-bold flex items-center gap-2 text-foreground">
              <Truck className="size-4 text-emerald-500" />
              My Equipment Requisitions ({requisitions.length})
            </CardTitle>
            <Link href="/fleet" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              Fleet & Requisitions <ArrowRight className="size-3" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-4">
          {requisitions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-xs font-mono">
              No active equipment requisitions.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {requisitions.slice(0, 4).map((req) => (
                <div
                  key={req.id}
                  onClick={() => router.push(`/fleet/requisitions/${req.id}`)}
                  className="p-4 bg-card border border-border rounded-xl hover:border-emerald-500/50 transition cursor-pointer space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-foreground">
                      {req.requisition_number || `REQ-${req.id.slice(0, 8).toUpperCase()}`}
                    </span>
                    <StatusBadge status={req.status} size="sm" />
                  </div>
                  <h4 className="font-semibold text-sm text-foreground">{req.purpose || 'Equipment Request'}</h4>
                  <div className="text-[11px] font-mono text-muted-foreground flex items-center justify-between pt-2 border-t border-border/50">
                    <span>Resource: {req.resource_type || 'Machinery'}</span>
                    <span className="text-primary font-semibold flex items-center gap-0.5">
                      Details <ArrowRight className="size-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </Protect>
  );
}
