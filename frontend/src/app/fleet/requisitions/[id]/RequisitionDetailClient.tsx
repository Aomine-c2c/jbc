'use client';

import React, { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { ArrowLeft, Truck, CheckCircle2, AlertCircle, FileText } from "lucide-react";

interface Requisition {
  id: string;
  requisition_number?: string;
  status: string;
  machine_type_id: string;
  machine_type_name?: string;
  machine_id?: string;
  machine_identifier?: string;
  purpose?: string;
  start_time: string;
  end_time: string;
  job_card_id?: string;
  start_hours?: number;
  end_hours?: number;
}

interface MachineOption {
  id: string;
  identifier: string;
  machine_type_name?: string;
  status: string;
  serial_number?: string;
}

export default function RequisitionDetailClient({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [req, setReq] = useState<Requisition | null>(null);
  const [machines, setMachines] = useState<MachineOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Form states for execution
  const [machineId, setMachineId] = useState("");
  const [startHours, setStartHours] = useState("");
  const [endHours, setEndHours] = useState("");
  const [executing, setExecuting] = useState(false);

  const fetchReq = useCallback(async () => {
    try {
      const res = await apiFetch<Requisition>(`/api/v1/fleet/requisitions/${id}`);
      if (res) {
        setReq(res);
      }
    } catch (e) {
      console.error("Failed to load requisition", e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchReq();
    
    // Also fetch machines for allocation
    apiFetch<MachineOption[]>('/api/v1/fleet/machines')
      .then((data) => {
        if (data && Array.isArray(data)) {
          setMachines(data);
          if (data.length > 0) {
            const available = data.find(m => m.status === 'AVAILABLE');
            const defaultId = available ? available.id : data[0].id;
            setMachineId(prev => prev || defaultId);
          }
        }
      })
      .catch(console.error);
  }, [fetchReq]);

  const handleAction = async (action: string, payload: Record<string, unknown> = {}) => {
    setActionError(null);
    setActionSuccess(null);
    setExecuting(true);
    try {
      const res = await apiFetch(`/api/v1/fleet/requisitions/${id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res !== undefined) {
        setActionSuccess(`Action '${action}' executed successfully.`);
        await fetchReq();
      }
    } catch (e: unknown) {
      console.error(e);
      const err = e as { message?: string };
      setActionError(err.message || `Failed to execute ${action}`);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-5xl mx-auto text-xs font-mono text-muted-foreground animate-pulse">
        Acquiring equipment requisition record...
      </div>
    );
  }

  if (!req) {
    return (
      <div className="p-8 max-w-5xl mx-auto space-y-4">
        <Link href="/fleet" className="text-xs font-mono text-muted-foreground hover:text-foreground flex items-center gap-1">
          <ArrowLeft className="size-3.5" /> Back to Fleet & Requisitions
        </Link>
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground text-xs font-mono">
            Requisition not found.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <Protect capability="fleet:view" isPageGuard moduleName="Fleet Requisition Details">
      <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-3 mb-1.5">
            <Link 
              href="/fleet" 
              className="text-xs font-mono text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="size-3.5" /> Back to Fleet
            </Link>
            <StatusBadge status={req.status} size="sm" />
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-foreground">
            Equipment Requisition {req.requisition_number ? `(${req.requisition_number})` : ''}
          </h1>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Resource UUID: <span className="text-foreground">{req.id}</span>
          </p>
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive flex items-center gap-2">
          <AlertCircle className="size-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
          <CheckCircle2 className="size-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Details Card */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                <FileText className="size-4 text-primary" />
                Requisition Parameters & Details
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Machine Type ID:</span>
                  <span className="font-mono text-foreground font-semibold">
                    {req.machine_type_name || req.machine_type_id}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Allocated Machine:</span>
                  <span className="font-mono text-foreground font-semibold">
                    {req.machine_identifier || (req.machine_id ? req.machine_id.slice(0, 8) : 'Not Allocated Yet')}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Required Start Time:</span>
                  <span className="font-mono text-foreground font-semibold">
                    {new Date(req.start_time).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Required End Time:</span>
                  <span className="font-mono text-foreground font-semibold">
                    {new Date(req.end_time).toLocaleString()}
                  </span>
                </div>
              </div>

              {req.purpose && (
                <div className="pt-3 border-t border-border/50">
                  <span className="text-muted-foreground block text-[11px]">Purpose / Scope:</span>
                  <p className="text-foreground mt-0.5">{req.purpose}</p>
                </div>
              )}

              {req.job_card_id && (
                <div className="pt-3 border-t border-border/50 flex items-center justify-between">
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Linked Maintenance Job Card:</span>
                    <span className="font-mono text-foreground font-bold">{req.job_card_id}</span>
                  </div>
                  <Link href={`/jobs/${req.job_card_id}`}>
                    <Button variant="outline" size="xs">
                      Open Job Card
                    </Button>
                  </Link>
                </div>
              )}

              {(req.start_hours !== undefined || req.end_hours !== undefined) && (
                <div className="pt-3 border-t border-border/50 grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Dispatch Meter Hours:</span>
                    <span className="font-mono text-foreground font-semibold">{req.start_hours ?? '—'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Return Meter Hours:</span>
                    <span className="font-mono text-foreground font-semibold">{req.end_hours ?? '—'}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Dynamic Action Panel based on Workflow State */}
        <div>
          <Card>
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                <Truck className="size-4 text-primary" />
                Workflow Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {req.status === "DRAFT" && (
                <Protect capability="requisition:submit">
                  <Button 
                    onClick={() => handleAction('submit')} 
                    disabled={executing}
                    className="w-full"
                    size="sm"
                  >
                    Submit for Approval
                  </Button>
                </Protect>
              )}

              {req.status === "SUBMITTED" && (
                <Protect capability="requisition:review">
                  <div className="space-y-2">
                    <Button 
                      onClick={() => handleAction('review', { comments: "Reviewed by supervisor" })} 
                      disabled={executing}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                      size="sm"
                    >
                      Review & Forward
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => handleAction('return-for-correction', { correction_reason: "Needs adjustment" })} 
                      disabled={executing}
                      className="w-full text-amber-600 dark:text-amber-400"
                      size="sm"
                    >
                      Return for Correction
                    </Button>
                    <Button 
                      variant="destructive"
                      onClick={() => handleAction('reject', { comments: "Requisition rejected" })} 
                      disabled={executing}
                      className="w-full"
                      size="sm"
                    >
                      Reject Request
                    </Button>
                  </div>
                </Protect>
              )}

              {(req.status === "REVIEWED" || req.status === "RETURNED_FOR_CORRECTION") && (
                <Protect capability="requisition:approve">
                  <div className="space-y-2">
                    <Button 
                      onClick={() => handleAction('approve', { comments: "Approved by manager" })} 
                      disabled={executing}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                      size="sm"
                    >
                      Authorize & Approve
                    </Button>
                    <Button 
                      variant="destructive"
                      onClick={() => handleAction('reject', { comments: "Rejected" })} 
                      disabled={executing}
                      className="w-full"
                      size="sm"
                    >
                      Reject
                    </Button>
                  </div>
                </Protect>
              )}

              {req.status === "AWAITING_ALLOCATION" && (
                <Protect capability="requisition:allocate">
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-foreground">Select Equipment Asset:</label>
                      <select
                        value={machineId}
                        onChange={(e) => setMachineId(e.target.value)}
                        className="w-full bg-background border border-input rounded-md px-2.5 py-1.5 text-xs text-foreground font-mono"
                      >
                        {machines.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.identifier} — {m.status}
                          </option>
                        ))}
                      </select>
                    </div>

                    <Button 
                      onClick={() => handleAction('allocate', { machine_id: machineId || "" })} 
                      disabled={executing || !machineId}
                      className="w-full"
                      size="sm"
                    >
                      Allocate Machine
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => handleAction('allocate-partial', { machine_id: machineId || "" })} 
                      disabled={executing}
                      className="w-full text-xs"
                      size="sm"
                    >
                      Allocate Partially
                    </Button>
                    <Button 
                      variant="destructive"
                      onClick={() => handleAction('mark-unavailable', { reason: "Equipment currently offline" })} 
                      disabled={executing}
                      className="w-full text-xs"
                      size="sm"
                    >
                      Mark Unavailable
                    </Button>
                  </div>
                </Protect>
              )}

              {(req.status === "ALLOCATED" || req.status === "PARTIALLY_ALLOCATED") && (
                <Protect capability="requisition:dispatch">
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-foreground">Initial Meter Hours (Start):</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 1500" 
                        className="w-full border border-input rounded-md px-2.5 py-1.5 text-xs font-mono bg-background text-foreground"
                        value={startHours}
                        onChange={(e) => setStartHours(e.target.value)}
                      />
                    </div>
                    <Button 
                      onClick={() => handleAction('start-use', { start_hours: parseInt(startHours) || 0 })} 
                      disabled={executing}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                      size="sm"
                    >
                      Confirm Dispatch & Start Use
                    </Button>
                  </div>
                </Protect>
              )}

              {req.status === "IN_USE" && (
                <Protect capability="requisition:return">
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-foreground">Ending Meter Hours (Return):</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 1512" 
                        className="w-full border border-input rounded-md px-2.5 py-1.5 text-xs font-mono bg-background text-foreground"
                        value={endHours}
                        onChange={(e) => setEndHours(e.target.value)}
                      />
                    </div>
                    <Button 
                      onClick={() => handleAction('return', { end_hours: parseInt(endHours) || 0, return_notes: "Returned to depot" })} 
                      disabled={executing}
                      className="w-full"
                      size="sm"
                    >
                      Return Equipment to Depot
                    </Button>
                  </div>
                </Protect>
              )}

              {req.status === "RETURNED" && (
                <Protect capability="requisition:close">
                  <Button 
                    onClick={() => handleAction('close', { close_notes: "Requisition completed" })} 
                    disabled={executing}
                    className="w-full"
                    size="sm"
                  >
                    Close Requisition Record
                  </Button>
                </Protect>
              )}

              {(req.status === "CLOSED" || req.status === "REJECTED" || req.status === "CANCELLED") && (
                <div className="p-3 bg-muted/40 rounded-lg text-center text-xs font-mono text-muted-foreground">
                  Requisition is in terminal state ({req.status}).
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      </div>
    </Protect>
  );
}
