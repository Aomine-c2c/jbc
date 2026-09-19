'use client';

import Image from 'next/image';
import { login } from '@/lib/auth';
import { useState, useEffect, useCallback } from 'react';
import { Lock, Mail, ChevronDown, AlertCircle, WifiOff, RefreshCw, CheckCircle2 } from 'lucide-react';
import { getProfiles, getActiveProfile, setActiveProfile, ServerProfile } from '@/lib/serverProfiles';
import { getApiUrl } from '@/lib/api';

const DEMO_ROLES = [
  { label: 'Admin',          email: 'admin@bikita.com',      pass: 'password123' },
  { label: 'Dept Manager',   email: 'mechmgr@bikita.com',    pass: 'password123' },
  { label: 'Supervisor',     email: 'supervisor@bikita.com', pass: 'password123' },
  { label: 'Technician',     email: 'tech@bikita.com',       pass: 'password123' },
  { label: 'Operator',       email: 'operator@bikita.com',   pass: 'password123' },
  { label: 'Safety Officer', email: 'safety@bikita.com',     pass: 'password123' },
];

type ServerStatus = 'checking' | 'online' | 'offline';

function isNetworkErrorMsg(msg: string): boolean {
  return (
    msg === 'Failed to fetch' ||
    msg === 'Load failed' ||
    msg.includes('NetworkError') ||
    msg.includes('ECONNREFUSED') ||
    msg.includes('unreachable') ||
    msg.includes('Failed to fetch') ||
    msg.includes('Load failed')
  );
}

