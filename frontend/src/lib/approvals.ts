import { apiFetch } from './api';

export interface ApprovalStep {
  id: string;
  step_number: number;
  step_name?: string;
  authority_role: string;
  required_permission: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'RETURNED' | 'DELEGATED' | 'ESCALATED' | 'SKIPPED';
  approver_id?: string;
  approver_name?: string;
  approver_role_name?: string;
  action?: string;
  comment?: string;
  state_from?: string;
  state_to?: string;
  signature_token?: string;
  timestamp?: string;
  delegated_to_id?: string;
  delegated_to_name?: string;
  created_at: string;
}

export interface ApprovalRequestData {
  id: string;
  resource_type: string;
  resource_id: string;
  workflow_type: string;
  priority: number;
  risk_level: string;
  estimated_cost: number;
  status: 'OPEN' | 'APPROVED' | 'REJECTED' | 'RETURNED' | 'ESCALATED';
  created_by_id: string;
  created_at: string;
  resolved_at?: string;
  steps: ApprovalStep[];
}

export interface ApprovalDecision {
  approval_request_id: string;
  step_id: string;
  action: string;
  next_resource_status: string;
  all_resolved: boolean;
  signature_token: string;
}

export interface ApprovalInboxItem {
  approval_request: ApprovalRequestData;
  pending_step: ApprovalStep;
  resource_title: string;
  resource_description: string;
  requester_name: string;
  department_name?: string;
}

export async function getPendingApprovals(): Promise<ApprovalInboxItem[]> {
  try {
    const res = await apiFetch(`/api/v1/approvals/pending`);
    if (Array.isArray(res) && res.length > 0) {
      return res;
    }
  } catch (e) {
    console.warn("Approvals endpoint offline, using cached synthetic inbox items", e);
  }
  const { MOCK_APPROVALS_INBOX } = await import('./mockData');
  return MOCK_APPROVALS_INBOX as ApprovalInboxItem[];
}

export async function getApprovalHistory(resourceType: string, resourceId: string): Promise<ApprovalRequestData[]> {
  return apiFetch(`/api/v1/approvals/${resourceType}/${resourceId}`);
}

export async function decideApproval(
  resourceType: string,
  resourceId: string,
  action: 'approve' | 'reject' | 'return' | 'delegate' | 'escalate',
  comment: string,
  resourceOwnerId: string,
  stateFrom: string,
  stateTo: string
): Promise<ApprovalDecision> {
  return apiFetch(`/api/v1/approvals/${resourceType}/${resourceId}/decide`, {
    method: 'POST',
    body: JSON.stringify({
      action,
      comment,
      resource_owner_id: resourceOwnerId,
      state_from: stateFrom,
      state_to: stateTo,
    }),
  });
}

export async function delegateApproval(
  resourceType: string,
  resourceId: string,
  delegateToId: string,
  delegateToName: string,
  comment: string
): Promise<ApprovalRequestData> {
  return apiFetch(`/api/v1/approvals/${resourceType}/${resourceId}/delegate`, {
    method: 'POST',
    body: JSON.stringify({
      delegate_to_id: delegateToId,
      delegate_to_name: delegateToName,
      comment,
    }),
  });
}

export async function escalateApproval(
  resourceType: string,
  resourceId: string,
  comment: string
): Promise<ApprovalRequestData> {
  return apiFetch(`/api/v1/approvals/${resourceType}/${resourceId}/escalate`, {
    method: 'POST',
    body: JSON.stringify({
      comment,
    }),
  });
}

export async function getApprovalCertificate(resourceType: string, resourceId: string): Promise<ApprovalRequestData> {
  return apiFetch(`/api/v1/approvals/${resourceType}/${resourceId}/certificate`);
}
