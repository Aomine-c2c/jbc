'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  X,
  HardHat,
  LayoutDashboard,
  Wrench,
  Layers,
  Truck,
  Boxes,
  FileText,
  Package,
  Briefcase,
  ShieldCheck,
  Timer,
  Users,
  Building2,
  MapPin,
  Settings,
  Server,
  Database,
  ShieldAlert,
  LogOut,
  ChevronRight,
} from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { logout } from '@/lib/auth';
import { hasCapability, isRouteAllowed } from '@/lib/rbac';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  capability?: string;
  exact?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface MobileNavDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenServerConfig: () => void;
  userInfo: { name: string; role: string; initials: string };
}

export function MobileNavDrawer({ isOpen, onClose, onOpenServerConfig, userInfo }: MobileNavDrawerProps) {
  const pathname = usePathname();
  const [permissions, setPermissions] = useState<string[]>([]);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [loadedPerms, setLoadedPerms] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    if (typeof window !== 'undefined') {
      const email = localStorage.getItem('user_email');
      const role = localStorage.getItem('user_role');
      setUserRole(role || email);
    }
    apiFetch("/api/v1/iam/auth/me/permissions")
      .then((res) => {
        if (Array.isArray(res)) {
          setPermissions(res);
        } else if (res && Array.isArray(res.data)) {
          setPermissions(res.data);
        }
      })
      .catch(() => {})
      .finally(() => setLoadedPerms(true));
  }, [isOpen]);

  if (!isOpen) return null;

  const sections: NavSection[] = [
    {
      title: "Core Operations",
      items: [
        { name: "My Work Hub", href: "/my-work", icon: Wrench, exact: true, capability: "my_work:view" },
        { name: "Ops Dashboard", href: "/dashboard", icon: LayoutDashboard, capability: "dashboard:view" },
        { name: "Job Cards", href: "/jobs", icon: Wrench, capability: "jobs:view" },
        { name: "Work Hub", href: "/work", icon: Layers, capability: "work_hub:view" },
      ],
    },
    {
      title: "Assets & Resources",
      items: [
        { name: "Fleet & Machines", href: "/fleet", icon: Truck, capability: "fleet:view" },
        { name: "Asset Registry", href: "/assets", icon: Boxes, capability: "assets:view" },
        { name: "Requisitions Hub", href: "/requests", icon: FileText, capability: "requisition:create" },
        { name: "Materials & Stores", href: "/materials", icon: Package, capability: "materials:view" },
        { name: "Contractors", href: "/contractors", icon: Briefcase, capability: "contractors:view" },
      ],
    },
    {
      title: "Control & SLA",
      items: [
        { name: "Approvals Inbox", href: "/approvals", icon: ShieldCheck, capability: "approvals:view" },
        { name: "SLA & Escalations", href: "/sla", icon: Timer, capability: "sla:view" },
      ],
    },
    {
      title: "Administration",
      items: [
        { name: "User Directory", href: "/admin/users", icon: Users, capability: "users:manage" },
        { name: "Organization", href: "/admin/org", icon: Building2, capability: "org:manage" },
        { name: "Locations", href: "/admin/locations", icon: MapPin, capability: "locations:manage" },
        { name: "Workflows", href: "/admin/workflows", icon: Settings, capability: "workflows:manage" },
        { name: "Platform Admin", href: "/admin/platform", icon: Server, capability: "platform:manage" },
        { name: "System Info", href: "/admin/system", icon: Database, capability: "system:manage" },
        { name: "Audit Logs", href: "/admin/audit", icon: ShieldAlert, capability: "audit:view" },
      ],
    },
  ];

  const hasPermission = (capability?: string, href?: string) => {
    if (href && !isRouteAllowed(userRole, href)) return false;
    if (!capability) return true;
    return hasCapability(userRole, permissions, capability);
  };

  return (
    <div className="md:hidden fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-zinc-950/70 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Sliding Sheet */}
      <div className="relative ml-auto w-full max-w-xs bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 flex flex-col h-full shadow-2xl p-5 overflow-y-auto animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center gap-2.5">
            <div className="size-8 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 flex items-center justify-center font-bold shadow-xs">
              <HardHat className="size-4" />
            </div>
            <div>
              <div className="font-bold text-xs uppercase tracking-wider text-zinc-900 dark:text-white">BIKITA DWRMS</div>
              <div className="text-[10px] text-zinc-500 font-mono">Mobile Operations Console</div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-zinc-800 dark:hover:text-white rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* User Card */}
        <div className="py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center font-bold text-xs text-zinc-900 dark:text-zinc-100 font-mono">
              {userInfo.initials}
            </div>
            <div>
              <div className="text-xs font-bold text-zinc-900 dark:text-white flex items-center gap-1">
                <span>{userInfo.name}</span>
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">{userInfo.role}</div>
            </div>
          </div>
          <ThemeToggle />
        </div>

        {/* Grouped Navigation */}
        <div className="py-4 flex-1 space-y-4">
          {sections.map((section) => {
            const visibleItems = section.items.filter((item) => hasPermission(item.capability, item.href));
            if (visibleItems.length === 0) return null;

            return (
              <div key={section.title} className="space-y-1">
                <div className="px-2 text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                  {section.title}
                </div>

                {visibleItems.map((item) => {
                  const isActive = item.exact
                    ? pathname === item.href
                    : pathname?.startsWith(item.href);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={onClose}
                      className={`flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-bold shadow-xs'
                          : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="size-4" />
                        <span>{item.name}</span>
                      </div>
                      <ChevronRight className="size-3.5 opacity-40" />
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* Server & Session Footer */}
        <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
          <button
            type="button"
            onClick={() => {
              onClose();
              onOpenServerConfig();
            }}
            className="w-full flex items-center justify-between p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-700 dark:text-zinc-300 hover:border-zinc-400 transition"
          >
            <div className="flex items-center gap-2">
              <Server className="size-4 text-zinc-700 dark:text-zinc-300" />
              <span>Server Connection Profiles</span>
            </div>
            <Badge variant="outline" className="text-[9px] border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
              MANAGE
            </Badge>
          </button>

          <button
            type="button"
            onClick={() => {
              onClose();
              logout();
            }}
            className="w-full flex items-center justify-center gap-2 p-2.5 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 text-xs font-bold transition"
          >
            <LogOut className="size-4" />
            Sign Out of Operations Console
          </button>
        </div>
      </div>
    </div>
  );
}
