"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Protect } from "@/components/auth/Protect";
import { apiFetch } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { TelemetrySpinner } from "@/components/ui/loading-state";
import { LayoutDashboard, Plus, Wrench, ShieldAlert, Activity, ArrowRight } from "lucide-react";

type RecentJob = {
  id: string;
  display_id: string;
  title: string;
  status: string;
  department: string;
};

type Analytics = {
  active_job_cards: number;
  pending_approvals: number;
  fleet_utilization: string;
  recent_activity: RecentJob[];
};

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const data = await apiFetch("/api/v1/dashboard/analytics");
        setAnalytics(data);
      } catch (error) {
        console.error("Failed to load analytics", error);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <TelemetrySpinner message="Acquiring mine site operational analytics..." />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <LayoutDashboard className="size-5 text-primary" />
            <h1 className="text-xl font-bold tracking-tight text-foreground">
              Operational Management Dashboard
            </h1>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Bikita Minerals • Concentrator, Shafts & Mobile Fleet Operations
          </p>
        </div>

        <Protect capability="job_card:create">
          <Link href="/jobs/new">
            <Button size="sm" variant="default">
              <Plus className="size-3.5 mr-1" />
              New Job Card
            </Button>
          </Link>
        </Protect>
      </div>
      
      {/* METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card variant="accent">
          <CardContent className="p-4 space-y-1">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Active Job Cards</span>
              <Wrench className="size-4 text-primary" />
            </div>
            <div className="text-2xl font-mono font-bold text-foreground">
              {analytics?.active_job_cards ?? 0}
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">
              Open mechanical & electrical jobs
            </div>
          </CardContent>
        </Card>
        
        <Card variant="warning">
          <CardContent className="p-4 space-y-1">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Pending Approvals</span>
              <ShieldAlert className="size-4 text-amber-500" />
            </div>
            <div className="text-2xl font-mono font-bold text-amber-600 dark:text-amber-400">
              {analytics?.pending_approvals ?? 0}
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">
              Awaiting manager / supervisor sign-off
            </div>
          </CardContent>
        </Card>
        
        <Card variant="info">
          <CardContent className="p-4 space-y-1">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-[10px] font-mono uppercase tracking-wider">Fleet Utilization</span>
              <Activity className="size-4 text-blue-500" />
            </div>
            <div className="text-2xl font-mono font-bold text-foreground">
              {analytics?.fleet_utilization ?? "0%"}
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">
              Active heavy equipment operating rate
            </div>
          </CardContent>
        </Card>
      </div>

      {/* RECENT ACTIVITY TABLE */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs">
            <span>Recent Job Card Activity</span>
          </CardTitle>
          <Link href="/jobs" className="text-[11px] font-mono text-primary hover:underline flex items-center gap-1">
            View All Job Cards
            <ArrowRight className="size-3" />
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <Table dense zebra>
            <TableHeader>
              <TableRow>
                <TableHead className="w-28">Job ID</TableHead>
                <TableHead>Task Title</TableHead>
                <TableHead className="w-36">Status</TableHead>
                <TableHead className="w-40">Department</TableHead>
                <TableHead className="w-20 text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analytics?.recent_activity?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-6 text-center text-muted-foreground">
                    No recent job cards found.
                  </TableCell>
                </TableRow>
              ) : (
                analytics?.recent_activity?.map((job) => (
                  <TableRow key={job.id} className="hover:bg-muted/40 cursor-pointer">
                    <TableCell mono className="font-bold text-foreground">
                      <Link href={`/jobs/${job.id}`}>
                        {job.display_id || `JC-${job.id.slice(0, 8).toUpperCase()}`}
                      </Link>
                    </TableCell>
                    <TableCell className="font-semibold text-xs text-foreground">
                      <Link href={`/jobs/${job.id}`} className="hover:text-primary transition-colors">
                        {job.title}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={job.status} size="sm" />
                    </TableCell>
                    <TableCell className="text-muted-foreground font-mono text-[11px]">
                      {job.department}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/jobs/${job.id}`}>
                        <Button variant="outline" size="xs" className="font-mono text-[10px]">
                          View
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
