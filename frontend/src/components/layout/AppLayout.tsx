'use client';

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Shield, LogOut, Cloud, ShieldAlert, X } from "lucide-react";
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
import { RoleSwitcher } from "./RoleSwitcher";
import { AccessRestricted } from "./AccessRestricted";

import { resolveUserRole, isRouteAllowed, getDefaultLandingRoute } from "@/lib/rbac";

interface UserProfile {
  name: string;
  role: string;
  initials: string;
}

const DEFAULT_PROFILE: UserProfile = {
  name: "Mine Operations",
  role: "Operator Level",
  initials: "OP",
};

function getUserProfile(): UserProfile {
  if (typeof window === "undefined") {
    return DEFAULT_PROFILE;
  }
  try {
    const email = localStorage.getItem("user_email") || "";
    const savedRole = localStorage.getItem("user_role");
    const role = resolveUserRole(savedRole || email);

    if (role === "Administrator") {
      return { name: "System Admin", role: "System Administrator", initials: "AD" };
    } else if (role === "Department Manager") {
      return { name: "Dept Superintendent", role: "Dept Manager / Superintendent", initials: "DM" };
    } else if (role === "Supervisor") {
      return { name: "Shift Supervisor", role: "Supervisor / Shift Boss", initials: "SV" };
    } else if (role === "Technician") {
      return { name: "Lead Artisan", role: "Technician / Artisan", initials: "TC" };
    } else if (role === "Safety Officer") {
      return { name: "HSE Officer", role: "Safety Officer (HSE)", initials: "SO" };
    } else if (role === "Operator") {
      return { name: "Equipment Operator", role: "Operator / Driver", initials: "OP" };
    }
  } catch {
    // fallback
  }
  return DEFAULT_PROFILE;
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [timeStr, setTimeStr] = useState<string>("");
  const [userInfo, setUserInfo] = useState<UserProfile>(DEFAULT_PROFILE);
  const [isConfigured, setIsConfigured] = useState(true);
  const [showSyncPanel, setShowSyncPanel] = useState(false);
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [showMobileDrawer, setShowMobileDrawer] = useState(false);
  const { isOnline } = useConnection();
  const isAuthPage = pathname === "/login" || pathname?.startsWith("/login");
  const isSetupPage = pathname === "/setup" || pathname?.startsWith("/setup");

  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);

  useSyncManager(); // Mount sync manager globally
  useLiveEvents({ enabled: !isAuthPage && !isSetupPage }); // Mount real-time SSE stream globally conditionally

  useEffect(() => {
    const syncRole = () => {
      setUserInfo(getUserProfile());
      if (typeof window !== 'undefined') {
        const email = localStorage.getItem("user_email");
        const role = localStorage.getItem("user_role");
        setCurrentUserRole(role || email);
      }
    };
    syncRole();

    window.addEventListener('role-changed', syncRole);
    return () => window.removeEventListener('role-changed', syncRole);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
      if (!localStorage.getItem('dwrms_active_profile_id')) {
        setIsConfigured(false);
      }
    }

    // Client-side auth fallback (useful for Tauri/PWA when middleware might be bypassed)
    if (!isAuthPage && !isSetupPage) {
      const email = localStorage.getItem("user_email");
      const hasCookie = document.cookie.includes("dwrms_access_token");
      if (!email && !hasCookie) {
        router.push("/login");
      }
    }

    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + " CAT");
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, [pathname, isAuthPage, isSetupPage, router]);

  const [restrictedNotice, setRestrictedNotice] = useState<string | null>(null);

  // Enforce zero-visibility URL navigation: automatically redirect unauthorized hits to permitted home hub
  useEffect(() => {
    if (!pathname || isAuthPage || isSetupPage || !currentUserRole) return;
    if (!isRouteAllowed(currentUserRole, pathname)) {
      const target = getDefaultLandingRoute(currentUserRole);
      setRestrictedNotice(`Access restricted: Your role does not have permission to access ${pathname}. Redirected to your primary hub.`);
      router.replace(target);
      const timer = setTimeout(() => setRestrictedNotice(null), 7000);
      return () => clearTimeout(timer);
    }
  }, [pathname, currentUserRole, isAuthPage, isSetupPage, router]);

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
    <div className="flex h-screen overflow-hidden bg-zinc-50 text-zinc-900 font-sans antialiased">
      <Sidebar onOpenServerConfig={() => setShowServerConfig(true)} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="h-14 bg-white border-b border-zinc-200 flex items-center px-4 md:px-6 justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full size-2 bg-emerald-500"></span>
              </span>
              <span className="font-bold text-xs uppercase tracking-wider text-zinc-900 truncate max-w-[140px] sm:max-w-none">
                Bikita Operations Console
              </span>
            </div>

            <ConnectionStatusBadge />
          </div>

          <div className="flex items-center space-x-2 sm:space-x-3">
            {timeStr && (
              <div
                suppressHydrationWarning
                className="hidden lg:block text-[11px] font-mono text-zinc-600 px-2.5 py-1 bg-zinc-100 rounded-md border border-zinc-200"
              >
                {timeStr}
              </div>
            )}

            <div className="relative">
              <button
                onClick={() => setShowSyncPanel(!showSyncPanel)}
                className={`relative p-2 rounded-md hover:bg-zinc-100 transition-colors ${!isOnline ? 'text-rose-600' : 'text-zinc-500 hover:text-zinc-900'}`}
              >
                <Cloud className="size-4" />
                {!isOnline && (
                  <span className="absolute top-1.5 right-1.5 size-2 bg-rose-500 rounded-full border border-white animate-pulse" />
                )}
              </button>
              {showSyncPanel && <SyncStatusPanel />}
            </div>

            <RoleSwitcher />
            <NotificationCenter />
            <ThemeToggle />

            <div className="flex items-center gap-2 pl-2 border-l border-zinc-200">
              <div
                suppressHydrationWarning
                className="size-8 rounded-full border border-zinc-200 bg-zinc-100 flex items-center justify-center font-bold text-xs text-zinc-800 font-mono"
              >
                {userInfo.initials}
              </div>
              <div className="hidden lg:block text-left">
                <div
                  suppressHydrationWarning
                  className="text-xs font-semibold leading-none text-zinc-900 flex items-center gap-1"
                >
                  <span>{userInfo.name}</span>
                  <Shield className="size-3 text-zinc-700" />
                </div>
                <div
                  suppressHydrationWarning
                  className="text-[10px] text-zinc-500 font-mono mt-0.5"
                >
                  {userInfo.role}
                </div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                title="Log out of system"
                className="ml-1 p-1.5 rounded-md hover:bg-rose-50 hover:text-rose-600 text-zinc-400 transition-colors cursor-pointer"
                aria-label="Logout"
              >
                <LogOut className="size-4" />
              </button>
            </div>
          </div>
        </header>
        {restrictedNotice && (
          <div className="fixed top-16 right-6 z-50 max-w-md p-3.5 bg-amber-500/15 border border-amber-500/30 text-amber-800 dark:text-amber-300 rounded-lg shadow-xl backdrop-blur-md flex items-start gap-2.5 text-xs animate-in fade-in slide-in-from-top-2">
            <ShieldAlert className="size-4 shrink-0 text-amber-600 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">{restrictedNotice}</div>
            <button onClick={() => setRestrictedNotice(null)} className="text-amber-600 hover:text-amber-800 dark:hover:text-amber-200">
              <X className="size-3.5" />
            </button>
          </div>
        )}

        {/* Main Content Area — with bottom padding on mobile for MobileBottomNav */}
        <main className="flex-1 overflow-auto bg-background/50 pb-16 md:pb-0">
          {!pathname || isRouteAllowed(currentUserRole, pathname) ? (
            children
          ) : (
            <div className="p-12 flex flex-col items-center justify-center min-h-[50vh] text-center space-y-2">
              <ShieldAlert className="size-8 text-amber-500 animate-pulse" />
              <div className="text-xs font-semibold text-foreground">Zero-Visibility Redirection</div>
              <div className="text-[11px] text-muted-foreground">Transferring you to your authorized operations hub...</div>
            </div>
          )}
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
