'use client';

import React, { useEffect, useState, useCallback } from "react";
import { Protect } from "@/components/auth/Protect";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Server, Database, MonitorSmartphone, Wifi, WifiOff, ShieldCheck, Cpu, RefreshCw, Smartphone, Globe, Terminal } from "lucide-react";
import { useConnection } from "@/lib/providers/ConnectionProvider";
import { getApiUrl, apiFetch } from "@/lib/api";
import { getVersion } from "@tauri-apps/api/app";
import { ServerConfigDialog } from "@/components/config/ServerConfigDialog";

interface PlatformInfo {
  serverVersion: string;
  serverEnv: string;
  clientVersion: string;
  clientType: string;
  dbStatus: string;
  apiUrl: string;
  architecture: string;
  authMethod: string;
  latencyMs: number | null;
}

export default function SystemPage() {
  const { status, isOnline, pingServer } = useConnection();
  const [info, setInfo] = useState<PlatformInfo | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  const fetchInfo = useCallback(async () => {
    try {
      let cv = "Web / PWA Client";
      let ct = "Modern Web Browser";
      if (typeof window !== 'undefined' && (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
        try {
          cv = `Tauri v${await getVersion()}`;
          ct = "Tauri Native Desktop Client";
        } catch {
          cv = "Tauri Desktop";
          ct = "Desktop App";
        }
      } else if (typeof window !== 'undefined' && window.matchMedia('(display-mode: standalone)').matches) {
        cv = "PWA Standalone";
        ct = "Mobile / Desktop Installed PWA";
      }

      const url = await getApiUrl();

      let sv = "v2.9.0";
      let se = "Unknown";
      let db = "Unknown";
      let arch = "Server-First Multi-Client";
      let auth = "LOCAL";
      let latency: number | null = null;

      if (isOnline) {
        try {
          const startTime = performance.now();
          const infoRes = await apiFetch("/api/v1/info");
          const endTime = performance.now();
          latency = Math.round(endTime - startTime);

          sv = infoRes.version || sv;
          se = infoRes.environment || se;
          arch = infoRes.architecture || arch;
          auth = infoRes.auth_method || auth;
          db = infoRes.database_connected ? "Connected (Authoritative)" : "Disconnected";
        } catch {
          try {
            const verRes = await apiFetch("/api/v1/version");
            sv = verRes.version || sv;
            se = verRes.environment || se;
            const readyRes = await apiFetch("/api/v1/readiness");
            db = readyRes.status === "ready" ? "Connected" : "Disconnected";
          } catch {
            // fallback
          }
        }
      }

      setInfo({
        serverVersion: sv,
        serverEnv: se,
        clientVersion: cv,
        clientType: ct,
        dbStatus: db,
        apiUrl: url || "(Same origin proxy)",
        architecture: arch,
        authMethod: auth,
        latencyMs: latency,
      });
    } catch (err) {
      console.error("Failed to load platform info:", err);
    }
  }, [isOnline]);

  useEffect(() => {
    fetchInfo();
    const interval = setInterval(fetchInfo, 10000);
    return () => clearInterval(interval);
  }, [fetchInfo]);

  return (
    <Protect capability="system:manage" isPageGuard moduleName="Platform System Telemetry">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground uppercase">
              Platform System Telemetry
            </h1>
            <p className="text-sm font-mono text-muted-foreground mt-0.5">
              Server-First Architecture V1.8 • Centralized Operations & Connectivity Status
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                pingServer();
                fetchInfo();
              }}
              className="text-xs font-mono"
            >
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh Telemetry
            </Button>
            <Button
              size="sm"
              onClick={() => setShowConfigModal(true)}
              className="text-xs font-mono"
            >
              <Server className="size-3.5 mr-1.5" />
              Configure Server Node
            </Button>
          </div>
        </div>

        {/* PRIMARY STATUS METRICS */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Connection Status
              </CardTitle>
              {isOnline ? (
                <Wifi className="size-4 text-emerald-500" />
              ) : (
                <WifiOff className="size-4 text-destructive" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono tracking-tight">{status}</div>
              <p className="text-[11px] text-muted-foreground mt-1 truncate">
                Target: <span className="font-mono text-foreground">{info?.apiUrl || "..."}</span>
              </p>
              {info?.latencyMs !== null && info?.latencyMs !== undefined && (
                <p className="text-[10px] font-mono text-emerald-500 mt-0.5">
                  RTT Latency: {info.latencyMs} ms
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Database Core
              </CardTitle>
              <Database className="size-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono tracking-tight">{info?.dbStatus || "..."}</div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Private isolated persistence layer
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Server Version
              </CardTitle>
              <Server className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono tracking-tight">{info?.serverVersion || "..."}</div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Env: <span className="font-mono text-foreground uppercase">{info?.serverEnv || "..."}</span>
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Active Client Target
              </CardTitle>
              <MonitorSmartphone className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold font-mono tracking-tight truncate">{info?.clientVersion || "..."}</div>
              <p className="text-[11px] text-muted-foreground mt-1 truncate">
                {info?.clientType || "..."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* ARCHITECTURAL TOPOLOGY & MULTI-CLIENT BREAKDOWN */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card className="border-border bg-card shadow-xs">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Cpu className="size-4 text-primary" />
                Authoritative Server Architecture (Ubuntu Core)
              </CardTitle>
              <CardDescription className="text-xs">
                The central Ubuntu Server is the single source of truth for authorization, workflows, and data mutations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded border border-border/70 bg-muted/30 space-y-2">
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="text-muted-foreground">PLATFORM TOPOLOGY</span>
                  <span className="text-emerald-500 font-semibold">{info?.architecture}</span>
                </div>
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="text-muted-foreground">AUTHENTICATION AUTHORITY</span>
                  <span className="text-foreground">{info?.authMethod} / JWT Bearer</span>
                </div>
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="text-muted-foreground">ROLE-BASED ACCESS CONTROL</span>
                  <span className="text-foreground">Scoped AuthzGuard (Server-Enforced)</span>
                </div>
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="text-muted-foreground">DATABASE EXPOSURE</span>
                  <span className="text-emerald-500 font-semibold">Strictly Isolated (No direct client access)</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <ShieldCheck className="size-4 text-emerald-500" />
                Supported Client Ecosystem
              </CardTitle>
              <CardDescription className="text-xs">
                Unified cross-platform operations supporting desktop, web browser, and mobile field workers.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="space-y-2">
                <div className="flex items-start gap-2.5 p-2 rounded bg-muted/20 border border-border/50">
                  <Terminal className="size-4 text-primary shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-foreground">Tauri Desktop Client</div>
                    <div className="text-[11px] text-muted-foreground">Native execution on Windows, Linux, and macOS with local SQLite buffer.</div>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-2 rounded bg-muted/20 border border-border/50">
                  <Globe className="size-4 text-blue-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-foreground">Web Browser Client</div>
                    <div className="text-[11px] text-muted-foreground">Zero-install console access via Chrome, Edge, Firefox, and Safari over HTTPS.</div>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-2 rounded bg-muted/20 border border-border/50">
                  <Smartphone className="size-4 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-foreground">Mobile Web / PWA Client</div>
                    <div className="text-[11px] text-muted-foreground">Standalone installable on Android and iOS devices for field operators with offline queueing.</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <ServerConfigDialog
          isOpen={showConfigModal}
          onClose={() => setShowConfigModal(false)}
          onConfigured={() => {
            setShowConfigModal(false);
            fetchInfo();
          }}
        />
      </div>
    </Protect>
  );
}
