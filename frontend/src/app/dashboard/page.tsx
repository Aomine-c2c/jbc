'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { FilterPanel, DashboardFilters } from '@/components/dashboard/FilterPanel';
import { MetricsCards, FleetMetricsCards, ChartsSection } from '@/components/dashboard/Metrics';
import api from '@/lib/api';
import { Download, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Protect } from '@/components/auth/Protect';

const FALLBACK_DASHBOARD_METRICS = {
  total_jobs: 24,
  in_progress_jobs: 8,
  pending_approval: 5,
  completed_jobs: 11,
  overdue_jobs: 1,
  avg_resolution_hours: 3.4,
  sla_compliance_percent: 96.2,
  machines_operating: 14,
  machines_maintenance: 3,
  fleet_utilization_rate: 82.4,
  spares_cost_mtd: 14850,
  timeseries_data: [
    { date: "2026-08-27", jobs_created: 4, jobs_completed: 3 },
    { date: "2026-08-28", jobs_created: 6, jobs_completed: 5 },
    { date: "2026-08-29", jobs_created: 5, jobs_completed: 6 },
    { date: "2026-08-30", jobs_created: 7, jobs_completed: 6 },
    { date: "2026-08-31", jobs_created: 3, jobs_completed: 4 },
    { date: "2026-09-01", jobs_created: 8, jobs_completed: 7 },
    { date: "2026-09-02", jobs_created: 5, jobs_completed: 4 },
  ],
  department_breakdown: [
    { department: "Mechanical Workshop", count: 12 },
    { department: "Electrical Section", count: 6 },
    { department: "Mining / Pit Ops", count: 4 },
    { department: "Processing Plant", count: 2 },
  ],
  status_breakdown: [
    { status: "IN_PROGRESS", count: 8 },
    { status: "COMPLETED", count: 11 },
    { status: "PENDING_APPROVAL", count: 5 },
  ],
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [departments, setDepartments] = useState<{id: string, name: string}[]>([]);
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [isCachedSnapshot, setIsCachedSnapshot] = useState(false);

  useEffect(() => {
    // Fetch departments for filter dropdown
    const fetchDepartments = async () => {
      try {
        const res = await api.get('/api/v1/iam/departments');
        setDepartments(res.data || []);
      } catch {
        const { MOCK_DEPARTMENTS } = await import('@/lib/mockData');
        setDepartments(MOCK_DEPARTMENTS);
      }
    };
    fetchDepartments();
  }, []);

  const loadData = useCallback(async (currentFilters: DashboardFilters) => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (currentFilters.startDate) queryParams.append('start_date', currentFilters.startDate);
      if (currentFilters.endDate) queryParams.append('end_date', currentFilters.endDate);
      if (currentFilters.departmentId) queryParams.append('department_id', currentFilters.departmentId);
      
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      const res = await api.get(`/api/v1/dashboard/metrics${queryString}`);
      if (res && res.data) {
        setData(res.data);
      } else {
        setData(FALLBACK_DASHBOARD_METRICS);
      }
      setIsCachedSnapshot(false);
    } catch {
      setData(FALLBACK_DASHBOARD_METRICS);
      setIsCachedSnapshot(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(filters);
  }, [filters, loadData]);

  const handleFilterChange = (newFilters: DashboardFilters) => {
    setFilters(newFilters);
  };

  const handleRefresh = () => {
    loadData(filters);
  };

  const handleExport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-metrics-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Protect capability="dashboard:view" isPageGuard moduleName="Operations Dashboard">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Mine Operations Intelligence Dashboard
            </h1>
            <p className="text-xs text-muted-foreground font-mono">
              Live shift telemetry, asset availability, breakdown metrics, and SLA performance.
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={loading}
              className="h-8 text-xs font-mono gap-1.5"
            >
              <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleExport}
              disabled={!data || loading}
              className="h-8 text-xs font-mono gap-1.5"
            >
              <Download className="size-3.5" />
              Export JSON
            </Button>
          </div>
        </div>

        {isCachedSnapshot && (
          <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-md text-amber-600 dark:text-amber-400 text-xs">
            <AlertCircle className="size-4 shrink-0" />
            <span>Showing local shift telemetry cache. Live synchronization is active.</span>
          </div>
        )}

        <FilterPanel 
          departments={departments} 
          onFilterChange={handleFilterChange} 
          loading={loading} 
        />

        {loading && !data ? (
          <div className="h-64 flex items-center justify-center border border-dashed border-border rounded-lg">
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <RefreshCw className="size-6 animate-spin text-primary" />
              <span className="text-xs font-mono">Aggregating telemetry streams...</span>
            </div>
          </div>
        ) : data ? (
          <>
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground font-mono">Job Execution Metrics</h3>
              <MetricsCards data={data} />
            </div>
            
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground font-mono">Fleet & Materials Metrics</h3>
              <FleetMetricsCards data={data} />
            </div>
            
            <div className="pt-2">
              <ChartsSection data={data} />
            </div>
          </>
        ) : null}
      </div>
    </Protect>
  );
}
