'use client';

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Protect } from "@/components/auth/Protect";
import { LayoutDashboard, Wrench, Truck, Users, Settings, Database, HardHat, ShieldAlert, ShieldCheck, Server, Building2 } from "lucide-react";
import { getPendingApprovals } from "@/lib/approvals";

interface SidebarProps {
  onOpenServerConfig?: () => void;
}

export function Sidebar({ onOpenServerConfig }: SidebarProps = {}) {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  useEffect(() => {
    getPendingApprovals().then(data => {
      setPendingCount(data.length);
    }).catch(() => {
      // Ignore errors for sidebar count
    });
  }, []);

  const navItems = [
    { name: "Home", href: "/", icon: LayoutDashboard, exact: true },
    { name: "Ops Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Approvals Inbox", href: "/approvals", icon: ShieldCheck, badge: pendingCount !== null && pendingCount > 0 ? pendingCount : null },
    { name: "Job Cards", href: "/jobs", icon: Wrench, capability: "job_card:read" },
    { name: "Fleet & Machines", href: "/fleet", icon: Truck },
    { name: "Organization", href: "/admin/org", icon: Building2, capability: "users:manage" },
    { name: "User Management", href: "/admin/users", icon: Users, capability: "users:manage" },
    { name: "Platform Admin", href: "/admin/platform", icon: Server, capability: "settings:manage" },
    { name: "System Info", href: "/admin/system", icon: Database },
    { name: "Audit Logs", href: "/admin/audit", icon: ShieldAlert, capability: "settings:manage" },
  ];

  return (
    <div className="hidden md:flex w-60 bg-card border-r border-border flex-col h-full shrink-0 select-none">
      <div className="h-14 flex items-center px-5 border-b border-border shrink-0 bg-muted/20">
        <div className="flex items-center gap-2.5">
          <div className="size-7 rounded bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
            <HardHat className="size-4" />
          </div>
          <div>
            <div className="font-bold text-xs tracking-wider text-foreground uppercase">
              BIKITA DWRMS
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">
              v1.8 • Server-First
            </div>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <div className="px-2 pb-1.5 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/70 font-semibold">
          Operations Navigation
        </div>

        {navItems.map((item) => {
          const isActive = item.exact 
            ? pathname === item.href 
            : pathname?.startsWith(item.href);

          const linkContent = (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center px-2.5 py-2 rounded text-xs font-medium transition-all ${
                isActive 
                  ? "bg-primary text-primary-foreground font-semibold shadow-xs" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <item.icon className="size-4 mr-2.5 shrink-0" />
              <span className="flex-1">{item.name}</span>
              {item.badge !== undefined && item.badge !== null && (
                <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full ${isActive ? 'bg-primary-foreground text-primary' : 'bg-primary text-primary-foreground'}`}>
                  {item.badge}
                </span>
              )}
              {isActive && item.badge === undefined && (
                <span className="size-1.5 rounded-full bg-primary-foreground/80 ml-auto" />
              )}
            </Link>
          );

          if (item.capability) {
            return (
              <Protect key={item.name} capability={item.capability}>
                {linkContent}
              </Protect>
            );
          }

          return linkContent;
        })}
      </nav>

      <div className="p-3 border-t border-border bg-muted/20">
        <button
          type="button"
          onClick={onOpenServerConfig}
          title="Click to configure central server endpoint"
          className="w-full text-left rounded border border-border/60 bg-card p-2.5 space-y-1.5 hover:bg-muted/50 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground">
            <span>SERVER FIRST</span>
            <span className="text-emerald-500 font-bold">NODE SYNC</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-foreground">
            <Database className="size-3 text-muted-foreground" />
            <span>Ubuntu Authoritative Core</span>
          </div>
        </button>
      </div>
    </div>
  );
}
