'use client';

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { Plus, Search, RefreshCw, Truck } from "lucide-react";
import { useRouter } from "next/navigation";

interface RequisitionItem {
  id: string;
  status: string;
  machine_type_id: string;
  department_id: string;
  start_time: string;
  end_time: string;
  created_at: string;
  notes?: string;
}

const STATUSES = [
  "ALL", "DRAFT", "SUBMITTED", "REVIEWED", "RETURNED_FOR_CORRECTION",
  "AWAITING_ALLOCATION", "ALLOCATED", "PARTIALLY_ALLOCATED", "UNAVAILABLE",
  "IN_USE", "RETURNED", "CLOSED", "REJECTED", "CANCELLED",
];

export default function RequisitionsListPage() {
  const router = useRouter();
  const [items, setItems] = useState<RequisitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const load = useCallback(() => {
    setLoading(true);
    apiFetch("/api/v1/fleet/requisitions")
      .then((res) => {
        if (res) setItems(Array.isArray(res) ? res : []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = items.filter((r) => {
    const matchStatus = statusFilter === "ALL" || r.status === statusFilter;
    const matchSearch =
      search === "" ||
      r.id.toLowerCase().includes(search.toLowerCase()) ||
      (r.notes || "").toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  return (
    <Protect capability="fleet:view" isPageGuard moduleName="Fleet Requisitions Registry">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Truck className="w-5 h-5 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">Fleet Requisitions</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manage machine and equipment requisitions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load} className="gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </Button>
          <Protect capability="requisition:create">
            <Link href="/fleet/requisitions/new">
              <Button size="sm" className="gap-1.5">
                <Plus className="w-3.5 h-3.5" /> New Requisition
              </Button>
            </Link>
          </Protect>
        </div>
      </div>

      {/* FILTERS */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by ID or notes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <select
          className="border border-border rounded-md px-3 py-2 text-sm bg-background text-foreground"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* TABLE */}
      {loading ? (
        <TableSkeleton />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Truck}
          title="No requisitions found"
          description="No fleet requisitions match your current filters. Create a new requisition to get started."
          actionLabel="New Requisition"
          onAction={() => router.push("/fleet/requisitions/new")}
        />
      ) : (
        <div className="rounded border border-border bg-card overflow-hidden shadow-2xs">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow
                  key={r.id}
                  className="cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => router.push(`/fleet/requisitions/${r.id}`)}
                >
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {r.id.slice(0, 8)}…
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={r.status} size="sm" />
                  </TableCell>
                  <TableCell className="text-sm">
                    {r.start_time ? new Date(r.start_time).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {r.end_time ? new Date(r.end_time).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground max-w-xs truncate">
                    {r.notes || "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      </div>
    </Protect>
  );
}
