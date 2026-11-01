// AI-GENERATED START
import { apiRequest } from './client';

export type ComplaintOut = {
  complaint_id: number;
  relationship_id: number;
  reason: string;
  support_comment_id: number | null;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at: string | null;
};

export type ComplaintEvidence = {
  support_comment_id: number;
  text: string;
  created_at: string;
};

export const COMPLAINT_REASON_MAX = 2000;

export const submitComplaint = (body: {
  relationship_id: number;
  reason: string;
  support_comment_id?: number;
}) => apiRequest<ComplaintOut>('/complaints', { method: 'POST', body: JSON.stringify(body) });

// Доказ береться з власного повідомлення підопічного (API Марії), не за ID коментаря.
export async function fetchEvidence(notificationId: number): Promise<ComplaintEvidence | null> {
  const notification = await apiRequest<{ support_comment: ComplaintEvidence | null }>(
    `/notifications/${notificationId}`,
  );
  return notification.support_comment;
}
// AI-GENERATED END
