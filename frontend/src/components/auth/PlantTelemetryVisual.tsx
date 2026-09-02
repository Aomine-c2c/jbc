'use client';

import React, { useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';
import { HardHat, Activity, Layers, Truck, Factory } from 'lucide-react';

export function PlantTelemetryVisual() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 1. Conveyor Belt Motion (Stroke Dash Offset)
    const conveyorAnim = animate('.conveyor-path', {
      strokeDashoffset: [0, -40],
      ease: 'linear',
      duration: 2000,
      loop: true,
    });

    // 2. Ore Particle Flow Animation across conveyors
    const oreParticles = animate('.ore-particle-1', {
      translateX: [0, 110],
      translateY: [0, 40],
      opacity: [
        { to: 1, duration: 200 },
        { to: 1, duration: 1200 },
        { to: 0, duration: 200 },
      ],
      ease: 'inOutSine',
      duration: 2400,
      delay: stagger(400),
      loop: true,
    });

    const oreParticles2 = animate('.ore-particle-2', {
      translateX: [0, 120],
      translateY: [0, 30],
      opacity: [
        { to: 1, duration: 200 },
        { to: 1, duration: 1200 },
        { to: 0, duration: 200 },
      ],
      ease: 'inOutSine',
      duration: 2200,
      delay: stagger(350),
      loop: true,
    });

    const oreParticles3 = animate('.ore-particle-3', {
      translateX: [0, 100],
      translateY: [0, 80],
      opacity: [
        { to: 1, duration: 200 },
        { to: 1, duration: 1100 },
        { to: 0, duration: 200 },
      ],
      ease: 'inOutSine',
      duration: 2000,
      delay: stagger(300),
      loop: true,
    });

    // 3. Excavator Arm Oscillation
    const boomAnim = animate('#excavator-arm', {
      rotate: [-4, 6],
      transformOrigin: '20px 80px',
      alternate: true,
      ease: 'inOutQuad',
      duration: 3200,
      loop: true,
    });

    // 4. Crusher Jaw Oscillation
    const crusherAnim = animate('#crusher-jaw', {
      scaleY: [1, 0.92],
      translateY: [0, 4],
      alternate: true,
      ease: 'inOutSine',
      duration: 600,
      loop: true,
    });

    // 5. Concentrator Gear Rotation
    const gearAnim = animate('.mill-gear', {
      rotate: 360,
      transformOrigin: 'center center',
      ease: 'linear',
      duration: 6000,
      loop: true,
    });

    // 6. Haul Truck Vibration
    const truckAnim = animate('#haul-truck', {
      translateY: [-0.5, 0.5],
      alternate: true,
      ease: 'inOutSine',
      duration: 400,
      loop: true,
    });

    return () => {
      conveyorAnim.pause?.();
      oreParticles.pause?.();
      oreParticles2.pause?.();
      oreParticles3.pause?.();
      boomAnim.pause?.();
      crusherAnim.pause?.();
      gearAnim.pause?.();
      truckAnim.pause?.();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col justify-between h-full w-full bg-zinc-100 p-6 md:p-10 overflow-hidden text-zinc-900 select-none border-r border-zinc-200"
    >
      {/* TECHNICAL SCHEMATIC BACKGROUND GRID */}
      <div
        className="absolute inset-0 opacity-[0.45] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(#e4e4e7 1px, transparent 1px), linear-gradient(90deg, #e4e4e7 1px, transparent 1px)`,
          backgroundSize: '24px 24px',
        }}
      />

      {/* TOP BRAND HEADER */}
      <div className="relative z-10 space-y-1.5">
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-700 font-semibold tracking-wider uppercase">
          <span className="relative flex size-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full size-2 bg-emerald-600"></span>
          </span>
          <Activity className="size-3.5" />
          <span>Bikita Mining & Concentrator Flow</span>
        </div>

        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-zinc-900 flex items-center gap-2 font-mono uppercase">
          Plant Process Schematic
        </h2>
        <p className="text-xs text-zinc-500 font-mono">
          Stage 1 Extraction → Stage 2 Crushing → Stage 3 Concentrator → Stage 4 Dispatch
        </p>
      </div>

      {/* CENTER: ANIMATED MINING SVG SCHEMATIC */}
      <div className="relative z-10 my-auto flex items-center justify-center py-4">
        <div className="relative w-full max-w-[560px] aspect-[16/11]">
          <svg
            viewBox="0 0 560 385"
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

            {/* STAGE 1: OPEN-PIT EXTRACTION (TOP-LEFT) */}
            <g id="stage-pit" transform="translate(20, 30)">
              {/* Pit Bench Background */}
              <path d="M 0 95 L 70 95 L 90 120 L 130 120" stroke="#d4d4d8" strokeWidth="2" fill="url(#diagonalHatch)" />
              
              {/* Stage Tag */}
              <rect x="0" y="0" width="115" height="18" rx="3" fill="#18181b" />
              <text x="6" y="12" fill="#ffffff" className="font-mono text-[9px] font-bold tracking-wider">01. PIT EXTRACTION</text>

              {/* Mining Excavator */}
              <g id="excavator" transform="translate(10, 25)">
                {/* Tracks */}
                <rect x="10" y="58" width="55" height="12" rx="4" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                <circle cx="20" cy="64" r="3" fill="#71717a" />
                <circle cx="37" cy="64" r="3" fill="#71717a" />
                <circle cx="55" cy="64" r="3" fill="#71717a" />
                {/* Body & Cab */}
                <rect x="15" y="38" width="38" height="20" rx="3" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                <rect x="35" y="42" width="14" height="10" rx="1" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
                <circle cx="24" cy="46" r="4" fill="#18181b" />
                
                {/* Moving Boom Arm & Bucket */}
                <g id="excavator-arm">
                  <path d="M 45 42 L 72 20 L 92 40" stroke="#18181b" strokeWidth="3" strokeLinecap="round" />
                  <path d="M 92 40 L 98 52 L 86 54 Z" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                  <circle cx="45" cy="42" r="2.5" fill="#18181b" />
                  <circle cx="72" cy="20" r="2.5" fill="#18181b" />
                </g>
              </g>

              {/* Hopper Feeder */}
              <path d="M 95 65 L 125 65 L 115 88 L 105 88 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
            </g>

            {/* CONVEYOR 1: PIT TO CRUSHER */}
            <g id="conveyor-1">
              <path
                d="M 140 115 L 210 145"
                stroke="#a1a1aa"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <path
                d="M 140 115 L 210 145"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
              {/* Ore particles */}
              <circle cx="140" cy="115" r="3.5" fill="#27272a" className="ore-particle-1" />
              <circle cx="140" cy="115" r="2.5" fill="#52525b" className="ore-particle-1" />
              <circle cx="140" cy="115" r="3" fill="#18181b" className="ore-particle-1" />
            </g>

            {/* STAGE 2: CRUSHING & SCREENING (CENTER-LEFT) */}
            <g id="stage-crushing" transform="translate(195, 105)">
              {/* Stage Tag */}
              <rect x="10" y="0" width="130" height="18" rx="3" fill="#18181b" />
              <text x="16" y="12" fill="#ffffff" className="font-mono text-[9px] font-bold tracking-wider">02. PRIMARY CRUSHER</text>

              {/* Jaw Crusher Housing */}
              <rect x="15" y="24" width="70" height="60" rx="4" fill="url(#zincGradient)" stroke="#18181b" strokeWidth="1.5" />
              
              {/* Crusher Hopper Throat */}
              <path d="M 25 24 L 75 24 L 65 44 L 35 44 Z" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
              
              {/* Oscillating Crusher Jaw Plate */}
              <g id="crusher-jaw">
                <rect x="42" y="44" width="16" height="18" rx="1" fill="#27272a" stroke="#18181b" strokeWidth="1" />
                <line x1="44" y1="48" x2="56" y2="48" stroke="#ffffff" strokeWidth="1" />
                <line x1="44" y1="52" x2="56" y2="52" stroke="#ffffff" strokeWidth="1" />
              </g>

              {/* Sizing Vibrating Screen */}
              <g transform="translate(55, 60)">
                <line x1="0" y1="0" x2="35" y2="18" stroke="#18181b" strokeWidth="3" />
                <line x1="0" y1="4" x2="32" y2="20" stroke="#71717a" strokeWidth="1.5" strokeDasharray="3 3" />
              </g>

              {/* Telemetry Indicator */}
              <rect x="15" y="88" width="55" height="14" rx="2" fill="#f4f4f5" stroke="#d4d4d8" strokeWidth="1" />
              <text x="20" y="98" fill="#52525b" className="font-mono text-[8px] font-semibold">P80: 12.4mm</text>
            </g>

            {/* CONVEYOR 2: CRUSHER TO CONCENTRATOR */}
            <g id="conveyor-2">
              <path
                d="M 285 180 L 375 205"
                stroke="#a1a1aa"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <path
                d="M 285 180 L 375 205"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
              {/* Crushed Ore particles */}
              <circle cx="285" cy="180" r="2.5" fill="#18181b" className="ore-particle-2" />
              <circle cx="285" cy="180" r="2" fill="#52525b" className="ore-particle-2" />
              <circle cx="285" cy="180" r="2.5" fill="#27272a" className="ore-particle-2" />
            </g>

            {/* STAGE 3: CONCENTRATOR & FLOTATION PLANT (CENTER-RIGHT) */}
            <g id="stage-concentrator" transform="translate(365, 90)">
              {/* Stage Tag */}
              <rect x="0" y="0" width="145" height="18" rx="3" fill="#18181b" />
              <text x="6" y="12" fill="#ffffff" className="font-mono text-[9px] font-bold tracking-wider">03. SPODUMENE PLANT</text>

              {/* Concentrator Building Outline */}
              <path d="M 10 105 L 10 40 L 45 24 L 95 24 L 95 105 Z" fill="url(#zincGradient)" stroke="#18181b" strokeWidth="1.5" />
              
              {/* Rotating Ball Mill Drum & Gear */}
              <g transform="translate(32, 60)">
                <rect x="-16" y="-12" width="32" height="24" rx="3" fill="#27272a" stroke="#18181b" strokeWidth="1" />
                <g className="mill-gear">
                  <circle cx="0" cy="0" r="8" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                  <line x1="-8" y1="0" x2="8" y2="0" stroke="#18181b" strokeWidth="1.5" />
                  <line x1="0" y1="-8" x2="0" y2="8" stroke="#18181b" strokeWidth="1.5" />
                </g>
              </g>

              {/* Flotation Column / Tank */}
              <g transform="translate(68, 50)">
                <rect x="0" y="0" width="22" height="42" rx="2" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                <line x1="3" y1="12" x2="19" y2="12" stroke="#10b981" strokeWidth="1.5" />
                <line x1="3" y1="20" x2="19" y2="20" stroke="#10b981" strokeWidth="1" strokeDasharray="2 2" />
                <line x1="3" y1="28" x2="19" y2="28" stroke="#10b981" strokeWidth="1" strokeDasharray="2 2" />
              </g>

              {/* Concentrate Storage Silo */}
              <g transform="translate(102, 35)">
                <path d="M 0 20 L 15 8 L 30 20 L 30 70 L 15 80 L 0 70 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                <line x1="5" y1="35" x2="25" y2="35" stroke="#e4e4e7" strokeWidth="1" />
                <line x1="5" y1="50" x2="25" y2="50" stroke="#e4e4e7" strokeWidth="1" />
              </g>

              {/* Telemetry Indicator */}
              <rect x="10" y="112" width="60" height="14" rx="2" fill="#ecfdf5" stroke="#a7f3d0" strokeWidth="1" />
              <text x="14" y="122" fill="#047857" className="font-mono text-[8px] font-bold">REC: 88.4% Li₂O</text>
            </g>

            {/* CONVEYOR 3: SILO TO DISPATCH TRUCK */}
            <g id="conveyor-3">
              <path
                d="M 480 205 L 430 270"
                stroke="#a1a1aa"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <path
                d="M 480 205 L 430 270"
                className="conveyor-path"
                stroke="#18181b"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
              {/* Fine Concentrate particles */}
              <circle cx="480" cy="205" r="2" fill="#047857" className="ore-particle-3" />
              <circle cx="480" cy="205" r="2" fill="#18181b" className="ore-particle-3" />
              <circle cx="480" cy="205" r="1.5" fill="#10b981" className="ore-particle-3" />
            </g>

            {/* STAGE 4: DISPATCH & HAULAGE (BOTTOM-RIGHT) */}
            <g id="stage-dispatch" transform="translate(310, 260)">
              {/* Stage Tag */}
              <rect x="0" y="0" width="135" height="18" rx="3" fill="#18181b" />
              <text x="6" y="12" fill="#ffffff" className="font-mono text-[9px] font-bold tracking-wider">04. PRODUCT DISPATCH</text>

              {/* Weighbridge Ground Line */}
              <line x1="-15" y1="80" x2="160" y2="80" stroke="#d4d4d8" strokeWidth="2" />
              <rect x="0" y="76" width="140" height="4" fill="#18181b" />

              {/* Haul Truck */}
              <g id="haul-truck" transform="translate(15, 25)">
                {/* Cab */}
                <path d="M 80 25 L 105 25 L 112 40 L 112 50 L 80 50 Z" fill="#ffffff" stroke="#18181b" strokeWidth="1.5" />
                <rect x="94" y="29" width="12" height="9" rx="1" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
                
                {/* Dump Bed with Mineral Concentrate */}
                <path d="M 10 20 L 75 20 L 78 50 L 15 50 Z" fill="#27272a" stroke="#18181b" strokeWidth="1.5" />
                <path d="M 16 20 Q 42 12 70 20 Z" fill="#10b981" />

                {/* Chassis Frame */}
                <rect x="15" y="48" width="90" height="4" fill="#18181b" />

                {/* Wheels */}
                <circle cx="28" cy="54" r="8" fill="#18181b" />
                <circle cx="28" cy="54" r="4" fill="#ffffff" />
                <circle cx="48" cy="54" r="8" fill="#18181b" />
                <circle cx="48" cy="54" r="4" fill="#ffffff" />
                <circle cx="98" cy="54" r="8" fill="#18181b" />
                <circle cx="98" cy="54" r="4" fill="#ffffff" />
              </g>

              {/* Dispatch Badge */}
              <rect x="0" y="90" width="75" height="14" rx="2" fill="#f4f4f5" stroke="#d4d4d8" strokeWidth="1" />
              <text x="5" y="100" fill="#52525b" className="font-mono text-[8px] font-semibold">OUT: 2,400 T/DAY</text>
            </g>

            {/* FLOW CONNECTION ARROWS */}
            <path d="M 120 185 L 140 185 L 140 250 L 260 250" stroke="#e4e4e7" strokeWidth="1.5" strokeDasharray="4 4" />
          </svg>
        </div>
      </div>

      {/* BOTTOM TELEMETRY STATUS CARDS */}
      <div className="relative z-10 space-y-3 pt-3 border-t border-zinc-200">
        <div className="grid grid-cols-3 gap-2.5">
          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1">
              <Layers className="size-3 text-zinc-700" />
              <span>FEED RATE</span>
            </div>
            <div className="text-xs font-mono font-bold text-zinc-900 mt-0.5">850 TPH</div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1">
              <Factory className="size-3 text-emerald-600" />
              <span>RECOVERY</span>
            </div>
            <div className="text-xs font-mono font-bold text-emerald-700 mt-0.5">88.4% Li₂O</div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white p-2.5 shadow-2xs text-center">
            <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-center gap-1">
              <Truck className="size-3 text-zinc-700" />
              <span>DISPATCH</span>
            </div>
            <div className="text-xs font-mono font-bold text-zinc-900 mt-0.5">2,400 T/DAY</div>
          </div>
        </div>

        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
          <span className="flex items-center gap-1">
            <HardHat className="size-3 text-zinc-700" />
            Bikita Minerals (Pvt) Ltd
          </span>
          <span>DWRMS Core v2.8</span>
        </div>
      </div>
    </div>
  );
}
