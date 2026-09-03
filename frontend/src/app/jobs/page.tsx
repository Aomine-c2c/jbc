'use client';

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";

// Design System Components
import { StatusBadge, PriorityBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { TableSkeleton } from "@/components/ui/loading-state";

import {
  Plus,
  Search,
  Wrench,
  Filter,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  MapPin,
  ChevronRight,
  Download,
} from "lucide-react";

interface JobCardItem {
  id: string;
  job_number?: string;
  title: string;
  description?: string;
  priority: string | number;
  status: string;
  department_id: string;
  workshop_code?: string;
  location?: string;
  maintenance_type?: string;
  created_at?: string;
  assigned_to_email?: string;
}

export default function JobCardList() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobCardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const fetchJobs = useCallback(() => {
    setLoading(true);
    apiFetch("/api/v1/job-cards")
      .then((res) => {
        if (Array.isArray(res) && res.length > 0) {
          setJobs(res);
        } else {
          import("@/lib/mockData").then((m) => setJobs(m.MOCK_JOB_CARDS));
        }
      })
      .catch((error) => {
        console.warn("Failed to fetch jobs from central API, using fallback data", error);
        import("@/lib/mockData").then((m) => setJobs(m.MOCK_JOB_CARDS));
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleExportCsv = async () => {
    try {
      const baseUrl = await (await import('@/lib/api')).getApiUrl();
      const exportUrl = `${baseUrl}/api/v1/export/job-cards${statusFilter !== 'ALL' ? `?status_filter=${statusFilter}` : ''}`;
      
      const res = await fetch(exportUrl, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to download CSV export');
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `job_cards_export_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export CSV failed:', err);
    }
  };

  useEffect(() => {
    let _isMounted = true;
    fetchJobs();

    // Real-time SSE Live Event Listener
    const handleLiveEvent = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail?.type?.startsWith('job_card.')) {
        fetchJobs();
      }
    };

    window.addEventListener('dwrms-live-event', handleLiveEvent);

    return () => {
      _isMounted = false;
      window.removeEventListener('dwrms-live-event', handleLiveEvent);
    };
  }, [fetchJobs]);

  const filterTabs = [
    { label: "All Records", value: "ALL" },
    { label: "My Work", value: "MY_WORK" },
    { label: "Pending Approval", value: "PENDING_APPROVAL" },
    { label: "Planning / Assigned", value: "PLANNING_GROUP" },
    { label: "Active Execution", value: "IN_PROGRESS_GROUP" },
    { label: "Completed / QA", value: "COMPLETED_GROUP" },
    { label: "Closed", value: "CLOSED" },
    { label: "Draft / Returned", value: "DRAFT_GROUP" },
  ];

  const filteredJobs = jobs.filter((job) => {
    const s = job.status?.toUpperCase() || "";

    // Status filter grouping
    if (statusFilter !== "ALL") {
      if (statusFilter === "MY_WORK") {
        const userEmail = typeof window !== 'undefined' ? localStorage.getItem('user_email') : null;
        if (userEmail && job.assigned_to_email && job.assigned_to_email !== userEmail) {
          return false;
        }
      } else if (statusFilter === "DRAFT_GROUP") {
        if (s !== "DRAFT" && s !== "SUBMITTED" && s !== "RETURNED") return false;
      } else if (statusFilter === "PENDING_APPROVAL") {
        if (s !== "PENDING_APPROVAL") return false;
      } else if (statusFilter === "PLANNING_GROUP") {
        if (s !== "APPROVED" && s !== "PLANNING" && s !== "ASSIGNED") return false;
      } else if (statusFilter === "IN_PROGRESS_GROUP") {
        if (s !== "IN_PROGRESS" && s !== "ON_HOLD") return false;
      } else if (statusFilter === "COMPLETED_GROUP") {
        if (s !== "COMPLETED" && s !== "PENDING_REVIEW" && s !== "VERIFIED") return false;
      } else if (statusFilter === "CLOSED") {
        if (s !== "CLOSED") return false;
      } else if (s !== statusFilter) {
        return false;
      }
    }

    // Search query filter
    if (searchQuery.trim() !== "") {
      const q = searchQuery.toLowerCase();
      const matchTitle = job.title?.toLowerCase().includes(q);
      const matchId = job.id?.toLowerCase().includes(q);
      const matchJobNum = job.job_number?.toLowerCase().includes(q);
      const matchLocation = job.location?.toLowerCase().includes(q);
      const matchWorkshop = job.workshop_code?.toLowerCase().includes(q);
      if (!matchTitle && !matchId && !matchJobNum && !matchLocation && !matchWorkshop) return false;
    }

    return true;
  });

  return (
    <Protect capability="jobs:view" isPageGuard moduleName="Job Cards Registry">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-4">
      {/* HEADER BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Wrench className="size-5 text-primary" />
            <h1 className="text-xl font-bold tracking-tight text-foreground">
              Bikita Job Card Operational Registry
            </h1>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Full Lifecycle Digital Work Orders • Crushing, Concentrator & Fleet Workflows
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            title="Export registry to CSV"
            className="font-mono text-xs"
          >
            <Download className="size-3.5 mr-1 text-primary" />
            Export CSV
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={fetchJobs}
            disabled={loading}
            title="Refresh Job Cards"
          >
            <RefreshCw className={`size-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Protect capability="job_card:create">
            <Link href="/jobs/new">
              <Button size="sm" variant="default">
                <Plus className="size-3.5 mr-1" />
                New Job Card
              </Button>
            </Link>
          </Protect>
        </div>
      </div>

      {/* FILTER CONTROLS & SEARCH */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 bg-card p-3 rounded border border-border shadow-2xs">
        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
          <span className="text-[11px] font-mono text-muted-foreground mr-1 flex items-center gap-1 shrink-0">
            <Filter className="size-3" />
            Queue:
          </span>
          {filterTabs.map((tab) => {
            const isActive = statusFilter === tab.value;
            return (
              <button
                key={tab.value}
                type="button"
                onClick={() => setStatusFilter(tab.value)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all cursor-pointer shrink-0 ${
                  isActive
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                    : "bg-muted/50 text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search Box */}
        <div className="w-full lg:w-80">
          <Input
            prefixIcon={<Search className="size-3.5" />}
            placeholder="Search by #JC, title, workshop..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery("")}
            className="h-8"
          />
        </div>
      </div>

      {/* STATS COUNTER STRIP */}
      <div className="flex items-center justify-between text-xs font-mono text-muted-foreground px-1">
        <span>
          Showing <strong>{filteredJobs.length}</strong> of <strong>{jobs.length}</strong> records
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="size-2 rounded-full bg-amber-500 animate-pulse" />
            <span>{jobs.filter(j => j.status === 'PENDING_APPROVAL').length} Pending</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="size-2 rounded-full bg-cyan-500" />
            <span>{jobs.filter(j => j.status === 'IN_PROGRESS' || j.status === 'ASSIGNED').length} Active</span>
          </span>
        </div>
      </div>

      {/* ── RESPONSIVE JOB CARDS / DATA GRID ──────────────────────────── */}
      {loading ? (
        <TableSkeleton rows={6} columns={6} />
      ) : filteredJobs.length === 0 ? (
        <EmptyState
          icon={SlidersHorizontal}
          title="No Matching Job Cards Found"
          description={
            searchQuery || statusFilter !== "ALL"
              ? "No job cards match your active filter criteria. Try clearing search filters or create a new job card."
              : "No job cards exist in the system yet. Initiate the first maintenance workflow."
          }
          code="STATUS: 0_RECORDS"
          actionLabel="Create Job Card"
          onAction={() => router.push("/jobs/new")}
          secondaryActionLabel={searchQuery || statusFilter !== "ALL" ? "Reset Filters" : undefined}
          onSecondaryAction={() => {
            setSearchQuery("");
            setStatusFilter("ALL");
          }}
        />
      ) : (
        <>
          {/* MOBILE CARDS VIEW (Visible only on < md screens) */}
          <div className="md:hidden space-y-3">
            {filteredJobs.map((job) => {
              const displayNum = job.job_number || `JC-${job.id.slice(0, 8).toUpperCase()}`;

              return (
                <div
                  key={job.id}
                  onClick={() => router.push(`/jobs/${job.id}`)}
                  className="p-4 bg-card border border-border rounded-xl shadow-xs hover:border-primary/50 transition-all cursor-pointer space-y-2.5 active:scale-[0.99]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-primary">
                      {displayNum}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <PriorityBadge priority={job.priority} size="sm" />
                      <StatusBadge status={job.status} size="sm" />
                    </div>
                  </div>

                  <div>
                    <h3 className="font-bold text-sm text-foreground leading-tight">
                      {job.title}
                    </h3>
                    {job.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                        {job.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground pt-2 border-t border-border/50">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <MapPin className="size-3" />
                        {job.workshop_code || "WS-MECH"}
                      </span>
                      {job.location && (
                        <span className="truncate max-w-[100px]">• {job.location}</span>
                      )}
                    </div>

                    <span className="flex items-center gap-1 text-primary font-semibold">
                      Open <ChevronRight className="size-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* DESKTOP TABLE VIEW (Visible only on >= md screens) */}
          <div className="hidden md:block">
            <Table dense zebra>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Job Card #</TableHead>
                  <TableHead>Task Title & Work Description</TableHead>
                  <TableHead className="w-32">Workshop / Area</TableHead>
                  <TableHead className="w-32">Priority</TableHead>
                  <TableHead className="w-48">Lifecycle Status</TableHead>
                  <TableHead className="w-28">Requested</TableHead>
                  <TableHead className="w-20 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredJobs.map((job) => {
                  const displayNum = job.job_number || `JC-${job.id.slice(0, 8).toUpperCase()}`;

                  return (
                    <TableRow key={job.id} className="hover:bg-muted/40 cursor-pointer">
                      <TableCell mono className="font-bold text-foreground">
                        <Link href={`/jobs/${job.id}`} className="hover:underline text-primary">
                          {displayNum}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link href={`/jobs/${job.id}`} className="block">
                          <div className="font-semibold text-xs text-foreground hover:text-primary transition-colors">
                            {job.title}
                          </div>
                          {job.description && (
                            <div className="text-[11px] text-muted-foreground truncate max-w-md">
                              {job.description}
                            </div>
                          )}
                        </Link>
                      </TableCell>
                      <TableCell mono className="text-[11px] text-muted-foreground">
                        <div>{job.workshop_code || "WS-MECH"}</div>
                        {job.location && (
                          <div className="text-[10px] text-muted-foreground/80 truncate max-w-[120px]">
                            {job.location}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <PriorityBadge priority={job.priority} size="sm" />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={job.status} size="sm" />
                      </TableCell>
                      <TableCell mono className="text-muted-foreground text-[11px]">
                        {job.created_at ? new Date(job.created_at).toLocaleDateString() : "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/jobs/${job.id}`}>
                          <Button variant="outline" size="xs" className="font-mono text-[10px]">
                            Open
                            <ArrowRight className="size-2.5 ml-1" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </>
      )}
      </div>
    </Protect>
  );
}
