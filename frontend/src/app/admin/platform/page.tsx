'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Server,
  Database,
  HardDrive,
  Cpu,
  Archive,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
  Clock,
  Radio,
  Lock,
  Terminal,
  Layers,
  Search,
  Filter,
  Play,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Protect } from '@/components/auth/Protect';
import { api } from '@/lib/api';

interface SubsystemInfo {
  status?: string;
  engine?: string;
  latency_ms?: number;
  free_percentage?: number;
  archive_count?: number;
  virtual_ip?: string;
}

interface PlatformStatusResponse {
  platform?: string;
  server_name?: string;
  environment?: string;
  timezone?: string;
  version?: string;
  subsystems?: Record<string, SubsystemInfo>;
}

interface DiagnosticsMemory {
  total_mb?: number;
  used_pct?: number;
  available_mb?: number;
}

interface DiagnosticsDisk {
  total_gb?: number;
  free_gb?: number;
  used_pct?: number;
}

interface DiagnosticsDbPool {
  engine?: string;
  size?: number;
  checked_in?: number;
  checked_out?: number;
}

interface PlatformDiagnosticsResponse {
  cpu_usage_pct?: number;
  memory?: DiagnosticsMemory;
  disk?: DiagnosticsDisk;
  database_pool?: DiagnosticsDbPool;
}

interface BackupArchiveItem {
  filename: string;
  backup_id?: string;
  backup_type?: string;
  database_engine?: string;
  platform_version?: string;
  size_mb?: number;
  created_at: string;
  integrity_status?: string;
}

interface PlatformBackupsResponse {
  retention_days?: number;
  backup_directory?: string;
  archives?: BackupArchiveItem[];
}

interface LogEntry {
  raw: string;
  level: string;
}

interface PlatformUpdateResponse {
  platform?: string;
  installed_version?: string;
  api_version?: string;
  schema_version?: string;
  web_client_version?: string;
  desktop_client_version?: string;
  min_supported_client_version?: string;
  target_version?: string;
  status?: string;
  update_policy?: string;
  environment?: string;
  channel?: string;
}

interface HealthCheckResponse {
  healthy: boolean;
  status: string;
  timestamp: string;
  latency_ms: number;
}

interface UpdateCheckResponse {
  current_version: string;
  channel: string;
  update_policy: string;
  checked_at: string;
  has_update: boolean;
  latest_approved_version: string;
  status: string;
  message: string;
}

interface UpdateApplyResponse {
  status: string;
  current_version: string;
  channel: string;
  pipeline_steps_completed: string[];
  applied_at: string;
  message: string;
}

