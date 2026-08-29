'use client'

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface ProtectProps {
  capability?: string | string[];
  children: React.ReactNode;
}

export function Protect({ capability, children }: ProtectProps) {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        const res = await apiFetch("/api/v1/iam/auth/me/permissions");
        if (Array.isArray(res)) {
          setPermissions(res);
        } else if (res && Array.isArray(res.data)) {
          setPermissions(res.data);
        }
      } catch (e) {
        console.error("Failed to fetch permissions", e);
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

  const required = Array.isArray(capability) ? capability : [capability];
  const hasPermission =
    permissions.includes("global_override") ||
    required.some((req) => permissions.includes(req));

  if (!hasPermission) return null;

  return <>{children}</>;
}
