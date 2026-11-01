// AI-GENERATED START
import { apiRequest } from './client';

export type ComplaintStatus = 'pending' | 'approved' | 'rejected';
export type ComplaintFilter = ComplaintStatus | 'all';

export type ComplaintParty = { nickname: string; email: string };

export type AdminComplaint = {
  complaint_id: number;
  relationship_id: number;
  reason: string;
  support_comment_id: number | null;
  status: ComplaintStatus;
  created_at: string;
  reviewed_at: string | null;
  reporter: ComplaintParty;
  reported: ComplaintParty;
  evidence: { text: string; created_at: string | null } | null;
};

export type AdminComplaintList = {
  items: AdminComplaint[];
  total: number;
  limit: number;
  offset: number;
};

export type AdminOverview = {
  registrations_last_30_days: number;
  active_mentors: number;
  active_relationships: number;
  pending_complaints: number;
  current_date: string;
};

export type TriggerCategory = 'stress' | 'holiday' | 'social' | 'other';

export type TriggerDistribution = {
  period_start: string;
  period_end: string;
  total: number;
  categories: { category: TriggerCategory; count: number; percentage: number }[];
};

export const COMPLAINT_PAGE = 30;

export const fetchComplaints = (status: ComplaintFilter, offset = 0) =>
  apiRequest<AdminComplaintList>(
    `/admin/complaints?status=${status}&limit=${COMPLAINT_PAGE}&offset=${offset}`,
  );

export const fetchComplaint = (complaintId: number) =>
  apiRequest<AdminComplaint>(`/admin/complaints/${complaintId}`);

export const decideComplaint = (complaintId: number, decision: 'approved' | 'rejected') =>
  apiRequest<Omit<AdminComplaint, 'reporter' | 'reported' | 'evidence'>>(
    `/admin/complaints/${complaintId}`,
    { method: 'PATCH', body: JSON.stringify({ decision }) },
  );

export const fetchOverview = () => apiRequest<AdminOverview>('/admin/overview');

export const fetchTriggerDistribution = () =>
  apiRequest<TriggerDistribution>('/admin/trigger-distribution');
// AI-GENERATED END
