import React from "react";
import { AuditLogViewer } from "@/components/audit/audit-log-viewer";
import { Protect } from "@/components/auth/Protect";

export const metadata = {
  title: "Audit Logs - Bikita DWRMS",
};

export default function AuditPage() {
  return (
    <Protect capability="audit:view" isPageGuard moduleName="Audit Logs & Compliance">
      <div className="h-full flex flex-col">
        <div className="p-6 border-b border-border shrink-0">
          <h1 className="text-2xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground mt-1">
            Immutable system audit trail for enterprise accountability.
          </p>
        </div>
        <div className="flex-1 p-6 overflow-hidden">
          <AuditLogViewer />
        </div>
      </div>
    </Protect>
  );
}
