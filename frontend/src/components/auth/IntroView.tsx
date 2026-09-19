'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import {
  ShieldCheck, ClipboardList, Wrench,
  BarChart3, Users, ArrowRight,
  Cpu, Layers, Activity,
  HardHat, RefreshCw, CheckCircle2, ChevronRight
} from 'lucide-react';
import { getDefaultLandingRoute } from '@/lib/rbac';

const PROCESS_STEPS = [
  {
    step: '01',
    title: 'Crushing & Sizing',
    subtitle: 'Primary & Secondary Ore Prep',
    desc: 'Jaw and cone crushers break down ROM spodumene and petalite ores into fine aggregate fractions under 12mm with continuous belt scale monitoring.',
    stats: '1,450 t/h capacity',
    tag: 'Mechanical / Feed'
  },
  {
    step: '02',
    title: 'Wet Grinding & Milling',
    subtitle: 'Closed-Circuit Comminution',
    desc: 'Dual ball mills paired with hydrocyclone classification clusters achieve P80 75μm liberation size, ensuring optimal mineral release for downstream recovery.',
    stats: 'P80 @ 75 µm',
    tag: 'Comminution'
  },
  {
    step: '03',
    title: 'Flotation & Separation',
    subtitle: 'Selective Chemical Beneficiation',
    desc: 'Multi-stage rougher, scavenger, and cleaner flotation cells selectively recover high-grade lithium concentrates with automated reagent dosing.',
    stats: '92.4% Recovery Rate',
    tag: 'Chemical Processing'
  },
  {
    step: '04',
    title: 'Dewatering & Tailing',
    subtitle: 'Concentrate Filtration & TSF',
    desc: 'High-rate thickeners and ceramic disc vacuum filters yield moisture-controlled cake for export, while tailings are safely slurried to the engineered TSF.',
    stats: '<8.5% Moisture Cake',
    tag: 'Dewatering & Waste'
  },
];

const METRICS = [
  {
    label: 'Concentrator Throughput',
    value: '1,240',
    unit: 'T / DAY',
    change: '+4.2% vs target',
    status: 'optimal',
    icon: Cpu,
  },
  {
    label: 'Plant Mechanical Availability',
    value: '98.4%',
    unit: 'UPTIME',
    change: 'Zero unplan downtime',
    status: 'optimal',
    icon: Activity,
  },
  {
    label: 'Active Work Orders',
    value: '14',
    unit: 'IN PROGRESS',
    change: '8 scheduled, 6 PM',
    status: 'neutral',
    icon: Wrench,
  },
  {
    label: 'Safety Performance Streak',
    value: '428',
    unit: 'DAYS LTI-FREE',
    change: 'Zero recordable incidents',
    status: 'optimal',
    icon: ShieldCheck,
  },
];

const FEATURES = [
  {
    icon: ClipboardList,
    title: 'Digital Job Card System',
    desc: 'Full lifecycle management from operator submission through engineering sign-off with multi-tier approval gates.',
  },
  {
    icon: Wrench,
    title: 'Predictive & Preventive PMs',
    desc: 'Automated maintenance triggers calibrated by operating hours, vibration telemetry, and scheduled component life.',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Telemetry & SCADA',
    desc: 'Live telemetry integration tracking feed rates, reagent additions, and power consumption across all concentrator banks.',
  },
  {
    icon: Users,
    title: 'Granular Role-Based Access',
    desc: 'Specialized workspace consoles tailored for Shift Supervisors, Lead Artisans, Mill Operators, and HSE Safety Officers.',
  },
  {
    icon: ShieldCheck,
    title: 'Audit & Compliance Ledger',
    desc: 'Tamper-evident operational audit logs conforming to ISO 14001 environmental and ISO 45001 safety mandates.',
  },
  {
    icon: HardHat,
    title: 'Off-Grid & Offline Resiliency',
    desc: 'Local SQLite fallback synchronizer ensures uninterrupted operations during mine pit radio network disruptions.',
  },
];

