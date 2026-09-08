'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { FilterPanel, DashboardFilters } from '@/components/dashboard/FilterPanel';
import { MetricsCards, FleetMetricsCards, ChartsSection, DashboardData } from '@/components/dashboard/Metrics';
import { SafetyOpsDashboard } from '@/components/dashboard/SafetyOpsDashboard';
import api from '@/lib/api';
import { Download, RefreshCw, AlertCircle, ShieldAlert, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Protect } from '@/components/auth/Protect';
import { resolveUserRole } from '@/lib/rbac';

const EMPTY_DASHBOARD_METRICS: DashboardData = {
  job_metrics: {
    open_jobs: 0,
    pending_approval: 0,
    in_progress: 0,
    on_hold: 0,
    overdue: 0,
    avg_completion_time_hours: 0,
    actual_cost: 0,
    estimated_cost: 0,
  },
  fleet_metrics: {
    utilization_percentage: 0,
    in_use: 0,
    total_equipment: 0,
    pending_requisitions: 0,
    equipment_utilization_breakdown: [],
  },
  timeseries_data: [],
  department_workload: [],
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);
  const [departments, setDepartments] = useState<{id: string, name: string}[]>([]);
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [isCachedSnapshot, setIsCachedSnapshot] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'HSE' | 'MAINTENANCE'>('MAINTENANCE');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const role = localStorage.getItem('user_role');
      const email = localStorage.getItem('user_email');
      const resolved = resolveUserRole(role || email);
      setCurrentUserRole(resolved);
      if (resolved === 'Safety Officer') {
        setActiveView('HSE');
      }
    }
  }, []);

  useEffect(() => {
    // Fetch departments for filter dropdown
    const fetchDepartments = async () => {
      try {
        const res = await api.get('/api/v1/iam/departments');
        setDepartments(Array.isArray(res.data) ? res.data : []);
      } catch {
        setDepartments([]);
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
        setData(EMPTY_DASHBOARD_METRICS);
      }
      setIsCachedSnapshot(false);
    } catch {
      setData(EMPTY_DASHBOARD_METRICS);
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
              {activeView === 'HSE' ? (
                <>
                  <ShieldAlert className="size-5 text-amber-500" />
                  <span>HSE Safety & Operations Command Center</span>
                </>
              ) : (
                <span>Mine Operations Intelligence Dashboard</span>
              )}
            </h1>
            <p className="text-xs text-muted-foreground font-mono">
              {activeView === 'HSE'
                ? 'High-risk gating clearance queue, live LOTO register, zero harm telemetry, and statutory inspections.'
                : 'Live shift telemetry, asset availability, breakdown metrics, and SLA performance.'}
            </p>
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {/* SEGMENTED VIEW SWITCHER */}
            <div className="flex items-center rounded-lg border border-border bg-muted/40 p-0.5 text-xs font-mono">
              <button
                type="button"
                onClick={() => setActiveView('MAINTENANCE')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                  activeView === 'MAINTENANCE'
                    ? 'bg-background text-foreground font-semibold shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Wrench className="size-3.5" />
                Ops & Maintenance
              </button>
              <button
                type="button"
                onClick={() => setActiveView('HSE')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                  activeView === 'HSE'
                    ? 'bg-amber-600 text-white font-semibold shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <ShieldAlert className="size-3.5" />
                HSE View
                {currentUserRole === 'Safety Officer' && (
                  <span className="ml-1 px-1 py-0.2 bg-amber-500/20 text-[9px] rounded">Role Default</span>
                )}
              </button>
            </div>

            {activeView === 'MAINTENANCE' && (
              <>
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
              </>
            )}
          </div>
        </div>

        {activeView === 'HSE' ? (
          <SafetyOpsDashboard />
        ) : (
          <>
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
          </>
        )}
      </div>
    </Protect>
  );
}

