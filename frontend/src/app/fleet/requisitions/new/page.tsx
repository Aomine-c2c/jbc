'use client';

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { Protect } from "@/components/auth/Protect";
import { useDraftPreserver } from "@/lib/useDraftPreserver";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { RotateCcw, Truck, ArrowLeft, Calendar, FileText, AlertCircle } from "lucide-react";

interface MachineTypeOption {
  id: string;
  name: string;
  category?: string;
  description?: string;
}

interface JobCardOption {
  id: string;
  job_number?: string;
  title: string;
  status: string;
}

export default function NewRequisition() {
  const router = useRouter();
  const [machineTypes, setMachineTypes] = useState<MachineTypeOption[]>([]);
  const [jobCards, setJobCards] = useState<JobCardOption[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const initialDraft = {
    machineTypeId: "",
    startTime: "",
    endTime: "",
    jobCardId: "",
    purpose: "",
  };

  const {
    values: draft,
    setValues: setDraft,
    hasSavedDraft,
    restoreDraft,
    clearDraft,
  } = useDraftPreserver("new_requisition", initialDraft);

  const machineTypeId = draft.machineTypeId;
  const startTime = draft.startTime;
  const endTime = draft.endTime;
  const jobCardId = draft.jobCardId;
  const purpose = draft.purpose;

  const setMachineTypeId = (val: string) => setDraft({ machineTypeId: val });
  const setStartTime = (val: string) => setDraft({ startTime: val });
  const setEndTime = (val: string) => setDraft({ endTime: val });
  const setJobCardId = (val: string) => setDraft({ jobCardId: val });
  const setPurpose = (val: string) => setDraft({ purpose: val });

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadFormOptions() {
      try {
        const [typesRes, jobsRes] = await Promise.allSettled([
          apiFetch<MachineTypeOption[]>("/api/v1/fleet/machine-types"),
          apiFetch<JobCardOption[]>("/api/v1/job-cards"),
        ]);

        if (mounted) {
          if (typesRes.status === "fulfilled" && Array.isArray(typesRes.value)) {
            setMachineTypes(typesRes.value);
            if (typesRes.value.length > 0) {
              setDraft((prev) => (!prev.machineTypeId ? { ...prev, machineTypeId: typesRes.value[0].id } : prev));
            }
          }
          if (jobsRes.status === "fulfilled" && Array.isArray(jobsRes.value)) {
            setJobCards(jobsRes.value.filter(j => j.status !== 'CLOSED' && j.status !== 'CANCELLED'));
          }
        }
      } catch (err) {
        console.error("Failed to load requisition form options:", err);
      } finally {
        if (mounted) setLoadingOptions(false);
      }
    }
    loadFormOptions();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    
    try {
      if (!startTime || !endTime) {
        setFormError("Please select both start and end times.");
        setIsSubmitting(false);
        return;
      }

      const start = new Date(startTime);
      const end = new Date(endTime);
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        setFormError("Invalid date/time format.");
        setIsSubmitting(false);
        return;
      }
      if (end <= start) {
        setFormError("End time must be after start time.");
        setIsSubmitting(false);
        return;
      }

      const payload = {
        machine_type_id: machineTypeId || (machineTypes[0]?.id ?? "00000000-0000-0000-0000-000000000000"),
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        job_card_id: jobCardId ? jobCardId : null,
        purpose: purpose.trim() || undefined,
      };

      const res = await apiFetch("/api/v1/fleet/requisitions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (res) {
        clearDraft();
        router.push(`/fleet/requisitions/${res.id}`);
      }
    } catch (e: unknown) {
      console.error(e);
      const err = e as { message?: string };
      setFormError(err.message || "Failed to submit requisition request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Protect capability="requisition:create" isPageGuard moduleName="Machine Requisition Request">
      <div className="max-w-2xl mx-auto p-4 md:p-8 space-y-5">
        <div className="flex items-center justify-between">
          <Link 
            href="/fleet" 
            className="text-xs font-mono text-muted-foreground hover:text-foreground flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="size-3.5" /> Back to Fleet & Requisitions
          </Link>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <Truck className="size-5 text-primary" />
            <h1 className="text-xl md:text-2xl font-bold text-foreground">
              Request Heavy Equipment Requisition
            </h1>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Bikita Minerals • Mining Fleet & Machinery Reservation Hub
          </p>
        </div>

        {hasSavedDraft && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs font-mono text-amber-600 dark:text-amber-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RotateCcw className="size-4 text-amber-500" />
              <span>Unsaved requisition draft detected.</span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="xs"
                variant="default"
                onClick={restoreDraft}
                className="h-6 text-[11px] font-bold"
              >
                Restore
              </Button>
              <Button
                type="button"
                size="xs"
                variant="ghost"
                onClick={clearDraft}
                className="h-6 text-[11px]"
              >
                Discard
              </Button>
            </div>
          </div>
        )}

        {formError && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="size-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}
        
        <Card>
          <CardHeader className="pb-3 border-b border-border">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
              <FileText className="size-4 text-primary" />
              Requisition Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Required Machine Type <span className="text-destructive">*</span>
                </label>
                {loadingOptions ? (
                  <div className="h-9 w-full bg-muted animate-pulse rounded-md" />
                ) : (
                  <select
                    value={machineTypeId}
                    onChange={(e) => setMachineTypeId(e.target.value)}
                    className="w-full bg-background border border-input rounded-md px-3 py-2 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  >
                    {machineTypes.length === 0 ? (
                      <option value="00000000-0000-0000-0000-000000000000">General Machinery / Excavator</option>
                    ) : (
                      machineTypes.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name} {t.category ? `(${t.category})` : ''}
                        </option>
                      ))
                    )}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Associated Job Card (Optional)
                </label>
                <select
                  value={jobCardId}
                  onChange={(e) => setJobCardId(e.target.value)}
                  className="w-full bg-background border border-input rounded-md px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                >
                  <option value="">-- No Direct Job Card Link --</option>
                  {jobCards.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.job_number || `JC-${j.id.slice(0, 8).toUpperCase()}`} — {j.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Purpose / Operation Scope
                </label>
                <input 
                  type="text" 
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full bg-background border border-input rounded-md px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="e.g. Pit 4 Spodumene bench haulage & loading"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5 flex items-center gap-1">
                    <Calendar className="size-3.5 text-muted-foreground" />
                    Required Start Time <span className="text-destructive">*</span>
                  </label>
                  <input 
                    type="datetime-local" 
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full bg-background border border-input rounded-md px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5 flex items-center gap-1">
                    <Calendar className="size-3.5 text-muted-foreground" />
                    Required End Time <span className="text-destructive">*</span>
                  </label>
                  <input 
                    type="datetime-local" 
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full bg-background border border-input rounded-md px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-border flex justify-end gap-2">
                <Link href="/fleet">
                  <Button type="button" variant="outline" size="sm">
                    Cancel
                  </Button>
                </Link>
                <Button 
                  type="submit" 
                  size="sm"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Submitting Requisition..." : "Submit Requisition"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </Protect>
  );
}
