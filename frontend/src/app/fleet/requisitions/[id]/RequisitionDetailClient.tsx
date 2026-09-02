'use client'

import React, { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";

interface Requisition {
  id: string;
  status: string;
  machine_type_id: string;
  start_time: string;
  end_time: string;
  job_card_id?: string;
}

export default function RequisitionDetailClient({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [req, setReq] = useState<Requisition | null>(null);
  const [loading, setLoading] = useState(true);

  // Form states for execution
  const [machineId, setMachineId] = useState("");
  const [startHours, setStartHours] = useState("");
  const [endHours, setEndHours] = useState("");

  const fetchReq = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/v1/fleet/requisitions/${id}`);
      if (res) {
        setReq(res);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchReq();
  }, [fetchReq]);

  const handleAction = async (action: string, payload: Record<string, unknown> = {}) => {
    try {
      const res = await apiFetch(`/api/v1/fleet/requisitions/${id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res !== undefined) {
        await fetchReq(); // Refresh state
      }
    } catch (e: unknown) {
      console.error(e);
      const err = e as { message?: string };
      alert(err.message || "Network error");
    }
  };

  if (loading) return <div className="p-8 text-muted-foreground">Loading requisition...</div>;
  if (!req) return <div className="p-8 text-muted-foreground">Requisition not found.</div>;

  return (
    <div className="max-w-5xl mx-auto p-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <Link href="/fleet" className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">&larr; Back to Fleet</Link>
            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 text-sm font-semibold rounded-full">
              {req.status.replace("_", " ")}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-foreground">Equipment Requisition</h1>
        </div>
        
        {/* Dynamic Action Panel based on Workflow State */}
        <div className="flex flex-col gap-2 bg-card p-4 rounded-lg border border-border shadow-xs min-w-[300px]">
          {req.status === "DRAFT" && (
            <Protect capability="requisition:submit">
              <button onClick={() => handleAction('submit')} className="btn-primary">Submit for Approval</button>
            </Protect>
          )}

          {req.status === "SUBMITTED" && (
            <Protect capability="requisition:review">
              <div className="flex flex-col gap-2">
                <button onClick={() => handleAction('review', { comments: "" })} className="btn-success">Review</button>
                <button onClick={() => handleAction('return-for-correction', { correction_reason: "" })} className="btn-warning">Return for Correction</button>
                <button onClick={() => handleAction('reject', { comments: "" })} className="btn-danger">Reject</button>
              </div>
            </Protect>
          )}

          {(req.status === "REVIEWED" || req.status === "RETURNED_FOR_CORRECTION") && (
            <Protect capability="requisition:approve">
              <div className="flex gap-2">
                <button onClick={() => handleAction('approve', { comments: "" })} className="btn-success flex-1">Approve</button>
                <button onClick={() => handleAction('reject', { comments: "" })} className="btn-danger flex-1">Reject</button>
              </div>
            </Protect>
          )}

          {req.status === "AWAITING_ALLOCATION" && (
            <Protect capability="requisition:allocate">
              <div className="flex flex-col gap-2">
                <input 
                  type="text" 
                  placeholder="Allocate Machine UUID..." 
                  className="border border-input rounded px-2 py-1 text-sm bg-background text-foreground"
                  value={machineId}
                  onChange={(e) => setMachineId(e.target.value)}
                />
                <button 
                  onClick={() => handleAction('allocate', { machine_id: machineId || "" })} 
                  className="btn-primary"
                >
                  Allocate Machine
                </button>
                <button 
                  onClick={() => handleAction('allocate-partial', { machine_id: machineId || "" })} 
                  className="btn-warning"
                >
                  Allocate Partially
                </button>
                <button 
                  onClick={() => handleAction('mark-unavailable', { reason: "" })} 
                  className="btn-danger"
                >
                  Mark Unavailable
                </button>
              </div>
            </Protect>
          )}

          {(req.status === "ALLOCATED" || req.status === "PARTIALLY_ALLOCATED") && (
            <Protect capability="requisition:dispatch">
              <div className="flex flex-col gap-2">
                <input 
                  type="number" 
                  placeholder="Start Hours (e.g. 1500)" 
                  className="border border-input rounded px-2 py-1 text-sm bg-background text-foreground"
                  value={startHours}
                  onChange={(e) => setStartHours(e.target.value)}
                />
                <button 
                  onClick={() => handleAction('start-use', { start_hours: parseInt(startHours) || 0 })} 
                  className="btn-success"
                >
                  Start Use (Confirm Received)
                </button>
              </div>
            </Protect>
          )}

          {req.status === "IN_USE" && (
            <Protect capability="requisition:return">
              <div className="flex flex-col gap-2">
                <input 
                  type="number" 
                  placeholder="End Hours (e.g. 1510)" 
                  className="border border-input rounded px-2 py-1 text-sm bg-background text-foreground"
                  value={endHours}
                  onChange={(e) => setEndHours(e.target.value)}
                />
                <button 
                  onClick={() => handleAction('return', { end_hours: parseInt(endHours) || 0, return_notes: "" })} 
                  className="btn-warning"
                >
                  Return Equipment
                </button>
              </div>
            </Protect>
          )}

          {req.status === "RETURNED" && (
            <Protect capability="requisition:close">
              <button onClick={() => handleAction('close', { close_notes: "" })} className="btn-primary">Close Requisition</button>
            </Protect>
          )}
        </div>
      </div>

      {/* Details Card */}
      <div className="bg-card shadow-xs rounded-lg border border-border p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 border-b border-border pb-2 text-foreground">Requisition Details</h2>
        <div className="grid grid-cols-2 gap-4 text-foreground">
          <div><strong>Requisition ID:</strong> <span className="font-mono">{req.id}</span></div>
          <div><strong>Machine Type:</strong> <span className="font-mono">{req.machine_type_id}</span></div>
          <div><strong>Start Time:</strong> {new Date(req.start_time).toLocaleString()}</div>
          <div><strong>End Time:</strong> {new Date(req.end_time).toLocaleString()}</div>
          {req.job_card_id && (
            <div className="col-span-2">
              <strong>Linked Job Card:</strong> 
              <Link href={`/jobs/${req.job_card_id}`} className="text-primary hover:underline ml-2 font-mono">
                {req.job_card_id}
              </Link>
            </div>
          )}
        </div>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        .btn-primary { background-color: #ea580c; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s; cursor: pointer; }
        .btn-primary:hover { background-color: #c2410c; }
        .btn-success { background-color: #22c55e; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s; cursor: pointer; }
        .btn-success:hover { background-color: #16a34a; }
        .btn-danger { background-color: #ef4444; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s; cursor: pointer; }
        .btn-danger:hover { background-color: #dc2626; }
        .btn-warning { background-color: #eab308; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s; cursor: pointer; }
        .btn-warning:hover { background-color: #ca8a04; }
      `}} />
    </div>
  );
}