export default function PlatformAdminPage() {
  const [activeTab, setActiveTab] = useState<'status' | 'backups' | 'diagnostics' | 'logs' | 'updates'>('status');
  const [statusData, setStatusData] = useState<PlatformStatusResponse | null>(null);
  const [diagnosticsData, setDiagnosticsData] = useState<PlatformDiagnosticsResponse | null>(null);
  const [backupsData, setBackupsData] = useState<PlatformBackupsResponse | null>(null);
  const [logsData, setLogsData] = useState<LogEntry[]>([]);
  const [updateData, setUpdateData] = useState<PlatformUpdateResponse | null>(null);

  // Health check trigger state
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [healthResult, setHealthResult] = useState<HealthCheckResponse | null>(null);

  // Backup creation & restore modal state
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [backupNote, setBackupNote] = useState('Manual admin snapshot');
  const [isCreatingBackup, setIsCreatingBackup] = useState(false);
  const [backupSuccessMessage, setBackupSuccessMessage] = useState<string | null>(null);

  // Verification & Restoration modal state
  const [verifyingArchive, setVerifyingArchive] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<{ filename: string; valid: boolean; message: string; sha256?: string } | null>(null);
  const [restoreModalTarget, setRestoreModalTarget] = useState<BackupArchiveItem | null>(null);
  const [restoreConfirmText, setRestoreConfirmText] = useState('');
  const [isRestoring, setIsRestoring] = useState(false);

  // Update management state
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);
  const [updateCheckResult, setUpdateCheckResult] = useState<UpdateCheckResponse | null>(null);
  const [isApplyingUpdate, setIsApplyingUpdate] = useState(false);
  const [updateApplyResult, setUpdateApplyResult] = useState<UpdateApplyResponse | null>(null);

  // Log filter state
  const [logLevelFilter, setLogLevelFilter] = useState('ALL');
  const [logSearchQuery, setLogSearchQuery] = useState('');

  // Load all platform telemetry
  const loadPlatformData = useCallback(async () => {
    try {
      const [statusRes, diagRes, backupsRes, logsRes, updateRes] = await Promise.allSettled([
        api.get('/api/v1/platform/status'),
        api.get('/api/v1/platform/diagnostics'),
        api.get('/api/v1/platform/backups'),
        api.get(`/api/v1/platform/logs?lines=150&level=${logLevelFilter}`),
        api.get('/api/v1/platform/update-status'),
      ]);

      if (statusRes.status === 'fulfilled') setStatusData(statusRes.value.data);
      if (diagRes.status === 'fulfilled') setDiagnosticsData(diagRes.value.data);
      if (backupsRes.status === 'fulfilled') setBackupsData(backupsRes.value.data);
      if (logsRes.status === 'fulfilled') setLogsData(logsRes.value.data?.logs || []);
      if (updateRes.status === 'fulfilled') setUpdateData(updateRes.value.data);
    } catch (err) {
      console.error('Failed to load platform data:', err);
    }
  }, [logLevelFilter]);

  useEffect(() => {
    loadPlatformData();
    const interval = setInterval(loadPlatformData, 15000);
    return () => clearInterval(interval);
  }, [loadPlatformData]);

  // Run live health check
  const handleRunHealthCheck = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await api.post('/api/v1/platform/health-check');
      setHealthResult(res.data);
      await loadPlatformData();
    } catch (err) {
      console.error('Health check failed:', err);
    } finally {
      setIsCheckingHealth(false);
    }
  };

  // Create backup
  const handleCreateBackup = async () => {
    setIsCreatingBackup(true);
    setBackupSuccessMessage(null);
    try {
      const res = await api.post('/api/v1/platform/backups/create', {
        note: backupNote,
        include_storage: true,
      });
      setBackupSuccessMessage(`Backup archive created successfully: ${res.data.filename}`);
      setShowBackupModal(false);
      await loadPlatformData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(`Failed to create backup: ${e.message || 'Error executing backup creation'}`);
    } finally {
      setIsCreatingBackup(false);
    }
  };

  // Verify backup integrity
  const handleVerifyBackup = async (filename: string) => {
    setVerifyingArchive(filename);
    setVerifyResult(null);
    try {
      const res = await api.post('/api/v1/platform/backups/verify', { filename });
      setVerifyResult(res.data);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setVerifyResult({
        filename,
        valid: false,
        message: e.message || 'Verification endpoint returned an error.',
      });
    } finally {
      setVerifyingArchive(null);
    }
  };

  // Restore backup
  const handleRestoreBackup = async () => {
    if (!restoreModalTarget || restoreConfirmText !== 'CONFIRM RESTORE') return;

    setIsRestoring(true);
    try {
      const res = await api.post('/api/v1/platform/backups/restore', {
        filename: restoreModalTarget.filename,
        confirmation_phrase: restoreConfirmText,
        pre_snapshot: true,
      });

      alert(res.data.message || 'Restoration successfully executed.');
      setRestoreModalTarget(null);
      setRestoreConfirmText('');
      await loadPlatformData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(`Restoration Failed: ${e.message || 'Error executing restore'}`);
    } finally {
      setIsRestoring(false);
    }
  };

  // Check for updates
  const handleCheckUpdates = async () => {
    setIsCheckingUpdate(true);
    setUpdateCheckResult(null);
    try {
      const res = await api.post('/api/v1/platform/update/check');
      setUpdateCheckResult(res.data);
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(`Update check failed: ${e.message || 'Error checking release channel'}`);
    } finally {
      setIsCheckingUpdate(false);
    }
  };

  // Apply update
  const handleApplyUpdate = async (targetVersion?: string) => {
    if (!confirm(`Are you sure you want to execute the 8-step controlled update pipeline for ${targetVersion || updateData?.installed_version}? A pre-upgrade snapshot will automatically be created.`)) {
      return;
    }

    setIsApplyingUpdate(true);
    setUpdateApplyResult(null);
    try {
      const res = await api.post('/api/v1/platform/update/apply', {
        target_version: targetVersion || updateData?.installed_version,
        skip_backup: false,
      });
      setUpdateApplyResult(res.data);
      await loadPlatformData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(`Update execution failed: ${e.message || 'Error executing update pipeline'}`);
    } finally {
      setIsApplyingUpdate(false);
    }
  };

  const filteredLogs = logsData.filter((entry) => {
    if (!logSearchQuery) return true;
    return entry.raw.toLowerCase().includes(logSearchQuery.toLowerCase());
  });

  return (
    <Protect capability="settings:manage">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Server className="size-6 text-amber-500" />
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white uppercase">
                Platform & Infrastructure Administration
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Authoritative Ubuntu Server Core • Subsystems, Diagnostics, Backups & Real-time Logs
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={loadPlatformData}
              className="border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-mono"
            >
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={handleRunHealthCheck}
              disabled={isCheckingHealth}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs"
            >
              <Zap className={`size-3.5 mr-1.5 ${isCheckingHealth ? 'animate-spin' : ''}`} />
              {isCheckingHealth ? 'Probing Subsystems...' : 'Run Live Health Probe'}
            </Button>
          </div>
        </div>

        {/* Live Health Alert Banner */}
        {healthResult && (
          <div
            className={`p-3.5 rounded-xl border flex items-center justify-between font-mono text-xs ${
              healthResult.healthy
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                : 'bg-red-950/40 border-red-500/40 text-red-300'
            }`}
          >
            <div className="flex items-center gap-2">
              {healthResult.healthy ? (
                <CheckCircle2 className="size-4 text-emerald-400" />
              ) : (
                <AlertTriangle className="size-4 text-red-400" />
              )}
              <span>
                <strong>System Health Probe:</strong> {healthResult.status} ({healthResult.latency_ms} ms roundtrip)
              </span>
            </div>
            <button
              onClick={() => setHealthResult(null)}
              className="text-slate-400 hover:text-white text-xs underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Backup Success Banner */}
        {backupSuccessMessage && (
          <div className="p-3.5 rounded-xl border bg-amber-950/40 border-amber-500/40 text-amber-300 flex items-center justify-between font-mono text-xs">
            <div className="flex items-center gap-2">
              <Archive className="size-4 text-amber-400" />
              <span>{backupSuccessMessage}</span>
            </div>
            <button
              onClick={() => setBackupSuccessMessage(null)}
              className="text-slate-400 hover:text-white text-xs underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ── SEVEN-MATRIX SYSTEM STATUS DASHBOARD ──────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
          {/* 1. APPLICATION */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>APPLICATION</span>
              <Server className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.application?.status || 'HEALTHY'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              {statusData?.version || 'v2.9.0'}
            </div>
          </div>

          {/* 2. DATABASE */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>DATABASE</span>
              <Database className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.database?.status || 'HEALTHY'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              {statusData?.subsystems?.database?.engine} • {statusData?.subsystems?.database?.latency_ms || 1.2} ms
            </div>
          </div>

          {/* 3. STORAGE */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>STORAGE</span>
              <HardDrive className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.storage?.status || 'HEALTHY'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              {statusData?.subsystems?.storage?.free_percentage}% free
            </div>
          </div>

          {/* 4. WORKER */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>WORKER</span>
              <Cpu className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.worker?.status || 'RUNNING'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              Queue: Active
            </div>
          </div>

          {/* 5. SCHEDULED TASKS */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>TASKS</span>
              <Clock className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.scheduled_tasks?.status || 'ACTIVE'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              Cron active
            </div>
          </div>

          {/* 6. BACKUP */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>BACKUP</span>
              <Archive className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.backup?.status || 'SUCCESSFUL'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              {statusData?.subsystems?.backup?.archive_count || 0} snapshots
            </div>
          </div>

          {/* 7. NETWORK */}
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1 col-span-2 sm:col-span-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
              <span>NETWORK</span>
              <Radio className="size-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400">
              {statusData?.subsystems?.network?.status || 'ONLINE'}
            </div>
            <div className="text-[10px] text-slate-500 font-mono truncate">
              {statusData?.server_name || 'Node Active'}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 overflow-x-auto space-x-2">
          {[
            { id: 'status', label: 'Subsystems & Network', icon: Layers },
            { id: 'backups', label: 'Backup History & Snapshots', icon: Archive },
            { id: 'diagnostics', label: 'System Diagnostics & Pool', icon: Cpu },
            { id: 'logs', label: 'Live Application Logs', icon: Terminal },
            { id: 'updates', label: 'Platform Updates & Version', icon: Activity },
          ].map((t) => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id as 'status' | 'backups' | 'diagnostics' | 'logs' | 'updates')}
                className={`py-3 px-4 text-xs font-bold font-mono border-b-2 whitespace-nowrap transition-all flex items-center gap-2 ${
                  isActive
                    ? 'border-amber-500 text-amber-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="size-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* ── TAB 1: SUBSYSTEMS & NETWORK ──────────────────────────────── */}
        {activeTab === 'status' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <Server className="size-4 text-amber-500" />
                  Authoritative Platform Specifications
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Authoritative runtime variables configured on the Ubuntu host.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between"><span className="text-slate-500">Platform Core:</span> <span className="text-white">{statusData?.platform}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Node Identifier:</span> <span className="text-amber-400">{statusData?.server_name}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Environment:</span> <span className="text-emerald-400 uppercase">{statusData?.environment}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Timezone:</span> <span className="text-white">{statusData?.timezone}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Active Version:</span> <span className="text-white">{statusData?.version}</span></div>
                </div>
              </CardContent>
            </Card>

            {/* Optional Secure Remote Connectivity Transport */}
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <Radio className="size-4 text-emerald-400" />
                  Optional Secure Remote Connectivity (Transport Layer)
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Provider-agnostic encrypted transport overlay (e.g. Tailscale / WireGuard mesh).
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono space-y-1">
                    <div className="text-slate-500 text-[10px]">INTEGRATION MODE</div>
                    <div className="font-bold text-white uppercase">{statusData?.subsystems?.remote_network?.engine || 'LOCAL_NETWORK'}</div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono space-y-1">
                    <div className="text-slate-500 text-[10px]">SECURITY LEVEL</div>
                    <div className="font-bold text-amber-400">AUTHORITATIVE CORE</div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono space-y-1">
                    <div className="text-slate-500 text-[10px]">TRANSPORT STATUS</div>
                    <div className={`font-bold ${statusData?.subsystems?.remote_network?.status === 'CONNECTED' ? 'text-emerald-400' : 'text-slate-400'}`}>
                      {statusData?.subsystems?.remote_network?.status || 'STANDBY'}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono space-y-1">
                    <div className="text-slate-500 text-[10px]">VIRTUAL MESH IP</div>
                    <div className="text-slate-300 font-mono truncate">{statusData?.subsystems?.remote_network?.virtual_ip || 'None (LAN/Domain Direct)'}</div>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 font-mono space-y-1">
                  <div className="text-amber-400 font-bold flex items-center gap-1.5">
                    <Lock className="size-3.5" /> Core Security Hierarchy:
                  </div>
                  <div>Transport Layer (LAN / Tailscale / Mesh) → App Auth (JWT) → RBAC (Capabilities) → Object Authorization (AuthzGuard) → Workflow Authority.</div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── TAB 2: BACKUP ARCHIVES & HISTORY ─────────────────────────── */}
        {activeTab === 'backups' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Disaster Recovery Snapshots & Retention</span>
                  <Badge variant="outline" className="border-amber-500/40 text-amber-400 font-mono text-[10px]">
                    RETENTION: {backupsData?.retention_days || 30} DAYS
                  </Badge>
                </h3>
                <p className="text-xs text-slate-400">
                  Authoritative repository: {backupsData?.backup_directory || '/var/dwrms/backups'}. All snapshots cryptographically verified via SHA-256.
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => setShowBackupModal(true)}
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
              >
                <Archive className="size-3.5 mr-1.5" />
                Create New Snapshot
              </Button>
            </div>

            {verifyResult && (
              <div className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
                verifyResult.valid
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : 'bg-red-950/40 border-red-500/40 text-red-300'
              }`}>
                <div className="flex items-center gap-2">
                  {verifyResult.valid ? (
                    <CheckCircle2 className="size-4 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="size-4 text-red-400" />
                  )}
                  <span><strong>{verifyResult.filename}:</strong> {verifyResult.message}</span>
                </div>
                <button
                  onClick={() => setVerifyResult(null)}
                  className="text-slate-400 hover:text-white text-xs underline cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            )}

            <Card className="bg-slate-900 border-slate-800">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead className="text-slate-400 font-mono text-xs">Archive / ID</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs">Type</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs">Engine / Version</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs">Size</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs">Created At</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs">Integrity</TableHead>
                    <TableHead className="text-slate-400 font-mono text-xs text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backupsData?.archives?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-xs text-slate-500">
                        No backup archives created yet. Click &apos;Create New Snapshot&apos; to generate the first archive.
                      </TableCell>
                    </TableRow>
                  ) : (
                    backupsData?.archives?.map((b: BackupArchiveItem) => (
                      <TableRow key={b.filename} className="border-slate-800 hover:bg-slate-800/40">
                        <TableCell className="font-mono text-xs font-bold text-white">
                          <div className="flex items-center gap-2">
                            <Archive className="size-3.5 text-amber-500 shrink-0" />
                            <div>
                              <div>{b.filename}</div>
                              <div className="text-[10px] text-slate-500 font-normal">{b.backup_id}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={`text-[10px] ${
                            b.backup_type === 'PRE_RESTORE_SAFETY'
                              ? 'border-blue-500/40 text-blue-400 bg-blue-500/10'
                              : 'border-slate-700 text-slate-300'
                          }`}>
                            {b.backup_type || 'MANUAL'}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-300">
                          <div>{b.database_engine || 'MYSQL'}</div>
                          <div className="text-[10px] text-slate-500">{b.platform_version || 'v2.8.0'}</div>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-300">
                          {b.size_mb} MB
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-400">
                          {new Date(b.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 text-[10px]">
                            <CheckCircle2 className="size-3 mr-1" /> {b.integrity_status || 'VERIFIED'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={verifyingArchive === b.filename}
                              onClick={() => handleVerifyBackup(b.filename)}
                              className="h-6 px-2 text-[11px] font-mono border-slate-700 hover:bg-slate-800 text-slate-300"
                            >
                              <ShieldCheck className="size-3 mr-1" />
                              {verifyingArchive === b.filename ? 'Verifying...' : 'Verify'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setRestoreModalTarget(b);
                                setRestoreConfirmText('');
                              }}
                              className="h-6 px-2 text-[11px] font-mono border-red-500/40 text-red-400 hover:bg-red-950/40"
                            >
                              <RotateCcw className="size-3 mr-1" />
                              Restore
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Card>
          </div>
        )}

        {/* ── TAB 3: DIAGNOSTICS & HARDWARE METRICS ─────────────────────── */}
        {activeTab === 'diagnostics' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CPU & Memory */}
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <Cpu className="size-4 text-primary" /> CPU & Memory Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between"><span className="text-slate-500">CPU Utilization:</span> <span className="text-white">{diagnosticsData?.cpu_usage_pct ?? 0}%</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Memory Total:</span> <span className="text-white">{diagnosticsData?.memory?.total_mb} MB</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Memory Used:</span> <span className="text-amber-400">{diagnosticsData?.memory?.used_pct}%</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Available:</span> <span className="text-emerald-400">{diagnosticsData?.memory?.available_mb} MB</span></div>
                </div>
              </CardContent>
            </Card>

            {/* Storage Drive Metrics */}
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <HardDrive className="size-4 text-emerald-400" /> Disk & Attachment Volume
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between"><span className="text-slate-500">Total Capacity:</span> <span className="text-white">{diagnosticsData?.disk?.total_gb} GB</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Free Space:</span> <span className="text-emerald-400">{diagnosticsData?.disk?.free_gb} GB</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Disk Used:</span> <span className="text-white">{diagnosticsData?.disk?.used_pct}%</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Write Status:</span> <span className="text-emerald-400 font-bold">PERMITTED</span></div>
                </div>
              </CardContent>
            </Card>

            {/* Database Connection Pool */}
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <Database className="size-4 text-blue-400" /> Database Connection Pool
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between"><span className="text-slate-500">Engine:</span> <span className="text-white">{diagnosticsData?.database_pool?.engine?.toUpperCase()}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Pool Size:</span> <span className="text-white">{diagnosticsData?.database_pool?.size}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Checked In:</span> <span className="text-emerald-400">{diagnosticsData?.database_pool?.checked_in}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Checked Out:</span> <span className="text-amber-400">{diagnosticsData?.database_pool?.checked_out}</span></div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── TAB 4: LIVE APPLICATION LOGS ─────────────────────────────── */}
        {activeTab === 'logs' && (
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900 p-3 rounded-xl border border-slate-800">
              {/* Level Filter Pills */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-mono text-slate-400 mr-2 flex items-center gap-1">
                  <Filter className="size-3.5" /> Level:
                </span>
                {['ALL', 'INFO', 'WARNING', 'ERROR'].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setLogLevelFilter(lvl)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                      logLevelFilter === lvl
                        ? 'bg-amber-500 text-slate-950 font-bold'
                        : 'bg-slate-950 text-slate-400 hover:text-white'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div className="w-full sm:w-72">
                <Input
                  prefixIcon={<Search className="size-3.5" />}
                  placeholder="Filter logs by keyword..."
                  value={logSearchQuery}
                  onChange={(e) => setLogSearchQuery(e.target.value)}
                  className="h-8 bg-slate-950 border-slate-700 font-mono text-xs text-slate-100"
                />
              </div>
            </div>

            {/* Log Stream Terminal View */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs overflow-x-auto max-h-125 overflow-y-auto space-y-1 shadow-inner">
              {filteredLogs.length === 0 ? (
                <div className="text-slate-500 text-center py-8">No log records match the current filter.</div>
              ) : (
                filteredLogs.map((log, idx) => {
                  const isErr = log.level === 'ERROR';
                  const isWarn = log.level === 'WARNING';
                  return (
                    <div
                      key={idx}
                      className={`leading-relaxed whitespace-pre-wrap ${
                        isErr
                          ? 'text-red-400 bg-red-950/20 px-1 rounded'
                          : isWarn
                          ? 'text-amber-400'
                          : 'text-slate-300'
                      }`}
                    >
                      {log.raw}
                    </div>
                  );
                })
              )}
            </div>
            <p className="text-[10px] text-slate-500 font-mono">
              Note: Database credentials, secret keys, and JWT secrets are automatically redacted from console output.
            </p>
          </div>
        )}

        {/* ── TAB 5: UPDATES & VERSION ─────────────────────────────────── */}
        {activeTab === 'updates' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="size-4 text-emerald-400" />
                  <span>Platform Version & Controlled Update Policy</span>
                  <Badge variant="outline" className="border-amber-500/40 text-amber-400 font-mono text-[10px]">
                    CHANNEL: {updateData?.channel || 'enterprise_lts'}
                  </Badge>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Update Policy: <strong className="text-slate-200">CONTROLLED MANUAL</strong> • Updates require explicit admin validation and safety snapshots.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isCheckingUpdate}
                  onClick={handleCheckUpdates}
                  className="border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-mono"
                >
                  <RefreshCw className={`size-3.5 mr-1.5 ${isCheckingUpdate ? 'animate-spin' : ''}`} />
                  {isCheckingUpdate ? 'Checking Channel...' : 'Check for Updates'}
                </Button>
                <Button
                  size="sm"
                  disabled={isApplyingUpdate}
                  onClick={() => handleApplyUpdate(updateData?.installed_version)}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
                >
                  <Play className="size-3.5 mr-1.5" />
                  {isApplyingUpdate ? 'Running 8-Step Pipeline...' : 'Execute Update Pipeline'}
                </Button>
              </div>
            </div>

            {updateCheckResult && (
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="size-4 text-emerald-400" />
                  <span>{updateCheckResult.message}</span>
                </div>
                <button
                  onClick={() => setUpdateCheckResult(null)}
                  className="text-slate-400 hover:text-white text-xs underline cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            )}

            {updateApplyResult && (
              <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-xl space-y-3 font-mono text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="size-5" />
                  <span>{updateApplyResult.message}</span>
                </div>
                <div className="space-y-1 text-slate-300 text-[11px]">
                  <div className="font-bold text-amber-400">8-Step Pipeline Verification Log:</div>
                  {updateApplyResult.pipeline_steps_completed?.map((step: string, idx: number) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="text-emerald-400">✓</span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Authoritative Version Matrix */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-2">
                <Layers className="size-3.5 text-primary" /> Authoritative Multi-Tier Version Matrix
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">SERVER PLATFORM CORE</CardDescription>
                    <CardTitle className="text-base font-mono text-white flex items-center justify-between">
                      <span>{updateData?.installed_version || 'v2.9.0'}</span>
                      <Badge className="bg-emerald-600 text-[10px]">ACTIVE</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    Ubuntu Server Authoritative Operational Core
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">BACKEND REST API</CardDescription>
                    <CardTitle className="text-base font-mono text-white flex items-center justify-between">
                      <span>{updateData?.api_version || 'v1'} ({updateData?.installed_version || 'v2.9.0'})</span>
                      <Badge className="bg-emerald-600 text-[10px]">AUTH V1</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    Authoritative Django/FastAPI API Endpoints
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">DATABASE SCHEMA</CardDescription>
                    <CardTitle className="text-base font-mono text-white flex items-center justify-between">
                      <span>{updateData?.schema_version || '2026.08.28.01'}</span>
                      <Badge className="bg-blue-600 text-[10px]">APPLIED</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    Relational Schema
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">WEB CLIENT (NEXT.JS)</CardDescription>
                    <CardTitle className="text-base font-mono text-white flex items-center justify-between">
                      <span>{updateData?.web_client_version || 'v2.9.0'}</span>
                      <Badge className="bg-emerald-600 text-[10px]">PWA READY</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    First-Class Browser & Responsive Mobile PWA
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">DESKTOP CLIENT (TAURI)</CardDescription>
                    <CardTitle className="text-base font-mono text-white flex items-center justify-between">
                      <span>{updateData?.desktop_client_version || 'v2.9.0'}</span>
                      <Badge className="bg-purple-600 text-[10px]">DESKTOP</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    Cross-Platform Tauri Native Application
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardDescription className="text-[10px] text-slate-500 font-mono">MIN COMPATIBLE CLIENT</CardDescription>
                    <CardTitle className="text-base font-mono text-amber-400 flex items-center justify-between">
                      <span>{updateData?.min_supported_client_version || 'v2.0.0'}</span>
                      <Badge variant="outline" className="border-amber-500/40 text-amber-400 text-[10px]">MIN THRESHOLD</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-[11px] text-slate-400 font-mono">
                    Connecting clients below this version will be rejected
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* 8-Step Controlled Update Lifecycle Standard */}
            <Card className="bg-slate-900 border-slate-800 text-slate-100">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="size-4 text-emerald-400" />
                  <span>8-Step Controlled Platform Update Lifecycle</span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Every software release follows this non-destructive sequential pipeline. Automatic rollback triggers if health verification fails.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-xs font-mono space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">01.</span>
                    <span>Validate current system health & storage writes</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">02.</span>
                    <span>Check target version compatibility & breaking changes</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">03.</span>
                    <span>Create pre-upgrade safety snapshot with SHA-256</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">04.</span>
                    <span>Stage and apply application code updates</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">05.</span>
                    <span>Apply database schema migrations transactionally</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">06.</span>
                    <span>Gracefully restart backend & background workers</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">07.</span>
                    <span>Execute post-update health & latency checks</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                    <span className="text-amber-400 font-bold">08.</span>
                    <span>Smoke test critical operational workflows (Auth/Jobs)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Backup Creation Modal */}
        <Dialog open={showBackupModal} onOpenChange={setShowBackupModal}>
          <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-slate-100" showCloseButton={false}>
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-white flex items-center gap-2">
                <Archive className="size-5 text-amber-500" />
                Initiate Platform Snapshot
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                Creates a verified disaster recovery archive containing database records and file storage manifests.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3 text-xs">
              <div className="space-y-1.5">
                <label className="text-slate-300 font-semibold">Snapshot Reference Note</label>
                <Input
                  value={backupNote}
                  onChange={(e) => setBackupNote(e.target.value)}
                  placeholder="e.g. Pre-migration maintenance snapshot"
                  className="bg-slate-950 border-slate-700 text-xs"
                />
              </div>

              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 text-xs flex items-center gap-2">
                <Lock className="size-4 shrink-0 text-amber-400" />
                <span>The backup snapshot will be saved with a cryptographically verified SHA-256 hash in the authoritative backup repository.</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowBackupModal(false)}
                disabled={isCreatingBackup}
                className="text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleCreateBackup}
                disabled={isCreatingBackup}
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
              >
                {isCreatingBackup ? 'Generating Archive...' : 'Confirm & Create Snapshot'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Disaster Recovery Restore Modal */}
        <Dialog open={!!restoreModalTarget} onOpenChange={(open) => { if (!open) setRestoreModalTarget(null); }}>
          <DialogContent className="sm:max-w-md bg-slate-900 border-red-500/40 text-slate-100" showCloseButton={false}>
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-red-400 flex items-center gap-2">
                <AlertTriangle className="size-5 text-red-500" />
                Confirm Disaster Recovery Restore
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                You are about to restore the system from snapshot: <strong className="text-white font-mono">{restoreModalTarget?.filename}</strong>.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3 text-xs">
              <div className="p-3 bg-red-950/60 border border-red-500/50 rounded-lg text-red-300 text-xs space-y-2">
                <div className="font-bold flex items-center gap-1.5 text-red-400">
                  <Lock className="size-4 shrink-0" /> CRITICAL DATA WARNING:
                </div>
                <div>
                  Restoration will overwrite active database records and attachment files. A pre-restore safety snapshot will automatically be generated prior to applying changes.
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-slate-300 font-semibold font-mono text-[11px]">
                  Type <span className="text-red-400 font-bold">CONFIRM RESTORE</span> to proceed:
                </label>
                <Input
                  value={restoreConfirmText}
                  onChange={(e) => setRestoreConfirmText(e.target.value)}
                  placeholder="CONFIRM RESTORE"
                  className="bg-slate-950 border-red-500/40 text-red-300 font-mono text-xs"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRestoreModalTarget(null)}
                disabled={isRestoring}
                className="text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleRestoreBackup}
                disabled={isRestoring || restoreConfirmText !== 'CONFIRM RESTORE'}
                className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs disabled:opacity-50"
              >
                {isRestoring ? 'Applying Restoration...' : 'Execute Restoration'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Protect>
  );
}
