'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Timer,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Flame,
  Search,
  Plus,
  RefreshCw,
  Play,
  Pause,
  ArrowRight,
  Eye,
  X,
  Sliders,
  BellRing,
  Activity,
  Layers,
  Building2,
  Check,
} from 'lucide-react';

interface SLADashboardData {
  total_active: number;
  on_track_count: number;
  at_risk_count: number;
  breached_count: number;
  critical_open_count: number;
  compliance_percentage: number;
  avg_response_minutes: number;
  avg_completion_minutes: number;
  recent_breaches: SLATrackerRow[];
  at_risk_trackers: SLATrackerRow[];
}

interface SLATrackerRow {
  id: string;
  resource_type: string;
  resource_id: string;
  resource_reference?: string;
  title: string;
  priority: string;
  status: string;
  health: string;
  target_response_at?: string;
  target_completion_at?: string;
  actual_response_at?: string;
  actual_completion_at?: string;
  current_escalation_level: number;
  department_name?: string;
  policy_name?: string;
  created_at?: string;
}

interface SLATrackerDetail extends SLATrackerRow {
  paused_at?: string;
  total_paused_minutes: number;
  breach_reason?: string;
  history_logs: Array<{
    event: string;
    timestamp: string;
    acknowledged_by?: string;
    paused_by?: string;
    resumed_by?: string;
    completed_by?: string;
    reason?: string;
    notes?: string;
    final_health?: string;
  }>;
  escalation_logs: Array<{
    id: string;
    escalation_level: number;
    trigger_type: string;
    notified_role?: string;
    message?: string;
    created_at: string;
  }>;
}

interface SLAPolicyRow {
  id: string;
  name: string;
  description?: string;
  priority?: string;
  work_type?: string;
  department_name?: string;
  response_time_minutes: number;
  completion_time_minutes: number;
  warning_threshold_percentage: number;
  escalation_rules: Array<{
    level: number;
    trigger: string;
    after_percentage: number;
    target_role?: string;
  }>;
  is_active: boolean;
  is_default: boolean;
}

