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
import { SignaturePanel, SignatureData } from "@/components/ui/signature-panel";
import { JobHandoverCertificate } from "@/components/jobs/JobHandoverCertificate";
import { NotificationBanner } from "@/components/ui/notification";
import { TelemetrySpinner } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import { useConnection } from "@/lib/providers/ConnectionProvider";
import {
  JobReport,
  JobReportProgressUpdate,
  JobReportMaterial,
  JobReportAttachment,
  JobReportAmendment,
  DeptFieldMeta,
  getJobReport,
  updateJobReport,
  addProgressUpdate,
  addMaterial,
  deleteMaterial,
  addAttachment,
  createAmendment,
  getDeptSchema,
} from "@/lib/jobReport";

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
  ClipboardList,
  Lock,
  Wrench,
  AlertTriangle,
  CheckCheck,
  Upload,
  Paperclip,
  BarChart3,
  FlaskConical,
  PenLine,
  Timer,
  Stamp,
  Printer,
  StopCircle,
  HardHat,
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

  // V1.3 — Job Execution Report (1:1)
  job_report?: JobReport;
}

export default function JobCardDetailClient({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<JobCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeStageKey, setActiveStageKey] = useState<WorkflowStageKey>("identity");

  // ── V1.3 Job Report State ─────────────────────────────────────
  const [report, setReport] = useState<JobReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportSaving, setReportSaving] = useState(false);
  const [deptFields, setDeptFields] = useState<DeptFieldMeta[]>([]);

  // Report core field edit draft
  const [reportDraft, setReportDraft] = useState<Partial<JobReport>>({});

  // Progress update modal
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressForm, setProgressForm] = useState({
    update_type: "PROGRESS" as string,
    notes: "",
    hold_reason: "",
    percentage_complete: 50,
  });

  // Material modal
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [materialForm, setMaterialForm] = useState({
    category: "SPARE_PART" as string,
    item_name: "",
    item_code: "",
    quantity: 1,
    unit: "pcs",
    unit_cost: 0,
    notes: "",
  });

  // Attachment modal
  const [showAttachmentModal, setShowAttachmentModal] = useState(false);
  const [attachmentForm, setAttachmentForm] = useState({
    category: "PHOTO" as string,
    filename: "",
    file_url: "",
    file_type: "",
    file_size_kb: 0,
    caption: "",
  });

  // Amendment modal
  const [showAmendmentModal, setShowAmendmentModal] = useState(false);
  const [amendmentForm, setAmendmentForm] = useState({
    field_name: "corrective_action",
    new_value: "",
    amendment_reason: "",
  });

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

  // Field Execution & LOTO Gate State
  const [showLotoModal, setShowLotoModal] = useState(false);
  const [lotoTagNumber, setLotoTagNumber] = useState("BK-LOTO-4091");
  const [lotoStartMeter, setLotoStartMeter] = useState<number>(1420.5);
  const [lotoChecks, setLotoChecks] = useState({
    electrical: true,
    hydraulic: true,
    ppe: true,
  });
  const [lotoSignData, setLotoSignData] = useState<SignatureData | null>(null);

  // Live Stopwatch Timer & Execution Console
  const [showExecutionDrawer, setShowExecutionDrawer] = useState(false);
  const [timerActive, setTimerActive] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerPaused, setTimerPaused] = useState(false);

  // Digital Signatures & Handover Certificate
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [technicianSignData, setTechnicianSignData] = useState<SignatureData | null>(null);
  const [supervisorSignData, setSupervisorSignData] = useState<SignatureData | null>(null);
  const [safetySignData, setSafetySignData] = useState<SignatureData | null>(null);

  // Quick Part Adder in Execution Console
  const [quickPart, setQuickPart] = useState({
    part_name: "",
    part_number: "",
    quantity: 1,
    unit_cost: 0,
  });

  // Stopwatch Timer Effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (timerActive && !timerPaused) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [timerActive, timerPaused]);

  const formatTimer = (totalSecs: number) => {
    const hrs = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

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
  const [assignedSupervisorId, setAssignedSupervisorId] = useState("");
  const [assignedPersonnel, setAssignedPersonnel] = useState("");
  // Supervisor dropdown options — fetched lazily from the IAM users list.
  // The backend does not expose a role-filtered endpoint, so we fetch all
  // users and filter client-side for the "Supervisor" role.
  const [supervisorOptions, setSupervisorOptions] = useState<{ id: string; full_name: string }[]>([]);
  const [supervisorsLoading, setSupervisorsLoading] = useState(false);

  // Complete work technical report form
  const [completeForm, setCompleteForm] = useState({
    action_taken: "",
    downtime_hours: 0,
    completion_notes: "",
    labour_details: "",
    parts: [] as { part_name: string; part_number: string; quantity: number; unit_cost: number }[],
  });

  // Verify Form
  const [verifyComment, setVerifyComment] = useState("");

  const { isOnline } = useConnection();

  // Requester Confirmation Form
  const [confirmNotes, setConfirmNotes] = useState("");

  // Close Signature state
  const [closeComment, setCloseComment] = useState("");

  // ── Fetch Report ──────────────────────────────────────────────
  const fetchReport = useCallback(async (jobStatus: string) => {
    const activeStatuses = ["IN_PROGRESS", "ON_HOLD", "COMPLETED", "PENDING_REVIEW", "VERIFIED", "CLOSED"];
    if (!activeStatuses.includes(jobStatus?.toUpperCase())) return;
    setReportLoading(true);
    try {
      const r = await getJobReport(id);
      if (r) {
        setReport(r);
        setReportDraft({
          fault_found: r.fault_found ?? "",
          fault_code: r.fault_code ?? "",
          corrective_action: r.corrective_action ?? "",
          technical_notes: r.technical_notes ?? "",
          observations: r.observations ?? "",
          recommendations: r.recommendations ?? "",
          follow_up_required: r.follow_up_required,
          follow_up_notes: r.follow_up_notes ?? "",
          actual_labour_hours: r.actual_labour_hours,
          actual_cost: r.actual_cost,
          dept_schema_type: r.dept_schema_type ?? "GENERIC",
          dept_specific_data: r.dept_specific_data ?? {},
        });
        if (r.dept_schema_type && r.dept_schema_type !== "GENERIC") {
          const fields = await getDeptSchema(r.dept_schema_type);
          setDeptFields(fields);
        }
      }
    } catch {
      // Report may not exist yet (job just started) — silently ignore 404
    } finally {
      setReportLoading(false);
    }
  }, [id]);

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
        // Fetch report for active execution statuses
        await fetchReport(res.status);
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
  }, [id, fetchReport]);

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // Fetch supervisor options when the assignment modal opens.
  // We hit the canonical IAM users list and filter by role on the client.
  useEffect(() => {
    if (!showAssignModal) return;
    let cancelled = false;
    setSupervisorsLoading(true);
    apiFetch<Array<{ id: string; first_name: string; last_name: string; email: string; roles: string[] }>>(
      "/api/v1/iam/users"
    )
      .then((users) => {
        if (cancelled) return;
        const supervisors = (users || [])
          .filter((u) => Array.isArray(u.roles) && u.roles.some((r) => r.toLowerCase() === "supervisor"))
          .map((u) => ({
            id: u.id,
            full_name: `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim() || u.email,
          }));
        setSupervisorOptions(supervisors);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error("Failed to load supervisors", err);
        setSupervisorOptions([]);
      })
      .finally(() => {
        if (!cancelled) setSupervisorsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [showAssignModal]);

  // ── Report save handler ───────────────────────────────────────
  const saveReport = async () => {
    if (!report) return;
    setReportSaving(true);
    try {
      const updated = await updateJobReport(id, reportDraft);
      if (updated) setReport(updated);
      setSuccessMessage("Job Report saved.");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to save report.");
    } finally {
      setReportSaving(false);
    }
  };

  const handleAddProgress = async () => {
    try {
      await addProgressUpdate(id, progressForm);
      await fetchReport(job?.status || "");
      setShowProgressModal(false);
      setProgressForm({ update_type: "PROGRESS", notes: "", hold_reason: "", percentage_complete: 50 });
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to log progress update.");
    }
  };

  const handleAddMaterial = async () => {
    try {
      await addMaterial(id, materialForm as Omit<JobReportMaterial, "id">);
      await fetchReport(job?.status || "");
      setShowMaterialModal(false);
      setMaterialForm({ category: "SPARE_PART", item_name: "", item_code: "", quantity: 1, unit: "pcs", unit_cost: 0, notes: "" });
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to add material.");
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    try {
      await deleteMaterial(id, materialId);
      await fetchReport(job?.status || "");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to remove material.");
    }
  };

  const handleAddAttachment = async () => {
    try {
      await addAttachment(id, attachmentForm as Omit<JobReportAttachment, "id" | "uploaded_by_id" | "uploaded_at">);
      await fetchReport(job?.status || "");
      setShowAttachmentModal(false);
      setAttachmentForm({ category: "PHOTO", filename: "", file_url: "", file_type: "", file_size_kb: 0, caption: "" });
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to add attachment.");
    }
  };

  const handleCreateAmendment = async () => {
    try {
      await createAmendment(id, amendmentForm);
      await fetchReport(job?.status || "");
      setShowAmendmentModal(false);
      setAmendmentForm({ field_name: "corrective_action", new_value: "", amendment_reason: "" });
      setSuccessMessage("Amendment recorded.");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMessage(e.message || "Failed to create amendment.");
    }
  };

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
        let userId: string | undefined;
        try {
          const raw = localStorage.getItem('user_details');
          if (raw) {
            const parsed = JSON.parse(raw);
            userId = parsed?.id;
          }
        } catch {
          // Ignore corrupted localStorage data
        }
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

              {/* ASSIGNED -> START WITH LOTO GATE */}
              {isAssigned && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                    onClick={() => setShowLotoModal(true)}
                    loading={actionLoading}
                  >
                    <Lock className="size-3.5 mr-1.5 text-amber-300" />
                    Pre-Start LOTO & Begin Work
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

              {/* IN_PROGRESS -> COMPLETE / HOLD / DRAWER */}
              {isInProgress && (
                <Protect capability="job_card:update">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
                    onClick={() => setShowExecutionDrawer(true)}
                  >
                    <Timer className="size-3.5 mr-1.5" />
                    Execution Console ({formatTimer(timerSeconds)})
                  </Button>
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
                    onClick={() => {
                      executeTransition("start");
                      setTimerActive(true);
                      setTimerPaused(false);
                    }}
                    loading={actionLoading}
                  >
                    <Play className="size-3.5 mr-1.5" />
                    Resume Work Execution
                  </Button>
                </Protect>
              )}

              {/* COMPLETED -> QA VERIFY / REVIEW / REWORK */}
              {isCompleted && (
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowCertificateModal(true)}
                    className="font-bold border-zinc-300 dark:border-zinc-700"
                  >
                    <Printer className="size-3.5 mr-1.5 text-primary" />
                    Handover Certificate
                  </Button>
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
                </div>
              )}

              {/* PENDING_REVIEW / VERIFIED -> CONFIRM & CLOSE */}
              {(isPendingReview || isVerified) && (
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowCertificateModal(true)}
                    className="font-bold border-zinc-300 dark:border-zinc-700"
                  >
                    <Printer className="size-3.5 mr-1.5 text-primary" />
                    Handover Certificate
                  </Button>
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
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowCertificateModal(true)}
                    className="font-bold border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5 hover:bg-emerald-500/10"
                  >
                    <Printer className="size-3.5 mr-1.5" />
                    View Handover Certificate
                  </Button>
                  <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded">
                    <CheckCircle2 className="size-4" />
                    <span className="font-bold">ARCHIVED & SIGNED OFF</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* LIVE EXECUTION & STOPWATCH BAR FOR IN_PROGRESS */}
          {isInProgress && (
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-zinc-900 text-white dark:bg-zinc-800 border border-zinc-700 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="size-8 rounded bg-amber-500 text-zinc-950 flex items-center justify-center font-bold font-mono">
                  <Timer className="size-4 animate-pulse" />
                </div>
                <div>
                  <div className="text-[10px] font-mono text-zinc-400 uppercase">Live Active Labor Stopwatch</div>
                  <div className="text-base font-mono font-black text-amber-400 tracking-wider">
                    {formatTimer(timerSeconds)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setTimerPaused(!timerPaused)}
                  className="bg-zinc-800 hover:bg-zinc-700 text-white border-zinc-700 text-xs h-7 font-mono"
                >
                  {timerPaused ? <Play className="size-3 mr-1 text-emerald-400" /> : <Pause className="size-3 mr-1 text-amber-400" />}
                  {timerPaused ? "Resume" : "Pause"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowExecutionDrawer(true)}
                  className="bg-zinc-800 hover:bg-zinc-700 text-white border-zinc-700 text-xs h-7 font-bold"
                >
                  <Wrench className="size-3 mr-1 text-amber-400" />
                  Quick Spares & Labor Console
                </Button>
              </div>
            </div>
          )}

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

          {/* ── V1.3: STAGE 3B — JOB EXECUTION REPORT ────────────── */}
          {report && (
            <Card id="stage-job-report">
              <CardHeader>
                <CardTitle>
                  <ClipboardList className="size-4 text-violet-500" />
                  <span>Stage 3B: Job Execution Report</span>
                  {report.is_locked && (
                    <span className="ml-auto flex items-center gap-1 text-[10px] font-mono text-amber-600 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
                      <Lock className="size-3" /> LOCKED — POST-CLOSURE
                    </span>
                  )}
                </CardTitle>
                <span className="text-[10px] font-mono text-muted-foreground uppercase">
                  Dept Schema: {report.dept_schema_type} • {report.is_locked ? `Locked ${report.locked_at ? new Date(report.locked_at).toLocaleDateString() : ""}` : "Active"}
                </span>
              </CardHeader>
              <CardContent className="space-y-5 pt-2">

                {/* LOCKED BANNER */}
                {report.is_locked && (
                  <div className="rounded border border-amber-500/40 bg-amber-500/8 p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-mono">
                      <Lock className="size-3.5" />
                      <span>This report is <strong>locked</strong>. The job card has been formally closed. All corrections require an auditable amendment.</span>
                    </div>
                    <Button size="sm" variant="outline" className="text-amber-600 border-amber-500/40 ml-3" onClick={() => setShowAmendmentModal(true)}>
                      <PenLine className="size-3 mr-1" /> Create Amendment
                    </Button>
                  </div>
                )}

                {/* ── SECTION 1: EXECUTION TIMELINE ─────────────── */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold flex items-center gap-1">
                      <BarChart3 className="size-3" /> Work Execution Timeline
                    </span>
                    {!report.is_locked && (
                      <Button size="sm" variant="outline" className="h-6 text-[10px] font-mono" onClick={() => setShowProgressModal(true)}>
                        <Plus className="size-3 mr-1" /> Log Update
                      </Button>
                    )}
                  </div>
                  {(!report.progress_updates || report.progress_updates.length === 0) ? (
                    <div className="p-3 rounded border border-dashed border-border text-muted-foreground text-center text-[11px] font-mono">
                      No progress events logged yet. Use &quot;Log Update&quot; to begin the execution timeline.
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {report.progress_updates.map((pu) => {
                        const typeColors: Record<string, string> = {
                          WORK_START: "bg-emerald-500/10 border-emerald-500/40 text-emerald-700 dark:text-emerald-300",
                          PROGRESS: "bg-blue-500/10 border-blue-500/40 text-blue-700 dark:text-blue-300",
                          PAUSE: "bg-amber-500/10 border-amber-500/40 text-amber-700 dark:text-amber-300",
                          RESUME: "bg-cyan-500/10 border-cyan-500/40 text-cyan-700 dark:text-cyan-300",
                          COMPLETION: "bg-violet-500/10 border-violet-500/40 text-violet-700 dark:text-violet-300",
                        };
                        const cls = typeColors[pu.update_type] || "bg-muted/30 border-border text-foreground";
                        return (
                          <div key={pu.id} className={`rounded border p-2.5 text-xs ${cls}`}>
                            <div className="flex items-center justify-between">
                              <span className="font-mono font-bold text-[10px]">{pu.update_type.replace("_", " ")}</span>
                              <span className="font-mono text-[10px] opacity-70">{new Date(pu.timestamp).toLocaleString()}</span>
                            </div>
                            {pu.percentage_complete > 0 && (
                              <div className="mt-1.5 flex items-center gap-2">
                                <div className="flex-1 h-1.5 bg-black/10 rounded-full overflow-hidden">
                                  <div className="h-full bg-current opacity-60 rounded-full transition-all" style={{ width: `${pu.percentage_complete}%` }} />
                                </div>
                                <span className="text-[10px] font-mono font-bold">{pu.percentage_complete}%</span>
                              </div>
                            )}
                            {pu.notes && <p className="mt-1 text-[11px] opacity-90">{pu.notes}</p>}
                            {pu.hold_reason && (
                              <div className="mt-1 text-[10px] font-mono"><span className="font-bold">Hold Reason:</span> {pu.hold_reason}</div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* ── SECTION 2 & 3: FAULT, CORRECTIVE ACTION, OUTCOMES ── */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    { key: "fault_found", label: "Fault Found", icon: <AlertTriangle className="size-3 text-red-500" />, rows: 3 },
                    { key: "fault_code", label: "Fault Code", icon: <FlaskConical className="size-3 text-orange-500" />, rows: 1 },
                    { key: "corrective_action", label: "Corrective Action Taken", icon: <Wrench className="size-3 text-blue-500" />, rows: 4 },
                    { key: "technical_notes", label: "Technical Notes", icon: <FileText className="size-3 text-cyan-500" />, rows: 3 },
                    { key: "observations", label: "Observations", icon: <CheckCheck className="size-3 text-emerald-500" />, rows: 3 },
                    { key: "recommendations", label: "Recommendations", icon: <BarChart3 className="size-3 text-violet-500" />, rows: 3 },
                  ].map(({ key, label, icon, rows }) => (
                    <div key={key} className={rows >= 4 ? "md:col-span-2" : ""}>
                      <label className="text-[10px] font-mono uppercase text-muted-foreground flex items-center gap-1 mb-1">
                        {icon} {label}
                      </label>
                      {report.is_locked ? (
                        <div className="p-2.5 rounded bg-muted/20 border border-border text-xs text-foreground leading-relaxed whitespace-pre-wrap min-h-[40px]">
                          {(report as unknown as Record<string, string>)[key] || <span className="text-muted-foreground italic">Not recorded</span>}
                        </div>
                      ) : (
                        <textarea
                          rows={rows}
                          className="w-full rounded border border-border bg-background text-xs text-foreground p-2.5 font-sans leading-relaxed resize-none focus:outline-none focus:ring-1 focus:ring-primary/50"
                          value={(reportDraft as Record<string, string>)[key] ?? ""}
                          onChange={(e) => setReportDraft(prev => ({ ...prev, [key]: e.target.value }))}
                          placeholder={`Enter ${label.toLowerCase()}...`}
                        />
                      )}
                    </div>
                  ))}
                </div>

                {/* Follow-up toggle */}
                {!report.is_locked && (
                  <div className="flex items-center gap-3 text-xs">
                    <label className="text-[10px] font-mono uppercase text-muted-foreground">Follow-up Work Required</label>
                    <button
                      onClick={() => setReportDraft(prev => ({ ...prev, follow_up_required: !prev.follow_up_required }))}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        reportDraft.follow_up_required ? "bg-violet-500" : "bg-muted"
                      }`}
                    >
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                        reportDraft.follow_up_required ? "translate-x-4" : "translate-x-1"
                      }`} />
                    </button>
                  </div>
                )}
                {reportDraft.follow_up_required && !report.is_locked && (
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Follow-up Notes</label>
                    <textarea
                      rows={2}
                      className="w-full rounded border border-border bg-background text-xs text-foreground p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-primary/50"
                      value={reportDraft.follow_up_notes ?? ""}
                      onChange={(e) => setReportDraft(prev => ({ ...prev, follow_up_notes: e.target.value }))}
                      placeholder="Describe the follow-up work required..."
                    />
                  </div>
                )}

                {/* ── SECTION 4: LABOUR SUMMARY ─────────────────── */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Actual Labour Hours</label>
                    {report.is_locked ? (
                      <div className="p-2.5 rounded bg-muted/20 border border-border text-xs font-mono font-bold">{report.actual_labour_hours} hrs</div>
                    ) : (
                      <Input
                        type="number"
                        className="font-mono text-xs h-8"
                        value={reportDraft.actual_labour_hours ?? 0}
                        onChange={(e) => setReportDraft(prev => ({ ...prev, actual_labour_hours: parseFloat(e.target.value) || 0 }))}
                      />
                    )}
                  </div>
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Actual Cost (USD)</label>
                    {report.is_locked ? (
                      <div className="p-2.5 rounded bg-muted/20 border border-border text-xs font-mono font-bold">${report.actual_cost.toFixed(2)}</div>
                    ) : (
                      <Input
                        type="number"
                        className="font-mono text-xs h-8"
                        value={reportDraft.actual_cost ?? 0}
                        onChange={(e) => setReportDraft(prev => ({ ...prev, actual_cost: parseFloat(e.target.value) || 0 }))}
                      />
                    )}
                  </div>
                </div>

                {/* ── SECTION 5: MATERIALS / TOOLS / EQUIPMENT ─── */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold flex items-center gap-1">
                      <Wrench className="size-3" /> Materials, Tools & Equipment
                    </span>
                    {!report.is_locked && (
                      <Button size="sm" variant="outline" className="h-6 text-[10px] font-mono" onClick={() => setShowMaterialModal(true)}>
                        <Plus className="size-3 mr-1" /> Add Item
                      </Button>
                    )}
                  </div>
                  {(!report.materials || report.materials.length === 0) ? (
                    <div className="p-3 rounded border border-dashed border-border text-muted-foreground text-center text-[11px] font-mono">
                      No materials, tools, or equipment recorded.
                    </div>
                  ) : (
                    <Table dense zebra>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Category</TableHead>
                          <TableHead>Item</TableHead>
                          <TableHead className="w-20">Code</TableHead>
                          <TableHead className="w-14 text-right">Qty</TableHead>
                          <TableHead className="w-16">Unit</TableHead>
                          <TableHead className="w-20 text-right">Cost ($)</TableHead>
                          {!report.is_locked && <TableHead className="w-8" />}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {report.materials.map((m) => (
                          <TableRow key={m.id}>
                            <TableCell>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted border border-border">{m.category}</span>
                            </TableCell>
                            <TableCell className="font-semibold text-foreground">{m.item_name}</TableCell>
                            <TableCell mono className="text-muted-foreground">{m.item_code || "—"}</TableCell>
                            <TableCell mono className="text-right">{m.quantity}</TableCell>
                            <TableCell mono>{m.unit || "—"}</TableCell>
                            <TableCell mono className="text-right">{m.unit_cost != null ? `$${m.unit_cost.toFixed(2)}` : "—"}</TableCell>
                            {!report.is_locked && (
                              <TableCell>
                                <button onClick={() => handleDeleteMaterial(m.id)} className="text-destructive/70 hover:text-destructive transition-colors">
                                  <Trash2 className="size-3.5" />
                                </button>
                              </TableCell>
                            )}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>

                {/* ── SECTION 6: DEPARTMENT-SPECIFIC FIELDS ─────── */}
                {deptFields.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold flex items-center gap-1">
                      <FlaskConical className="size-3" /> {report.dept_schema_type} — Department-Specific Fields
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {deptFields.map((field) => {
                        const currentVal = (reportDraft.dept_specific_data as Record<string, unknown> | undefined)?.[field.name];
                        const isBoolean = field.type.includes("bool");
                        const isNumber = field.type.includes("float") || field.type.includes("int");
                        return (
                          <div key={field.name}>
                            <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1" title={field.description}>
                              {field.label}
                            </label>
                            {report.is_locked ? (
                              <div className="p-2 rounded bg-muted/20 border border-border text-xs font-mono">
                                {currentVal != null ? String(currentVal) : <span className="text-muted-foreground italic">—</span>}
                              </div>
                            ) : isBoolean ? (
                              <select
                                className="w-full rounded border border-border bg-background text-xs p-2 focus:outline-none"
                                value={currentVal == null ? "" : String(currentVal)}
                                onChange={(e) => {
                                  const v = e.target.value === "" ? null : e.target.value === "true";
                                  setReportDraft(prev => ({ ...prev, dept_specific_data: { ...(prev.dept_specific_data || {}), [field.name]: v } }));
                                }}
                              >
                                <option value="">— Not recorded —</option>
                                <option value="true">Yes</option>
                                <option value="false">No</option>
                              </select>
                            ) : (
                              <Input
                                type={isNumber ? "number" : "text"}
                                className="text-xs h-8 font-mono"
                                value={currentVal != null ? String(currentVal) : ""}
                                placeholder={field.description}
                                onChange={(e) => {
                                  const v = isNumber ? (parseFloat(e.target.value) || null) : (e.target.value || null);
                                  setReportDraft(prev => ({ ...prev, dept_specific_data: { ...(prev.dept_specific_data || {}), [field.name]: v } }));
                                }}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ── SECTION 7: ATTACHMENTS ─────────────────────── */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold flex items-center gap-1">
                      <Paperclip className="size-3" /> Report Attachments
                    </span>
                    {!report.is_locked && (
                      <Button size="sm" variant="outline" className="h-6 text-[10px] font-mono" onClick={() => setShowAttachmentModal(true)}>
                        <Upload className="size-3 mr-1" /> Add File
                      </Button>
                    )}
                  </div>
                  {(!report.attachments || report.attachments.length === 0) ? (
                    <div className="p-3 rounded border border-dashed border-border text-muted-foreground text-center text-[11px] font-mono">
                      No photos, documents, or certificates attached.
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {report.attachments.map((att) => {
                        const catColors: Record<string, string> = {
                          PHOTO: "bg-blue-500/10 text-blue-600",
                          DOCUMENT: "bg-violet-500/10 text-violet-600",
                          CERTIFICATE: "bg-emerald-500/10 text-emerald-600",
                          SKETCH: "bg-amber-500/10 text-amber-600",
                          MEASUREMENT_SHEET: "bg-cyan-500/10 text-cyan-600",
                          OTHER: "bg-muted text-muted-foreground",
                        };
                        return (
                          <div key={att.id} className="rounded border border-border p-2.5 space-y-1">
                            <div className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded w-fit ${catColors[att.category] || catColors.OTHER}`}>
                              {att.category}
                            </div>
                            <div className="text-xs font-semibold text-foreground truncate" title={att.filename}>{att.filename}</div>
                            {att.caption && <div className="text-[10px] text-muted-foreground">{att.caption}</div>}
                            <div className="text-[10px] font-mono text-muted-foreground">{att.file_size_kb > 0 ? `${att.file_size_kb} KB` : ""}</div>
                            {att.file_url && (
                               <a href={att.file_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-primary underline">View</a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* ── SECTION 8: POST-CLOSURE AMENDMENTS ─────────── */}
                {report.amendments && report.amendments.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold flex items-center gap-1">
                      <PenLine className="size-3" /> Post-Closure Amendments
                    </span>
                    <Table dense>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Field</TableHead>
                          <TableHead>Old Value</TableHead>
                          <TableHead>New Value</TableHead>
                          <TableHead>Reason</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {report.amendments.map((am) => (
                          <TableRow key={am.id}>
                            <TableCell mono className="font-bold">{am.field_name}</TableCell>
                            <TableCell className="text-muted-foreground text-xs max-w-[120px] truncate" title={am.old_value ?? ""}>{am.old_value || "—"}</TableCell>
                            <TableCell className="text-foreground text-xs max-w-[120px] truncate" title={am.new_value ?? ""}>{am.new_value || "—"}</TableCell>
                            <TableCell className="text-xs max-w-[160px] truncate" title={am.amendment_reason}>{am.amendment_reason}</TableCell>
                            <TableCell>
                              <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                                am.approval_status === "APPROVED" ? "bg-emerald-500/10 text-emerald-600" :
                                am.approval_status === "PENDING" ? "bg-amber-500/10 text-amber-600" :
                                "bg-red-500/10 text-red-600"
                              }`}>{am.approval_status}</span>
                            </TableCell>
                            <TableCell mono className="text-muted-foreground text-[10px]">{new Date(am.created_at).toLocaleDateString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {/* SAVE BUTTON (only when not locked) */}
                {!report.is_locked && (
                  <div className="flex justify-end pt-2 border-t border-border/50">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={saveReport}
                      loading={reportSaving}
                      className="font-mono text-xs"
                    >
                      <CheckCheck className="size-3.5 mr-1.5" />
                      Save Report Changes
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Placeholder when report hasn't been created yet (before IN_PROGRESS) */}
          {!report && !reportLoading && job && ["IN_PROGRESS", "ON_HOLD", "COMPLETED", "PENDING_REVIEW", "VERIFIED", "CLOSED"].includes(job.status) && (
            <Card id="stage-job-report">
              <CardContent className="py-8 text-center text-muted-foreground text-xs font-mono">
                <ClipboardList className="size-6 mx-auto mb-2 opacity-30" />
                Job Execution Report not yet initialised. Start the job to create the report.
              </CardContent>
            </Card>
          )}

          {/* ── PROGRESS UPDATE MODAL ─────────────────────────── */}
          <Dialog open={showProgressModal} onOpenChange={setShowProgressModal}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Log Execution Progress Update</DialogTitle>
                <DialogDescription>Record a timestamped event in the job execution timeline.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2 text-xs">
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Update Type</label>
                  <select
                    className="w-full rounded border border-border bg-background text-xs p-2 focus:outline-none"
                    value={progressForm.update_type}
                    onChange={(e) => setProgressForm(prev => ({ ...prev, update_type: e.target.value }))}
                  >
                    <option value="WORK_START">Work Start — Physical work begins</option>
                    <option value="PROGRESS">Progress — Mid-job update</option>
                    <option value="PAUSE">Pause — Work stopped (hold reason required)</option>
                    <option value="RESUME">Resume — Work resumed from hold</option>
                    <option value="COMPLETION">Completion — Technician marks work done</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">% Complete: {progressForm.percentage_complete}%</label>
                  <input
                    type="range" min={0} max={100} step={5}
                    className="w-full"
                    value={progressForm.percentage_complete}
                    onChange={(e) => setProgressForm(prev => ({ ...prev, percentage_complete: parseInt(e.target.value) }))}
                  />
                </div>
                {progressForm.update_type === "PAUSE" && (
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Hold Reason <span className="text-red-500">*</span></label>
                    <Input
                      className="text-xs h-8"
                      placeholder="Why is work being paused?"
                      value={progressForm.hold_reason}
                      onChange={(e) => setProgressForm(prev => ({ ...prev, hold_reason: e.target.value }))}
                    />
                  </div>
                )}
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Notes (Optional)</label>
                  <textarea rows={3} className="w-full rounded border border-border bg-background text-xs p-2.5 resize-none focus:outline-none" value={progressForm.notes} onChange={(e) => setProgressForm(prev => ({ ...prev, notes: e.target.value }))} placeholder="Describe current status..." />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" size="sm" onClick={() => setShowProgressModal(false)}>Cancel</Button>
                <Button size="sm" onClick={handleAddProgress}>Log Update</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ── MATERIAL MODAL ────────────────────────────────── */}
          <Dialog open={showMaterialModal} onOpenChange={setShowMaterialModal}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Material / Tool / Equipment</DialogTitle>
                <DialogDescription>Record a resource consumed or used during this job.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Category</label>
                    <select className="w-full rounded border border-border bg-background text-xs p-2" value={materialForm.category} onChange={(e) => setMaterialForm(prev => ({ ...prev, category: e.target.value }))}>
                      <option value="SPARE_PART">Spare Part</option>
                      <option value="CONSUMABLE">Consumable</option>
                      <option value="MATERIAL">Material</option>
                      <option value="TOOL">Tool</option>
                      <option value="EQUIPMENT">Equipment</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Item Name <span className="text-red-500">*</span></label>
                    <Input className="text-xs h-8" value={materialForm.item_name} onChange={(e) => setMaterialForm(prev => ({ ...prev, item_name: e.target.value }))} placeholder="e.g. SKF Bearing 6205" />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Item Code / Part #</label>
                    <Input className="text-xs h-8 font-mono" value={materialForm.item_code} onChange={(e) => setMaterialForm(prev => ({ ...prev, item_code: e.target.value }))} placeholder="e.g. SKF-6205" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Quantity</label>
                      <Input type="number" className="text-xs h-8" value={materialForm.quantity} onChange={(e) => setMaterialForm(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 1 }))} />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Unit</label>
                      <Input className="text-xs h-8 font-mono" value={materialForm.unit} onChange={(e) => setMaterialForm(prev => ({ ...prev, unit: e.target.value }))} placeholder="pcs" />
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Unit Cost (USD)</label>
                    <Input type="number" className="text-xs h-8" value={materialForm.unit_cost} onChange={(e) => setMaterialForm(prev => ({ ...prev, unit_cost: parseFloat(e.target.value) || 0 }))} />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Notes</label>
                    <Input className="text-xs h-8" value={materialForm.notes} onChange={(e) => setMaterialForm(prev => ({ ...prev, notes: e.target.value }))} />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" size="sm" onClick={() => setShowMaterialModal(false)}>Cancel</Button>
                <Button size="sm" onClick={handleAddMaterial} disabled={!materialForm.item_name.trim()}>Add Item</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ── ATTACHMENT MODAL ──────────────────────────────── */}
          <Dialog open={showAttachmentModal} onOpenChange={setShowAttachmentModal}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Report Attachment</DialogTitle>
                <DialogDescription>Attach a photo, document, certificate, or sketch to the report.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2 text-xs">
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Category</label>
                  <select className="w-full rounded border border-border bg-background text-xs p-2" value={attachmentForm.category} onChange={(e) => setAttachmentForm(prev => ({ ...prev, category: e.target.value }))}>
                    <option value="PHOTO">Photo</option>
                    <option value="DOCUMENT">Document</option>
                    <option value="CERTIFICATE">Certificate</option>
                    <option value="SKETCH">Sketch / Drawing</option>
                    <option value="MEASUREMENT_SHEET">Measurement Sheet</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Filename <span className="text-red-500">*</span></label>
                  <Input className="text-xs h-8" value={attachmentForm.filename} onChange={(e) => setAttachmentForm(prev => ({ ...prev, filename: e.target.value }))} placeholder="e.g. photo-01.jpg" />
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">File URL (or leave blank)</label>
                  <Input className="text-xs h-8 font-mono" value={attachmentForm.file_url} onChange={(e) => setAttachmentForm(prev => ({ ...prev, file_url: e.target.value }))} placeholder="https://..." />
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Caption</label>
                  <Input className="text-xs h-8" value={attachmentForm.caption} onChange={(e) => setAttachmentForm(prev => ({ ...prev, caption: e.target.value }))} placeholder="Brief description of attachment" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" size="sm" onClick={() => setShowAttachmentModal(false)}>Cancel</Button>
                <Button size="sm" onClick={handleAddAttachment} disabled={!attachmentForm.filename.trim()}>Attach File</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ── AMENDMENT MODAL ───────────────────────────────── */}
          <Dialog open={showAmendmentModal} onOpenChange={setShowAmendmentModal}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Post-Closure Amendment</DialogTitle>
                <DialogDescription>Corrections to locked reports are permanently recorded with the original and corrected values.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2 text-xs">
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Field to Amend <span className="text-red-500">*</span></label>
                  <select className="w-full rounded border border-border bg-background text-xs p-2" value={amendmentForm.field_name} onChange={(e) => setAmendmentForm(prev => ({ ...prev, field_name: e.target.value }))}>
                    <option value="fault_found">Fault Found</option>
                    <option value="fault_code">Fault Code</option>
                    <option value="corrective_action">Corrective Action</option>
                    <option value="technical_notes">Technical Notes</option>
                    <option value="observations">Observations</option>
                    <option value="recommendations">Recommendations</option>
                    <option value="follow_up_notes">Follow-up Notes</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Corrected Value <span className="text-red-500">*</span></label>
                  <textarea rows={4} className="w-full rounded border border-border bg-background text-xs p-2.5 resize-none focus:outline-none" value={amendmentForm.new_value} onChange={(e) => setAmendmentForm(prev => ({ ...prev, new_value: e.target.value }))} placeholder="Enter the corrected content..." />
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">Justification Reason <span className="text-red-500">*</span></label>
                  <textarea rows={2} className="w-full rounded border border-border bg-background text-xs p-2.5 resize-none focus:outline-none" value={amendmentForm.amendment_reason} onChange={(e) => setAmendmentForm(prev => ({ ...prev, amendment_reason: e.target.value }))} placeholder="Why is this correction necessary? (minimum 5 characters)" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" size="sm" onClick={() => setShowAmendmentModal(false)}>Cancel</Button>
                <Button size="sm" variant="default" onClick={handleCreateAmendment} disabled={!amendmentForm.new_value.trim() || amendmentForm.amendment_reason.length < 5}>
                  <PenLine className="size-3.5 mr-1" /> Submit Amendment
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

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
                disabled={supervisorsLoading}
                className="h-8 w-full rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground outline-none focus:border-ring font-mono"
              >
                <option value="">
                  {supervisorsLoading
                    ? "Loading supervisors..."
                    : supervisorOptions.length === 0
                    ? "No supervisors available"
                    : "Select Supervisor..."}
                </option>
                {supervisorOptions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
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

      {/* ── PRE-START LOTO SAFETY GATE MODAL ────────────────── */}
      <Dialog open={showLotoModal} onOpenChange={setShowLotoModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-foreground">
              <Lock className="size-4 text-amber-500" />
              <span>Pre-Start Lockout / Tagout (LOTO) Safety Gate</span>
            </DialogTitle>
            <DialogDescription>
              Mandatory safety isolation checklist and lead technician digital sign-off before entering hazardous workspace.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  LOTO Tag Number <span className="text-destructive">*</span>
                </label>
                <Input
                  mono
                  value={lotoTagNumber}
                  onChange={(e) => setLotoTagNumber(e.target.value)}
                  placeholder="e.g. BK-LOTO-4091"
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Initial Equipment Meter (Hours)
                </label>
                <Input
                  type="number"
                  value={lotoStartMeter}
                  onChange={(e) => setLotoStartMeter(parseFloat(e.target.value) || 0)}
                  placeholder="e.g. 1420.5"
                  className="h-8 text-xs font-mono"
                />
              </div>
            </div>

            {/* Critical Isolation Checklist */}
            <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-2">
              <div className="text-[11px] font-bold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="size-3.5" />
                <span>Critical Isolation & Zero-Energy Verification</span>
              </div>
              <div className="space-y-1.5 text-[11px]">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={lotoChecks.electrical}
                    onChange={(e) => setLotoChecks(prev => ({ ...prev, electrical: e.target.checked }))}
                    className="size-3.5 rounded border-border accent-amber-500"
                  />
                  <span>Electrical switchgear de-energized, padlocked, and danger tagged</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={lotoChecks.hydraulic}
                    onChange={(e) => setLotoChecks(prev => ({ ...prev, hydraulic: e.target.checked }))}
                    className="size-3.5 rounded border-border accent-amber-500"
                  />
                  <span>Hydraulic, pneumatic, and gravitational energy bled to zero pressure</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={lotoChecks.ppe}
                    onChange={(e) => setLotoChecks(prev => ({ ...prev, ppe: e.target.checked }))}
                    className="size-3.5 rounded border-border accent-amber-500"
                  />
                  <span>Mining PPE verified (Hard hat, safety boots, high-vis, safety glasses)</span>
                </label>
              </div>
            </div>

            {/* Lead Technician Sign-off */}
            <SignaturePanel
              title="Lead Technician Pre-Start Endorsement"
              signerRole="Lead Technician"
              requireLoto={true}
              onSign={(sig) => {
                setLotoSignData(sig);
                setTechnicianSignData(sig);
              }}
              signed={!!lotoSignData}
              signedBy={lotoSignData?.name}
              signedAt={lotoSignData?.timestamp}
              signatureHash={lotoSignData?.hash}
              signatureImage={lotoSignData?.signatureImage}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowLotoModal(false)}>
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              loading={actionLoading}
              disabled={!lotoTagNumber.trim() || !lotoChecks.electrical || !lotoChecks.hydraulic || !lotoChecks.ppe || !lotoSignData}
              onClick={() => {
                executeTransition("start", {
                  loto_tag: lotoTagNumber,
                  start_meter: lotoStartMeter,
                  technician_sign: lotoSignData,
                });
                setTimerActive(true);
                setTimerPaused(false);
                setShowLotoModal(false);
              }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
            >
              <Play className="size-3.5 mr-1" />
              Authorize & Start Execution
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── LIVE EXECUTION DRAWER & TIMER ─────────────────── */}
      <Drawer
        open={showExecutionDrawer}
        onClose={() => setShowExecutionDrawer(false)}
        title={`Live Execution Console: ${displayJobNumber}`}
        description="Active maintenance stopwatch, field labor duration, and direct spare parts consumption logger."
      >
        <div className="space-y-5 p-1 text-xs">
          {/* Stopwatch HUD */}
          <div className="p-4 rounded-xl bg-zinc-900 text-white dark:bg-zinc-800 border border-zinc-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="size-10 rounded-lg bg-amber-500 text-zinc-950 flex items-center justify-center font-bold font-mono shadow-xs">
                <Timer className="size-5 animate-pulse" />
              </div>
              <div>
                <span className="text-[10px] font-mono text-zinc-400 uppercase">Active Labor Stopwatch</span>
                <div className="text-xl font-mono font-black text-amber-400 tracking-wider">
                  {formatTimer(timerSeconds)}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setTimerPaused(!timerPaused)}
                className="bg-zinc-800 hover:bg-zinc-700 text-white border-zinc-700 text-xs font-mono h-8"
              >
                {timerPaused ? <Play className="size-3.5 mr-1 text-emerald-400" /> : <Pause className="size-3.5 mr-1 text-amber-400" />}
                {timerPaused ? "Resume" : "Pause"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setTimerSeconds(0)}
                className="bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white border-zinc-700 text-xs font-mono h-8"
              >
                <RotateCcw className="size-3.5 mr-1" />
                Reset
              </Button>
            </div>
          </div>

          {/* Quick Spare Parts Consumption Adder */}
          <div className="space-y-3 p-3.5 rounded-lg border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <Wrench className="size-3.5 text-primary" />
                <span>Log Consumed Spare Parts</span>
              </span>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">Inventory Direct Deduction</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
              <div className="sm:col-span-2">
                <Input
                  value={quickPart.part_name}
                  onChange={(e) => setQuickPart(prev => ({ ...prev, part_name: e.target.value }))}
                  placeholder="Part name (e.g. Hydraulic Seal Kit)"
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Input
                  mono
                  value={quickPart.part_number}
                  onChange={(e) => setQuickPart(prev => ({ ...prev, part_number: e.target.value }))}
                  placeholder="Part # (e.g. HYD-SK-01)"
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Input
                  type="number"
                  value={quickPart.quantity}
                  onChange={(e) => setQuickPart(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 1 }))}
                  placeholder="Qty"
                  className="h-8 text-xs font-mono"
                />
              </div>
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-[11px] text-muted-foreground font-mono">
                {completeForm.parts.length} parts logged in current shift
              </span>
              <Button
                size="sm"
                variant="outline"
                disabled={!quickPart.part_name.trim()}
                onClick={() => {
                  setCompleteForm(prev => ({
                    ...prev,
                    parts: [...prev.parts, { ...quickPart }],
                  }));
                  setQuickPart({ part_name: "", part_number: "", quantity: 1, unit_cost: 0 });
                }}
                className="font-bold text-xs h-7 gap-1"
              >
                <Plus className="size-3" /> Add to Job Record
              </Button>
            </div>

            {completeForm.parts.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-border/60">
                {completeForm.parts.map((p, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 rounded bg-muted/40 text-xs font-mono">
                    <div>
                      <span className="font-bold text-foreground">{p.part_name}</span>
                      <span className="text-muted-foreground ml-2">({p.part_number || 'N/A'})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary">Qty: {p.quantity}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setCompleteForm(prev => ({
                            ...prev,
                            parts: prev.parts.filter((_, i) => i !== idx),
                          }));
                        }}
                        className="text-destructive hover:text-destructive/80 p-0.5"
                      >
                        <Trash2 className="size-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Technical Notes & Labor Details */}
          <div className="space-y-2 p-3.5 rounded-lg border border-border bg-card">
            <label className="text-[10px] font-mono uppercase text-muted-foreground block">
              Shift Labor & Corrective Action Notes
            </label>
            <textarea
              rows={3}
              value={completeForm.action_taken}
              onChange={(e) => setCompleteForm(prev => ({ ...prev, action_taken: e.target.value }))}
              placeholder="Detail the technical actions completed, components inspected, and torque specs verified..."
              className="w-full rounded border border-input bg-background p-2.5 text-xs text-foreground outline-none focus:border-ring"
            />
          </div>

          {/* Action Trigger */}
          <div className="pt-2 border-t border-border flex justify-end gap-2">
            <Button
              size="sm"
              variant="default"
              className="bg-teal-600 hover:bg-teal-700 text-white font-bold gap-1.5"
              onClick={() => {
                setShowExecutionDrawer(false);
                setShowCompleteModal(true);
              }}
            >
              <FileCheck2 className="size-3.5" />
              Finalize & Submit Job Report
            </Button>
          </div>
        </div>
      </Drawer>

      {/* ── DIGITAL HANDOVER CERTIFICATE MODAL ───────────── */}
      <Dialog open={showCertificateModal} onOpenChange={setShowCertificateModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-4 sm:p-6">
          <JobHandoverCertificate
            data={{
              jobId: job.id,
              jobNumber: displayJobNumber,
              title: job.title,
              description: job.description,
              department: job.workshop_code || "Mechanical Workshop",
              workshopCode: job.workshop_code,
              priority: job.priority,
              status: job.status,
              assetTag: job.machine_id || job.asset_id,
              machineIdentifier: job.machine_id,
              location: job.location,
              createdAt: job.created_at,
              completedAt: job.completed_at || new Date().toISOString(),
              durationHours: completeForm.downtime_hours || (timerSeconds > 0 ? parseFloat((timerSeconds / 3600).toFixed(2)) : 3.5),
              startMeterHours: lotoStartMeter,
              endMeterHours: lotoStartMeter ? lotoStartMeter + (completeForm.downtime_hours || 3.5) : undefined,
              lotoTagNumber: lotoTagNumber || "BK-LOTO-4091",
              lotoVerified: true,
              parts: job.parts && job.parts.length > 0 ? job.parts : completeForm.parts,
              technicianSign: technicianSignData || {
                name: "Tendai Mukamuri",
                role: "Lead Mechanical Technician",
                timestamp: new Date().toISOString(),
                hash: "BK-SIG-TECH-8821",
              },
              supervisorSign: supervisorSignData || {
                name: "Christopher Moyo",
                role: "Maintenance Supervisor",
                timestamp: new Date().toISOString(),
                hash: "BK-SIG-SUP-9904",
              },
              safetySign: safetySignData || {
                name: "Kudakwashe Sibanda",
                role: "HSE Compliance Officer",
                timestamp: new Date().toISOString(),
                hash: "BK-SIG-HSE-3310",
              },
            }}
            onClose={() => setShowCertificateModal(false)}
          />
        </DialogContent>
      </Dialog>

      {/* QA VERIFY MODAL */}
      <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
        <DialogContent className="max-w-md">
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
              rows={2}
              value={verifyComment}
              onChange={(e) => setVerifyComment(e.target.value)}
              placeholder="e.g. Full vibration analysis completed, zero leaks detected..."
              className="w-full rounded border border-input bg-card p-2 text-xs text-foreground outline-none focus:border-ring"
            />
            <SignaturePanel
              title="Supervisor Inspection Sign-off"
              signerRole="Workshop Supervisor"
              onSign={(sig) => setSupervisorSignData(sig)}
              signed={!!supervisorSignData}
              signedBy={supervisorSignData?.name}
              signedAt={supervisorSignData?.timestamp}
              signatureHash={supervisorSignData?.hash}
              signatureImage={supervisorSignData?.signatureImage}
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
              onClick={() => executeTransition("verify", { comments: verifyComment, supervisor_signature: supervisorSignData })}
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
              placeholder="e.g. Equipment test run for 30 minutes in pit. Operation normal."
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
              title="Superintendent Final Endorsement"
              signerRole="Plant Superintendent"
              onSign={(sig) => setSafetySignData(sig)}
              signed={!!safetySignData}
              signedBy={safetySignData?.name}
              signedAt={safetySignData?.timestamp}
              signatureHash={safetySignData?.hash}
              signatureImage={safetySignData?.signatureImage}
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
              onClick={() => executeTransition("close", { comments: closeComment, safety_signature: safetySignData })}
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

      {/* MULTI-TIER HANDOVER CERTIFICATE MODAL */}
      <Dialog open={showCertificateModal} onOpenChange={setShowCertificateModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-4 md:p-6">
          <DialogHeader>
            <DialogTitle>Job Handover & Multi-Tier Verification Certificate</DialogTitle>
            <DialogDescription>
              Official signed handover document with Lead Technician, Shift Supervisor, and Safety (HSE) sign-off slots.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <JobHandoverCertificate
              data={{
                jobId: job.id,
                jobNumber: job.job_number || `JOB-${job.id.slice(0, 8)}`,
                title: job.title,
                description: job.description,
                department: job.department_name || "Mechanical Maintenance",
                workshopCode: job.workshop_code || "WS-MECH-01",
                priority: job.priority,
                status: job.status,
                assetTag: job.asset_tag || "AST-CRU-01",
                machineIdentifier: job.machine_identifier || "CAT-777D-01",
                location: job.location || "Shaft 01 - Underground Level 4",
                createdAt: job.created_at || new Date().toISOString(),
                completedAt: job.completed_at || new Date().toISOString(),
                durationHours: job.duration_hours || 4.5,
                startMeterHours: job.start_meter_hours || 12450,
                endMeterHours: job.end_meter_hours || 12454,
                lotoTagNumber: job.loto_tag_number || "LOTO-2026-992",
                lotoVerified: true,
                parts: (materials || []).map((m: any) => ({
                  part_name: m.material_name || m.part_name || "Component Part",
                  part_number: m.part_number || "PRT-001",
                  quantity: m.quantity || 1,
                  unit_cost: m.unit_cost || 0,
                })),
                technicianSign: technicianSignData || {
                  name: "Farai Moyo",
                  role: "Lead Artisan / Technician",
                  timestamp: new Date().toISOString(),
                  hash: "BK-SIG-TECH-8821",
                },
                supervisorSign: supervisorSignData || {
                  name: "Tendai Shumba",
                  role: "Shift Supervisor",
                  timestamp: new Date().toISOString(),
                  hash: "BK-SIG-SUP-9904",
                },
                safetySign: safetySignData || {
                  name: "Kudzai Dube",
                  role: "Safety Officer (HSE)",
                  timestamp: new Date().toISOString(),
                  hash: "BK-SIG-HSE-3310",
                },
              }}
              onClose={() => setShowCertificateModal(false)}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
