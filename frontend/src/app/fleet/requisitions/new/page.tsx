'use client';

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { Protect } from "@/components/auth/Protect";
import { useDraftPreserver } from "@/lib/useDraftPreserver";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

export default function NewRequisition() {
  const router = useRouter();

  const initialDraft = {
    machineTypeId: "",
    startTime: "",
    endTime: "",
    jobCardId: "",
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

  const setMachineTypeId = (val: string) => setDraft({ machineTypeId: val });
  const setStartTime = (val: string) => setDraft({ startTime: val });
  const setEndTime = (val: string) => setDraft({ endTime: val });
  const setJobCardId = (val: string) => setDraft({ jobCardId: val });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      if (!startTime || !endTime) {
        alert("Please select both start and end times.");
        setIsSubmitting(false);
        return;
      }

      const start = new Date(startTime);
      const end = new Date(endTime);
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        alert("Invalid date format.");
        setIsSubmitting(false);
        return;
      }
      if (end <= start) {
        alert("End time must be after start time.");
        setIsSubmitting(false);
        return;
      }

      const payload = {
        machine_type_id: machineTypeId || "00000000-0000-0000-0000-000000000000",
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        job_card_id: jobCardId ? jobCardId : null,
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
      alert(err.message || "Network Error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Protect capability="requisition:create">
      <div className="max-w-2xl mx-auto p-4 md:p-8 space-y-4">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/fleet" className="text-slate-500 hover:text-slate-800 text-sm font-mono">&larr; Back to Fleet</Link>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Request Equipment Requisition</h1>
        </div>

        {hasSavedDraft && (
          <div className="p-3 bg-amber-950/40 border border-amber-500/40 rounded-xl text-xs font-mono text-amber-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RotateCcw className="size-4 text-amber-400" />
              <span>Unsaved requisition draft detected.</span>
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
        
        <form onSubmit={handleSubmit} className="bg-card p-6 rounded-lg shadow border border-border space-y-4">
          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Machine Type ID</label>
            <input 
              type="text" 
              value={machineTypeId}
              onChange={e => setMachineTypeId(e.target.value)}
              className="w-full bg-background border border-input rounded px-3 py-2 text-sm text-foreground"
              placeholder="UUID of requested type"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Job Card ID (Optional)</label>
            <input 
              type="text" 
              value={jobCardId}
              onChange={e => setJobCardId(e.target.value)}
              className="w-full bg-background border border-input rounded px-3 py-2 text-sm text-foreground"
              placeholder="Associated Job Card UUID (Optional)"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Required Start Time</label>
              <input 
                type="datetime-local" 
                value={startTime}
                onChange={e => setStartTime(e.target.value)}
                className="w-full bg-background border border-input rounded px-3 py-2 text-sm text-foreground"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Required End Time</label>
              <input 
                type="datetime-local" 
                value={endTime}
                onChange={e => setEndTime(e.target.value)}
                className="w-full bg-background border border-input rounded px-3 py-2 text-sm text-foreground"
                required
              />
            </div>
          </div>

          <div className="pt-2">
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold py-2 px-4 rounded text-sm disabled:opacity-50 transition"
            >
              {isSubmitting ? "Submitting Request..." : "Submit Requisition"}
            </button>
          </div>
        </form>
      </div>
    </Protect>
  );
}
