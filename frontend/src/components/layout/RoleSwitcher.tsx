'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  ShieldCheck,
  Users,
  UserCheck,
  Wrench,
  Gauge,
  Shield,
  ChevronDown,
  Check,
} from 'lucide-react';
import { UserRole, resolveUserRole, getDefaultLandingRoute, isRouteAllowed } from '@/lib/rbac';

interface Persona {
  role: UserRole;
  name: string;
  email: string;
  badge: string;
  badgeColor: string;
  icon: React.ElementType;
  description: string;
}

const PERSONAS: Persona[] = [
  {
    role: 'Administrator',
    name: 'System Admin',
    email: 'admin@bikita.com',
    badge: 'ADMIN',
    badgeColor: 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900',
    icon: ShieldCheck,
    description: 'Full master governance, platform telemetry, and audit visibility',
  },
  {
    role: 'Department Manager',
    name: 'Dept Superintendent',
    email: 'mechmgr@bikita.com',
    badge: 'MANAGER',
    badgeColor: 'bg-amber-500/10 text-amber-600 border border-amber-500/20',
    icon: Users,
    description: 'Org hierarchy, shift approval escalations, and section budgets',
  },
  {
    role: 'Supervisor',
    name: 'Shift Supervisor',
    email: 'supervisor@bikita.com',
    badge: 'SUPERVISOR',
    badgeColor: 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20',
    icon: UserCheck,
    description: 'Work order sign-offs, machine allocation, and shift planning',
  },
  {
    role: 'Technician',
    name: 'Lead Artisan',
    email: 'tech@bikita.com',
    badge: 'ARTISAN',
    badgeColor: 'bg-blue-500/10 text-blue-600 border border-blue-500/20',
    icon: Wrench,
    description: 'Field execution, meter logging, spare parts requisitions',
  },
  {
    role: 'Operator',
    name: 'Equipment Operator',
    email: 'operator@bikita.com',
    badge: 'OPERATOR',
    badgeColor: 'bg-orange-500/10 text-orange-600 border border-orange-500/20',
    icon: Gauge,
    description: 'Equipment pre-use inspections, haulage tickets, assigned jobs',
  },
  {
    role: 'Safety Officer',
    name: 'HSE Officer',
    email: 'safety@bikita.com',
    badge: 'HSE',
    badgeColor: 'bg-rose-500/10 text-rose-600 border border-rose-500/20',
    icon: Shield,
    description: 'Hazard checklists, incident reviews, compliance audits',
  },
];

export function RoleSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const [currentRole, setCurrentRole] = useState<UserRole>('Administrator');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const syncCurrentRole = () => {
    if (typeof window !== 'undefined') {
      const email = localStorage.getItem('user_email');
      const role = localStorage.getItem('user_role');
      setCurrentRole(resolveUserRole(role || email));
    }
  };

  useEffect(() => {
    syncCurrentRole();

    const handleRoleChanged = () => {
      syncCurrentRole();
    };

    window.addEventListener('role-changed', handleRoleChanged);
    return () => window.removeEventListener('role-changed', handleRoleChanged);
  }, []);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleSelectPersona = (persona: Persona) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_role', persona.role);
      localStorage.setItem('user_email', persona.email);
      setCurrentRole(persona.role);
      window.dispatchEvent(new CustomEvent('role-changed', { detail: { role: persona.role, email: persona.email } }));

      setIsOpen(false);

      // Check if current route is allowed for new persona
      if (!isRouteAllowed(persona.role, pathname)) {
        const landing = getDefaultLandingRoute(persona.role);
        router.replace(landing);
      }
    }
  };

  const activePersona = PERSONAS.find((p) => p.role === currentRole) || PERSONAS[0];
  const Icon = activePersona.icon;

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-zinc-300 transition-colors text-left cursor-pointer"
        title="Switch active user role persona"
      >
        <Icon className="size-3.5 text-zinc-700 dark:text-zinc-300 shrink-0" />
        <div className="hidden xl:flex flex-col">
          <span className="text-[10px] font-mono leading-none text-zinc-500 uppercase">
            Active Persona
          </span>
          <span className="text-xs font-semibold leading-tight text-zinc-900 dark:text-zinc-100">
            {activePersona.role}
          </span>
        </div>
        <span className="xl:hidden text-xs font-semibold text-zinc-800">
          {activePersona.badge}
        </span>
        <ChevronDown className={`size-3 text-zinc-400 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-72 rounded-xl border border-zinc-200 bg-white dark:bg-zinc-950 p-1.5 shadow-xl z-50 text-zinc-900 dark:text-zinc-100 space-y-1">
          <div className="px-2.5 py-1.5 border-b border-zinc-100 dark:border-zinc-800">
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
              Switch Operational Role Persona
            </div>
            <div className="text-[10px] text-zinc-400 mt-0.5">
              Instantly audit views, buttons & permission guards
            </div>
          </div>

          <div className="space-y-0.5 max-h-80 overflow-y-auto">
            {PERSONAS.map((p) => {
              const PIcon = p.icon;
              const isSelected = p.role === currentRole;
              return (
                <button
                  key={p.role}
                  type="button"
                  onClick={() => handleSelectPersona(p)}
                  className={`w-full flex items-start gap-2.5 p-2 rounded-lg text-left transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800'
                      : 'hover:bg-zinc-50 dark:hover:bg-zinc-900/50 border border-transparent'
                  }`}
                >
                  <div className="p-1.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 mt-0.5 shrink-0">
                    <PIcon className="size-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-semibold truncate">{p.name}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold ${p.badgeColor}`}>
                        {p.badge}
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-zinc-500 truncate mt-0.5">
                      {p.email}
                    </div>
                    <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5 line-clamp-1">
                      {p.description}
                    </div>
                  </div>
                  {isSelected && (
                    <Check className="size-3.5 text-emerald-600 shrink-0 self-center" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