export default function LoginPage() {
  const [email, setEmail]               = useState('');
  const [password, setPassword]         = useState('');
  const [error, setError]               = useState<string | null>(null);
  const [loading, setLoading]           = useState(false);
  const [profiles, setProfiles]         = useState<ServerProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string>('');
  const [demoOpen, setDemoOpen]         = useState(false);
  const [serverStatus, setServerStatus] = useState<ServerStatus>('checking');
  const [retrying, setRetrying]         = useState(false);

  // Proactive server health check
  const checkServer = useCallback(async (quiet = false) => {
    if (!quiet) setRetrying(true);
    try {
      const baseUrl = await getApiUrl();
      const cleanBase = baseUrl ? baseUrl.replace(/\/+$/, '') : '';
      const endpoint = cleanBase ? `${cleanBase}/api/v1/health` : '/api/v1/health';

      const res = await fetch(endpoint, {
        signal: AbortSignal.timeout(5000),
        cache: 'no-store',
      });
      setServerStatus(res.ok ? 'online' : 'offline');
      if (res.ok) setError(null);
    } catch {
      setServerStatus('offline');
    } finally {
      setRetrying(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    // Load profiles
    getProfiles().then((list) => {
      if (cancelled) return;
      setProfiles(list);
      getActiveProfile().then((active) => {
        if (cancelled) return;
        setActiveProfileId(active?.id || list[0]?.id || '');
      });
    });

    // Initial health probe
    checkServer(true);

    return () => { cancelled = true; };
  }, [checkServer]);

  const handleProfileChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setActiveProfileId(newId);
    await setActiveProfile(newId);
    setError(null);
    // Re-probe after profile switch
    setTimeout(() => checkServer(true), 300);
  };

  const doLogin = async (loginEmail: string, loginPass: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await login(loginEmail, loginPass);
      if (result?.error) {
        // Normalise raw browser network errors before displaying
        const raw = result.error;
        if (isNetworkErrorMsg(raw)) {
          setServerStatus('offline');
          setError('Cannot reach the operations server. Please ensure the backend is running and try again.');
        } else {
          setError(raw);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (email && password) doLogin(email, password);
  };

  const handleDemoSelect = (roleEmail: string, rolePass: string) => {
    setDemoOpen(false);
    setEmail(roleEmail);
    setPassword(rolePass);
    doLogin(roleEmail, rolePass);
  };

  const isOffline = serverStatus === 'offline';

  return (
    <div className="min-h-screen w-full bg-zinc-50 flex items-center justify-center p-4">

      {/* Server offline banner — shown above card */}
      {isOffline && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-sm">
          <div className="mx-4 flex items-start gap-2.5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 shadow-lg shadow-amber-100 text-xs text-amber-800">
            <WifiOff className="size-3.5 shrink-0 mt-0.5 text-amber-600" />
            <div className="flex-1">
              <span className="font-semibold">Operations server unreachable.</span>{' '}
              Ensure the backend service is running on port 8000.
            </div>
            <button
              type="button"
              onClick={() => checkServer()}
              disabled={retrying}
              className="shrink-0 flex items-center gap-1 text-amber-700 hover:text-amber-900 font-semibold transition-colors disabled:opacity-50 cursor-pointer"
              title="Retry connection"
            >
              <RefreshCw className={`size-3.5 ${retrying ? 'animate-spin' : ''}`} />
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Card */}
      <div className="w-full max-w-sm bg-white rounded-2xl border border-zinc-200 shadow-sm overflow-hidden">

        {/* Brand strip */}
        <div className="flex flex-col items-center gap-3 px-8 pt-8 pb-6 border-b border-zinc-100">
          <div className="size-12 rounded-xl border border-zinc-200 bg-white shadow-xs flex items-center justify-center p-1.5">
            <Image src="/bikita-emblem.png" alt="Bikita Minerals" width={36} height={36} className="object-contain" />
          </div>
          <div className="text-center">
            <h1 className="text-sm font-bold uppercase tracking-widest text-zinc-900">
              Bikita Minerals · DWRMS
            </h1>
            <p className="text-[11px] text-zinc-400 font-mono mt-0.5">Operations &amp; Resource Management Portal</p>
          </div>

          {/* Server status pill */}
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-semibold transition-colors ${
            serverStatus === 'online'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
              : serverStatus === 'offline'
              ? 'bg-rose-50 border border-rose-200 text-rose-700'
              : 'bg-zinc-50 border border-zinc-200 text-zinc-500'
          }`}>
            {serverStatus === 'online' && <CheckCircle2 className="size-3" />}
            {serverStatus === 'offline' && <WifiOff className="size-3" />}
            {serverStatus === 'checking' && <RefreshCw className="size-3 animate-spin" />}
            {serverStatus === 'online'   ? 'Server Online'
            : serverStatus === 'offline' ? 'Server Offline'
            : 'Checking…'}
          </div>
        </div>

        {/* Form body */}
        <div className="px-8 py-6 space-y-4">

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2.5 text-xs text-red-700">
              <AlertCircle className="size-3.5 mt-0.5 shrink-0" />
              <span>{error}</span>
              <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600 shrink-0 cursor-pointer">✕</button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Email */}
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-zinc-400" />
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                disabled={loading}
                className="h-10 w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm text-zinc-900 outline-none transition focus:border-[#2E2F83] focus:bg-white focus:ring-2 focus:ring-[#2E2F83]/10 placeholder:text-zinc-400 disabled:opacity-60"
              />
            </div>

            {/* Password */}
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-zinc-400" />
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                disabled={loading}
                className="h-10 w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm text-zinc-900 outline-none transition focus:border-[#2E2F83] focus:bg-white focus:ring-2 focus:ring-[#2E2F83]/10 placeholder:text-zinc-400 disabled:opacity-60"
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !email || !password}
              className="h-10 w-full rounded-lg bg-[#2E2F83] text-white text-sm font-semibold tracking-wide hover:bg-[#24256b] active:bg-[#1c1d56] transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="size-3.5 animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          {/* Demo logins — collapsible */}
          {process.env.NEXT_PUBLIC_ENABLE_DEMO_LOGINS !== 'false' && (
            <div className="border-t border-zinc-100 pt-3">
              <button
                type="button"
                onClick={() => setDemoOpen((v) => !v)}
                className="flex w-full items-center justify-between text-[11px] font-mono text-zinc-400 hover:text-zinc-600 transition-colors cursor-pointer select-none"
              >
                <span>Demo accounts</span>
                <ChevronDown
                  className={`size-3.5 transition-transform duration-200 ${demoOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {demoOpen && (
                <div className="mt-2 grid grid-cols-2 gap-1.5">
                  {DEMO_ROLES.map((role) => (
                    <button
                      key={role.email}
                      type="button"
                      onClick={() => handleDemoSelect(role.email, role.pass)}
                      disabled={loading}
                      className="rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-left text-[11px] font-medium text-zinc-700 hover:bg-[#2E2F83]/5 hover:border-[#2E2F83]/30 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {role.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-8 py-3 border-t border-zinc-100 bg-zinc-50/60">
          <span className="text-[10px] font-mono text-zinc-400">
            © Bikita Minerals (Pvt) Ltd
          </span>
          {profiles.length > 1 && (
            <div className="flex items-center gap-1.5">
              <span className={`size-1.5 rounded-full ${serverStatus === 'online' ? 'bg-emerald-500' : serverStatus === 'offline' ? 'bg-rose-500 animate-pulse' : 'bg-zinc-400'}`} />
              <select
                value={activeProfileId}
                onChange={handleProfileChange}
                className="text-[10px] font-mono text-zinc-500 bg-transparent outline-none cursor-pointer"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}{p.isDefault ? ' (Default)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
