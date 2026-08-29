'use client';

import React, { useEffect, useRef } from 'react';
import { animate } from 'animejs';
import { Shield, Sparkles, Activity, Layers, Radio } from 'lucide-react';

export function PlantTelemetryVisual() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 1. Smooth rotation of the central concentric telemetry rings
    const ring1 = animate('.telemetry-ring-1', {
      rotate: [0, 360],
      ease: 'linear',
      duration: 36000,
      loop: true,
    });

    const ring2 = animate('.telemetry-ring-2', {
      rotate: [360, 0],
      ease: 'linear',
      duration: 48000,
      loop: true,
    });

    // 2. Gentle pulsing of the core and nodes
    const pulse = animate('.circuit-node', {
      scale: [1, 1.15, 1],
      opacity: [0.7, 1, 0.7],
      ease: 'easeInOutSine',
      duration: 3200,
      loop: true,
    });

    // 3. Subtle circuit stream lines
    const stream = animate('.circuit-stream', {
      strokeDashoffset: [400, 0],
      ease: 'linear',
      duration: 4000,
      loop: true,
    });

    return () => {
      try {
        ring1?.pause?.();
        ring2?.pause?.();
        pulse?.pause?.();
        stream?.pause?.();
      } catch {
        // cleanup
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col justify-between h-full w-full bg-slate-950 p-8 md:p-12 overflow-hidden text-slate-100 select-none border-r border-slate-800/80"
    >
      {/* AMBIENT BACKGROUND GRADIENT */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(16,185,129,0.12),transparent_60%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_70%,rgba(245,158,11,0.06),transparent_60%)] pointer-events-none" />
      
      {/* SUBTLE GRID */}
      <div
        className="absolute inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(#10b981 1px, transparent 1px), linear-gradient(90deg, #10b981 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />

      {/* TOP BRAND HEADER */}
      <div className="relative z-10 space-y-2">
        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-semibold tracking-wider uppercase">
          <span className="relative flex size-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full size-2 bg-emerald-500"></span>
          </span>
          <Radio className="size-3.5 ml-1" />
          <span>Bikita Operations Network</span>
        </div>

        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          Enterprise Resource Console
          <Sparkles className="size-4 text-amber-400" />
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          Integrated Mining, Concentrator & Fleet Workflows
        </p>
      </div>

      {/* CENTER: CLEAN, BEAUTIFUL ORBITAL SVG GRAPHIC */}
      <div className="relative z-10 my-auto flex items-center justify-center py-6">
        <div className="relative size-64 md:size-80 flex items-center justify-center">
          
          {/* SVG Animated Orbital Rings and Constellation Nodes */}
          <svg viewBox="0 0 320 320" className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="orbitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.8" />
              </linearGradient>
              <filter id="nodeGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* OUTER ORBITAL RING (Anime.js rotating) */}
            <g className="telemetry-ring-1 origin-center">
              <circle
                cx="160"
                cy="160"
                r="130"
                fill="none"
                stroke="#1e293b"
                strokeWidth="1.5"
                strokeDasharray="6 8"
              />
              <circle
                cx="290"
                cy="160"
                r="4"
                fill="#10b981"
                filter="url(#nodeGlow)"
              />
              <circle
                cx="30"
                cy="160"
                r="3"
                fill="#38bdf8"
              />
            </g>

            {/* INNER ORBITAL RING (Anime.js reverse rotating) */}
            <g className="telemetry-ring-2 origin-center">
              <circle
                cx="160"
                cy="160"
                r="90"
                fill="none"
                stroke="#334155"
                strokeWidth="1.5"
                strokeDasharray="4 6"
              />
              <circle
                cx="160"
                cy="70"
                r="3.5"
                fill="#f59e0b"
                filter="url(#nodeGlow)"
              />
              <circle
                cx="160"
                cy="250"
                r="3.5"
                fill="#10b981"
              />
            </g>

            {/* CONNECTING CIRCUIT PATHS */}
            <path
              d="M 60 160 Q 110 90 160 160 T 260 160"
              fill="none"
              stroke="#1e293b"
              strokeWidth="2"
            />
            <path
              d="M 60 160 Q 110 90 160 160 T 260 160"
              fill="none"
              stroke="url(#orbitGrad)"
              strokeWidth="2"
              strokeDasharray="16 48"
              className="circuit-stream"
            />

            <path
              d="M 160 60 Q 230 110 160 160 T 160 260"
              fill="none"
              stroke="#1e293b"
              strokeWidth="1.5"
            />

            {/* CORE CENTER GLOW HUB */}
            <circle
              cx="160"
              cy="160"
              r="34"
              fill="#090d16"
              stroke="#10b981"
              strokeWidth="2"
              className="circuit-node"
              filter="url(#nodeGlow)"
            />
            <circle
              cx="160"
              cy="160"
              r="22"
              fill="#0f172a"
              stroke="#334155"
              strokeWidth="1"
            />
            <circle
              cx="160"
              cy="160"
              r="6"
              fill="#10b981"
            />

            {/* CONSTELLATION SATELLITE NODES */}
            <g transform="translate(160, 60)">
              <circle cx="0" cy="0" r="10" fill="#090d16" stroke="#38bdf8" strokeWidth="1.5" />
              <text x="0" y="3" textAnchor="middle" fill="#94a3b8" className="font-mono text-[7px] font-bold">CR</text>
            </g>

            <g transform="translate(260, 160)">
              <circle cx="0" cy="0" r="10" fill="#090d16" stroke="#10b981" strokeWidth="1.5" />
              <text x="0" y="3" textAnchor="middle" fill="#94a3b8" className="font-mono text-[7px] font-bold">BM</text>
            </g>

            <g transform="translate(160, 260)">
              <circle cx="0" cy="0" r="10" fill="#090d16" stroke="#f59e0b" strokeWidth="1.5" />
              <text x="0" y="3" textAnchor="middle" fill="#94a3b8" className="font-mono text-[7px] font-bold">FL</text>
            </g>

            <g transform="translate(60, 160)">
              <circle cx="0" cy="0" r="10" fill="#090d16" stroke="#06b6d4" strokeWidth="1.5" />
              <text x="0" y="3" textAnchor="middle" fill="#94a3b8" className="font-mono text-[7px] font-bold">SH</text>
            </g>
          </svg>

          {/* CENTER EMBLEM ICON OVERLAY */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <Shield className="size-5 text-emerald-400 opacity-90" />
          </div>
        </div>
      </div>

      {/* BOTTOM METRIC PILLS & TRUST INDICATORS */}
      <div className="relative z-10 space-y-3 pt-4 border-t border-slate-800/80">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <Activity className="size-3 text-emerald-400" />
              <span>UPTIME</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">99.8%</div>
          </div>

          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <Layers className="size-3 text-cyan-400" />
              <span>OPERATIONS</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">ONLINE</div>
          </div>

          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <Shield className="size-3 text-amber-400" />
              <span>SECURITY</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">256-BIT</div>
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>Bikita Minerals (Pvt) Ltd</span>
          <span>v2.4.0 • Enterprise</span>
        </div>
      </div>
    </div>
  );
}