export default function IntroView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [loggedInUser, setLoggedInUser] = useState<{ email: string; role: string } | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const email = localStorage.getItem('user_email');
      const role = localStorage.getItem('user_role');
      if (email || role) {
        setLoggedInUser({ email: email || 'Operator', role: role || 'Authorized User' });
      }
    }
  }, []);

  /* Technical animated particle mesh — adapted for light backgrounds */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf: number;
    let t = 0;

    const draw = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const spacing = 40;
      const cols = Math.ceil(canvas.width / spacing) + 1;
      const rows = Math.ceil(canvas.height / spacing) + 1;

      for (let x = 0; x < cols; x++) {
        for (let y = 0; y < rows; y++) {
          const wave = Math.sin(x * 0.35 + y * 0.25 + t) * 0.5 + 0.5;
          // Indigo-500 dots, subtle on light background
          const alpha = 0.04 + wave * 0.13;
          ctx.beginPath();
          ctx.arc(x * spacing, y * spacing, 1.2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(99, 102, 241, ${alpha})`;
          ctx.fill();
        }
      }
      t += 0.01;
      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col antialiased selection:bg-indigo-100 selection:text-indigo-900">

      {/* ── TOP ANNOUNCEMENT / LOGGED IN BANNER ─────────────────── */}
      {loggedInUser && (
        <div className="bg-[#1f2048] border-b border-[#3b3d88] px-4 py-2 text-xs font-mono flex items-center justify-between text-indigo-200">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Active Session: <strong className="text-indigo-900">{loggedInUser.email}</strong> ({loggedInUser.role})</span>
          </div>
          <Link
            href={getDefaultLandingRoute(loggedInUser.role)}
            className="flex items-center gap-1.5 px-3 py-1 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 rounded text-[11px] transition-colors font-semibold"
          >
            Enter Dashboard Console <ArrowRight className="size-3" />
          </Link>
        </div>
      )}

      {/* ── STICKY NAVIGATION BAR ───────────────────────────────── */}
      <header className="flex items-center justify-between px-6 md:px-12 py-3.5 border-b border-border backdrop-blur-md sticky top-0 z-40 bg-background/85 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-xl bg-gradient-to-br from-[#2E2F83] to-[#1e2055] flex items-center justify-center p-1.5 shadow-md shadow-indigo-900/20 border border-indigo-200">
            <Image
              src="/bikita-emblem.png"
              alt="Bikita Minerals"
              width={24}
              height={24}
              className="object-contain brightness-0 invert"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                Bikita Minerals
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-600">
                DWRMS Core
              </span>
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">
              Concentrator &amp; Mine Operations Hub
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-[#2E2F83] hover:bg-[#25266e] active:bg-[#1a1b4d] text-xs font-semibold text-white transition-all shadow-sm shadow-indigo-900/25 border border-indigo-900/20"
          >
            Sign In to Console <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </header>

      {/* ── HERO SECTION ────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-16 pb-14 overflow-hidden">
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

        {/* Soft ambient indigo wash — subtle on white */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(99, 102, 241, 0.07) 0%, transparent 70%)',
          }}
        />

        <div className="relative z-10 max-w-4xl mx-auto space-y-6">
          {/* Live Status Banner */}
          <div className="flex justify-center mb-2">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-200 bg-indigo-50 text-indigo-600 text-xs font-mono font-medium shadow-sm">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              Concentrator Telemetry Online · Masvingo Province, Zimbabwe
            </div>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.15] text-foreground">
            Digital Work &amp; Resource{' '}
            <span className="bg-gradient-to-r from-indigo-700 via-indigo-500 to-indigo-400 bg-clip-text text-transparent">
              Management Platform
            </span>
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            The mission-critical operations portal powering maintenance workflows, asset reliability,
            shift logs, and automated compliance tracking for Bikita Minerals concentrator facilities.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
            <Link
              href="/login"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-[#2E2F83] hover:bg-[#25266e] active:bg-[#1a1b4d] text-white text-sm font-semibold tracking-wide transition-all shadow-lg shadow-indigo-900/25 hover:shadow-indigo-900/35 border border-indigo-900/20"
            >
              Access Operations Console <ArrowRight className="size-4" />
            </Link>
            <a
              href="#process-flow"
              className="flex items-center gap-2 px-5 py-3 rounded-xl border border-border hover:border-indigo-300 bg-background hover:bg-indigo-50/60 text-muted-foreground hover:text-indigo-700 text-sm font-medium transition-all"
            >
              Concentrator Architecture
            </a>
          </div>
        </div>
      </section>

      {/* ── KEY PLANT METRICS SHOWCASE ─────────────────────────── */}
      <section className="px-6 md:px-12 py-8 border-y border-border bg-muted/40">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="size-4 text-indigo-500" />
              <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground font-semibold">
                Live Plant Operational Indicators
              </span>
            </div>
            <span className="text-[10px] font-mono text-emerald-600 flex items-center gap-1.5">
              <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Real-Time Feed
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {METRICS.map((m) => (
              <div
                key={m.label}
                className="rounded-xl border border-border bg-card p-4 flex flex-col justify-between space-y-3 shadow-sm hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between">
                  <span className="text-xs font-mono text-muted-foreground">{m.label}</span>
                  <div className="p-1.5 rounded-md bg-indigo-50 border border-indigo-100 text-indigo-500">
                    <m.icon className="size-3.5" />
                  </div>
                </div>

                <div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold font-mono tracking-tight text-foreground">{m.value}</span>
                    <span className="text-[10px] font-mono text-muted-foreground">{m.unit}</span>
                  </div>
                  <div className="text-[11px] font-mono text-emerald-600 mt-1 flex items-center gap-1">
                    <CheckCircle2 className="size-3" />
                    <span>{m.change}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CONCENTRATOR PROCESS FLOW ARCHITECTURE ─────────────── */}
      <section id="process-flow" className="px-6 md:px-12 py-16 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
          <div className="inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-widest text-indigo-600 font-semibold">
            <Layers className="size-3.5" />
            <span>Engineering Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">
            Concentrator Beneficiation Circuit
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground">
            End-to-end digital tracking across each stage of Bikita Minerals petalite and spodumene processing lines.
          </p>
        </div>

        {/* Process Flow Interactive Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {PROCESS_STEPS.map((s, idx) => {
            const isSelected = activeStep === idx;
            return (
              <div
                key={s.step}
                onClick={() => setActiveStep(idx)}
                className={`relative rounded-xl border p-5 transition-all duration-200 cursor-pointer flex flex-col justify-between ${isSelected
                    ? 'border-indigo-400 bg-indigo-50 shadow-md shadow-indigo-100 ring-1 ring-indigo-300'
                    : 'border-border bg-card hover:border-indigo-300 hover:bg-indigo-50/50 shadow-sm hover:shadow-md'
                  }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-muted text-indigo-600">
                      STAGE {s.step}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground">{s.tag}</span>
                  </div>

                  <h3 className="text-base font-semibold text-foreground mb-1">{s.title}</h3>
                  <div className="text-xs font-mono text-indigo-600 mb-2.5">{s.subtitle}</div>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-4">{s.desc}</p>
                </div>

                <div className="pt-3 border-t border-border flex items-center justify-between text-xs font-mono">
                  <span className="text-muted-foreground">Throughput Target</span>
                  <span className="text-emerald-600 font-semibold">{s.stats}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Stage Detail Showcase Callout */}
        <div className="mt-6 rounded-2xl border border-indigo-200 bg-indigo-50 p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-600">
              <RefreshCw className="size-3.5 animate-spin text-indigo-500" />
              <span>DWRMS Automation Gate · {PROCESS_STEPS[activeStep].title}</span>
            </div>
            <div className="text-sm text-foreground">
              Work orders and preventive checklists for <strong>{PROCESS_STEPS[activeStep].title}</strong> are synchronized automatically with shift logbooks.
            </div>
          </div>

          <Link
            href="/login"
            className="shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg bg-[#2E2F83] hover:bg-[#25266e] text-white text-xs font-semibold font-mono tracking-wide transition-colors shadow-sm"
          >
            Manage Stage {PROCESS_STEPS[activeStep].step} <ChevronRight className="size-3.5" />
          </Link>
        </div>
      </section>

      {/* ── PLATFORM CAPABILITIES ──────────────────────────────── */}
      <section className="px-6 md:px-12 py-16 border-t border-border bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <div className="text-[11px] font-mono uppercase tracking-widest text-indigo-600 font-semibold">
              Operational Toolkit
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">
              Enterprise Work &amp; Asset Management
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Built purposely for heavy industrial concentrators, open-pit haulage fleets, and maintenance workshops.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-border bg-card hover:border-indigo-300 hover:bg-indigo-50/40 p-5 transition-all space-y-3 shadow-sm hover:shadow-md"
              >
                <div className="size-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                  <f.icon className="size-4.5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground mb-1">{f.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CALL TO ACTION STRIP ───────────────────────────────── */}
      <section className="px-6 md:px-12 py-16 border-t border-border bg-background">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="size-14 rounded-2xl bg-gradient-to-br from-[#2E2F83] to-indigo-700 border border-indigo-300 p-3 mx-auto shadow-xl shadow-indigo-200 flex items-center justify-center">
            <Image
              src="/bikita-emblem.png"
              alt="Bikita Minerals"
              width={36}
              height={36}
              className="object-contain brightness-0 invert"
            />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">
              Ready to Access the Operations Portal?
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-lg mx-auto">
              Authenticate with your assigned corporate credentials or select a demo operator profile to begin.
            </p>
          </div>

          <div className="pt-2">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-[#2E2F83] hover:bg-[#25266e] active:bg-[#1a1b4d] text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-900/25 hover:shadow-indigo-900/35 border border-indigo-900/20 font-mono uppercase tracking-wider"
            >
              Sign In to Console <ArrowRight className="size-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── SYSTEM FOOTER ──────────────────────────────────────── */}
      <footer className="border-t border-border px-6 md:px-12 py-5 bg-muted/50">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-[10px] font-mono text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="text-foreground font-semibold">© Bikita Minerals (Pvt) Ltd</span>
            <span>•</span>
            <span>Sinomine Resource Group</span>
          </div>
          <div>
            DWRMS v2.8 Authoritative Production Gateway • Masvingo, Zimbabwe
          </div>
        </div>
      </footer>

    </div>
  );
}
