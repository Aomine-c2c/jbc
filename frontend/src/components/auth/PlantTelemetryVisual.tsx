'use client';

import React, { useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';
import { HardHat, Activity, Layers, Truck, Factory, ShieldCheck } from 'lucide-react';

export function PlantTelemetryVisual() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 1. Conveyor Belt Motion (Stroke Dash Offset)
    const conveyorAnim = animate('.conveyor-path', {
      strokeDashoffset: [0, -48],
      ease: 'linear',
      duration: 1800,
      loop: true,
    });

    // 2. Ore Particle Flow Animation across conveyors
    const oreParticles1 = animate('.ore-particle-1', {
      translateX: [0, 135],
      translateY: [0, 55],
      opacity: [
        { to: 1, duration: 150 },
        { to: 1, duration: 1300 },
        { to: 0, duration: 150 },
      ],
      ease: 'inOutSine',
      duration: 2200,
      delay: stagger(350),
      loop: true,
    });

    const oreParticles2 = animate('.ore-particle-2', {
      translateX: [0, 155],
      translateY: [0, -10],
      opacity: [
        { to: 1, duration: 150 },
        { to: 1, duration: 1300 },
        { to: 0, duration: 150 },
      ],
      ease: 'inOutSine',
      duration: 2100,
      delay: stagger(300),
      loop: true,
    });

    const oreParticles3 = animate('.ore-particle-3', {
      translateX: [0, -50],
      translateY: [0, 110],
      opacity: [
        { to: 1, duration: 150 },
        { to: 1, duration: 1200 },
        { to: 0, duration: 150 },
      ],
      ease: 'inOutSine',
      duration: 1900,
      delay: stagger(280),
      loop: true,
    });

    // 3. Excavator Arm Oscillation
    const boomAnim = animate('#excavator-arm', {
      rotate: [-5, 7],
      transformOrigin: '28px 105px',
      alternate: true,
      ease: 'inOutQuad',
      duration: 3000,
      loop: true,
    });

    // 4. Crusher Jaw Oscillation
    const crusherAnim = animate('#crusher-jaw', {
      scaleY: [1, 0.90],
      translateY: [0, 6],
      alternate: true,
      ease: 'inOutSine',
      duration: 550,
      loop: true,
    });

    // 5. Concentrator Gear Rotation
    const gearAnim = animate('.mill-gear', {
      rotate: 360,
      transformOrigin: 'center center',
      ease: 'linear',
      duration: 5000,
      loop: true,
    });

    // 6. Haul Truck Vibration
    const truckAnim = animate('#haul-truck', {
      translateY: [-0.8, 0.8],
      alternate: true,
      ease: 'inOutSine',
      duration: 350,
      loop: true,
    });

    // 7. HUD Radar Pulse
    const radarAnim = animate('.radar-pulse', {
      scale: [1, 2.2],
      opacity: [0.8, 0],
      ease: 'outExpo',
      duration: 1800,
      delay: stagger(450),
      loop: true,
    });

    return () => {
      conveyorAnim.pause?.();
      oreParticles1.pause?.();
      oreParticles2.pause?.();
      oreParticles3.pause?.();
      boomAnim.pause?.();
      crusherAnim.pause?.();
      gearAnim.pause?.();
      truckAnim.pause?.();
      radarAnim.pause?.();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col justify-between h-full w-full bg-zinc-100/90 p-6 md:p-8 lg:p-10 overflow-hidden text-zinc-900 select-none border-r border-zinc-200"
    >
      {/* TECHNICAL SCHEMATIC BACKGROUND GRID */}
      <div
        className="absolute inset-0 opacity-[0.55] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(#e4e4e7 1px, transparent 1px), linear-gradient(90deg, #e4e4e7 1px, transparent 1px)`,
          backgroundSize: '24px 24px',
        }}
      />

      {/* TOP BRAND HEADER & DWRMS SYSTEM IDENTITY */}
      <div className="relative z-10 space-y-1">
        <div className="flex items-center gap-2 text-[11px] font-mono text-zinc-700 font-semibold tracking-wider uppercase">
          <span className="relative flex size-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full size-2.5 bg-emerald-600"></span>
          </span>
          <Activity className="size-3.5 text-zinc-800" />
          <span>Bikita DWRMS • Operations & Asset Control Hub</span>
        </div>

        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2 font-mono uppercase">
          Plant Telemetry & Work Execution
        </h2>
        <p className="text-xs text-zinc-500 font-mono">
          Integrated Work Cards, Real-Time Asset Health & Concentrator Circuit
        </p>
      </div>

      {/* CENTER: ENLARGED ANIMATED DWRMS MINING SVG SCHEMATIC */}
      <div className="relative z-10 my-auto flex items-center justify-center py-2">
        <div className="relative w-full max-w-[680px] aspect-[16/10.5]">
          <svg
            viewBox="0 0 720 460"
            className="w-full h-full overflow-visible"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* DEFINITIONS */}
            <defs>
              <linearGradient id="zincGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="100%" stopColor="#f4f4f5" />
              </linearGradient>
              <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="8" stroke="#e4e4e7" strokeWidth="1.5" />
              </pattern>
            </defs>

            {/* ========================================================================= */}
            {/* STAGE 1: ASSET EXC-01 (PIT EXTRACTION) */}
            {/* ========================================================================= */}
            <g id="stage-pit" transform="translate(15, 20)">
              {/* Pit Rock Strata Terrace */}
              <path d="M 0 135 L 90 135 L 115 165 L 170 165" stroke="#d4d4d8" strokeWidth="2.5" fill="url(#diagonalHatch)" />
              
              {/* DWRMS HUD CARD: EXC-01 */}
              <g transform="translate(0, 0)">
                <rect x="0" y="0" width="180" height="38" rx="4" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" className="shadow-xs" />
                <rect x="0" y="0" width="4" height="38" rx="2" fill="#10b981" />
                
                {/* Asset Tag & Status */}
                <text x="10" y="14" fill="#18181b" className="font-mono text-[10px] font-bold">ASSET: EXC-01 (CAT 6020B)</text>
                <rect x="118" y="5" width="54" height="12" rx="2" fill="#ecfdf5" stroke="#a7f3d0" strokeWidth="0.8" />
                <text x="122" y="14" fill="#047857" className="font-mono text-[7.5px] font-bold">● SIGNED OFF</text>
                
                {/* DWRMS Job Card Detail */}
                <text x="10" y="26" fill="#52525b" className="font-mono text-[8.5px]">JC-1042 • Pre-Start Sign-off</text>
                <text x="10" y="34" fill="#a1a1aa" className="font-mono text-[7.5px]">Op: T. Mukamuri • Shift A</text>
              </g>

              {/* Connecting HUD Radar Signal Line */}
              <line x1="85" y1="38" x2="85" y2="70" stroke="#18181b" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx="85" cy="70" r="3" fill="#10b981" />
              <circle cx="85" cy="70" r="3" fill="none" stroke="#10b981" strokeWidth="1.5" className="radar-pulse" />

              {/* Mining Excavator Machine */}
              <g id="excavator" transform="translate(15, 60)">
                {/* Crawler Tracks */}
                <rect x="10" y="72" width="75" height="16" rx="5" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                <circle cx="22" cy="80" r="4.5" fill="#71717a" />
                <circle cx="37" cy="80" r="4.5" fill="#71717a" />
                <circle cx="52" cy="80" r="4.5" fill="#71717a" />
                <circle cx="68" cy="80" r="4.5" fill="#71717a" />
                {/* Body & Operator Cabin */}
                <rect x="18" y="46" width="50" height="28" rx="4" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                <rect x="44" y="50" width="20" height="14" rx="2" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
                <circle cx="30" cy="56" r="5" fill="#18181b" />
                
                {/* Moving Hydraulic Boom Arm & Bucket */}
                <g id="excavator-arm">
                  <path d="M 58 52 L 95 24 L 122 52" stroke="#18181b" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M 122 52 L 132 68 L 115 72 Z" fill="#27272a" stroke="#18181b" strokeWidth="1.8" />
                  <circle cx="58" cy="52" r="3.5" fill="#18181b" />
                  <circle cx="95" cy="24" r="3.5" fill="#18181b" />
                </g>
              </g>

              {/* Pit Surge Hopper Feeder */}
              <path d="M 130 95 L 168 95 L 155 125 L 142 125 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.8" />
            </g>

            {/* ========================================================================= */}
            {/* CONVEYOR 1: PIT TO PRIMARY CRUSHER */}
            {/* ========================================================================= */}
            <g id="conveyor-1">
              <path
                d="M 185 145 L 320 200"
                stroke="#a1a1aa"
                strokeWidth="5"
                strokeLinecap="round"
              />
              <path
                d="M 185 145 L 320 200"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeDasharray="8 8"
              />
              {/* Large Ore Particles Traveling */}
              <circle cx="185" cy="145" r="4.5" fill="#27272a" className="ore-particle-1" />
              <circle cx="185" cy="145" r="3.5" fill="#52525b" className="ore-particle-1" />
              <circle cx="185" cy="145" r="4" fill="#18181b" className="ore-particle-1" />
            </g>

            {/* ========================================================================= */}
            {/* STAGE 2: ASSET CRU-01 (PRIMARY JAW CRUSHER & SCREEN) */}
            {/* ========================================================================= */}
            <g id="stage-crushing" transform="translate(255, 140)">
              {/* DWRMS HUD CARD: CRU-01 */}
              <g transform="translate(0, -50)">
                <rect x="0" y="0" width="185" height="38" rx="4" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" className="shadow-xs" />
                <rect x="0" y="0" width="4" height="38" rx="2" fill="#f59e0b" />
                
                {/* Asset Tag & Status */}
                <text x="10" y="14" fill="#18181b" className="font-mono text-[10px] font-bold">ASSET: CRU-01 (METSO C160)</text>
                <rect x="118" y="5" width="58" height="12" rx="2" fill="#fffbeb" stroke="#fde68a" strokeWidth="0.8" />
                <text x="122" y="14" fill="#b45309" className="font-mono text-[7.5px] font-bold">● IN PROGRESS</text>
                
                {/* DWRMS Job Card Detail */}
                <text x="10" y="26" fill="#52525b" className="font-mono text-[8.5px]">JC-1088 • 250hr Liner Service</text>
                <text x="10" y="34" fill="#a1a1aa" className="font-mono text-[7.5px]">Tech: C. Moyo • Priority 2</text>
              </g>

              {/* Connecting HUD Signal Line */}
              <line x1="90" y1="-12" x2="90" y2="20" stroke="#18181b" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx="90" cy="20" r="3" fill="#f59e0b" />
              <circle cx="90" cy="20" r="3" fill="none" stroke="#f59e0b" strokeWidth="1.5" className="radar-pulse" />

              {/* Primary Jaw Crusher Housing Frame */}
              <rect x="25" y="20" width="90" height="78" rx="5" fill="url(#zincGradient)" stroke="#18181b" strokeWidth="1.8" />
              
              {/* Crusher Feed Chute */}
              <path d="M 38 20 L 102 20 L 90 48 L 50 48 Z" fill="#e4e4e7" stroke="#18181b" strokeWidth="1.2" />
              
              {/* Moving Jaw Crusher Plate */}
              <g id="crusher-jaw">
                <rect x="58" y="48" width="24" height="24" rx="2" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                <line x1="62" y1="54" x2="78" y2="54" stroke="#ffffff" strokeWidth="1.2" />
                <line x1="62" y1="60" x2="78" y2="60" stroke="#ffffff" strokeWidth="1.2" />
                <line x1="62" y1="66" x2="78" y2="66" stroke="#ffffff" strokeWidth="1.2" />
              </g>

              {/* Vibrating Sizing Screen */}
              <g transform="translate(75, 70)">
                <line x1="0" y1="0" x2="45" y2="24" stroke="#18181b" strokeWidth="3.5" />
                <line x1="0" y1="5" x2="42" y2="27" stroke="#71717a" strokeWidth="2" strokeDasharray="4 4" />
              </g>

              {/* Sensor Badge */}
              <rect x="25" y="104" width="70" height="15" rx="2" fill="#f4f4f5" stroke="#d4d4d8" strokeWidth="1" />
              <text x="30" y="115" fill="#52525b" className="font-mono text-[9px] font-bold">P80: 12.4mm</text>
            </g>

            {/* ========================================================================= */}
            {/* CONVEYOR 2: CRUSHER TO CONCENTRATOR PLANT */}
            {/* ========================================================================= */}
            <g id="conveyor-2">
              <path
                d="M 390 230 L 545 220"
                stroke="#a1a1aa"
                strokeWidth="5"
                strokeLinecap="round"
              />
              <path
                d="M 390 230 L 545 220"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeDasharray="8 8"
              />
              {/* Crushed Ore particles */}
              <circle cx="390" cy="230" r="3" fill="#18181b" className="ore-particle-2" />
              <circle cx="390" cy="230" r="2.5" fill="#52525b" className="ore-particle-2" />
              <circle cx="390" cy="230" r="3" fill="#27272a" className="ore-particle-2" />
            </g>

            {/* ========================================================================= */}
            {/* STAGE 3: ASSET PLANT-01 (SPODUMENE CONCENTRATOR & FLOTATION) */}
            {/* ========================================================================= */}
            <g id="stage-concentrator" transform="translate(485, 20)">
              {/* DWRMS HUD CARD: PLANT-01 */}
              <g transform="translate(0, 0)">
                <rect x="0" y="0" width="200" height="38" rx="4" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" className="shadow-xs" />
                <rect x="0" y="0" width="4" height="38" rx="2" fill="#10b981" />
                
                {/* Asset Tag & Status */}
                <text x="10" y="14" fill="#18181b" className="font-mono text-[10px] font-bold">ASSET: PLANT-01 (CONCENTRATOR)</text>
                <rect x="142" y="5" width="50" height="12" rx="2" fill="#ecfdf5" stroke="#a7f3d0" strokeWidth="0.8" />
                <text x="146" y="14" fill="#047857" className="font-mono text-[7.5px] font-bold">● VERIFIED</text>
                
                {/* DWRMS Job Card Detail */}
                <text x="10" y="26" fill="#52525b" className="font-mono text-[8.5px]">JC-1102 • Flotation Reagent Setup</text>
                <text x="10" y="34" fill="#a1a1aa" className="font-mono text-[7.5px]">Tech: K. Sibanda • Grade: 5.8% Li₂O</text>
              </g>

              {/* Connecting HUD Signal Line */}
              <line x1="100" y1="38" x2="100" y2="70" stroke="#18181b" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx="100" cy="70" r="3" fill="#10b981" />
              <circle cx="100" cy="70" r="3" fill="none" stroke="#10b981" strokeWidth="1.5" className="radar-pulse" />

              {/* Concentrator Plant Facility Frame */}
              <g transform="translate(10, 65)">
                <path d="M 0 135 L 0 50 L 50 30 L 120 30 L 120 135 Z" fill="url(#zincGradient)" stroke="#18181b" strokeWidth="1.8" />
                
                {/* Rotating Ball Mill Drum & Gear */}
                <g transform="translate(40, 75)">
                  <rect x="-22" y="-16" width="44" height="32" rx="4" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                  <g className="mill-gear">
                    <circle cx="0" cy="0" r="10" fill="#ffffff" stroke="#18181b" strokeWidth="1.8" />
                    <line x1="-10" y1="0" x2="10" y2="0" stroke="#18181b" strokeWidth="1.8" />
                    <line x1="0" y1="-10" x2="0" y2="10" stroke="#18181b" strokeWidth="1.8" />
                  </g>
                </g>

                {/* Flotation Column Tank */}
                <g transform="translate(85, 60)">
                  <rect x="0" y="0" width="28" height="55" rx="3" fill="#ffffff" stroke="#18181b" strokeWidth="1.8" />
                  <line x1="4" y1="16" x2="24" y2="16" stroke="#10b981" strokeWidth="2" />
                  <line x1="4" y1="26" x2="24" y2="26" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 3" />
                  <line x1="4" y1="36" x2="24" y2="36" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 3" />
                </g>

                {/* Refined Spodumene Silo */}
                <g transform="translate(130, 40)">
                  <path d="M 0 25 L 20 10 L 40 25 L 40 95 L 20 110 L 0 95 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.8" />
                  <line x1="6" y1="45" x2="34" y2="45" stroke="#e4e4e7" strokeWidth="1.5" />
                  <line x1="6" y1="65" x2="34" y2="65" stroke="#e4e4e7" strokeWidth="1.5" />
                </g>

                {/* Telemetry Indicator */}
                <rect x="0" y="142" width="80" height="15" rx="2" fill="#ecfdf5" stroke="#a7f3d0" strokeWidth="1" />
                <text x="5" y="153" fill="#047857" className="font-mono text-[9px] font-bold">REC: 88.4% Li₂O</text>
              </g>
            </g>

            {/* ========================================================================= */}
            {/* CONVEYOR 3: SILO TO DISPATCH WEIGHBRIDGE */}
            {/* ========================================================================= */}
            <g id="conveyor-3">
              <path
                d="M 635 240 L 585 350"
                stroke="#a1a1aa"
                strokeWidth="5"
                strokeLinecap="round"
              />
              <path
                d="M 635 240 L 585 350"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2.5"
                strokeDasharray="8 8"
              />
              {/* Fine Concentrate particles */}
              <circle cx="635" cy="240" r="3" fill="#047857" className="ore-particle-3" />
              <circle cx="635" cy="240" r="2.5" fill="#18181b" className="ore-particle-3" />
              <circle cx="635" cy="240" r="2" fill="#10b981" className="ore-particle-3" />
            </g>

            {/* ========================================================================= */}
            {/* STAGE 4: ASSET TRK-05 (HAULAGE & EXPORT DISPATCH) */}
            {/* ========================================================================= */}
            <g id="stage-dispatch" transform="translate(390, 275)">
              {/* DWRMS HUD CARD: TRK-05 */}
              <g transform="translate(0, 0)">
                <rect x="0" y="0" width="185" height="38" rx="4" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" className="shadow-xs" />
                <rect x="0" y="0" width="4" height="38" rx="2" fill="#10b981" />
                
                {/* Asset Tag & Status */}
                <text x="10" y="14" fill="#18181b" className="font-mono text-[10px] font-bold">ASSET: TRK-05 (KOMATSU HD785)</text>
                <rect x="136" y="5" width="42" height="12" rx="2" fill="#ecfdf5" stroke="#a7f3d0" strokeWidth="0.8" />
                <text x="140" y="14" fill="#047857" className="font-mono text-[7.5px] font-bold">● READY</text>
                
                {/* DWRMS Job Card Detail */}
                <text x="10" y="26" fill="#52525b" className="font-mono text-[8.5px]">REQ-042 • Spodumene Haulage</text>
                <text x="10" y="34" fill="#a1a1aa" className="font-mono text-[7.5px]">Driver: R. Ndlovu • Gate Pass #88</text>
              </g>

              {/* Connecting HUD Signal Line */}
              <line x1="90" y1="38" x2="90" y2="70" stroke="#18181b" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx="90" cy="70" r="3" fill="#10b981" />
              <circle cx="90" cy="70" r="3" fill="none" stroke="#10b981" strokeWidth="1.5" className="radar-pulse" />

              {/* Weighbridge Platform Bed */}
              <line x1="-20" y1="140" x2="200" y2="140" stroke="#d4d4d8" strokeWidth="3" />
              <rect x="0" y="135" width="180" height="5" fill="#18181b" />

              {/* 100-Ton Heavy Haul Truck */}
              <g id="haul-truck" transform="translate(15, 65)">
                {/* Driver Cabin */}
                <path d="M 105 32 L 138 32 L 146 52 L 146 64 L 105 64 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.8" />
                <rect x="122" y="36" width="16" height="12" rx="1.5" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
                
                {/* Dump Bed Filled with Refined Lithium Concentrate */}
                <path d="M 15 26 L 98 26 L 102 64 L 20 64 Z" fill="#27272a" stroke="#18181b" strokeWidth="1.8" />
                <path d="M 22 26 Q 58 14 92 26 Z" fill="#10b981" />

                {/* Heavy Chassis Beam */}
                <rect x="20" y="62" width="120" height="6" fill="#18181b" />

                {/* Massive Mining Wheels */}
                <circle cx="38" cy="70" r="11" fill="#18181b" />
                <circle cx="38" cy="70" r="5" fill="#ffffff" />
                <circle cx="65" cy="70" r="11" fill="#18181b" />
                <circle cx="65" cy="70" r="5" fill="#ffffff" />
                <circle cx="128" cy="70" r="11" fill="#18181b" />
                <circle cx="128" cy="70" r="5" fill="#ffffff" />
              </g>

              {/* Dispatch Rate Badge */}
              <rect x="0" y="148" width="90" height="15" rx="2" fill="#f4f4f5" stroke="#d4d4d8" strokeWidth="1" />
              <text x="6" y="159" fill="#52525b" className="font-mono text-[9px] font-bold">OUT: 2,400 T/DAY</text>
            </g>

          </svg>
        </div>
      </div>

      {/* BOTTOM TELEMETRY STATUS CARDS */}
      <div className="relative z-10 space-y-2.5 pt-2 border-t border-zinc-200">
        <div className="grid grid-cols-3 gap-2.5">
          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1 font-semibold">
              <Layers className="size-3 text-zinc-700" />
              <span>FEED RATE</span>
            </div>
            <div className="text-xs font-mono font-bold text-zinc-900 mt-0.5">850 TPH</div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1 font-semibold">
              <Factory className="size-3 text-emerald-600" />
              <span>RECOVERY</span>
            </div>
            <div className="text-xs font-mono font-bold text-emerald-700 mt-0.5">88.4% Li₂O</div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1 font-semibold">
              <Truck className="size-3 text-zinc-700" />
              <span>DISPATCH</span>
            </div>
            <div className="text-xs font-mono font-bold text-zinc-900 mt-0.5">2,400 T/DAY</div>
          </div>
        </div>

        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
          <span className="flex items-center gap-1.5 font-semibold text-zinc-700">
            <HardHat className="size-3 text-zinc-800" />
            Bikita Minerals (Pvt) Ltd
          </span>
          <span className="flex items-center gap-1 text-emerald-600 font-semibold">
            <ShieldCheck className="size-3" />
            DWRMS Authoritative Core v2.8
          </span>
        </div>
      </div>
    </div>
  );
}
