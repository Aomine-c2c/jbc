'use client';

import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import { Shield, Sparkles, Activity, Layers, FileCheck2 } from 'lucide-react';

export function PlantTelemetryVisual() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // We use standard anime API, importing default as `anime`
    const path = anime.path('.workflow-track');

    // 1. Packets traveling along the workflow track
    const packets = anime({
      targets: '.job-packet',
      translateX: path('x'),
      translateY: path('y'),
      easing: 'linear',
      duration: 12000,
      loop: true,
      delay: anime.stagger(4000)
    });

    // 2. Circuit stream lines moving
    const stream = anime({
      targets: '.workflow-stream',
      strokeDashoffset: [754, 0], // Circumference of R=120 circle
      ease: 'linear',
      duration: 8000,
      loop: true,
    });
    
    // 3. Node pulsing effect to simulate processing
    const nodes = anime({
      targets: '.workflow-node circle',
      scale: [1, 1.1, 1],
      easing: 'easeInOutSine',
      duration: 2000,
      loop: true,
      delay: anime.stagger(1000)
    });

    return () => {
      try {
        packets.pause();
        stream.pause();
        nodes.pause();
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
          <Activity className="size-3.5 ml-1" />
          <span>Workflow Visualizer</span>
        </div>

        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          Enterprise Resource Console
          <Sparkles className="size-4 text-amber-400" />
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          Integrated Mining, Concentrator & Fleet Workflows
        </p>
      </div>

      {/* CENTER: WORKFLOW DIAGRAM */}
      <div className="relative z-10 my-auto flex items-center justify-center py-6">
        <div className="relative size-64 md:size-80 flex items-center justify-center">
          
          <svg viewBox="0 0 320 320" className="w-full h-full overflow-visible">
            <defs>
              <filter id="nodeGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* MAIN TRACK */}
            <path 
              className="workflow-track"
              d="M 160 40 A 120 120 0 1 1 159.9 40" 
              fill="none" 
              stroke="#1e293b" 
              strokeWidth="2" 
              strokeDasharray="4 8"
            />

            {/* ACTIVE STREAM */}
            <path 
              className="workflow-stream"
              d="M 160 40 A 120 120 0 1 1 159.9 40" 
              fill="none" 
              stroke="#10b981" 
              strokeWidth="2" 
              strokeDasharray="40 200"
            />

            {/* NODES */}
            {/* DRAFT */}
            <g transform="translate(160, 40)" className="workflow-node">
              <circle r="18" fill="#090d16" stroke="#64748b" strokeWidth="2" filter="url(#nodeGlow)" />
              <circle r="8" fill="#475569" />
              <text y="34" textAnchor="middle" fill="#94a3b8" className="font-mono text-[9px] font-bold tracking-wider">DRAFT</text>
            </g>
            
            {/* APPROVED */}
            <g transform="translate(280, 160)" className="workflow-node">
              <circle r="18" fill="#090d16" stroke="#38bdf8" strokeWidth="2" filter="url(#nodeGlow)" />
              <circle r="8" fill="#0ea5e9" />
              <text y="34" textAnchor="middle" fill="#38bdf8" className="font-mono text-[9px] font-bold tracking-wider">APPROVED</text>
            </g>

            {/* IN PROGRESS */}
            <g transform="translate(160, 280)" className="workflow-node">
              <circle r="18" fill="#090d16" stroke="#f59e0b" strokeWidth="2" filter="url(#nodeGlow)" />
              <circle r="8" fill="#d97706" />
              <text y="34" textAnchor="middle" fill="#f59e0b" className="font-mono text-[9px] font-bold tracking-wider">IN PROGRESS</text>
            </g>

            {/* COMPLETED */}
            <g transform="translate(40, 160)" className="workflow-node">
              <circle r="18" fill="#090d16" stroke="#10b981" strokeWidth="2" filter="url(#nodeGlow)" />
              <circle r="8" fill="#059669" />
              <text y="34" textAnchor="middle" fill="#10b981" className="font-mono text-[9px] font-bold tracking-wider">COMPLETED</text>
            </g>

            {/* PACKETS */}
            <circle className="job-packet" r="5" fill="#fff" filter="url(#nodeGlow)" />
            <circle className="job-packet" r="5" fill="#38bdf8" filter="url(#nodeGlow)" />
            <circle className="job-packet" r="5" fill="#f59e0b" filter="url(#nodeGlow)" />
          </svg>

        </div>
      </div>

      {/* BOTTOM METRIC PILLS & TRUST INDICATORS */}
      <div className="relative z-10 space-y-3 pt-4 border-t border-slate-800/80">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <Layers className="size-3 text-emerald-400" />
              <span>ACTIVE JOBS</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">42</div>
          </div>

          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <FileCheck2 className="size-3 text-cyan-400" />
              <span>COMPLETED</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">18,392</div>
          </div>

          <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 backdrop-blur-xs text-center">
            <div className="text-[10px] font-mono text-slate-400 flex items-center justify-center gap-1">
              <Shield className="size-3 text-amber-400" />
              <span>PORTAL</span>
            </div>
            <div className="text-sm font-mono font-bold text-white mt-0.5">SECURE</div>
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

