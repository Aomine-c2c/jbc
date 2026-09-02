'use client';

import React, { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Protect } from "@/components/auth/Protect";
import { getPendingApprovals, ApprovalInboxItem } from "@/lib/approvals";

function formatDistanceToNow(date: Date, options?: { addSuffix?: boolean }): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  let text = "";
  if (diffDays > 0) {
    text = `${diffDays} day${diffDays > 1 ? "s" : ""}`;
  } else if (diffHours > 0) {
    text = `${diffHours} hour${diffHours > 1 ? "s" : ""}`;
  } else if (diffMins > 0) {
    text = `${diffMins} min${diffMins > 1 ? "s" : ""}`;
  } else {
    return "just now";
  }
  return options?.addSuffix ? `${text} ago` : text;
}

import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { TelemetrySpinner } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import {
  ShieldCheck,
  Clock,
  ArrowRight,
  User,
  Building2,
  AlertTriangle,
  CheckCircle,
  Zap,
} from "lucide-react";

export default function ApprovalsInboxPage() {
  const router = useRouter();
  const [items, setItems] = useState<ApprovalInboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPendingApprovals();
      setItems(data);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || "Failed to load pending approvals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();

    const handleLiveEvent = (e: Event) => {
      const customEvent = e as CustomEvent;
      const type = customEvent.detail?.type || '';
      if (type.startsWith('approval.') || type.startsWith('sla.')) {
        load();
      }
    };

    window.addEventListener('dwrms-live-event', handleLiveEvent);
    return () => {
      window.removeEventListener('dwrms-live-event', handleLiveEvent);
    };
  }, [load]);

  const handleRowClick = (resourceType: string, resourceId: string) => {
    if (resourceType === "job_card") {
      router.push(`/jobs/${resourceId}`);
    } else {
      router.push(`/fleet/requisitions/${resourceId}`);
    }
  };

  return (
    <Protect capability="approvals:view" isPageGuard moduleName="Approvals Inbox">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-4 md:space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="size-5 md:size-6 text-primary" />
              Approvals Inbox
            </h1>
            <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Review and authorize pending operational requests assigned to your role.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setLoading(true);
                getPendingApprovals()
                  .then(setItems)
                  .catch((err) => setError(err.message))
                  .finally(() => setLoading(false));
              }}
            >
              <Clock className="size-4 mr-1.5" />
              Refresh
            </Button>
          </div>
        </div>

        {error ? (
          <ErrorState title="Failed to load inbox" message={error} />
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-card rounded-lg border border-border">
            <TelemetrySpinner message="Loading your pending approvals..." />
          </div>
        ) : items.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16 md:py-20 text-center">
              <div className="size-14 md:size-16 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4">
                <CheckCircle className="size-7 md:size-8 text-emerald-500" />
              </div>
              <h3 className="text-base md:text-lg font-medium text-foreground">You&apos;re all caught up!</h3>
              <p className="text-xs md:text-sm text-muted-foreground mt-1 max-w-sm">
                There are no pending approval requests requiring your authorization at this time.
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* MOBILE APPROVAL CARDS (Visible only on < md screens) */}
            <div className="md:hidden space-y-3">
              {items.map((item) => {
                const isEmergency = item.approval_request.workflow_type === "EMERGENCY";
                const isCapex = item.approval_request.workflow_type === "CAPEX";

                return (
                  <div
                    key={item.pending_step.id}
                    onClick={() => handleRowClick(item.approval_request.resource_type, item.approval_request.resource_id)}
                    className={`p-4 bg-card border rounded-xl shadow-xs transition-all cursor-pointer space-y-3 active:scale-[0.99] ${
                      isEmergency
                        ? 'border-red-500/50 bg-red-500/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <StatusBadge
                          status={item.approval_request.resource_type === 'job_card' ? 'Job Card' : 'Requisition'}
                          size="sm"
                        />
                        {isEmergency && (
                          <span className="text-[10px] uppercase font-bold text-red-500 bg-red-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                            <Zap className="size-3" /> Emergency
                          </span>
                        )}
                        {isCapex && (
                          <span className="text-[10px] uppercase font-bold text-purple-500 bg-purple-500/10 px-2 py-0.5 rounded">
                            Capex
                          </span>
                        )}
                      </div>
                      <PriorityBadge priority={item.approval_request.priority} size="sm" />
                    </div>

                    <div>
                      <h3 className="font-bold text-sm text-foreground leading-tight">
                        {item.resource_title || "Untitled Request"}
                      </h3>
                      {item.resource_description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                          {item.resource_description}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground pt-2 border-t border-border/50">
                      <div className="flex items-center gap-1 truncate">
                        <User className="size-3 shrink-0" />
                        <span className="truncate">{item.requester_name}</span>
                      </div>
                      <div className="flex items-center gap-1 justify-end font-mono">
                        <Clock className="size-3 shrink-0" />
                        <span>{formatDistanceToNow(new Date(item.pending_step.created_at), { addSuffix: true })}</span>
                      </div>
                    </div>

                    <div className="pt-1">
                      <Button
                        type="button"
                        size="sm"
                        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs"
                        onClick={() => handleRowClick(item.approval_request.resource_type, item.approval_request.resource_id)}
                      >
                        Review & Authorize <ArrowRight className="size-3.5 ml-1.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* DESKTOP TABLE VIEW (Visible only on >= md screens) */}
            <div className="hidden md:block">
              <Card>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead className="w-[30%]">Request Details</TableHead>
                      <TableHead>Priority / Risk</TableHead>
                      <TableHead>Requester</TableHead>
                      <TableHead>Waiting Since</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((item) => {
                      const isEmergency = item.approval_request.workflow_type === "EMERGENCY";
                      const isCapex = item.approval_request.workflow_type === "CAPEX";

                      return (
                        <TableRow
                          key={item.pending_step.id}
                          className="cursor-pointer hover:bg-muted/50 transition-colors group"
                          onClick={() => handleRowClick(item.approval_request.resource_type, item.approval_request.resource_id)}
                        >
                          <TableCell>
                            <div className="flex flex-col gap-1.5">
                              <StatusBadge
                                status={item.approval_request.resource_type === 'job_card' ? 'Job Card' : 'Requisition'}
                                size="sm"
                              />
                              {isEmergency && (
                                <span className="text-[10px] uppercase font-bold text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded w-fit">
                                  Emergency
                                </span>
                              )}
                              {isCapex && (
                                <span className="text-[10px] uppercase font-bold text-purple-500 bg-purple-500/10 px-1.5 py-0.5 rounded w-fit">
                                  Capex
                                </span>
                              )}
                            </div>
                          </TableCell>

                          <TableCell>
                            <div className="font-medium text-sm text-foreground mb-1 line-clamp-1 group-hover:text-primary transition-colors">
                              {item.resource_title || "Untitled Request"}
                            </div>
                            <div className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                              {item.resource_description || "No description provided."}
                            </div>
                            <div className="flex items-center gap-2 mt-2 text-[10px] font-mono text-muted-foreground">
                              <span className="bg-muted px-1.5 py-0.5 rounded border border-border">
                                Role: {item.pending_step.authority_role}
                              </span>
                            </div>
                          </TableCell>

                          <TableCell>
                            <div className="flex flex-col gap-2">
                              <PriorityBadge priority={item.approval_request.priority} size="sm" />
                              {item.approval_request.risk_level !== "LOW" && (
                                <div className="flex items-center gap-1 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                                  <AlertTriangle className="size-3" />
                                  {item.approval_request.risk_level} Risk
                                </div>
                              )}
                            </div>
                          </TableCell>

                          <TableCell>
                            <div className="flex flex-col gap-1.5">
                              <div className="flex items-center gap-1.5 text-sm text-foreground">
                                <User className="size-3.5 text-muted-foreground" />
                                {item.requester_name}
                              </div>
                              {item.department_name && (
                                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                                  <Building2 className="size-3" />
                                  {item.department_name}
                                </div>
                              )}
                            </div>
                          </TableCell>

                          <TableCell>
                            <div className="flex flex-col gap-1 text-sm text-foreground">
                              <span>{formatDistanceToNow(new Date(item.pending_step.created_at), { addSuffix: true })}</span>
                              <span className="text-[11px] text-muted-foreground">
                                {new Date(item.pending_step.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </TableCell>

                          <TableCell className="text-right align-middle">
                            <Button variant="ghost" size="sm" className="group-hover:bg-primary/10 group-hover:text-primary">
                              Review
                              <ArrowRight className="size-4 ml-1.5 opacity-50 group-hover:opacity-100 transition-opacity" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </Card>
            </div>
          </>
        )}
      </div>
    </Protect>
  );
}
