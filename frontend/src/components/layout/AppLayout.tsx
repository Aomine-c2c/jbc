'use client';

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Shield, LogOut, Cloud } from "lucide-react";
import { logout } from "@/lib/auth";
import { NotificationCenter } from "@/components/notifications/NotificationCenter";
import { SyncStatusPanel } from "@/components/notifications/SyncStatusPanel";
import { useConnection } from "@/lib/providers/ConnectionProvider";
import { useSyncManager } from "@/lib/SyncManager";
import { useLiveEvents } from "@/lib/useLiveEvents";
import { ConnectionStatusBadge } from "./ConnectionStatusBadge";
import { NetworkStatusBar } from "./NetworkStatusBar";
import { MobileBottomNav } from "./MobileBottomNav";
import { MobileNavDrawer } from "./MobileNavDrawer";
import { ServerConfigDialog } from "@/components/config/ServerConfigDialog";

interface UserProfile {
  name: string;
  role: string;
  initials: string;
}

const DEFAULT_PROFILE: UserProfile = {
  name: "Maint Ops",
  role: "Operations Role",
  initials: "BK",
};

function getUserProfile(): UserProfile {
  if (typeof window === "undefined") {
    return DEFAULT_PROFILE;
  }
  try {
    const email = localStorage.getItem("user_email");
    if (email === "admin@bikita.com") {
      return { name: "Admin User", role: "System Admin", initials: "AD" };
    } else if (email === "supervisor@bikita.com") {
      return { name: "Super Visor", role: "Supervisor Level", initials: "SV" };
    } else if (email === "tech@bikita.com") {
      return { name: "Tech User", role: "Technician Level", initials: "TC" };
    }
  } catch {
    // fallback
  }
  return DEFAULT_PROFILE;
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [timeStr, setTimeStr] = useState<string>("");
  const [userInfo, setUserInfo] = useState<UserProfile>(DEFAULT_PROFILE);
  const [isConfigured, setIsConfigured] = useState(true);
  const [showSyncPanel, setShowSyncPanel] = useState(false);
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [showMobileDrawer, setShowMobileDrawer] = useState(false);
  const { isOnline } = useConnection();
  const isAuthPage = pathname === "/login" || pathname?.startsWith("/login");
  const isSetupPage = pathname === "/setup" || pathname?.startsWith("/setup");

  useSyncManager(); // Mount sync manager globally
  useLiveEvents({ enabled: !isAuthPage && !isSetupPage }); // Mount real-time SSE stream globally conditionally

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).__TAURI_INTERNALS__) {
      if (!localStorage.getItem('dwrms_active_profile_id')) {
        setIsConfigured(false);
      }
    }

    // Client-side auth fallback (useful for Tauri/PWA when middleware might be bypassed)
    if (!isAuthPage && !isSetupPage) {
      const email = localStorage.getItem("user_email");
      const hasCookie = document.cookie.includes("dwrms_access_token");
      if (!email && !hasCookie) {
        window.location.href = "/login";
      }
    }

    setUserInfo(getUserProfile());

    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + " CAT");
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, [pathname, isAuthPage, isSetupPage]);

  if (!isConfigured) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans antialiased">
        <ServerConfigDialog onConfigured={() => setIsConfigured(true)} />
      </div>
    );
  }

  // Auth or Setup pages render full-screen without operations sidebar/header
  if (isAuthPage || isSetupPage) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans antialiased">
        {children}
        <ServerConfigDialog
          isOpen={showServerConfig}
          onClose={() => setShowServerConfig(false)}
        />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground font-sans antialiased">
      <Sidebar onOpenServerConfig={() => setShowServerConfig(true)} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="h-14 bg-card border-b border-border flex items-center px-4 md:px-6 justify-between shrink-0 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full size-2 bg-emerald-500"></span>
              </span>
              <span className="font-bold text-xs uppercase tracking-wider text-foreground truncate max-w-[140px] sm:max-w-none">
                Bikita Operations Console
              </span>
            </div>

            <ConnectionStatusBadge />
          </div>

          <div className="flex items-center space-x-2 sm:space-x-3">
            {timeStr && (
              <div
                suppressHydrationWarning
                className="hidden lg:block text-[11px] font-mono text-muted-foreground px-2 py-0.5 bg-muted/50 rounded border border-border/40"
              >
                {timeStr}
              </div>
            )}

            <div className="relative">
              <button
                onClick={() => setShowSyncPanel(!showSyncPanel)}
                className={`relative p-2 rounded-md hover:bg-muted transition-colors ${!isOnline ? 'text-destructive' : 'text-muted-foreground'}`}
              >
                <Cloud className="size-5" />
                {!isOnline && (
                  <span className="absolute top-1.5 right-1.5 size-2 bg-destructive rounded-full border border-card animate-pulse" />
                )}
              </button>
              {showSyncPanel && <SyncStatusPanel />}
            </div>

            <NotificationCenter />
            <ThemeToggle />

            <div className="flex items-center gap-2 pl-2 border-l border-border">
              <div
                suppressHydrationWarning
                className="w-7 h-7 rounded border border-border bg-muted flex items-center justify-center font-bold text-xs text-foreground font-mono"
              >
                {userInfo.initials}
              </div>
              <div className="hidden lg:block text-left">
                <div
                  suppressHydrationWarning
                  className="text-xs font-semibold leading-none text-foreground flex items-center gap-1"
                >
                  <span>{userInfo.name}</span>
                  <Shield className="size-3 text-primary" />
                </div>
                <div
                  suppressHydrationWarning
                  className="text-[10px] text-muted-foreground font-mono mt-0.5"
                >
                  {userInfo.role}
                </div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                title="Log out of system"
                className="ml-1 p-1.5 rounded hover:bg-destructive/10 hover:text-destructive text-muted-foreground transition-colors cursor-pointer"
                aria-label="Logout"
              >
                <LogOut className="size-3.5" />
              </button>
            </div>
          </div>
        </header>
        <NetworkStatusBar />

        {/* Main Content Area — with bottom padding on mobile for MobileBottomNav */}
        <main className="flex-1 overflow-auto bg-background/50 pb-16 md:pb-0">
          {children}
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar (< md screens) */}
      <MobileBottomNav onOpenDrawer={() => setShowMobileDrawer(true)} />

      {/* Mobile Sliding Navigation Drawer */}
      <MobileNavDrawer
        isOpen={showMobileDrawer}
        onClose={() => setShowMobileDrawer(false)}
        onOpenServerConfig={() => setShowServerConfig(true)}
        userInfo={userInfo}
      />

      <ServerConfigDialog
        isOpen={showServerConfig}
        onClose={() => setShowServerConfig(false)}
      />
    </div>
  );
}
