'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldAlert, ArrowLeft, Lock, UserCheck } from 'lucide-react';
import { resolveUserRole, getDefaultLandingRoute, ROLE_CONFIGS, UserRole } from '@/lib/rbac';
import { Button } from '@/components/ui/button';

interface AccessRestrictedProps {
  pathname: string;
  userRole?: string | null;
}

export function AccessRestricted({ pathname, userRole }: AccessRestrictedProps) {
  const role: UserRole = resolveUserRole(userRole);
  const roleConfig = ROLE_CONFIGS[role];
  const homeRoute = getDefaultLandingRoute(userRole);

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4 sm:p-6">
      <div className="max-w-lg w-full rounded-xl border border-destructive/30 bg-card p-6 md:p-8 shadow-sm text-center space-y-5">
        <div className="mx-auto size-14 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <ShieldAlert className="size-7" />
        </div>

        <div className="space-y-2">
          <div className="text-xs font-mono uppercase tracking-widest text-destructive font-bold flex items-center justify-center gap-1.5">
            <Lock className="size-3.5" />
            <span>HTTP 403 • Operational Access Denied</span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
            Restricted Operational Subsystem
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
            Your active operational role (
            <span className="font-semibold text-foreground">{roleConfig?.title || role}</span>
            ) does not have authorization to view or manage the subsystem at{' '}
            <span className="font-mono text-foreground font-semibold px-1.5 py-0.5 rounded bg-muted/60">
              {pathname}
            </span>.
          </p>
        </div>

        <div className="rounded-lg border border-border/80 bg-muted/30 p-3.5 text-left space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-muted-foreground uppercase">Current Role:</span>
            <span className="font-bold text-foreground flex items-center gap-1">
              <UserCheck className="size-3 text-primary" />
              {roleConfig?.title || role}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-muted-foreground uppercase">Target Route:</span>
            <span className="font-semibold text-foreground">{pathname}</span>
          </div>
          <div className="text-[10px] text-muted-foreground pt-1 border-t border-border/40">
            Access to this facility is governed by strict mine safety and operational compliance policies. If you require access, request role escalation from your Department Superintendent.
          </div>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row gap-2 justify-center">
          <Link href={homeRoute} className="w-full sm:w-auto">
            <Button variant="default" size="sm" className="w-full gap-2 font-mono text-xs">
              <ArrowLeft className="size-3.5" />
              Return to Authorized Workspace ({homeRoute})
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
