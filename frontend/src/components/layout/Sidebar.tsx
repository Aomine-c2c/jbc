'use client';

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
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
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { getPendingApprovals } from "@/lib/approvals";
import { hasCapability, isRouteAllowed } from "@/lib/rbac";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  exact?: boolean;
  capability?: string;
  badge?: number | null;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  onOpenServerConfig?: () => void;
}

export function Sidebar({ onOpenServerConfig }: SidebarProps = {}) {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = useState<number | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [loadedPerms, setLoadedPerms] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const email = localStorage.getItem('user_email');
      const role = localStorage.getItem('user_role');
      setUserRole(role || email);
    }

    getPendingApprovals()
      .then((data) => {
        setPendingCount(data.length);
      })
      .catch(() => {});

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
  }, []);

  const sections: NavSection[] = [
    {
      title: "Core Operations",
      items: [
        { name: "My Work", href: "/my-work", icon: Wrench, exact: true, capability: "my_work:view" },
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
        {
          name: "Approvals Inbox",
          href: "/approvals",
          icon: ShieldCheck,
          capability: "approvals:view",
          badge: pendingCount !== null && pendingCount > 0 ? pendingCount : null,
        },
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
    <aside className="hidden md:flex w-60 bg-white border-r border-zinc-200 flex-col h-full shrink-0 select-none">
      {/* BRAND HEADER */}
      <div className="h-14 flex items-center px-4 border-b border-zinc-200 shrink-0 bg-zinc-50/50">
        <div className="flex items-center gap-2.5">
          <div className="size-8 rounded-md bg-zinc-900 text-white flex items-center justify-center font-bold shadow-xs">
            <HardHat className="size-4" />
          </div>
          <div>
            <div className="font-bold text-xs tracking-wider text-zinc-900 uppercase">
              BIKITA DWRMS
            </div>
            <div className="text-[10px] font-mono text-zinc-500">
              Operations Console
            </div>
          </div>
        </div>
      </div>

      {/* GROUPED NAVIGATION */}
      <nav className="flex-1 overflow-y-auto py-3 px-2.5 space-y-4">
        {sections.map((section) => {
          const visibleItems = section.items.filter((item) => hasPermission(item.capability, item.href));
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title} className="space-y-0.5">
              <div className="px-2 pb-1 text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                {section.title}
              </div>

              {visibleItems.map((item) => {
                const isActive = item.exact
                  ? pathname === item.href
                  : pathname?.startsWith(item.href);

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`group flex items-center px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-zinc-900 text-white font-semibold shadow-xs"
                        : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                    }`}
                  >
                    <item.icon
                      className={`size-4 mr-2.5 shrink-0 transition-colors ${
                        isActive
                          ? "text-white"
                          : "text-zinc-400 group-hover:text-zinc-900"
                      }`}
                    />
                    <span className="flex-1 truncate">{item.name}</span>

                    {item.badge !== undefined && item.badge !== null && (
                      <span
                        className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                          isActive
                            ? "bg-white text-zinc-900"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* SERVER STATUS FOOTER */}
      <div className="p-2.5 border-t border-zinc-200 bg-zinc-50/50">
        <button
          type="button"
          onClick={onOpenServerConfig}
          title="Click to configure central server endpoint"
          className="w-full text-left rounded-md border border-zinc-200 bg-white p-2 space-y-1 hover:border-zinc-300 hover:bg-zinc-50 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500">
            <span>NODE STATUS</span>
            <span className="text-emerald-600 font-semibold flex items-center gap-1">
              <span className="size-1.5 rounded-full bg-emerald-500 inline-block" />
              ONLINE
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-800">
            <Database className="size-3 text-zinc-400" />
            <span className="truncate">Bikita Mining Core</span>
          </div>
        </button>
      </div>
    </aside>
  );
}

