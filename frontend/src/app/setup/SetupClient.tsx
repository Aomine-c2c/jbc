'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Server,
  Database,
  Shield,
  HardDrive,
  Archive,
  Network,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Lock,
  Globe,
  Radio,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api';

const STEPS = [
  { id: 1, title: 'Platform', icon: Server, desc: 'Organization & Server' },
  { id: 2, title: 'Network', icon: Globe, desc: 'Endpoints & CORS' },
  { id: 3, title: 'Database', icon: Database, desc: 'Engine & Credentials' },
  { id: 4, title: 'Admin', icon: Shield, desc: 'Initial Superuser' },
  { id: 5, title: 'Storage', icon: HardDrive, desc: 'Attachments & Space' },
  { id: 6, title: 'Backups', icon: Archive, desc: 'Disaster Recovery' },
  { id: 7, title: 'Remote', icon: Radio, desc: 'Network Access' },
  { id: 8, title: 'Verify', icon: CheckCircle2, desc: 'System Finalize' },
];

export function SetupClient() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    // Step 1: Platform & Organization
    organization_name: 'Bikita Minerals DWRMS',
    installation_name: 'Masvingo Lithium Operation',
    primary_site: 'Bikita Mining Site 1',
    server_name: 'masvingo-srv-01',
    environment: 'production',
    timezone: 'Africa/Harare',

    // Step 2: Server & Network
    primary_url: typeof window !== 'undefined' ? window.location.origin : 'https://dwrms.bikita.com',
    domain_name: 'dwrms.bikita.com',
    internal_address: '192.168.1.100',
    local_ip: '192.168.1.100',
    https_enabled: true,
    cors_origins: 'https://dwrms.bikita.com,http://localhost:3000,tauri://localhost',

    // Step 3: Database
    db_engine: 'mysql',
    db_host: 'db',
    db_port: 3306,
    db_name: 'dwrms',
    db_user: 'user',
    db_password: '',

    // Step 4: Administrator
    admin_email: 'admin@bikita.com',
    admin_fname: 'System',
    admin_lname: 'Administrator',
    admin_dept: 'Maintenance',
    admin_password: '',
    admin_confirm_password: '',

    // Step 5: Storage
    storage_path: '/var/dwrms/storage',
    max_upload_size_mb: 25,

    // Step 6: Backups
    backup_path: '/var/dwrms/backups',
    backup_freq: 'daily',
    retention_days: 30,

    // Step 7: Remote Access
    remote_mode: 'local_only', // local_only, org_managed, tailscale
    tailscale_auth_key: '',
  });

  // Pre-flight test results
  const [dbTestResult, setDbTestResult] = useState<{ status: 'idle' | 'testing' | 'success' | 'error'; message?: string; latency?: number }>({ status: 'idle' });
  const [storageTestResult, setStorageTestResult] = useState<{ status: 'idle' | 'testing' | 'success' | 'error'; freeGb?: number; freePct?: number; message?: string }>({ status: 'idle' });
  const [finalReport, setFinalReport] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    // Check initial setup status from backend
    async function checkStatus() {
      try {
        const res = await apiClient.get('/setup/status');
        if (res.data.is_completed) {
          setIsCompleted(true);
          setCurrentStep(8);
        } else if (res.data.current_step) {
          setCurrentStep(res.data.current_step);
          if (res.data.state) {
            // merge saved state if any
            const s = res.data.state;
            setFormData((prev) => ({
              ...prev,
              ...(s.step_1_platform || {}),
              ...(s.step_2_network || {}),
              ...(s.step_3_database || {}),
              ...(s.step_4_admin || {}),
              ...(s.step_5_storage || {}),
              ...(s.step_6_backups || {}),
              ...(s.step_7_remote || {}),
            }));
          }
        }
      } catch (err) {
        console.log('Setup status probe deferred:', err);
      }
    }
    checkStatus();
  }, []);

  const handleChange = (field: string, value: string | boolean | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setStatusMessage(null);
  };

  // Test Database Connection
  const handleTestDatabase = async () => {
    setDbTestResult({ status: 'testing' });
    try {
      const res = await apiClient.post('/setup/test-db', {
        engine: formData.db_engine,
        host: formData.db_host,
        port: Number(formData.db_port),
        name: formData.db_name,
        user: formData.db_user,
        password: formData.db_password,
      });
      setDbTestResult({
        status: 'success',
        latency: res.data.latency_ms,
        message: `Connected successfully (${res.data.latency_ms} ms round-trip)`,
      });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setDbTestResult({
        status: 'error',
        message: e.response?.data?.detail || 'Failed to connect to database.',
      });
    }
  };

  // Test Storage
  const handleTestStorage = async () => {
    setStorageTestResult({ status: 'testing' });
    try {
      const res = await apiClient.post('/setup/test-storage', {
        path: formData.storage_path,
      });
      setStorageTestResult({
        status: 'success',
        freeGb: res.data.free_gb,
        freePct: res.data.free_percentage,
        message: `Path writable: ${res.data.free_gb} GB free space (${res.data.free_percentage}%)`,
      });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setStorageTestResult({
        status: 'error',
        message: e.response?.data?.detail || 'Storage directory unwritable.',
      });
    }
  };

  // Step Navigation
  const handleNext = async () => {
    setStatusMessage(null);

    // Step-specific validations
    if (currentStep === 4) {
      if (formData.admin_password && formData.admin_password.length < 8) {
        setStatusMessage({ type: 'error', text: 'Administrator password must be at least 8 characters long.' });
        return;
      }
      if (formData.admin_password !== formData.admin_confirm_password) {
        setStatusMessage({ type: 'error', text: 'Passwords do not match.' });
        return;
      }
    }

    // Save step progress to backend
    try {
      setLoading(true);
      await apiClient.post(`/setup/step/${currentStep}`, {
        step_data: formData,
      });
      setCurrentStep((prev) => Math.min(prev + 1, 8));
    } catch (err) {
      // Continue anyway for local testing
      setCurrentStep((prev) => Math.min(prev + 1, 8));
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
    setStatusMessage(null);
  };

  // Step 8 Finalize
  const handleFinalize = async () => {
    setLoading(true);
    setStatusMessage(null);
    try {
      const payload = {
        step_1_platform: {
          organization_name: formData.organization_name,
          installation_name: formData.installation_name,
          server_name: formData.server_name,
          environment: formData.environment,
          timezone: formData.timezone,
        },
        step_2_network: {
          primary_url: formData.primary_url,
          domain_name: formData.domain_name,
          local_ip: formData.local_ip,
          https_enabled: formData.https_enabled,
          cors_origins: formData.cors_origins,
        },
        step_3_database: {
          engine: formData.db_engine,
          host: formData.db_host,
          port: Number(formData.db_port),
          name: formData.db_name,
          user: formData.db_user,
          password: formData.db_password,
        },
        step_4_admin: {
          email: formData.admin_email,
          first_name: formData.admin_fname,
          last_name: formData.admin_lname,
          department: formData.admin_dept,
          password: formData.admin_password,
        },
        step_5_storage: {
          path: formData.storage_path,
          max_upload_size_mb: Number(formData.max_upload_size_mb),
        },
        step_6_backups: {
          path: formData.backup_path,
          frequency: formData.backup_freq,
          retention_days: Number(formData.retention_days),
        },
        step_7_remote: {
          mode: formData.remote_mode,
          tailscale_auth_key: formData.tailscale_auth_key,
        },
      };

      const res = await apiClient.post('/setup/finalize', { config: payload });
      setFinalReport(res.data);
      setIsCompleted(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setStatusMessage({
        type: 'error',
        text: e.response?.data?.detail || 'Finalization failed. Please verify database and permissions.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 md:p-8">
      {/* Header Branding */}
      <div className="w-full max-w-4xl mb-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
          <Server className="w-3.5 h-3.5" /> Authoritative Server Setup Wizard
        </div>
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">Bikita Minerals DWRMS</h1>
        <p className="text-slate-400 text-sm mt-1">Platform First-Time Installation & Architecture Configuration (V2.1)</p>
      </div>

      {/* 8-Step Stepper Progress Bar */}
      <div className="w-full max-w-4xl mb-8 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[640px] bg-slate-900/80 border border-slate-800 rounded-xl p-3 shadow-lg backdrop-blur">
          {STEPS.map((s, idx) => {
            const Icon = s.icon;
            const isCurrent = currentStep === s.id;
            const isPassed = currentStep > s.id || isCompleted;

            return (
              <div key={s.id} className="flex items-center gap-2">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs transition-all ${
                    isPassed
                      ? 'bg-emerald-600 text-white'
                      : isCurrent
                      ? 'bg-amber-500 text-slate-950 ring-2 ring-amber-400 ring-offset-2 ring-offset-slate-950 shadow-md shadow-amber-500/20'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isPassed ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                <div className="hidden sm:block">
                  <div className={`text-xs font-bold ${isCurrent ? 'text-white' : 'text-slate-400'}`}>{s.title}</div>
                  <div className="text-[10px] text-slate-500">{s.desc}</div>
                </div>
                {idx < STEPS.length - 1 && <div className="w-4 h-0.5 bg-slate-800 hidden md:block" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Wizard Card */}
      <Card className="w-full max-w-4xl bg-slate-900 border-slate-800 shadow-2xl text-slate-100">
        <CardHeader className="border-b border-slate-800 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                {STEPS[currentStep - 1].title}: {STEPS[currentStep - 1].desc}
              </CardTitle>
              <CardDescription className="text-slate-400">Step {currentStep} of 8 — Required for Authoritative Core Operations</CardDescription>
            </div>
            <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/5">
              Stage {currentStep}/8
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-6">
          {/* Status / Alert Message */}
          {statusMessage && (
            <div
              className={`p-3 rounded-lg flex items-center gap-2 text-sm border ${
                statusMessage.type === 'error'
                  ? 'bg-red-500/10 border-red-500/30 text-red-400'
                  : statusMessage.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
              }`}
            >
              {statusMessage.type === 'error' ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
              <span>{statusMessage.text}</span>
            </div>
          )}

          {/* ── STEP 1: PLATFORM CONFIGURATION ────────────────────────── */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Organization Name</Label>
                  <Input
                    value={formData.organization_name}
                    onChange={(e) => handleChange('organization_name', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                  <p className="text-xs text-slate-500">Corporate entity or operational group name.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Installation / Mine Site Name</Label>
                  <Input
                    value={formData.installation_name}
                    onChange={(e) => handleChange('installation_name', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                  <p className="text-xs text-slate-500">Physical facility location or project zone.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label>Server Node Identifier</Label>
                  <Input
                    value={formData.server_name}
                    onChange={(e) => handleChange('server_name', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Unique server host identifier.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Deployment Environment</Label>
                  <select
                    value={formData.environment}
                    onChange={(e) => handleChange('environment', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-slate-950 border border-slate-700 text-sm text-slate-100"
                  >
                    <option value="production">Production (Hardened)</option>
                    <option value="staging">Staging (Testing)</option>
                    <option value="development">Development (Debug)</option>
                  </select>
                  <p className="text-xs text-slate-500">Security and logging profile.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Operational Timezone</Label>
                  <Input
                    value={formData.timezone}
                    onChange={(e) => handleChange('timezone', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">e.g. Africa/Harare, UTC, CAT.</p>
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 2: NETWORK CONFIGURATION ─────────────────────────── */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="p-3 bg-blue-950/30 border border-blue-800/40 rounded-lg text-xs text-blue-300 flex items-center gap-2">
                <Globe className="w-4 h-4 shrink-0" />
                <span>Fixed public IP is NOT required. Dynamic DNS, internal LAN IP addresses, and reverse proxies are fully supported.</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Primary Application URL</Label>
                  <Input
                    value={formData.primary_url}
                    onChange={(e) => handleChange('primary_url', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">The authoritative URL used by operators and desktop clients.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Domain Name (where applicable)</Label>
                  <Input
                    value={formData.domain_name}
                    onChange={(e) => handleChange('domain_name', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Public or internal FQDN (e.g. dwrms.bikita.com).</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Local LAN Binding IP</Label>
                  <Input
                    value={formData.local_ip}
                    onChange={(e) => handleChange('local_ip', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Internal network interface IP address.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Trusted CORS Origins</Label>
                  <Input
                    value={formData.cors_origins}
                    onChange={(e) => handleChange('cors_origins', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-xs"
                  />
                  <p className="text-xs text-slate-500">Comma-separated allowlist for API clients.</p>
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 3: DATABASE CONFIGURATION & PRE-FLIGHT ───────────── */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label>Database Engine</Label>
                  <select
                    value={formData.db_engine}
                    onChange={(e) => handleChange('db_engine', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-slate-950 border border-slate-700 text-sm text-slate-100"
                  >
                    <option value="postgresql">PostgreSQL 16 (Recommended)</option>
                    <option value="mysql">MySQL 8.0</option>
                    <option value="sqlite">SQLite (Embedded / Testing)</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label>Database Host</Label>
                  <Input
                    value={formData.db_host}
                    onChange={(e) => handleChange('db_host', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Database Port</Label>
                  <Input
                    type="number"
                    value={formData.db_port}
                    onChange={(e) => handleChange('db_port', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label>Database Name</Label>
                  <Input
                    value={formData.db_name}
                    onChange={(e) => handleChange('db_name', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Database User</Label>
                  <Input
                    value={formData.db_user}
                    onChange={(e) => handleChange('db_user', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Database Password</Label>
                  <Input
                    type="password"
                    value={formData.db_password}
                    onChange={(e) => handleChange('db_password', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
              </div>

              {/* Pre-flight test button */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-800">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleTestDatabase}
                  disabled={dbTestResult.status === 'testing'}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-100"
                >
                  <Database className="w-4 h-4 mr-2" />
                  {dbTestResult.status === 'testing' ? 'Testing Connection...' : 'Test Database Connection'}
                </Button>

                {dbTestResult.status === 'success' && (
                  <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-400 p-2">
                    <CheckCircle2 className="w-4 h-4 mr-1" /> {dbTestResult.message}
                  </Badge>
                )}
                {dbTestResult.status === 'error' && (
                  <Badge variant="outline" className="border-red-500/50 bg-red-500/10 text-red-400 p-2">
                    <AlertCircle className="w-4 h-4 mr-1" /> {dbTestResult.message}
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* ── STEP 4: INITIAL ADMINISTRATOR ACCOUNT ─────────────────── */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Administrator Email</Label>
                  <Input
                    type="email"
                    value={formData.admin_email}
                    onChange={(e) => handleChange('admin_email', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                  <p className="text-xs text-slate-500">Will be granted System Administrator role.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Primary Department</Label>
                  <Input
                    value={formData.admin_dept}
                    onChange={(e) => handleChange('admin_dept', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>First Name</Label>
                  <Input
                    value={formData.admin_fname}
                    onChange={(e) => handleChange('admin_fname', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Last Name</Label>
                  <Input
                    value={formData.admin_lname}
                    onChange={(e) => handleChange('admin_lname', e.target.value)}
                    className="bg-slate-950 border-slate-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1.5">
                  <Label>Secure Administrator Password</Label>
                  <Input
                    type="password"
                    value={formData.admin_password}
                    onChange={(e) => handleChange('admin_password', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono"
                  />
                  <p className="text-xs text-slate-500">Minimum 8 characters with numbers and mixed case.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Confirm Password</Label>
                  <Input
                    type="password"
                    value={formData.admin_confirm_password}
                    onChange={(e) => handleChange('admin_confirm_password', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 5: FILE STORAGE CONFIGURATION ────────────────────── */}
          {currentStep === 5 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2 space-y-1.5">
                  <Label>Storage Directory Path</Label>
                  <Input
                    value={formData.storage_path}
                    onChange={(e) => handleChange('storage_path', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Persistent path for job cards, inspection reports, and signatures.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Max Attachment Size (MB)</Label>
                  <Input
                    type="number"
                    value={formData.max_upload_size_mb}
                    onChange={(e) => handleChange('max_upload_size_mb', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                </div>
              </div>

              {/* Pre-flight storage probe */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-800">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleTestStorage}
                  disabled={storageTestResult.status === 'testing'}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-100"
                >
                  <HardDrive className="w-4 h-4 mr-2" />
                  {storageTestResult.status === 'testing' ? 'Probing Disk Space...' : 'Probe Storage Capacity'}
                </Button>

                {storageTestResult.status === 'success' && (
                  <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-400 p-2">
                    <CheckCircle2 className="w-4 h-4 mr-1" /> {storageTestResult.message}
                  </Badge>
                )}
                {storageTestResult.status === 'error' && (
                  <Badge variant="outline" className="border-red-500/50 bg-red-500/10 text-red-400 p-2">
                    <AlertCircle className="w-4 h-4 mr-1" /> {storageTestResult.message}
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* ── STEP 6: BACKUPS & RETENTION POLICY ────────────────────── */}
          {currentStep === 6 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2 space-y-1.5">
                  <Label>Backup Archive Directory</Label>
                  <Input
                    value={formData.backup_path}
                    onChange={(e) => handleChange('backup_path', e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Destination for daily database dumps and storage tarballs.</p>
                </div>
                <div className="space-y-1.5">
                  <Label>Backup Frequency</Label>
                  <select
                    value={formData.backup_freq}
                    onChange={(e) => handleChange('backup_freq', e.target.value)}
                    className="w-full h-10 px-3 rounded-md bg-slate-950 border border-slate-700 text-sm text-slate-100"
                  >
                    <option value="daily">Daily (02:00 CAT)</option>
                    <option value="weekly">Weekly</option>
                    <option value="hourly">Hourly</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Retention Policy Window (Days)</Label>
                <Input
                  type="number"
                  value={formData.retention_days}
                  onChange={(e) => handleChange('retention_days', e.target.value)}
                  className="bg-slate-950 border-slate-700 font-mono text-sm w-48"
                />
                <p className="text-xs text-slate-500">Backups older than this retention window will be automatically pruned.</p>
              </div>
            </div>
          )}

          {/* ── STEP 7: OPTIONAL REMOTE CONNECTIVITY ──────────────────── */}
          {currentStep === 7 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div
                  onClick={() => handleChange('remote_mode', 'local_only')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    formData.remote_mode === 'local_only'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Network className="w-5 h-5 mb-2 text-amber-400" />
                  <div className="font-bold text-sm">Local Network Only</div>
                  <p className="text-xs mt-1 text-slate-400">Strict on-premise access within the mining facility LAN.</p>
                </div>

                <div
                  onClick={() => handleChange('remote_mode', 'org_managed')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    formData.remote_mode === 'org_managed'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Globe className="w-5 h-5 mb-2 text-blue-400" />
                  <div className="font-bold text-sm">Corporate VPN / Proxy</div>
                  <p className="text-xs mt-1 text-slate-400">Routed through corporate firewall, Nginx, or enterprise VPN.</p>
                </div>

                <div
                  onClick={() => handleChange('remote_mode', 'tailscale')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    formData.remote_mode === 'tailscale'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Radio className="w-5 h-5 mb-2 text-emerald-400" />
                  <div className="font-bold text-sm">Tailscale Mesh (Optional)</div>
                  <p className="text-xs mt-1 text-slate-400">Zero-config secure mesh network across distributed field laptops.</p>
                </div>
              </div>

              {formData.remote_mode === 'tailscale' && (
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                  <Label>Optional Tailscale Auth Key</Label>
                  <Input
                    type="password"
                    placeholder="tskey-auth-..."
                    value={formData.tailscale_auth_key}
                    onChange={(e) => handleChange('tailscale_auth_key', e.target.value)}
                    className="bg-slate-900 border-slate-700 font-mono text-sm"
                  />
                  <p className="text-xs text-slate-500">Leave blank to authenticate manually via &apos;tailscale up&apos;.</p>
                </div>
              )}

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-400 flex items-center gap-2">
                <Lock className="w-4 h-4 shrink-0 text-amber-400" />
                <span>SSH server administration operates independently on port 22 and is isolated from application user access.</span>
              </div>
            </div>
          )}

          {/* ── STEP 8: SYSTEM VERIFICATION & FINALIZATION ────────────── */}
          {currentStep === 8 && (
            <div className="space-y-6">
              {!isCompleted ? (
                <>
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Pre-Finalization Review</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                        <div className="font-bold text-slate-200">Platform & Identity</div>
                        <div className="text-slate-400">Org: {formData.organization_name}</div>
                        <div className="text-slate-400">Node: {formData.server_name} ({formData.environment})</div>
                      </div>
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                        <div className="font-bold text-slate-200">Network Endpoints</div>
                        <div className="text-slate-400">URL: {formData.primary_url}</div>
                        <div className="text-slate-400">Local IP: {formData.local_ip}</div>
                      </div>
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                        <div className="font-bold text-slate-200">Database & Engine</div>
                        <div className="text-slate-400">Engine: {formData.db_engine.toUpperCase()}</div>
                        <div className="text-slate-400">Target: {formData.db_host}:{formData.db_port}/{formData.db_name}</div>
                      </div>
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                        <div className="font-bold text-slate-200">Initial Administrator</div>
                        <div className="text-slate-400">Email: {formData.admin_email}</div>
                        <div className="text-slate-400">Name: {formData.admin_fname} {formData.admin_lname}</div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300">
                    <strong>Finalization Action:</strong> Clicking the button below will apply database schema migrations, seed default mining roles, provision the initial administrator account, and permanently lock the setup interface.
                  </div>
                </>
              ) : (
                <div className="space-y-4 text-center py-4">
                  <div className="w-16 h-16 bg-emerald-600/20 border border-emerald-500 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <h2 className="text-2xl font-bold text-white">Platform Setup Completed & Verified!</h2>
                  <p className="text-sm text-slate-400 max-w-lg mx-auto">
                    The authoritative Ubuntu Server core is online and locked against unauthorized re-configuration.
                  </p>

                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl max-w-md mx-auto text-left text-xs space-y-2">
                    <div className="flex justify-between"><span className="text-slate-500">Application URL:</span> <span className="font-mono text-white">{finalReport?.application_url || formData.primary_url}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Server Node:</span> <span className="text-white">{finalReport?.server_name || formData.server_name}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Admin Account:</span> <span className="text-white">{finalReport?.admin_email || formData.admin_email}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Status:</span> <Badge className="bg-emerald-600 text-white">ONLINE & LOCKED</Badge></div>
                  </div>

                  <div className="pt-4">
                    <Button
                      onClick={() => router.push('/login')}
                      className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-8"
                    >
                      Go to Operations Portal Login <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>

        <CardFooter className="border-t border-slate-800 pt-4 flex items-center justify-between">
          {!isCompleted ? (
            <>
              <Button
                type="button"
                variant="ghost"
                onClick={handleBack}
                disabled={currentStep === 1 || loading}
                className="text-slate-400 hover:text-white"
              >
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>

              {currentStep < 8 ? (
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={loading}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
                >
                  Continue to Step {currentStep + 1} <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={handleFinalize}
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {loading ? 'Finalizing Setup...' : 'Finalize Setup & Lock Server'} <CheckCircle2 className="w-4 h-4 ml-2" />
                </Button>
              )}
            </>
          ) : (
            <div className="w-full text-center text-xs text-slate-500">
              Setup is locked. Technical administration is managed via the &apos;ops&apos; CLI.
            </div>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
