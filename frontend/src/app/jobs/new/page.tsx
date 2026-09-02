'use client';

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { Protect } from "@/components/auth/Protect";

// Design System Components
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PriorityBadge } from "@/components/ui/status-badge";
import { NotificationBanner } from "@/components/ui/notification";
import { useConnection } from "@/lib/providers/ConnectionProvider";
import { DateTimePicker } from "@/components/ui/date-time-picker";
import { useDraftPreserver } from "@/lib/useDraftPreserver";

// Icons
import {
  ArrowLeft,
  PlusCircle,
  AlertTriangle,
  Layers,
  FileCheck2,
  Calendar,
  DollarSign,
  MapPin,
  Building,
  Wrench,
  FileText,
  Save,
  RotateCcw,
} from "lucide-react";

export default function CreateJobCard() {
  const router = useRouter();
  
  const initialDraft = {
    title: "",
    description: "",
    priority: "NORMAL",
    departmentId: "",
    jobType: "Corrective Maintenance",
    workshopCode: "WS-MECH-01",
    location: "Shaft 01 - Level 4 Underground",
    plantArea: "Primary Crushing & Comminution Section",
    reportedIssue: "",
    jobInstruction: "",
    requiredDate: "",
    estimatedHours: 4.0,
    estimatedCost: 1250.0,
    isEmergency: false,
  };

  const {
    values: draft,
    setValues: setDraft,
    hasSavedDraft,
    restoreDraft,
    clearDraft,
  } = useDraftPreserver("new_job_card", initialDraft);

  const title = draft.title;
  const description = draft.description;
  const priority = draft.priority;
  const departmentId = draft.departmentId;
  const jobType = draft.jobType;
  const workshopCode = draft.workshopCode;
  const location = draft.location;
  const plantArea = draft.plantArea;
  const reportedIssue = draft.reportedIssue;
  const jobInstruction = draft.jobInstruction;
  const requiredDate = draft.requiredDate;
  const estimatedHours = draft.estimatedHours;
  const estimatedCost = draft.estimatedCost;
  const isEmergency = draft.isEmergency ?? false;

  const setTitle = (val: string) => setDraft({ title: val });
  const setDescription = (val: string) => setDraft({ description: val });
  const setPriority = (val: string) => setDraft({ priority: val });
  const setDepartmentId = (val: string) => setDraft({ departmentId: val });
  const setJobType = (val: string) => setDraft({ jobType: val });
  const setWorkshopCode = (val: string) => setDraft({ workshopCode: val });
  const setLocation = (val: string) => setDraft({ location: val });
  const setPlantArea = (val: string) => setDraft({ plantArea: val });
  const setReportedIssue = (val: string) => setDraft({ reportedIssue: val });
  const setJobInstruction = (val: string) => setDraft({ jobInstruction: val });
  const setRequiredDate = (val: string) => setDraft({ requiredDate: val });
  const setEstimatedHours = (val: number) => setDraft({ estimatedHours: val });
  const setEstimatedCost = (val: number) => setDraft({ estimatedCost: val });
  const setIsEmergency = (val: boolean | ((prev: boolean) => boolean)) => {
    if (typeof val === 'function') {
      setDraft((prev) => ({ ...prev, isEmergency: val(prev.isEmergency ?? false) }));
    } else {
      setDraft({ isEmergency: val });
    }
  };

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { isOnline } = useConnection();

  const [departments, setDepartments] = useState<Array<{ id: string; name: string }>>([]);

  useEffect(() => {
    import('@/lib/mockData').then((m) => {
      setDepartments(m.MOCK_DEPARTMENTS);
    });
    apiFetch<Array<{ id: string; name: string }>>('/api/v1/iam/departments')
      .then((res) => {
        if (Array.isArray(res) && res.length > 0) {
          setDepartments(res);
        }
      })
      .catch(() => {});
  }, []);

  const jobTypes = [
    "Breakdown / Emergency Repair",
    "Corrective Maintenance",
    "Preventive Scheduled Maintenance",
    "Routine Servicing & Inspection",
    "Major Plant Overhaul",
    "Modification & Plant Installation",
  ];

  const workshopCodes = [
    { code: "WS-MECH-01", label: "WS-MECH-01: Main Mechanical Engineering Workshop" },
    { code: "WS-ELEC-02", label: "WS-ELEC-02: Electrical & Automation Workshop" },
    { code: "WS-PLNT-03", label: "WS-PLNT-03: Concentrator & Chemical Processing" },
    { code: "WS-FLT-04", label: "WS-FLT-04: Mobile Heavy Equipment Workshop" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setErrorMsg("Job Card title is required.");
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    let priorityVal = 1;
    if (priority === "LOW") priorityVal = 0;
    else if (priority === "NORMAL") priorityVal = 1;
    else if (priority === "HIGH") priorityVal = 2;
    else if (priority === "EMERGENCY") priorityVal = 3;

    try {
      const res = await apiFetch("/api/v1/job-cards", {
        method: "POST",
        syncable: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          priority: priorityVal,
          department_id: departmentId || (departments.length > 0 ? departments[0].id : "dept-mech"),
          job_type: jobType,
          maintenance_type: jobType,
          workshop_code: workshopCode,
          location: location.trim(),
          plant_area: plantArea.trim(),
          required_date: requiredDate ? new Date(requiredDate).toISOString() : undefined,
          reported_issue: reportedIssue.trim() || undefined,
          job_instruction: jobInstruction.trim() || undefined,
          estimated_hours: Number(estimatedHours) || 0.0,
          estimated_cost: Number(estimatedCost) || 0.0,
        }),
      });

      if (res && (res.id || res._offline)) {
        clearDraft();
        if (res._offline) {
          router.push('/jobs');
        } else {
          router.push(`/jobs/${res.id}`);
        }
      }
    } catch (e: unknown) {
      const err = e as { message?: string };
      setErrorMsg(err.message || "Failed to create Job Card. Please check connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Protect capability="job_card:create" isPageGuard moduleName="Create Job Card">
      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
        {/* HEADER BAR */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-3">
            <Link
              href="/jobs"
              className="inline-flex items-center gap-1 text-xs font-mono text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded bg-muted/40 border border-border/50"
            >
              <ArrowLeft className="size-3" />
              <span>CANCEL</span>
            </Link>
            <span className="text-border">/</span>
            <span className="text-xs font-mono font-bold text-foreground">
              NEW JOB CARD
            </span>
          </div>

          <span className="text-[11px] font-mono text-muted-foreground">
            Bikita Minerals • DWRMS Standard Form
          </span>
        </div>

        {hasSavedDraft && (
          <div className="p-3 bg-amber-950/40 border border-amber-500/40 rounded-xl text-xs font-mono text-amber-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RotateCcw className="size-4 text-amber-400" />
              <span>Unsaved job card draft detected from a previous session.</span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={restoreDraft}
                className="h-6 text-[11px] bg-amber-500 text-slate-950 hover:bg-amber-400 font-bold border-none"
              >
                Restore Draft
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={clearDraft}
                className="h-6 text-[11px] text-slate-400 hover:text-white"
              >
                Discard
              </Button>
            </div>
          </div>
        )}

        {errorMsg && (
          <NotificationBanner
            type="error"
            title="Validation / Creation Error"
            message={errorMsg}
            dismissible
            onDismiss={() => setErrorMsg(null)}
          />
        )}

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>
                <PlusCircle className="size-4 text-primary" />
                <span>Initiate Digital Job Card Lifecycle</span>
              </CardTitle>
              <span className="text-[10px] font-mono text-muted-foreground uppercase">
                Stage 01: Job Request & Technical Specifications
              </span>
            </CardHeader>

            <CardContent className="space-y-5 pt-4">
              {/* Job Title & Summary */}
              <div>
                <label className="text-[11px] font-mono uppercase text-foreground font-semibold block mb-1">
                  Job Card Title / Breakdown Summary *
                </label>
                <Input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Replace Worn Jaw Plates and Adjust Toggle on Primary Crusher 01"
                  className="font-medium text-sm"
                />
              </div>

              {/* SECTION: CLASSIFICATION & WORKSHOP */}
              <div className="rounded border border-border/60 bg-muted/10 p-3.5 space-y-3">
                <div className="text-[11px] font-mono font-bold text-foreground flex items-center gap-1.5 uppercase">
                  <Wrench className="size-3.5 text-primary" />
                  <span>1. Job Classification & Workshop Assignment</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Job / Maintenance Type *
                    </label>
                    <select
                      value={jobType}
                      onChange={(e) => setJobType(e.target.value)}
                      className="h-8 w-full rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground transition-all outline-none focus:border-ring"
                    >
                      {jobTypes.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Target Workshop Code *
                    </label>
                    <select
                      value={workshopCode}
                      onChange={(e) => setWorkshopCode(e.target.value)}
                      className="h-8 w-full rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground font-mono transition-all outline-none focus:border-ring"
                    >
                      {workshopCodes.map((w) => (
                        <option key={w.code} value={w.code}>
                          {w.code}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Responsible Department *
                    </label>
                    <select
                      value={departmentId}
                      onChange={(e) => setDepartmentId(e.target.value)}
                      className="h-8 w-full rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground transition-all outline-none focus:border-ring"
                    >
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Location / Mine Section
                    </label>
                    <Input
                      prefixIcon={<MapPin className="size-3.5" />}
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. Shaft 01 Underground - Level 4"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Plant / Process Area
                    </label>
                    <Input
                      prefixIcon={<Building className="size-3.5" />}
                      value={plantArea}
                      onChange={(e) => setPlantArea(e.target.value)}
                      placeholder="e.g. Primary Crushing & Comminution Section"
                    />
                  </div>
                </div>
              </div>

              {/* SECTION: PRIORITY & TARGET SCHEDULE */}
              <div className="rounded border border-border/60 bg-muted/10 p-3.5 space-y-3">
                <div className="text-[11px] font-mono font-bold text-foreground flex items-center gap-1.5 uppercase">
                  <Calendar className="size-3.5 text-amber-500" />
                  <span>2. Priority & Target Schedule</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Operational Priority
                    </label>
                    <div className="flex items-center gap-2">
                      <select
                        value={priority}
                        onChange={(e) => {
                          setPriority(e.target.value);
                          setIsEmergency(e.target.value === "EMERGENCY");
                        }}
                        className="h-8 flex-1 rounded border border-input bg-card px-2.5 py-1 text-xs text-foreground transition-all outline-none focus:border-ring font-mono"
                      >
                        <option value="LOW">Low (Routine / Next Shift)</option>
                        <option value="NORMAL">Normal (Standard Shift)</option>
                        <option value="HIGH">High (Production Bottleneck)</option>
                        <option value="EMERGENCY">Emergency (Plant Stoppage)</option>
                      </select>
                      <PriorityBadge priority={priority} size="sm" showDot={false} />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                      Required Completion Date
                    </label>
                    <DateTimePicker
                      value={requiredDate}
                      onChange={setRequiredDate}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                        Est. Hours
                      </label>
                      <Input
                        mono
                        type="number"
                        step="0.5"
                        value={estimatedHours}
                        onChange={(e) => setEstimatedHours(parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                        Est. Cost
                      </label>
                      <Input
                        mono
                        type="number"
                        prefixIcon={<DollarSign className="size-3" />}
                        value={estimatedCost}
                        onChange={(e) => setEstimatedCost(parseFloat(e.target.value) || 0)}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* SECTION: PROBLEM & SCOPE SPECIFICATIONS */}
              <div className="rounded border border-border/60 bg-muted/10 p-3.5 space-y-3">
                <div className="text-[11px] font-mono font-bold text-foreground flex items-center gap-1.5 uppercase">
                  <FileText className="size-3.5 text-cyan-500" />
                  <span>3. Problem Description & Maintenance Instructions</span>
                </div>

                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Observed Symptom / Reported Issue
                  </label>
                  <Input
                    value={reportedIssue}
                    onChange={(e) => setReportedIssue(e.target.value)}
                    placeholder="e.g. Excessive mechanical vibration, hydraulic pressure drop, abnormal bearing noise"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Specific Job Instructions for Maintenance Crew
                  </label>
                  <textarea
                    rows={2}
                    value={jobInstruction}
                    onChange={(e) => setJobInstruction(e.target.value)}
                    placeholder="e.g. Lockout/Tagout breaker CB-04. Inspect eccentric shaft bearings. Replace toggle seat if worn > 3mm."
                    className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring leading-relaxed font-sans"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                    Detailed Scope Narrative *
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe equipment condition, suspected root cause, safety precautions, and requested spare parts..."
                    className="w-full rounded border border-input bg-card p-2.5 text-xs text-foreground outline-none focus:border-ring leading-relaxed font-sans"
                  />
                </div>
              </div>

              {/* Safety & Emergency Notice */}
              {isEmergency ? (
                <div className="rounded border border-red-500/40 bg-red-500/10 p-3 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="size-4 text-red-500 shrink-0 mt-0.5" />
                  <div className="text-[11px] text-red-900 dark:text-red-200">
                    <strong>CRITICAL EMERGENCY ALERT:</strong> Marking this job card as EMERGENCY will notify the plant superintendent and shift maintenance engineers immediately.
                  </div>
                </div>
              ) : (
                <div className="rounded border border-border/70 bg-muted/20 p-3 text-xs flex items-start gap-2.5 text-muted-foreground">
                  <Layers className="size-4 shrink-0 mt-0.5 text-primary" />
                  <div className="text-[11px] leading-relaxed">
                    Upon creation, this Job Card will be registered in <strong>DRAFT</strong> status. You can review and adjust specifications before submitting for supervisor authorization.
                  </div>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex justify-end gap-2.5">
              <Link href="/jobs">
                <Button type="button" variant="outline" size="sm">
                  Cancel
                </Button>
              </Link>
              <Button
                type="submit"
                variant={isOnline ? "default" : "secondary"}
                size="sm"
                loading={loading}
                hotkey="Ctrl+Enter"
              >
                <FileCheck2 className="size-3.5 mr-1" />
                {isOnline ? "Create Job Card" : "Save Offline Draft"}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>
    </Protect>
  );
}
