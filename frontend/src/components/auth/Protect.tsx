'use client';

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ShieldAlert, ArrowLeft, Lock } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { resolveUserRole, getDefaultLandingRoute, hasCapability, ROLE_CONFIGS } from "@/lib/rbac";
import { Button } from "@/components/ui/button";

interface ProtectProps {
  capability?: string | string[];
  isPageGuard?: boolean;
  moduleName?: string;
  children: React.ReactNode;
}

export function Protect({ capability, isPageGuard = false, moduleName, children }: ProtectProps) {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let email: string | null = null;
    if (typeof window !== 'undefined') {
      email = localStorage.getItem('user_email');
      const savedRole = localStorage.getItem('user_role');
      setUserRole(savedRole || email);
    }

    const fetchPermissions = async () => {
      try {
        const res = await apiFetch("/api/v1/iam/auth/me/permissions");
        if (Array.isArray(res)) {
          setPermissions(res);
        } else if (res && Array.isArray(res.data)) {
          setPermissions(res.data);
        }
      } catch {
        // use local role capabilities
      } finally {
        setLoading(false);
      }
    };
    fetchPermissions();
  }, []);

  if (loading) return null;

  if (!capability) {
    return <>{children}</>;
  }

  const role = resolveUserRole(userRole);
  const authorized = hasCapability(userRole, permissions, capability);

  if (authorized) {
    return <>{children}</>;
  }

  if (isPageGuard) {
    const roleConfig = ROLE_CONFIGS[role];
    const homeRoute = getDefaultLandingRoute(userRole);

    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="max-w-md w-full rounded-lg border border-border bg-card p-6 shadow-sm text-center space-y-4">
          <div className="mx-auto size-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
            <ShieldAlert className="size-6" />
          </div>

          <div className="space-y-1.5">
            <div className="text-xs font-mono uppercase tracking-wider text-destructive font-bold">
              HTTP 403 • ACCESS RESTRICTED
            </div>
            <h2 className="text-lg font-bold text-foreground">
              Unauthorized Module Access
            </h2>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Your active authorization tier (
              <span className="font-semibold text-foreground">{roleConfig?.title || role}</span>
              ) does not have clearance to access {moduleName || "this operational subsystem"}.
            </p>
          </div>

          <div className="rounded border border-border/70 bg-muted/20 p-3 text-left space-y-1">
            <div className="text-[10px] font-mono uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
              <Lock className="size-3 text-amber-500" />
              <span>Required Clearance</span>
            </div>
            <div className="text-xs font-mono text-foreground font-semibold">
              {Array.isArray(capability) ? capability.join(' OR ') : capability}
            </div>
          </div>

          <div className="pt-2">
            <Link href={homeRoute}>
              <Button variant="default" size="sm" className="w-full gap-2 font-mono text-xs">
                <ArrowLeft className="size-3.5" />
                Return to Designated Home Hub ({homeRoute})
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
