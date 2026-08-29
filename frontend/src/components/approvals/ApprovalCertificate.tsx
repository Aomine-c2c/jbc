import React from 'react';
import { ShieldCheck, CheckCircle2, Clock, MapPin, Printer } from 'lucide-react';
import { ApprovalRequestData } from '@/lib/approvals';
import { Button } from '@/components/ui/button';

interface ApprovalCertificateProps {
  request: ApprovalRequestData;
}

export function ApprovalCertificate({ request }: ApprovalCertificateProps) {
  const isApproved = request.status === 'APPROVED';

  return (
    <div className="border border-border/80 rounded bg-card p-6 space-y-6 print:border-none print:shadow-none print:p-0">
      <div className="flex items-start justify-between border-b border-border/50 pb-4">
        <div>
          <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
            <ShieldCheck className="size-5 text-primary" />
            Digital Approval Certificate
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Reference: {request.resource_type.toUpperCase()} / {request.resource_id.split('-')[0]}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="print:hidden"
          onClick={() => window.print()}
        >
          <Printer className="size-4 mr-2" />
          Print Record
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm bg-muted/20 p-4 rounded border border-border/40">
        <div>
          <span className="text-muted-foreground block text-xs">Workflow Type</span>
          <span className="font-mono">{request.workflow_type}</span>
        </div>
        <div>
          <span className="text-muted-foreground block text-xs">Risk Level</span>
          <span className="font-mono">{request.risk_level}</span>
        </div>
        <div>
          <span className="text-muted-foreground block text-xs">Final Status</span>
          <span className="font-bold flex items-center gap-1.5 mt-0.5">
            {isApproved ? <CheckCircle2 className="size-4 text-emerald-500" /> : <Clock className="size-4 text-amber-500" />}
            {request.status}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground block text-xs">Resolution Date</span>
          <span className="font-mono">{request.resolved_at ? new Date(request.resolved_at).toLocaleString() : 'Pending'}</span>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-1">
          Cryptographic Sign-off History
        </h3>
        <div className="space-y-3">
          {request.steps.map((step) => (
            <div key={step.id} className="border border-border/60 rounded p-3 bg-muted/10">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="font-bold text-sm text-foreground">{step.authority_role}</span>
                  <span className="text-xs text-muted-foreground block mt-0.5">
                    {step.approver_name || 'Unassigned'} ({step.approver_role_name || step.required_permission})
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-muted">
                    {step.status}
                  </span>
                  <span className="block text-[10px] text-muted-foreground mt-1">
                    {step.timestamp ? new Date(step.timestamp).toLocaleString() : ''}
                  </span>
                </div>
              </div>
              
              {step.comment && (
                <div className="text-xs text-foreground bg-background border border-border/40 p-2 rounded mb-2">
                  <span className="text-muted-foreground font-semibold">Note:</span> {step.comment}
                </div>
              )}

              {step.signature_token && (
                <div className="text-[10px] font-mono text-muted-foreground border-t border-dashed border-border/40 pt-2 flex flex-col gap-1">
                  <div className="flex items-center gap-1">
                    <ShieldCheck className="size-3 text-primary/60" />
                    HMAC Signature Token:
                  </div>
                  <span className="break-all text-primary/80">{step.signature_token}</span>
                  {(step as { ip_address?: string }).ip_address && (
                    <div className="flex items-center gap-1">
                      <MapPin className="size-3 text-muted-foreground/60" />
                      IP: {(step as { ip_address?: string }).ip_address}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div className="text-center pt-6 border-t border-border/50 text-[10px] text-muted-foreground">
        <p>This certificate represents a cryptographically verifiable record of digital authorization.</p>
        <p>Generated by Bikita Minerals DWRMS • {new Date().toISOString()}</p>
      </div>
    </div>
  );
}
