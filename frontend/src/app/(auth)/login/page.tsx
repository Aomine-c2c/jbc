'use client';

import { login } from '@/lib/auth';
import { useState } from 'react';
import { HardHat, ShieldCheck, Wrench, UserCheck, Lock, Mail, ArrowRight } from 'lucide-react';
import { NotificationBanner } from '@/components/ui/notification';
import { PlantTelemetryVisual } from '@/components/auth/PlantTelemetryVisual';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e?: React.FormEvent<HTMLFormElement>) => {
    if (e) e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    setError(null);
    const result = await login(email, password);
    if (result?.error) {
      setError(result.error);
      setLoading(false);
    }
  };

  const handleQuickLogin = async (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setLoading(true);
    setError(null);
    const result = await login(roleEmail, rolePass);
    if (result?.error) {
      setError(result.error);
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen w-full bg-background text-foreground antialiased selection:bg-primary/30">
      {/* LEFT 50% PANEL: ANIME.JS PLANT TELEMETRY SHOWCASE */}
      <div className="w-full lg:w-1/2 min-h-[420px] lg:min-h-screen flex flex-col">
        <PlantTelemetryVisual />
      </div>

      {/* RIGHT 50% PANEL: INDUSTRIAL AUTHENTICATION PORTAL */}
      <div className="relative w-full lg:w-1/2 min-h-[600px] lg:min-h-screen flex items-center justify-center p-6 md:p-12 bg-background">
        {/* TOP RIGHT THEME TOGGLE */}
        <div className="absolute top-4 right-4 z-20">
          <ThemeToggle />
        </div>

        <div className="w-full max-w-md space-y-6 rounded border border-border bg-card p-6 md:p-8 shadow-2xl">
          {/* BRAND HEADER */}
          <div className="text-center space-y-2">
            <div className="mx-auto flex size-12 items-center justify-center rounded bg-primary text-primary-foreground shadow-xs">
              <HardHat className="size-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground uppercase">
                Bikita Minerals DWRMS
              </h1>
              <p className="text-xs font-mono text-muted-foreground mt-0.5">
                Digital Work & Resource Management System • Operations Console
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
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Operator Email Address *
                </label>
                <div className="relative flex items-center">
                  <span className="pointer-events-none absolute pl-2.5 text-muted-foreground">
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
                    className="h-8 w-full rounded border border-input bg-card pl-8 pr-2.5 text-xs text-foreground font-mono transition-all outline-none focus:border-ring"
                    placeholder="admin@bikita.com"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase text-muted-foreground block mb-1">
                  Access Password / Passcode *
                </label>
                <div className="relative flex items-center">
                  <span className="pointer-events-none absolute pl-2.5 text-muted-foreground">
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
                    className="h-8 w-full rounded border border-input bg-card pl-8 pr-2.5 text-xs text-foreground font-mono transition-all outline-none focus:border-ring"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="flex h-9 w-full items-center justify-center rounded bg-primary px-3 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Authenticating Operator..." : "Authenticate & Open Console"}
              <ArrowRight className="size-3.5 ml-1.5" />
            </button>
          </form>

          {/* QUICK CREDENTIALS SELECTOR */}
          <div className="pt-4 border-t border-border space-y-2.5">
            <div className="flex items-center justify-between text-[10px] font-mono uppercase text-muted-foreground">
              <span>Pre-configured Test Credentials:</span>
              <span>Pass: password123</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@bikita.com', 'password123')}
                className="p-2 rounded border border-border/80 bg-muted/40 hover:bg-muted text-left transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-[11px] font-semibold text-foreground group-hover:text-primary">
                  <ShieldCheck className="size-3 text-primary" />
                  <span>Admin</span>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground truncate mt-0.5">
                  admin@bikita.com
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('supervisor@bikita.com', 'password123')}
                className="p-2 rounded border border-border/80 bg-muted/40 hover:bg-muted text-left transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-[11px] font-semibold text-foreground group-hover:text-primary">
                  <UserCheck className="size-3 text-emerald-500" />
                  <span>Supervisor</span>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground truncate mt-0.5">
                  supervisor@bikita.com
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('tech@bikita.com', 'password123')}
                className="p-2 rounded border border-border/80 bg-muted/40 hover:bg-muted text-left transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-1 text-[11px] font-semibold text-foreground group-hover:text-primary">
                  <Wrench className="size-3 text-blue-500" />
                  <span>Technician</span>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground truncate mt-0.5">
                  tech@bikita.com
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
