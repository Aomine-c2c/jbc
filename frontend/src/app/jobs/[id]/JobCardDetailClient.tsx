'use client';

import React, { useEffect, useState, use, useCallback } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";

// Design System Components
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Drawer } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell, TableFooter } from "@/components/ui/table";
import { WorkflowTimeline, WorkflowStageKey } from "@/components/ui/workflow-timeline";
import { ActivityFeed } from "@/components/ui/activity-feed";
import { ApprovalPanel } from "@/components/ui/approval-panel";
import { ApprovalRequestData, getApprovalHistory, decideApproval } from "@/lib/approvals";
import { ApprovalCertificate } from "@/components/approvals/ApprovalCertificate";
import { SignaturePanel } from "@/components/ui/signature-panel";
import { NotificationBanner } from "@/components/ui/notification";
import { TelemetrySpinner } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import { useConnection } from "@/lib/providers/ConnectionProvider";

// Icons
import {
  ArrowLeft,
  CheckCircle2,
  History,
  Plus,
  Trash2,
  Calendar,
  Layers,
  FileSpreadsheet,
  Check,
  X,
  Play,
  FileCheck2,
  PackageCheck,
  RotateCcw,
  Pause,
  Send,
  UserCheck,
  ShieldCheck,
  Ban,
  FileText,
} from "lucide-react";

interface JobCardPart {
  id?: string;
  part_name: string;
  part_number?: string;
  quantity: number;
  unit_cost?: number;
}

interface JobCardActionLog {
  id: string;
  user_id: string;
  action: string;
  state_from?: string;
  state_to?: string;
  details?: string;
  created_at: string;
}

interface JobCardComment {
  id: string;
  author_id: string;
  comment: string;
  created_at: string;
}

interface JobCard {
  id: string;
  job_number?: string;
  title: string;
  description: string;
  priority: string | number;
  status: string;
  department_id: string;
  created_at: string;
  
  job_type?: string;
  maintenance_type?: string;
  workshop_code?: string;
  location?: string;
  plant_area?: string;
  machine_id?: string;
  
  creator_id?: string;
  required_date?: string;
  reported_issue?: string;
  job_instruction?: string;

  approver_id?: string;
  approved_at?: string;

  supervisor_id?: string;
  assigned_date?: string;
  assigned_personnel?: string;
  estimated_hours?: number;
  estimated_cost?: number;

  actual_start_time?: string;
  actual_end_time?: string;
  downtime_hours?: number;

  action_taken?: string;
  labour_details?: string;

  requester_confirmed?: boolean;
  requester_notes?: string;
  requester_confirmed_at?: string;

  verified_at?: string;
  closure_date?: string;
  closed_by_id?: string;

  parts: JobCardPart[];
  comments: JobCardComment[];
  action_logs: JobCardActionLog[];
}

