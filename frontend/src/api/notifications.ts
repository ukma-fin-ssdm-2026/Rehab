import { apiRequest } from './client';
import { getMessageVariation } from '../messages/rotation';

export type Contact = { nickname: string; email: string };
export type SupportComment = {
  support_comment_id: number; relationship_id: number; relapse_notification_id: number;
  author: Contact; text: string; created_at: string;
};
export type Notification = {
  notification_id: number; kind: 'daily_reminder' | 'relapse' | 'support_comment';
  created_at: string; read_at: string | null; business_date: string;
  relationship_id: number | null; record_id: number | null; sender: Contact | null;
  title: string; body: string; support_comment: SupportComment | null;
  can_support: boolean; can_view_mentee: boolean; can_report_mentor: boolean;
};
export type NotificationPage = { items: Notification[]; total: number; limit: number; offset: number };
export const listNotifications = (limit = 30, offset = 0): Promise<NotificationPage> =>
  apiRequest(`/notifications?limit=${limit}&offset=${offset}&variant=${getMessageVariation()}`);
export const getUnreadCount = (): Promise<{count: number}> => apiRequest('/notifications/unread-count');
export const getNotification = (id: number): Promise<Notification> => apiRequest(`/notifications/${id}?variant=${getMessageVariation()}`);
export const markNotificationRead = (id: number): Promise<Notification> => apiRequest(`/notifications/${id}/read?variant=${getMessageVariation()}`, {method: 'PATCH'});
export async function sendSupport(id: number, text: string): Promise<SupportComment> {
  const trimmed = text.trim();
  if (!trimmed || [...trimmed].length > 2000) throw new Error('Введіть від 1 до 2000 символів');
  return apiRequest(`/notifications/${id}/support`, {method:'POST', body: JSON.stringify({text:trimmed})});
}
