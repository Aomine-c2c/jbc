'use client';

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getDefaultLandingRoute, resolveUserRole } from "@/lib/rbac";
import { TelemetrySpinner } from "@/components/ui/loading-state";

export default function RootRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    let email: string | null = null;
    let role: string | null = null;
    if (typeof window !== 'undefined') {
      email = localStorage.getItem('user_email');
      role = localStorage.getItem('user_role');
    }

    const targetRoute = getDefaultLandingRoute(role || email);
    router.replace(targetRoute);
  }, [router]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-8">
      <TelemetrySpinner message="Routing to authorized operational workspace..." />
    </div>
  );
}