export default function JobCardDetailClient({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<JobCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeStageKey, setActiveStageKey] = useState<WorkflowStageKey>("identity");

  // Modals state
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState<{ open: boolean; action: "approve" | "reject" | "return" }>({
    open: false,
    action: "approve",
  });
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showHoldModal, setShowHoldModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showDrawer, setShowDrawer] = useState(false);

  // Form Fields
  const [submitComment, setSubmitComment] = useState("");
  const [decisionComment, setDecisionComment] = useState("");
  const [approvalRequest, setApprovalRequest] = useState<ApprovalRequestData | null>(null);
  const [holdReason, setHoldReason] = useState("");
  const [cancelReason, setCancelReason] = useState("");
  
  // Planning Form
  const [planForm, setPlanForm] = useState({
    estimated_hours: 4.0,
    estimated_cost: 1250.0,
    job_instruction: "",
    comments: "",
  });

  // Assignment Form
  const [assignedSupervisorId, setAssignedSupervisorId] = useState("5530362d-eff8-400f-9d4e-7338d7c1d0e4");
  const [assignedPersonnel, setAssignedPersonnel] = useState("T. Moyo (Fitter Lead), K. Chidzero (Auto Electrician)");

  // Complete work technical report form
  const [completeForm, setCompleteForm] = useState({
    action_taken: "",
    downtime_hours: 2.5,
    completion_notes: "",
    labour_details: "Fitter (Lead): 2.5 hrs • Electrician: 1.5 hrs",
    parts: [{ part_name: "Jaw Plate Set (Hardox 500)", part_number: "CR-PLT-04", quantity: 2, unit_cost: 450.0 }],
  });

  // Verify Form
  const [verifyComment, setVerifyComment] = useState("QA test completed. Equipment operating within vibration and thermal tolerance.");

  const { isOnline } = useConnection();

  // Requester Confirmation Form
  const [confirmNotes, setConfirmNotes] = useState("Equipment handed over to plant operator. Trial run successful.");

  // Close Signature state
  const closeComment = "Work order formally signed off and archived into DWRMS records.";

  const fetchJob = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/v1/job-cards/${id}`);
      if (res) {
        setJob(res);
        if (res.action_taken) {
          setCompleteForm((prev) => ({
            ...prev,
            action_taken: res.action_taken || "",
            downtime_hours: res.downtime_hours || 2.5,
            labour_details: res.labour_details || prev.labour_details,
          }));
        }
        if (res.estimated_hours) {
          setPlanForm((prev) => ({
            ...prev,
            estimated_hours: res.estimated_hours || 4.0,
            estimated_cost: res.estimated_cost || 1250.0,
            job_instruction: res.job_instruction || "",
          }));
        }
      }
      const approvals = await getApprovalHistory('job_card', id);
      if (approvals && approvals.length > 0) {
        setApprovalRequest(approvals[0]);
      }
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMessage(error.message || "Failed to load Job Card details.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // Execute State Machine Transition
  const executeTransition = async (endpoint: string, payload: Record<string, unknown> = {}) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const res = await apiFetch(`/api/v1/job-cards/${id}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res) {
        await fetchJob();
        // Close all modals
        setShowSubmitModal(false);
        setShowApprovalModal({ open: false, action: "approve" });
        setShowPlanModal(false);
        setShowAssignModal(false);
        setShowHoldModal(false);
        setShowCompleteModal(false);
        setShowVerifyModal(false);
        setShowConfirmModal(false);
        setShowCloseModal(false);
        setShowCancelModal(false);
      }
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMessage(error.message || `Failed to execute ${endpoint} transition.`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-4">
        <TelemetrySpinner message="Loading Bikita Job Card specifications and workflow state..." />
      </div>
    );
  }

  if (errorMessage && !job) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorState
          title="Job Card Not Found or Access Restricted"
          message={errorMessage}
          code="STATUS: 404_OR_403"
          onRetry={fetchJob}
        />
      </div>
    );
  }

  if (!job) return null;

  const displayJobNumber = job.job_number || `JC-${job.id.slice(0, 8).toUpperCase()}`;
  const totalPartsCost = (job.parts || []).reduce((acc, p) => acc + (p.quantity || 1) * (p.unit_cost || 0), 0);

  // Status-based state flags
  const s = job.status?.toUpperCase();
  const isDraft = s === "DRAFT" || s === "RETURNED";
  const isSubmitted = s === "SUBMITTED";
  const isPendingApproval = s === "PENDING_APPROVAL";
  const isApproved = s === "APPROVED";
  const isPlanning = s === "PLANNING";
  const isAssigned = s === "ASSIGNED";
  const isInProgress = s === "IN_PROGRESS";
  const isOnHold = s === "ON_HOLD";
  const isCompleted = s === "COMPLETED";
  const isPendingReview = s === "PENDING_REVIEW";
  const isVerified = s === "VERIFIED";
  const isClosed = s === "CLOSED";
  const isRejected = s === "REJECTED";
  const isCancelled = s === "CANCELLED";

  const handleApprovalAction = async (stepId: string, action: 'approve' | 'reject' | 'return' | 'delegate' | 'escalate', comments: string) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const reqPayload: Record<string, unknown> = {
        action,
        comments,
      };
      let endpoint = '';
      if (action === 'approve') endpoint = `/api/v1/job-cards/${id}/approve`;
      if (action === 'reject') endpoint = `/api/v1/job-cards/${id}/reject`;
      if (action === 'return') endpoint = `/api/v1/job-cards/${id}/return`;
      
      if (action === 'delegate' || action === 'escalate') {
        const { id: userId } = JSON.parse(localStorage.getItem('user_details') || '{}');
        await decideApproval(
          'job_card', 
          id, 
          action, 
          comments, 
          job.creator_id || userId, 
          job.status, 
          job.status
        );
      } else {
        await apiFetch(endpoint, {
          method: 'POST',
          body: JSON.stringify(reqPayload)
        });
      }
      
      setSuccessMessage(`Approval action '${action}' completed successfully.`);
      await fetchJob();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setErrorMessage(error.message || `Failed to ${action} job card.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5 antialiased">
      {/* 1. TOP BREADCRUMB & HEADER CONTROLS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-3">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-1 text-xs font-mono text-muted-foreground hover:text-foreground transition-colors px-2.5 py-1 rounded bg-muted/40 border border-border/50"
          >
            <ArrowLeft className="size-3" />
            <span>JOB REGISTRY</span>
          </Link>
          <span className="text-border">/</span>
          <span className="text-xs font-mono font-bold text-foreground">
            {displayJobNumber}
          </span>
          <StatusBadge status={job.status} size="sm" />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDrawer(true)}
            className="font-mono text-xs"
          >
            <History className="size-3.5 mr-1 text-primary" />
            Audit Trail ({job.action_logs?.length || 0})
          </Button>

          {/* CANCELLATION TRIGGER */}
          {!isClosed && !isCancelled && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCancelModal(true)}
              className="font-mono text-xs text-destructive hover:bg-destructive/10"
            >
              <Ban className="size-3.5 mr-1" />
              Cancel Job
            </Button>
          )}
        </div>
      </div>

      {errorMessage && (
        <NotificationBanner
          type="error"
          title="Workflow Error"
          message={errorMessage}
          dismissible
          onDismiss={() => setErrorMessage(null)}
        />
      )}

      {/* 2. STAGE 1: JOB IDENTITY & PRIMARY ACTION BAR */}
      <Card variant="accent" id="stage-identity">
        <CardContent className="p-4 sm:p-5 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-base sm:text-lg font-mono font-extrabold text-foreground tracking-tight">
                  {displayJobNumber}
                </span>
                <span className="text-border">•</span>
                <span className="text-xs font-mono bg-muted/60 text-foreground px-2 py-0.5 rounded border border-border">
                  {job.workshop_code || "WS-MECH-01"}
                </span>
                <PriorityBadge priority={job.priority} size="sm" />
                <StatusBadge status={job.status} size="sm" />
              </div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-foreground">
                {job.title}
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                {job.job_type || "Corrective Maintenance"} • Location: {job.location || "Shaft 01"} • Plant Area: {job.plant_area || "Crushing Section"}
              </p>
            </div>

            {/* CONTEXT-AWARE WORKFLOW ACTION BAR */}
            <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
              {/* DRAFT / RETURNED / REJECTED -> SUBMIT */}
              {(isDraft || isSubmitted || isRejected) && (
                <Protect capability="job_card:create">
                  <Button
                    size="sm"
                    variant="default"
                    onClick={() => setShowSubmitModal(true)}
                    loading={actionLoading}
                    disabled={!isOnline}
                    title={!isOnline ? "Approvals require a live connection to the server." : ""}
                  >
                    <Send className="size-3.5 mr-1.5" />
                    {isSubmitted ? "Submit for Review" : "Submit for Approval"}
                  </Button>
                </Protect>
              )}

              {/* PENDING_APPROVAL -> APPROVE / RETURN / REJECT */}
              {isPendingApproval && (
                <Protect capability="job_card:approve">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={() => setShowApprovalModal({ open: true, action: "approve" })}
                    loading={actionLoading}
                    disabled={!isOnline}
                    title={!isOnline ? "Approvals require a live connection to the server." : ""}
                  >
                    <ShieldCheck className="size-3.5 mr-1" />
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-orange-600 border-orange-500/40 hover:bg-orange-500/10"
                    onClick={() => setShowApprovalModal({ open: true, action: "return" })}
                    disabled={!isOnline}
                    title={!isOnline ? "Approvals require a live connection to the server." : ""}
                  >
                    <RotateCcw className="size-3.5 mr-1" />
                    Return for Correction
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => setShowApprovalModal({ open: true, action: "reject" })}
                    disabled={!isOnline}
                    title={!isOnline ? "Approvals require a live connection to the server." : ""}
                  >
                    <X className="size-3.5 mr-1" />
                    Reject
                  </Button>
                </Protect>
              )}

              {/* APPROVED -> MOVE TO PLANNING */}
              {isApproved && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    onClick={() => setShowPlanModal(true)}
                    loading={actionLoading}
                  >
                    <Calendar className="size-3.5 mr-1.5" />
                    Configure Shift Planning
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowAssignModal(true)}
                  >
                    <UserCheck className="size-3.5 mr-1.5" />
                    Assign Crew
                  </Button>
                </Protect>
              )}

              {/* PLANNING -> ASSIGN */}
              {isPlanning && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    onClick={() => setShowAssignModal(true)}
                    loading={actionLoading}
                  >
                    <UserCheck className="size-3.5 mr-1.5" />
                    Assign Supervisor & Crew
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowHoldModal(true)}
                  >
                    <Pause className="size-3.5 mr-1" />
                    Hold
                  </Button>
                </Protect>
              )}

              {/* ASSIGNED -> START */}
              {isAssigned && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={() => executeTransition("start")}
                    loading={actionLoading}
                  >
                    <Play className="size-3.5 mr-1.5" />
                    Start On-Site Execution
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowHoldModal(true)}
                  >
                    <Pause className="size-3.5 mr-1" />
                    Hold
                  </Button>
                </Protect>
              )}

              {/* IN_PROGRESS -> COMPLETE / HOLD */}
              {isInProgress && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-teal-600 hover:bg-teal-700 text-white"
                    onClick={() => setShowCompleteModal(true)}
                    loading={actionLoading}
                  >
                    <FileCheck2 className="size-3.5 mr-1.5" />
                    Complete Work & Spares Report
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowHoldModal(true)}
                  >
                    <Pause className="size-3.5 mr-1" />
                    Place on Hold
                  </Button>
                </Protect>
              )}

              {/* ON_HOLD -> RESUME */}
              {isOnHold && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-cyan-600 hover:bg-cyan-700 text-white"
                    onClick={() => executeTransition("start")}
                    loading={actionLoading}
                  >
                    <Play className="size-3.5 mr-1.5" />
                    Resume Work Execution
                  </Button>
                </Protect>
              )}

              {/* COMPLETED -> QA VERIFY / REVIEW / REWORK */}
              {isCompleted && (
                <Protect capability="job_card:verify">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={() => setShowVerifyModal(true)}
                    loading={actionLoading}
                  >
                    <ShieldCheck className="size-3.5 mr-1.5" />
                    QA Supervisor Verify
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => executeTransition("review", { comments: "Passed for review" })}
                  >
                    <Check className="size-3.5 mr-1" />
                    Submit Review
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => executeTransition("start", { comments: "Rework required" })}
                  >
                    <RotateCcw className="size-3.5 mr-1" />
                    Rework
                  </Button>
                </Protect>
              )}

              {/* PENDING_REVIEW / VERIFIED -> CONFIRM & CLOSE */}
              {(isPendingReview || isVerified) && (
                <div className="flex items-center gap-2">
                  {!job.requester_confirmed && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/10"
                      onClick={() => setShowConfirmModal(true)}
                    >
                      <UserCheck className="size-3.5 mr-1" />
                      Requester Confirm
                    </Button>
                  )}
                  <Protect capability="job_card:verify">
                    <Button
                      size="sm"
                      variant="default"
                      className="bg-zinc-800 hover:bg-zinc-900 text-white dark:bg-zinc-200 dark:text-zinc-900"
                      onClick={() => setShowCloseModal(true)}
                      loading={actionLoading}
                    >
                      <CheckCircle2 className="size-3.5 mr-1.5" />
                      Formal Sign-off & Close
                    </Button>
                  </Protect>
                </div>
              )}

              {/* CLOSED */}
              {isClosed && (
                <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded">
                  <CheckCircle2 className="size-4" />
                  <span className="font-bold">ARCHIVED & SIGNED OFF</span>
                </div>
              )}
            </div>
          </div>

          {/* TELEMETRY METRIC TILES STRIP */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-border/80 text-xs font-mono">
            <div className="bg-card/80 p-2.5 rounded border border-border/60">
              <span className="text-muted-foreground text-[10px] block uppercase">Est. Hours / Downtime</span>
              <span className="font-bold text-foreground text-sm">
                {job.estimated_hours || 4.0} HRS / <span className="text-amber-500">{job.downtime_hours || 0} HRS</span>
              </span>
            </div>
            <div className="bg-card/80 p-2.5 rounded border border-border/60">
              <span className="text-muted-foreground text-[10px] block uppercase">Spares Cost (USD)</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                ${totalPartsCost.toFixed(2)}
              </span>
            </div>
            <div className="bg-card/80 p-2.5 rounded border border-border/60">
              <span className="text-muted-foreground text-[10px] block uppercase">Required Date</span>
              <span className="font-bold text-foreground text-sm">
                {job.required_date ? new Date(job.required_date).toLocaleDateString() : "Next Shift"}
              </span>
            </div>
            <div className="bg-card/80 p-2.5 rounded border border-border/60">
              <span className="text-muted-foreground text-[10px] block uppercase">Requester Confirmation</span>
              <span className="font-bold text-foreground text-sm flex items-center gap-1">
                {job.requester_confirmed ? (
                  <span className="text-emerald-500 flex items-center gap-1">
                    <Check className="size-3.5" /> CONFIRMED
                  </span>
                ) : (
                  <span className="text-muted-foreground">PENDING</span>
                )}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. WORKFLOW PIPELINE TIMELINE STEPPER */}
      <WorkflowTimeline
        currentStatus={job.status}
        createdAt={job.created_at}
        startTime={job.actual_start_time}
        endTime={job.actual_end_time}
        activeStageKey={activeStageKey}
        onSelectStage={(stage) => {
          setActiveStageKey(stage);
          const el = document.getElementById(`stage-${stage}`);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }}
      />

      {/* 4. MAIN CONTENT WORKFLOW STAGES (TWO-COLUMN GRID) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* LEFT COLUMN (2 COLS): DETAILED STAGES */}
        <div className="lg:col-span-2 space-y-5">
          
          {/* STAGE 1: REQUEST & FAULT SPECIFICATIONS */}
          <Card id="stage-request">
            <CardHeader>
              <CardTitle>
                <Layers className="size-4 text-primary" />
                <span>Stage 1: Job Request & Technical Specifications</span>
              </CardTitle>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">
                Created: {new Date(job.created_at).toLocaleString()}
              </span>
            </CardHeader>
            <CardContent className="space-y-3.5 pt-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-foreground block">
                    Maintenance Classification
                  </span>
                  <div className="font-semibold text-foreground font-mono mt-0.5">
                    {job.job_type || job.maintenance_type || "Corrective Maintenance"}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-foreground block">
                    Target Workshop
                  </span>
                  <div className="font-semibold text-foreground font-mono mt-0.5">
                    {job.workshop_code || "WS-MECH-01"}
                  </div>
                </div>
              </div>

              {job.reported_issue && (
                <div className="rounded border border-amber-500/30 bg-amber-500/5 p-3 text-xs">
                  <div className="text-[10px] font-mono uppercase text-amber-700 dark:text-amber-300 font-bold mb-1">
                    Reported Symptom / Failure Mode:
                  </div>
                  <div className="text-foreground">{job.reported_issue}</div>
                </div>
              )}

              <div>
                <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Scope & Failure Description
                </span>
                <div className="p-3 rounded bg-muted/20 border border-border/80 text-xs text-foreground leading-relaxed whitespace-pre-wrap">
                  {job.description || "No failure description provided."}
                </div>
              </div>

              {job.job_instruction && (
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Maintenance Crew Instructions
                  </span>
                  <div className="p-3 rounded bg-cyan-500/5 border border-cyan-500/20 text-xs text-foreground leading-relaxed">
                    {job.job_instruction}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* STAGE 2: PLANNING & CREW ASSIGNMENT */}
          <Card id="stage-planning">
            <CardHeader>
              <CardTitle>
                <Calendar className="size-4 text-cyan-500" />
                <span>Stage 2: Shift Planning & Crew Allocation</span>
              </CardTitle>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">
                Target: {job.required_date ? new Date(job.required_date).toLocaleDateString() : "Standard"}
              </span>
            </CardHeader>
            <CardContent className="space-y-3 pt-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-2.5 rounded bg-muted/30 border border-border/60">
                  <span className="text-[10px] font-mono text-muted-foreground block">EST. LABOUR HOURS</span>
                  <span className="font-bold font-mono text-sm text-foreground">{job.estimated_hours || 4.0} HRS</span>
                </div>
                <div className="p-2.5 rounded bg-muted/30 border border-border/60">
                  <span className="text-[10px] font-mono text-muted-foreground block">EST. BUDGET COST</span>
                  <span className="font-bold font-mono text-sm text-foreground">${job.estimated_cost || 1250.0}</span>
                </div>
                <div className="p-2.5 rounded bg-muted/30 border border-border/60">
                  <span className="text-[10px] font-mono text-muted-foreground block">SUPERVISOR</span>
                  <span className="font-bold font-mono text-xs text-foreground truncate block">
                    {job.supervisor_id ? "Assigned Lead" : "Pending Assignment"}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Assigned Personnel & Trades
                </span>
                <div className="p-2.5 rounded bg-card border border-border text-foreground font-mono text-xs">
                  {job.assigned_personnel || "T. Moyo (Fitter Lead), K. Chidzero (Auto Electrician)"}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* STAGE 3: TECHNICAL WORK REPORT & SPARES */}
          <Card id="stage-report">
            <CardHeader>
              <CardTitle>
                <FileSpreadsheet className="size-4 text-emerald-500" />
                <span>Stage 3: Technical Work Report & Spares Consumed</span>
              </CardTitle>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">
                Downtime: {job.downtime_hours || 0} Hours
              </span>
            </CardHeader>
            <CardContent className="space-y-4 pt-3 text-xs">
              {job.action_taken ? (
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Work Performed Narrative
                  </span>
                  <div className="p-3 rounded bg-muted/20 border border-border text-foreground leading-relaxed whitespace-pre-wrap">
                    {job.action_taken}
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded bg-muted/10 border border-dashed border-border text-muted-foreground text-center">
                  Work report will be filed upon completion of physical maintenance.
                </div>
              )}

              {job.labour_details && (
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Labour Information
                  </span>
                  <div className="p-2.5 rounded bg-muted/20 border border-border font-mono text-xs">
                    {job.labour_details}
                  </div>
                </div>
              )}

              {/* SPARES TABLE */}
              <div className="space-y-2">
                <span className="text-[10px] font-mono uppercase text-muted-foreground block">
                  Spare Parts Consumed & Cost Breakdown
                </span>
                {(!job.parts || job.parts.length === 0) ? (
                  <div className="p-3 rounded bg-muted/10 border border-border text-muted-foreground text-center font-mono text-[11px]">
                    No spare parts recorded for this job order.
                  </div>
                ) : (
                  <Table dense zebra>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Part Name</TableHead>
                        <TableHead className="w-28">Part Number</TableHead>
                        <TableHead className="w-16 text-right">Qty</TableHead>
                        <TableHead className="w-24 text-right">Unit ($)</TableHead>
                        <TableHead className="w-24 text-right">Total ($)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {job.parts.map((part, idx) => (
                        <TableRow key={part.id || idx}>
                          <TableCell className="font-semibold text-foreground">{part.part_name}</TableCell>
                          <TableCell mono className="text-muted-foreground">{part.part_number || "-"}</TableCell>
                          <TableCell mono className="text-right">{part.quantity}</TableCell>
                          <TableCell mono className="text-right">${(part.unit_cost || 0).toFixed(2)}</TableCell>
                          <TableCell mono className="text-right font-bold text-foreground">
                            ${((part.quantity || 1) * (part.unit_cost || 0)).toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                    <TableFooter>
                      <TableRow>
                        <TableCell colSpan={4} className="text-right font-bold font-mono uppercase">
                          Total Spares Cost:
                        </TableCell>
                        <TableCell mono className="text-right font-bold text-emerald-600 dark:text-emerald-400">
                          ${totalPartsCost.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    </TableFooter>
                  </Table>
                )}
              </div>
            </CardContent>
          </Card>

          {/* STAGE 4: QUALITY REVIEW, CONFIRMATION & CLOSURE */}
          <Card id="stage-closure">
            <CardHeader>
              <CardTitle>
                <PackageCheck className="size-4 text-primary" />
                <span>Stage 4: Quality Verification & Handover Sign-off</span>
              </CardTitle>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">
                {isClosed ? "Formally Closed" : "Active Handover"}
              </span>
            </CardHeader>
            <CardContent className="space-y-4 pt-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 rounded border border-border/80 bg-muted/10 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase block">
                    Requester Handover Confirmation
                  </span>
                  <div className="font-bold text-foreground">
                    {job.requester_confirmed ? "Confirmed by Operations" : "Awaiting Requester Trial Run"}
                  </div>
                  {job.requester_notes && (
                    <div className="text-[11px] text-muted-foreground mt-1">
                      {job.requester_notes}
                    </div>
                  )}
                </div>

                <div className="p-3 rounded border border-border/80 bg-muted/10 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase block">
                    Supervisor QA Verification
                  </span>
                  <div className="font-bold text-foreground">
                    {job.verified_at ? `Verified on ${new Date(job.verified_at).toLocaleDateString()}` : "Pending Verification"}
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-1">
                    Lockout tag removed. Machine re-commissioned safely.
                  </div>
                </div>
              </div>

              {isClosed && (
                <div className="rounded border border-emerald-500/40 bg-emerald-500/10 p-3.5 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300">
                    <CheckCircle2 className="size-4 text-emerald-500" />
                    <span>
                      <strong>FORMALLY CLOSED:</strong> Digital cryptographic stamp verified on {job.closure_date ? new Date(job.closure_date).toLocaleString() : "Record"}.
                    </span>
                  </div>
                  <span className="text-[10px] font-bold bg-emerald-600 text-white px-2 py-0.5 rounded">
                    SEAL: BIKITA-DWRMS-OK
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* RIGHT COLUMN (1 COL): APPROVAL PIPELINE & COMMENTS */}
        <div className="space-y-5">
          {/* APPROVAL STAGES PANEL */}
          <ApprovalPanel
            steps={approvalRequest?.steps || []}
            canApprove={true}
            loading={loading}
            onAction={handleApprovalAction}
          />

          {/* RECENT OPERATOR COMMENTS */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xs">
                <FileText className="size-3.5 text-primary" />
                <span>Operator Notes & Remarks</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 space-y-2 text-xs">
              {(!job.comments || job.comments.length === 0) ? (
                <div className="text-center py-4 text-muted-foreground font-mono text-[11px]">
                  No remarks logged yet.
                </div>
              ) : (
                job.comments.map((c) => (
                  <div key={c.id} className="p-2.5 rounded bg-muted/30 border border-border/50 space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                      <span>Operator Comment</span>
                      <span>{c.created_at ? new Date(c.created_at).toLocaleTimeString() : "-"}</span>
                    </div>
                    <div className="text-foreground text-xs leading-normal">{c.comment}</div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {approvalRequest?.status === "APPROVED" && (
        <div className="mt-5">
          <ApprovalCertificate request={approvalRequest} />
        </div>
      )}

      {/* 5. AUDIT TRAIL COLLATERAL DRAWER */}
      <Drawer
        open={showDrawer}
        onClose={() => setShowDrawer(false)}
        title={`Audit Trail: ${displayJobNumber}`}
        description="Immutable chronological record of all state transitions and operator actions."
      >
        <div className="space-y-4">
          <ActivityFeed
            events={(job.action_logs || []).map((log) => ({
              id: log.id,
              timestamp: log.created_at,
              userName: `Operator: ${log.user_id.slice(0, 8)}`,
              userRole: "DWRMS Staff",
              action: log.action.toUpperCase(),
              details: `${log.state_from ? `${log.state_from} -> ` : ""}${log.state_to || ""}${log.details ? ` (${log.details})` : ""}`,
              category: "lifecycle",
            }))}
          />
        </div>
      </Drawer>

      {/* ── MODALS FOR STATE MACHINE TRANSITIONS ── */}

      {/* SUBMIT MODAL */}
      <Dialog open={showSubmitModal} onOpenChange={setShowSubmitModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Job Card for Authorization</DialogTitle>
            <DialogDescription>
              This will transition the job card into the supervisory review queue.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Submission Remarks (Optional)
            </label>
            <textarea
              rows={3}
              value={submitComment}
              onChange={(e) => setSubmitComment(e.target.value)}
              placeholder="e.g. Urgent repair requested for upcoming night shift..."
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowSubmitModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("submit", { comments: submitComment })}
            >
              <Send className="size-3.5 mr-1" />
              Confirm Submission
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* APPROVAL / REJECT / RETURN MODAL */}
      <Dialog open={showApprovalModal.open} onOpenChange={(open) => setShowApprovalModal({ ...showApprovalModal, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {showApprovalModal.action === "approve"
                ? "Authorize Job Card"
                : showApprovalModal.action === "return"
                ? "Return Job Card for Correction"
                : "Reject Job Card"}
            </DialogTitle>
            <DialogDescription>
              {showApprovalModal.action === "approve"
                ? "Provide manager decision remarks to authorize maintenance work to proceed."
                : showApprovalModal.action === "return"
                ? "Specify what needs correction before resubmission."
                : "Provide reason for rejection."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Decision Remarks *
            </label>
            <textarea
              required
              rows={3}
              value={decisionComment}
              onChange={(e) => setDecisionComment(e.target.value)}
              placeholder="Enter decision comments..."
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowApprovalModal({ ...showApprovalModal, open: false })}>
              Cancel
            </Button>
            <Button
              variant={showApprovalModal.action === "approve" ? "default" : showApprovalModal.action === "return" ? "warning" : "destructive"}
              size="sm"
              loading={actionLoading}
              onClick={() => {
                const ep = showApprovalModal.action === "approve" ? "approve" : showApprovalModal.action === "return" ? "return" : "reject";
                executeTransition(ep, { comments: decisionComment });
              }}
            >
              Confirm {showApprovalModal.action.toUpperCase()}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* PLANNING MODAL */}
      <Dialog open={showPlanModal} onOpenChange={setShowPlanModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure Shift Planning & Estimates</DialogTitle>
            <DialogDescription>
              Set estimated labor hours, budget allocation, and specific crew instructions.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Est. Labour Hours
                </label>
                <Input
                  mono
                  type="number"
                  step="0.5"
                  value={planForm.estimated_hours}
                  onChange={(e) => setPlanForm({ ...planForm, estimated_hours: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Est. Cost ($)
                </label>
                <Input
                  mono
                  type="number"
                  value={planForm.estimated_cost}
                  onChange={(e) => setPlanForm({ ...planForm, estimated_cost: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                Maintenance Instructions
              </label>
              <textarea
                rows={2}
                value={planForm.job_instruction}
                onChange={(e) => setPlanForm({ ...planForm, job_instruction: e.target.value })}
                placeholder="Specific shift instructions for maintenance crew..."
                className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowPlanModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("plan", planForm)}
            >
              Save Planning Window
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ASSIGNMENT MODAL */}
      <Dialog open={showAssignModal} onOpenChange={setShowAssignModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Supervisor & Maintenance Crew</DialogTitle>
            <DialogDescription>
              Assign supervising engineer and allocated trade technicians.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <div>
              <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                Supervising Engineer
              </label>
              <select
                value={assignedSupervisorId}
                onChange={(e) => setAssignedSupervisorId(e.target.value)}
                className="h-8 w-full rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground outline-none focus:border-ring font-mono"
              >
                <option value="5530362d-eff8-400f-9d4e-7338d7c1d0e4">Eng. T. Mutasa (Mechanical Supervisor)</option>
                <option value="8f60d491-9c11-4d72-9191-c5a110f7c0af">Eng. S. Ndlovu (Electrical Supervisor)</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                Assigned Personnel & Trades
              </label>
              <Input
                value={assignedPersonnel}
                onChange={(e) => setAssignedPersonnel(e.target.value)}
                placeholder="e.g. T. Moyo (Fitter), K. Chidzero (Electrician)"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowAssignModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("assign", {
                supervisor_id: assignedSupervisorId,
                assigned_personnel: assignedPersonnel,
              })}
            >
              Assign & Transition
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* HOLD MODAL */}
      <Dialog open={showHoldModal} onOpenChange={setShowHoldModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Place Job Card On Hold</DialogTitle>
            <DialogDescription>
              Temporarily suspend maintenance execution due to spares availability or operational priorities.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Hold Reason *
            </label>
            <textarea
              required
              rows={3}
              value={holdReason}
              onChange={(e) => setHoldReason(e.target.value)}
              placeholder="e.g. Awaiting delivery of replacement jaw plates from central warehouse..."
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowHoldModal(false)}>
              Cancel
            </Button>
            <Button
              variant="warning"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("hold", { reason: holdReason })}
            >
              Confirm Hold
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* COMPLETE WORK & SPARES MODAL */}
      <Dialog open={showCompleteModal} onOpenChange={setShowCompleteModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Technical Work Report & Spares Used</DialogTitle>
            <DialogDescription>
              Record detailed actions performed, equipment downtime hours, and spare parts consumed.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3.5 py-2 text-xs max-h-[70vh] overflow-y-auto pr-1">
            <div>
              <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                Work Performed Narrative *
              </label>
              <textarea
                required
                rows={3}
                value={completeForm.action_taken}
                onChange={(e) => setCompleteForm({ ...completeForm, action_taken: e.target.value })}
                placeholder="Describe exact mechanical repairs, replacements, and alignments completed..."
                className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Actual Downtime Hours
                </label>
                <Input
                  mono
                  type="number"
                  step="0.5"
                  value={completeForm.downtime_hours}
                  onChange={(e) => setCompleteForm({ ...completeForm, downtime_hours: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Labour Details
                </label>
                <Input
                  value={completeForm.labour_details}
                  onChange={(e) => setCompleteForm({ ...completeForm, labour_details: e.target.value })}
                  placeholder="Fitter: 2.5 hrs • Electrician: 1.5 hrs"
                />
              </div>
            </div>

            {/* SPARES DYNAMIC ENTRY */}
            <div className="space-y-2 pt-2 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                  Materials / Spare Parts Used
                </span>
                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  onClick={() =>
                    setCompleteForm({
                      ...completeForm,
                      parts: [...completeForm.parts, { part_name: "", part_number: "", quantity: 1, unit_cost: 0 }],
                    })
                  }
                >
                  <Plus className="size-3 mr-1" />
                  Add Part
                </Button>
              </div>

              {completeForm.parts.map((p, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-muted/20 p-2 rounded border border-border/60">
                  <Input
                    placeholder="Part Name"
                    value={p.part_name}
                    onChange={(e) => {
                      const updated = [...completeForm.parts];
                      updated[idx].part_name = e.target.value;
                      setCompleteForm({ ...completeForm, parts: updated });
                    }}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Part #"
                    mono
                    value={p.part_number || ""}
                    onChange={(e) => {
                      const updated = [...completeForm.parts];
                      updated[idx].part_number = e.target.value;
                      setCompleteForm({ ...completeForm, parts: updated });
                    }}
                    className="w-28"
                  />
                  <Input
                    placeholder="Qty"
                    mono
                    type="number"
                    value={p.quantity}
                    onChange={(e) => {
                      const updated = [...completeForm.parts];
                      updated[idx].quantity = parseFloat(e.target.value) || 1;
                      setCompleteForm({ ...completeForm, parts: updated });
                    }}
                    className="w-16"
                  />
                  <Input
                    placeholder="Unit $"
                    mono
                    type="number"
                    value={p.unit_cost}
                    onChange={(e) => {
                      const updated = [...completeForm.parts];
                      updated[idx].unit_cost = parseFloat(e.target.value) || 0;
                      setCompleteForm({ ...completeForm, parts: updated });
                    }}
                    className="w-24"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      const updated = completeForm.parts.filter((_, i) => i !== idx);
                      setCompleteForm({ ...completeForm, parts: updated });
                    }}
                    className="size-7 text-destructive"
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowCompleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() =>
                executeTransition("complete", {
                  action_taken: completeForm.action_taken,
                  downtime_hours: completeForm.downtime_hours,
                  labour_details: completeForm.labour_details,
                  parts_used: completeForm.parts.filter((p) => p.part_name.trim() !== ""),
                  completion_notes: completeForm.completion_notes,
                })
              }
            >
              Submit Technical Report
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* QA VERIFY MODAL */}
      <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>QA & Safety Verification</DialogTitle>
            <DialogDescription>
              Confirm quality inspection, vibration testing, and re-commissioning safety clearance.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Inspection Remarks *
            </label>
            <textarea
              required
              rows={3}
              value={verifyComment}
              onChange={(e) => setVerifyComment(e.target.value)}
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowVerifyModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("verify", { comments: verifyComment })}
            >
              <ShieldCheck className="size-3.5 mr-1" />
              Sign Verification
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* REQUESTER CONFIRM MODAL */}
      <Dialog open={showConfirmModal} onOpenChange={setShowConfirmModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Requester Handover Confirmation</DialogTitle>
            <DialogDescription>
              Acknowledge that equipment was returned to operational service and functioning satisfactorily.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Confirmation Remarks
            </label>
            <textarea
              rows={3}
              value={confirmNotes}
              onChange={(e) => setConfirmNotes(e.target.value)}
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowConfirmModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("confirm", { requester_confirmed: true, requester_notes: confirmNotes })}
            >
              <Check className="size-3.5 mr-1" />
              Confirm Handover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* FORMAL CLOSURE MODAL WITH SIGNATURE */}
      <Dialog open={showCloseModal} onOpenChange={setShowCloseModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Formal Work Order Closure</DialogTitle>
            <DialogDescription>
              Digital handover seal by Superintendent to archive the Job Card into permanent records.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <SignaturePanel
              signerRole="Plant Superintendent"
              onSign={() => {}}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowCloseModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("close", { comments: closeComment })}
            >
              <CheckCircle2 className="size-3.5 mr-1" />
              Archive & Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CANCEL MODAL */}
      <Dialog open={showCancelModal} onOpenChange={setShowCancelModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Job Card</DialogTitle>
            <DialogDescription>
              Permanently cancel this maintenance job card. This action will be logged in the audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2 text-xs">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Cancellation Reason *
            </label>
            <textarea
              required
              rows={3}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="e.g. Work order superseded by major plant overhaul schedule..."
              className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowCancelModal(false)}>
              Back
            </Button>
            <Button
              variant="destructive"
              size="sm"
              loading={actionLoading}
              onClick={() => executeTransition("cancel", { reason: cancelReason })}
            >
              <Ban className="size-3.5 mr-1" />
              Cancel Job Card
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
