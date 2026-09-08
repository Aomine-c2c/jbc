'use client';

import React from 'react';
import { ShieldCheck, Shield } from 'lucide-react';

export function PlantTelemetryVisual() {
  return (
    <div className="relative flex flex-col justify-between h-full w-full bg-zinc-100/75 p-8 md:p-12 lg:p-16 overflow-hidden text-zinc-900 select-none border-r border-zinc-200">
      {/* TECHNICAL SCHEMATIC BACKGROUND GRID */}
      <div
        className="absolute inset-0 opacity-[0.4] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(#e4e4e7 1px, transparent 1px), linear-gradient(90deg, #e4e4e7 1px, transparent 1px)`,
          backgroundSize: '28px 28px',
        }}
      />

      {/* TOP HEADER: SYSTEM IDENTITY & STATUS */}
      <div className="relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="size-8 rounded-lg bg-[#2E2F83] text-white flex items-center justify-center font-bold shadow-xs">
            <img
              src="/bikita-emblem.png"
              alt="Emblem"
              className="size-5 object-contain brightness-0 invert"
            />
          </div>
          <div>
            <div className="flex items-center gap-2 text-[11px] font-mono font-bold text-zinc-800 uppercase tracking-wider">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full size-2 bg-emerald-600"></span>
              </span>
              <span>BIKITA MINERALS • DWRMS CORE</span>
              <span className="text-zinc-300">•</span>
              <span className="text-emerald-700 font-mono text-[9px] bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded font-semibold">
                ONLINE
              </span>
            </div>
            <div className="text-[10px] font-mono text-zinc-500">
              Operations & Concentrator Maintenance Hub
            </div>
          </div>
        </div>
      </div>

      {/* CENTER: MINIMALIST CORPORATE BRAND SHOWCASE */}
      <div className="relative z-10 my-auto flex flex-col items-center justify-center text-center space-y-6 max-w-lg mx-auto py-8">
        {/* Architectural Ambient Cobalt Aura */}
        <div
          className="absolute inset-0 pointer-events-none opacity-30"
          style={{
            background: 'radial-gradient(ellipse at 50% 40%, rgba(46, 47, 131, 0.1) 0%, transparent 70%)',
          }}
        />

        {/* Prominent Official Bikita Minerals Logo */}
        <div className="relative flex items-center justify-center py-2 transition-transform duration-300 hover:scale-[1.01]">
          <img
            src="/bikita-logo.png"
            alt="Bikita Minerals"
            className="h-36 md:h-44 w-auto max-w-full object-contain drop-shadow-xs"
          />
        </div>

        {/* Corporate Title & Hierarchy */}
        <div className="relative space-y-3 pt-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2E2F83]/10 text-[#2E2F83] text-[11px] font-mono font-bold uppercase tracking-wider">
            <ShieldCheck className="size-3.5 text-[#2E2F83]" />
            <span>Digital Work & Resource Management System</span>
          </div>

          <div className="space-y-1">
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-zinc-900 font-sans uppercase">
              Operations & Concentrator Maintenance Core
            </h1>
            <p className="text-xs font-mono text-zinc-500 font-medium">
              Sinomine Resource Group • Masvingo Province, Zimbabwe
            </p>
          </div>
        </div>
      </div>

      {/* BOTTOM FOOTER (With generous clearance for floating dev badges) */}
      <div className="relative z-10 pt-4 border-t border-zinc-200/90 pl-16 pr-4">
        <div className="flex flex-col sm:flex-row items-center justify-between text-[10px] font-mono text-zinc-500 gap-1.5">
          <span className="flex items-center gap-1.5 font-semibold text-zinc-700">
            <img src="/bikita-emblem.png" alt="Emblem" className="size-3.5 object-contain" />
            © Bikita Minerals (Pvt) Ltd • Sinomine Resource Group
          </span>
          <span className="flex items-center gap-1 text-emerald-700 font-semibold">
            <Shield className="size-3.5 text-emerald-600" />
            DWRMS Authoritative Core v2.8 • Secure Gateway
          </span>
        </div>
      </div>
    </div>
  );
}
