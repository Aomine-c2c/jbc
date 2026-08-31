import { apiFetch } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface JobReportProgressUpdate {
  id: string;
  update_type: "WORK_START" | "PROGRESS" | "PAUSE" | "RESUME" | "COMPLETION";
  timestamp: string;
  percentage_complete: number;
  notes?: string;
  hold_reason?: string;
  reported_by_id: string;
}

export interface JobReportMaterial {
  id: string;
  category: "SPARE_PART" | "CONSUMABLE" | "MATERIAL" | "TOOL" | "EQUIPMENT" | "OTHER";
  item_name: string;
  item_code?: string;
  quantity: number;
  unit?: string;
  unit_cost?: number;
  notes?: string;
}

export interface JobReportAttachment {
  id: string;
  category: "PHOTO" | "DOCUMENT" | "SKETCH" | "CERTIFICATE" | "MEASUREMENT_SHEET" | "OTHER";
  filename: string;
  file_url?: string;
  file_type?: string;
  file_size_kb: number;
  caption?: string;
  uploaded_by_id: string;
  uploaded_at: string;
}

export interface JobReportAmendment {
  id: string;
  field_name: string;
  old_value?: string;
  new_value?: string;
  amendment_reason: string;
  approval_status: "PENDING" | "APPROVED" | "REJECTED";
  amended_by_id: string;
  approved_by_id?: string;
  created_at: string;
  approved_at?: string;
}

export interface DeptFieldMeta {
  name: string;
  label: string;
  description: string;
  type: string;
}

export interface JobReport {
  id: string;
  job_card_id: string;
  is_locked: boolean;
  locked_at?: string;
  locked_by_id?: string;
  fault_found?: string;
  fault_code?: string;
  corrective_action?: string;
  technical_notes?: string;
  observations?: string;
  recommendations?: string;
  follow_up_required: boolean;
  follow_up_notes?: string;
  actual_labour_hours: number;
  actual_cost: number;
  dept_schema_type: string;
  dept_specific_data?: Record<string, unknown>;
  progress_updates: JobReportProgressUpdate[];
  materials: JobReportMaterial[];
  attachments: JobReportAttachment[];
  amendments: JobReportAmendment[];
  created_at: string;
  updated_at: string;
}

// ── API Calls ──────────────────────────────────────────────────────────────

export async function getJobReport(jobId: string): Promise<JobReport | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report`);
}

export async function updateJobReport(
  jobId: string,
  data: Partial<Pick<JobReport,
    "fault_found" | "fault_code" | "corrective_action" | "technical_notes" |
    "observations" | "recommendations" | "follow_up_required" | "follow_up_notes" |
    "actual_labour_hours" | "actual_cost" | "dept_schema_type" | "dept_specific_data"
  >>
): Promise<JobReport | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function addProgressUpdate(
  jobId: string,
  data: { update_type: string; notes?: string; hold_reason?: string; percentage_complete: number }
): Promise<JobReportProgressUpdate | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report/progress`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function addMaterial(
  jobId: string,
  data: Omit<JobReportMaterial, "id">
): Promise<JobReportMaterial | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report/materials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteMaterial(jobId: string, materialId: string): Promise<void> {
  await apiFetch(`/api/v1/job-cards/${jobId}/report/materials/${materialId}`, {
    method: "DELETE",
  });
}

export async function addAttachment(
  jobId: string,
  data: Omit<JobReportAttachment, "id" | "uploaded_by_id" | "uploaded_at">
): Promise<JobReportAttachment | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report/attachments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function createAmendment(
  jobId: string,
  data: { field_name: string; new_value: string; amendment_reason: string }
): Promise<JobReportAmendment | null> {
  return apiFetch(`/api/v1/job-cards/${jobId}/report/amend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getDeptSchema(deptSchemaType: string): Promise<DeptFieldMeta[]> {
  const res = await apiFetch(`/api/v1/job-cards/report/dept-schema/${deptSchemaType}`);
  return res?.fields ?? [];
}
