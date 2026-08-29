'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  X,
  HardHat,
  Users,
  Settings,
  Database,
  ShieldAlert,
  Server,
  LogOut,
  Shield,
  Cloud,
  ChevronRight,
} from 'lucide-react';
import { Protect } from '@/components/auth/Protect';
import { logout } from '@/lib/auth';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Badge } from '@/components/ui/badge';

interface MobileNavDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenServerConfig: () => void;
  userInfo: { name: string; role: string; initials: string };
}

export function MobileNavDrawer({ isOpen, onClose, onOpenServerConfig, userInfo }: MobileNavDrawerProps) {
  const pathname = usePathname();

  if (!isOpen) return null;

  const adminLinks = [
    { name: 'User Management', href: '/admin/users', icon: Users, capability: 'users:manage' },
    { name: 'Platform Admin', href: '/admin/platform', icon: Server, capability: 'settings:manage' },
    { name: 'System Info & Telemetry', href: '/admin/system', icon: Database },
    { name: 'Security Audit Logs', href: '/admin/audit', icon: ShieldAlert, capability: 'settings:manage' },
  ];

  return (
    <div className="md:hidden fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sliding Sheet */}
      <div className="relative ml-auto w-full max-w-xs bg-slate-900 border-l border-slate-800 text-slate-100 flex flex-col h-full shadow-2xl p-5 overflow-y-auto animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 flex items-center justify-center font-bold">
              <HardHat className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-xs uppercase tracking-wider text-white">BIKITA DWRMS</div>
              <div className="text-[10px] text-slate-400 font-mono">Mobile Operations Hub</div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User Card */}
        <div className="py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-amber-400 font-mono">
              {userInfo.initials}
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-1">
                <span>{userInfo.name}</span>
                <Shield className="w-3 h-3 text-amber-400" />
              </div>
              <div className="text-[10px] text-slate-400 font-mono">{userInfo.role}</div>
            </div>
          </div>
          <ThemeToggle />
        </div>

        {/* Admin Navigation */}
        <div className="py-4 flex-1 space-y-1">
          <div className="px-2 pb-2 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Administrative & System Modules
          </div>

          {adminLinks.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href);
            const Icon = item.icon;

            const linkEl = (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 opacity-50" />
              </Link>
            );

            if (item.capability) {
              return (
                <Protect key={item.name} capability={item.capability}>
                  {linkEl}
                </Protect>
              );
            }
            return linkEl;
          })}
        </div>

        {/* Server & Session Footer */}
        <div className="pt-4 border-t border-slate-800 space-y-2">
          <button
            type="button"
            onClick={() => {
              onClose();
              onOpenServerConfig();
            }}
            className="w-full flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 hover:border-slate-700"
          >
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-amber-400" />
              <span>Server Connection Profiles</span>
            </div>
            <Badge variant="outline" className="text-[9px] border-emerald-500/40 text-emerald-400">
              MANAGE
            </Badge>
          </button>

          <button
            type="button"
            onClick={() => {
              onClose();
              logout();
            }}
            className="w-full flex items-center justify-center gap-2 p-2.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs font-bold transition"
          >
            <LogOut className="w-4 h-4" />
            Sign Out of Operations Console
          </button>
        </div>
      </div>
    </div>
  );
}
