'use client';

import { login } from '@/lib/auth';
import { useState, useEffect } from 'react';
import { HardHat, ShieldCheck, Wrench, UserCheck, Users, Gauge, Shield, Lock, Mail, ArrowRight } from 'lucide-react';
import { NotificationBanner } from '@/components/ui/notification';
import { PlantTelemetryVisual } from '@/components/auth/PlantTelemetryVisual';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { getProfiles, getActiveProfile, setActiveProfile, ServerProfile } from '@/lib/serverProfiles';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [profiles, setProfiles] = useState<ServerProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    getProfiles().then((list) => {
      if (cancelled) return;
      setProfiles(list);
      getActiveProfile().then((active) => {
        if (cancelled) return;
        setActiveProfileId(active?.id || list[0]?.id || '');
      });
    });
    return () => { cancelled = true; };
  }, []);

  const handleProfileChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setActiveProfileId(newId);
    await setActiveProfile(newId);
    setError(null);
  };

  const handleSubmit = async (e?: React.FormEvent<HTMLFormElement>) => {
    if (e) e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    setError(null);
    try {
      const result = await login(email, password);
      if (result?.error) {
        setError(result.error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setLoading(true);
    setError(null);
    try {
      const result = await login(roleEmail, rolePass);
      if (result?.error) {
        setError(result.error);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen w-full bg-zinc-50 text-zinc-900 antialiased selection:bg-zinc-200">
      {/* LEFT 50% PANEL: PLANT TELEMETRY SHOWCASE */}
      <div className="w-full lg:w-1/2 min-h-[400px] lg:min-h-screen flex flex-col">
        <PlantTelemetryVisual />
      </div>

      {/* RIGHT 50% PANEL: INDUSTRIAL AUTHENTICATION PORTAL */}
      <div className="relative w-full lg:w-1/2 min-h-[600px] lg:min-h-screen flex items-center justify-center p-6 md:p-10 lg:p-12 bg-zinc-50/60">
        {/* TOP RIGHT CONTROLS */}
        <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-white border border-zinc-200 rounded-md px-2 py-1 shadow-2xs">
            <span className="size-2 rounded-full bg-emerald-500 inline-block" />
            <select
              value={activeProfileId}
              onChange={handleProfileChange}
              className="h-6 bg-transparent text-[11px] font-mono text-zinc-800 outline-none cursor-pointer"
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.isDefault ? '(Default)' : ''}
                </option>
              ))}
            </select>
          </div>
          <ThemeToggle />
        </div>

        <div className="w-full max-w-md space-y-5 rounded-xl border border-zinc-200/80 bg-white p-6 md:p-8 shadow-sm">
          {/* BRAND HEADER */}
          <div className="text-center space-y-2">
            <div className="mx-auto flex size-12 items-center justify-center rounded-lg bg-zinc-900 text-white shadow-xs">
              <HardHat className="size-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-zinc-900 uppercase">
                Bikita Minerals DWRMS
              </h1>
              <p className="text-xs font-mono text-zinc-500 mt-0.5">
                Digital Work & Resource Management • Operations Portal
              </p>
            </div>
          </div>

          {error && (
            <NotificationBanner
              type={error.toLowerCase().includes("pending") ? "warning" : "error"}
              title={error.toLowerCase().includes("pending") ? "Account Pending" : "Authentication Failure"}
              message={error}
              dismissible
              onDismiss={() => setError(null)}
            />
          )}

          {/* LOGIN FORM */}
          <form onSubmit={(e) => handleSubmit(e)} className="space-y-4">
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[10px] font-mono uppercase text-zinc-500 font-medium block mb-1">
                  Operator Email Address *
                </label>
                <div className="relative flex items-center">
                  <span className="pointer-events-none absolute pl-2.5 text-zinc-400">
                    <Mail className="size-3.5" />
                  </span>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-9 w-full rounded-md border border-zinc-200 bg-white pl-8 pr-2.5 text-xs text-zinc-900 font-mono transition-all outline-none focus:border-zinc-400 focus:ring-1 focus:ring-zinc-400"
                    placeholder="admin@bikita.com"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase text-zinc-500 font-medium block mb-1">
                  Access Password / Passcode *
                </label>
                <div className="relative flex items-center">
                  <span className="pointer-events-none absolute pl-2.5 text-zinc-400">
                    <Lock className="size-3.5" />
                  </span>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-9 w-full rounded-md border border-zinc-200 bg-white pl-8 pr-2.5 text-xs text-zinc-900 font-mono transition-all outline-none focus:border-zinc-400 focus:ring-1 focus:ring-zinc-400"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="flex h-9 w-full items-center justify-center rounded-md bg-zinc-900 px-3 text-xs font-semibold text-white shadow-xs hover:bg-black transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Authenticating Operator..." : "Authenticate & Open Console"}
              <ArrowRight className="size-3.5 ml-1.5" />
            </button>
          </form>

          {/* QUICK CREDENTIALS SELECTOR */}
          {process.env.NEXT_PUBLIC_ENABLE_DEMO_LOGINS !== 'false' && (
            <div className="pt-4 border-t border-zinc-200 space-y-2.5">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase text-zinc-500 font-semibold">
                <span>Select Operational Role:</span>
                <span>Pass: password123</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('admin@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <ShieldCheck className="size-3.5 text-zinc-800" />
                    <span>Admin</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    admin@bikita.com
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('mechmgr@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <Users className="size-3.5 text-amber-600" />
                    <span>Dept Manager</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    mechmgr@bikita.com
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('supervisor@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <UserCheck className="size-3.5 text-emerald-600" />
                    <span>Supervisor</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    supervisor@bikita.com
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('tech@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <Wrench className="size-3.5 text-blue-600" />
                    <span>Technician</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    tech@bikita.com
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('operator@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <Gauge className="size-3.5 text-orange-600" />
                    <span>Operator</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    operator@bikita.com
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickLogin('safety@bikita.com', 'password123')}
                  className="p-2.5 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 text-left transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-900">
                    <Shield className="size-3.5 text-rose-600" />
                    <span>Safety Officer</span>
                  </div>
                  <div className="text-[9px] font-mono text-zinc-500 truncate mt-0.5">
                    safety@bikita.com
                  </div>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