export default function SLAManagementPage() {
  const [activeTab, setActiveTab] = useState<'DASHBOARD' | 'TRACKERS' | 'POLICIES'>('DASHBOARD');
  const [dashboardData, setDashboardData] = useState<SLADashboardData | null>(null);
  const [trackers, setTrackers] = useState<SLATrackerRow[]>([]);
  const [policies, setPolicies] = useState<SLAPolicyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [healthFilter, setHealthFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');

  // Detail Drawer
  const [selectedTracker, setSelectedTracker] = useState<SLATrackerDetail | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [actionNotes, setActionNotes] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);

  // Policy Modal
  const [isCreatePolicyOpen, setIsCreatePolicyOpen] = useState(false);
  const [newPolicyName, setNewPolicyName] = useState('');
  const [newPolicyDesc, setNewPolicyDesc] = useState('');
  const [newPolicyPriority, setNewPolicyPriority] = useState('NORMAL');
  const [newResponseMins, setNewResponseMins] = useState('60');
  const [newCompMins, setNewCompMins] = useState('480');
  const [newWarnPct, setNewWarnPct] = useState('80');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const dash = await apiFetch<SLADashboardData>('/api/v1/sla/dashboard');
      if (dash) setDashboardData(dash);

      if (activeTab === 'TRACKERS' || activeTab === 'DASHBOARD') {
        let url = `/api/v1/sla/trackers?limit=100`;
        if (healthFilter !== 'ALL') url += `&health=${healthFilter}`;
        if (priorityFilter !== 'ALL') url += `&priority=${priorityFilter}`;
        if (searchQuery.trim()) url += `&search=${encodeURIComponent(searchQuery.trim())}`;
        const trData = await apiFetch<SLATrackerRow[]>(url);
        setTrackers(trData || []);
      }

      if (activeTab === 'POLICIES') {
        const pData = await apiFetch<SLAPolicyRow[]>('/api/v1/sla/policies');
        setPolicies(pData || []);
      }
    } catch (err) {
      console.error('Failed to load SLA data', err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, healthFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const viewTrackerDetail = async (id: string) => {
    setDrawerLoading(true);
    try {
      const data = await apiFetch<SLATrackerDetail>(`/api/v1/sla/trackers/${id}`);
      setSelectedTracker(data);
    } catch (err) {
      console.error('Failed to load tracker detail', err);
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!selectedTracker) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<SLATrackerDetail>(`/api/v1/sla/trackers/${selectedTracker.id}/acknowledge`, {
        method: 'POST',
        body: JSON.stringify({ notes: actionNotes.trim() || undefined }),
      });
      setSelectedTracker(updated);
      setActionNotes('');
      loadData();
    } catch (err) {
      console.error('Failed to acknowledge SLA', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handlePause = async () => {
    if (!selectedTracker) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<SLATrackerDetail>(`/api/v1/sla/trackers/${selectedTracker.id}/pause`, {
        method: 'POST',
        body: JSON.stringify({ reason: actionNotes.trim() || undefined }),
      });
      setSelectedTracker(updated);
      setActionNotes('');
      loadData();
    } catch (err) {
      console.error('Failed to pause SLA', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleResume = async () => {
    if (!selectedTracker) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<SLATrackerDetail>(`/api/v1/sla/trackers/${selectedTracker.id}/resume`, {
        method: 'POST',
        body: JSON.stringify({ notes: actionNotes.trim() || undefined }),
      });
      setSelectedTracker(updated);
      setActionNotes('');
      loadData();
    } catch (err) {
      console.error('Failed to resume SLA', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleComplete = async () => {
    if (!selectedTracker) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<SLATrackerDetail>(`/api/v1/sla/trackers/${selectedTracker.id}/complete`, {
        method: 'POST',
      });
      setSelectedTracker(updated);
      loadData();
    } catch (err) {
      console.error('Failed to complete SLA', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleTriggerEvaluation = async () => {
    try {
      await apiFetch('/api/v1/sla/evaluate', { method: 'POST' });
      loadData();
    } catch (err) {
      console.error('Evaluation run failed', err);
    }
  };

  const handleCreatePolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPolicyName.trim()) return;
    try {
      await apiFetch('/api/v1/sla/policies', {
        method: 'POST',
        body: JSON.stringify({
          name: newPolicyName.trim(),
          description: newPolicyDesc.trim() || undefined,
          priority: newPolicyPriority,
          response_time_minutes: parseInt(newResponseMins) || 60,
          completion_time_minutes: parseInt(newCompMins) || 480,
          warning_threshold_percentage: parseInt(newWarnPct) || 80,
          escalation_rules: [
            { level: 1, trigger: 'RESPONSE_WARNING', after_percentage: parseInt(newWarnPct) || 80, target_role: 'Supervisor' },
            { level: 2, trigger: 'RESPONSE_BREACH', after_percentage: 100, target_role: 'Department Manager' },
            { level: 3, trigger: 'COMPLETION_BREACH', after_percentage: 100, target_role: 'Plant Manager' },
          ],
        }),
      });
      setIsCreatePolicyOpen(false);
      setNewPolicyName('');
      setNewPolicyDesc('');
      loadData();
    } catch (err) {
      console.error('Failed to create policy', err);
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'ON_TRACK':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">ON TRACK</Badge>;
      case 'AT_RISK':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">AT RISK</Badge>;
      case 'BREACHED_RESPONSE':
        return <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/30 text-[10px]">RESPONSE BREACH</Badge>;
      case 'BREACHED_COMPLETION':
        return <Badge className="bg-rose-600/20 text-rose-500 border-rose-600/30 text-[10px]">COMPLETION BREACH</Badge>;
      case 'MET':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">SLA MET</Badge>;
      case 'BREACHED_MET':
        return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[10px]">MET (LATE RESP)</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{health}</Badge>;
    }
  };

  const getPriorityBadge = (pri: string) => {
    switch (pri) {
      case 'CRITICAL':
        return <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/30 text-[10px] font-bold">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px] font-bold">HIGH</Badge>;
      case 'NORMAL':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">NORMAL</Badge>;
      case 'LOW':
        return <Badge variant="secondary" className="text-[10px]">LOW</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{pri}</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Timer className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Priority, SLA & Escalation Engine
            </h1>
            <p className="text-xs text-muted-foreground">
              Monitor operational response times, completion deadlines, pause extensions, and multi-tier escalation triggers.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleTriggerEvaluation} className="text-xs gap-1.5 border-amber-500/30 text-amber-400 hover:bg-amber-500/10">
            <BellRing className="size-3.5" />
            Evaluate Escalations
          </Button>
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {activeTab === 'POLICIES' && (
            <Button size="sm" onClick={() => setIsCreatePolicyOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
              <Plus className="size-3.5" />
              New Policy
            </Button>
          )}
        </div>
      </div>

      {/* KPI Metrics Row */}
      {dashboardData && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-mono text-muted-foreground uppercase">SLA Compliance</p>
                <p className="text-2xl font-mono font-bold text-emerald-400 mt-1">
                  {dashboardData.compliance_percentage}%
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-emerald-500/10 text-emerald-400">
                <CheckCircle2 className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-mono text-muted-foreground uppercase">On Track</p>
                <p className="text-2xl font-mono font-bold text-foreground mt-1">
                  {dashboardData.on_track_count}
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
                <Clock className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-mono text-muted-foreground uppercase">At Risk (Warning)</p>
                <p className="text-2xl font-mono font-bold text-amber-400 mt-1">
                  {dashboardData.at_risk_count}
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
                <AlertTriangle className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-mono text-muted-foreground uppercase">Breached / Overdue</p>
                <p className="text-2xl font-mono font-bold text-rose-500 mt-1">
                  {dashboardData.breached_count}
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-rose-500/10 text-rose-500">
                <ShieldAlert className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-mono text-muted-foreground uppercase">Critical Open</p>
                <p className="text-2xl font-mono font-bold text-rose-400 mt-1">
                  {dashboardData.critical_open_count}
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-rose-500/10 text-rose-400">
                <Flame className="size-5" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Segmented View Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border w-fit">
        <button
          onClick={() => setActiveTab('DASHBOARD')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'DASHBOARD'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Activity className="size-3.5" />
          <span>SLA Dashboard</span>
        </button>
        <button
          onClick={() => setActiveTab('TRACKERS')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'TRACKERS'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Timer className="size-3.5" />
          <span>Live Trackers</span>
        </button>
        <button
          onClick={() => setActiveTab('POLICIES')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'POLICIES'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Sliders className="size-3.5" />
          <span>SLA Policies</span>
        </button>
      </div>

      {/* Dashboard View */}
      {activeTab === 'DASHBOARD' && dashboardData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* At Risk List */}
            <Card className="bg-card border-border">
              <CardHeader className="p-4 border-b border-border">
                <CardTitle className="text-sm font-bold flex items-center gap-2 text-amber-400">
                  <AlertTriangle className="size-4" />
                  <span>At Risk Work (Approaching Threshold)</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {dashboardData.at_risk_trackers.length === 0 ? (
                  <div className="p-6 text-center text-xs text-muted-foreground">
                    No work items currently at risk.
                  </div>
                ) : (
                  <div className="divide-y divide-border/60">
                    {dashboardData.at_risk_trackers.map((t) => (
                      <div key={t.id} className="p-3 flex items-center justify-between hover:bg-muted/30 text-xs">
                        <div>
                          <div className="font-semibold text-foreground">{t.title}</div>
                          <div className="text-[10px] font-mono text-muted-foreground">{t.resource_reference} • {t.department_name}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getPriorityBadge(t.priority)}
                          <Button variant="ghost" size="sm" onClick={() => viewTrackerDetail(t.id)} className="h-7 text-xs">
                            View
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Breaches List */}
            <Card className="bg-card border-border">
              <CardHeader className="p-4 border-b border-border">
                <CardTitle className="text-sm font-bold flex items-center gap-2 text-rose-500">
                  <ShieldAlert className="size-4" />
                  <span>Recent SLA Breaches</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {dashboardData.recent_breaches.length === 0 ? (
                  <div className="p-6 text-center text-xs text-muted-foreground">
                    No SLA breaches recorded.
                  </div>
                ) : (
                  <div className="divide-y divide-border/60">
                    {dashboardData.recent_breaches.map((t) => (
                      <div key={t.id} className="p-3 flex items-center justify-between hover:bg-muted/30 text-xs">
                        <div>
                          <div className="font-semibold text-foreground">{t.title}</div>
                          <div className="text-[10px] font-mono text-muted-foreground">{t.resource_reference} • Level {t.current_escalation_level} Escalated</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getHealthBadge(t.health)}
                          <Button variant="ghost" size="sm" onClick={() => viewTrackerDetail(t.id)} className="h-7 text-xs">
                            View
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Trackers List View */}
      {activeTab === 'TRACKERS' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, reference number, work item..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 text-xs h-9"
              />
            </div>
            <select
              value={healthFilter}
              onChange={(e) => setHealthFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-card px-3 text-xs text-foreground shrink-0"
            >
              <option value="ALL">All SLA Health</option>
              <option value="ON_TRACK">ON TRACK</option>
              <option value="AT_RISK">AT RISK</option>
              <option value="BREACHED_RESPONSE">RESPONSE BREACH</option>
              <option value="BREACHED_COMPLETION">COMPLETION BREACH</option>
              <option value="MET">SLA MET</option>
            </select>
          </div>

          <Card className="bg-card border-border">
            <CardContent className="p-0">
              {loading ? (
                <div className="p-12 text-center text-xs text-muted-foreground">Loading SLA trackers...</div>
              ) : trackers.length === 0 ? (
                <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                  No active SLA trackers found.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                        <th className="p-3 pl-4">REFERENCE & RESOURCE</th>
                        <th className="p-3">TITLE</th>
                        <th className="p-3">PRIORITY</th>
                        <th className="p-3">SLA HEALTH</th>
                        <th className="p-3">RESPONSE TARGET</th>
                        <th className="p-3">COMPLETION TARGET</th>
                        <th className="p-3">ESCALATION</th>
                        <th className="p-3 pr-4 text-right">ACTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {trackers.map((tr) => (
                        <tr key={tr.id} className="hover:bg-muted/30 transition-colors">
                          <td className="p-3 pl-4 font-mono font-bold text-foreground">
                            <div>{tr.resource_reference || 'N/A'}</div>
                            <div className="text-[10px] text-muted-foreground font-normal">{tr.resource_type}</div>
                          </td>
                          <td className="p-3 max-w-xs">
                            <div className="font-semibold text-foreground truncate">{tr.title}</div>
                            <div className="text-[10px] text-muted-foreground">{tr.department_name}</div>
                          </td>
                          <td className="p-3">{getPriorityBadge(tr.priority)}</td>
                          <td className="p-3">{getHealthBadge(tr.health)}</td>
                          <td className="p-3 font-mono text-[11px] text-muted-foreground">
                            {tr.actual_response_at ? (
                              <span className="text-emerald-400">Acknowledged</span>
                            ) : tr.target_response_at ? (
                              new Date(tr.target_response_at).toLocaleTimeString()
                            ) : (
                              '—'
                            )}
                          </td>
                          <td className="p-3 font-mono text-[11px] text-muted-foreground">
                            {tr.target_completion_at ? new Date(tr.target_completion_at).toLocaleString() : '—'}
                          </td>
                          <td className="p-3 font-mono font-bold text-amber-400">
                            {tr.current_escalation_level > 0 ? `Level ${tr.current_escalation_level}` : '—'}
                          </td>
                          <td className="p-3 pr-4 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewTrackerDetail(tr.id)}
                              className="h-7 text-xs gap-1"
                            >
                              <Eye className="size-3" />
                              <span>Manage</span>
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Policies View */}
      {activeTab === 'POLICIES' && (
        <Card className="bg-card border-border">
          <CardContent className="p-0">
            {policies.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                No custom SLA policies defined.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                      <th className="p-3 pl-4">POLICY NAME</th>
                      <th className="p-3">PRIORITY</th>
                      <th className="p-3">DEPARTMENT</th>
                      <th className="p-3">RESPONSE TARGET</th>
                      <th className="p-3">COMPLETION TARGET</th>
                      <th className="p-3">WARNING THRESHOLD</th>
                      <th className="p-3 pr-4">ESCALATION TIERS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {policies.map((pol) => (
                      <tr key={pol.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-semibold text-foreground">{pol.name}</td>
                        <td className="p-3">{pol.priority ? getPriorityBadge(pol.priority) : <span className="text-muted-foreground">Any</span>}</td>
                        <td className="p-3 text-muted-foreground">{pol.department_name || 'All Departments'}</td>
                        <td className="p-3 font-mono text-cyan-400 font-bold">{pol.response_time_minutes} mins</td>
                        <td className="p-3 font-mono text-emerald-400 font-bold">{pol.completion_time_minutes} mins</td>
                        <td className="p-3 font-mono">{pol.warning_threshold_percentage}%</td>
                        <td className="p-3 pr-4">
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {pol.escalation_rules.length} tiers
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tracker Detail & Action Drawer */}
      {selectedTracker && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-primary/10 text-primary">
                  <Timer className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">{selectedTracker.title}</h2>
                    {getHealthBadge(selectedTracker.health)}
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    {selectedTracker.resource_reference || selectedTracker.resource_type} • Priority {selectedTracker.priority}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedTracker(null)} className="size-8 p-0">
                <X className="size-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
              {/* Timing Milestones Card */}
              <div className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="font-semibold text-foreground text-xs">SLA Targets & Elapsed Times</div>
                <div className="grid grid-cols-2 gap-3 text-[11px]">
                  <div>
                    <span className="text-muted-foreground">Response Deadline: </span>
                    <span className="font-mono text-foreground font-bold">
                      {selectedTracker.target_response_at ? new Date(selectedTracker.target_response_at).toLocaleString() : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Completion Deadline: </span>
                    <span className="font-mono text-foreground font-bold">
                      {selectedTracker.target_completion_at ? new Date(selectedTracker.target_completion_at).toLocaleString() : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Actual Acknowledged: </span>
                    <span className="font-mono text-emerald-400 font-bold">
                      {selectedTracker.actual_response_at ? new Date(selectedTracker.actual_response_at).toLocaleString() : 'Pending'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Total Paused Time: </span>
                    <span className="font-mono text-amber-400 font-bold">{selectedTracker.total_paused_minutes.toFixed(1)} mins</span>
                  </div>
                </div>
              </div>

              {/* Actions Box */}
              <div className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="font-semibold text-foreground text-xs">Operational SLA Controls</div>
                <Input
                  placeholder="Action notes / reason for pause or acknowledgment..."
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  className="h-8 text-xs"
                />
                <div className="flex flex-wrap gap-2 pt-1">
                  {!selectedTracker.actual_response_at && (
                    <Button size="sm" onClick={handleAcknowledge} disabled={actionSubmitting} className="text-xs bg-blue-600 hover:bg-blue-700 text-white gap-1">
                      <Check className="size-3" /> Acknowledge Response
                    </Button>
                  )}
                  {selectedTracker.status !== 'PAUSED' ? (
                    <Button size="sm" onClick={handlePause} disabled={actionSubmitting} variant="outline" className="text-xs border-amber-500/40 text-amber-400 hover:bg-amber-500/10 gap-1">
                      <Pause className="size-3" /> Pause SLA Clock
                    </Button>
                  ) : (
                    <Button size="sm" onClick={handleResume} disabled={actionSubmitting} className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
                      <Play className="size-3" /> Resume SLA Clock
                    </Button>
                  )}
                  {selectedTracker.status !== 'COMPLETED' && (
                    <Button size="sm" onClick={handleComplete} disabled={actionSubmitting} className="text-xs bg-purple-600 hover:bg-purple-700 text-white gap-1">
                      <CheckCircle2 className="size-3" /> Mark Completed
                    </Button>
                  )}
                </div>
              </div>

              {/* Escalation Logs */}
              <div className="space-y-2">
                <div className="font-semibold text-foreground text-xs flex items-center justify-between">
                  <span>Escalation Log Trail</span>
                  <Badge variant="outline" className="text-[10px]">{selectedTracker.escalation_logs.length} events</Badge>
                </div>
                {selectedTracker.escalation_logs.length === 0 ? (
                  <div className="p-3 border border-dashed rounded text-center text-muted-foreground text-[11px]">
                    No escalations triggered.
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {selectedTracker.escalation_logs.map((log) => (
                      <div key={log.id} className="p-2.5 rounded border border-border bg-card/40 space-y-1 text-[11px]">
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-bold text-amber-400">Level {log.escalation_level} — {log.trigger_type}</span>
                          <span className="text-muted-foreground text-[10px]">{new Date(log.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-muted-foreground text-[10px]">{log.message}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Policy Modal */}
      {isCreatePolicyOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-md bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Sliders className="size-5 text-primary" />
                <span>Create SLA Policy</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Configure target response, completion times, and warning thresholds.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreatePolicySubmit}>
              <CardContent className="p-4 space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Policy Name *</label>
                  <Input
                    required
                    value={newPolicyName}
                    onChange={(e) => setNewPolicyName(e.target.value)}
                    placeholder="e.g. Critical Breakdown SLA"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Priority Level</label>
                  <select
                    value={newPolicyPriority}
                    onChange={(e) => setNewPolicyPriority(e.target.value)}
                    className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="NORMAL">NORMAL</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Response Time (mins)</label>
                    <Input
                      type="number"
                      required
                      value={newResponseMins}
                      onChange={(e) => setNewResponseMins(e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Completion Time (mins)</label>
                    <Input
                      type="number"
                      required
                      value={newCompMins}
                      onChange={(e) => setNewCompMins(e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Warning Threshold (%)</label>
                  <Input
                    type="number"
                    value={newWarnPct}
                    onChange={(e) => setNewWarnPct(e.target.value)}
                    className="h-8 text-xs font-mono"
                  />
                </div>
              </CardContent>
              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreatePolicyOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs">
                  Save Policy
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
