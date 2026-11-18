import { ApiError, apiRequest } from './client';
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
// AI-GENERATED START
// Як R3 у Лаб 9: apiRequest лише приводить JSON до типу, тому відповіді для списку
// повідомлень і лічильника перевіряються тут. Некоректна структура дає контрольовану
// помилку з людським текстом замість TypeError у loadInboxPages або undefined у бейджі.
const KINDS: readonly unknown[] = ['daily_reminder', 'relapse', 'support_comment'];
const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
const isCount = (value: unknown) => Number.isInteger(value) && (value as number) >= 0;
const isOptionalId = (value: unknown) => value === null || Number.isInteger(value);

export function isNotification(value: unknown): value is Notification {
  return isObject(value) && Number.isInteger(value.notification_id) && KINDS.includes(value.kind)
    && typeof value.title === 'string' && typeof value.body === 'string'
    && typeof value.created_at === 'string' && (value.read_at === null || typeof value.read_at === 'string')
    && isOptionalId(value.relationship_id) && isOptionalId(value.record_id)
    && (value.sender === null || isObject(value.sender))
    && (value.support_comment === null || isObject(value.support_comment));
}

export function isNotificationPage(value: unknown): value is NotificationPage {
  return isObject(value) && Array.isArray(value.items) && value.items.every(isNotification)
    && isCount(value.total) && isCount(value.limit) && isCount(value.offset);
}

function invalidMessagesResponse(): ApiError {
  console.warn('Notifications API returned an unexpected response shape');
  return new ApiError(200, 'INVALID_RESPONSE', 'Сервер повернув некоректні дані повідомлень. Спробуй пізніше.');
}

export async function listNotifications(limit = 30, offset = 0): Promise<NotificationPage> {
  const page: unknown = await apiRequest(`/notifications?limit=${limit}&offset=${offset}&variant=${getMessageVariation()}`);
  if (!isNotificationPage(page)) throw invalidMessagesResponse();
  return page;
}

export async function getUnreadCount(): Promise<{count: number}> {
  const result: unknown = await apiRequest('/notifications/unread-count');
  if (!isObject(result) || !isCount(result.count)) throw invalidMessagesResponse();
  return { count: result.count as number };
}
// AI-GENERATED END
export const getNotification = (id: number): Promise<Notification> => apiRequest(`/notifications/${id}?variant=${getMessageVariation()}`);
export const markNotificationRead = (id: number): Promise<Notification> => apiRequest(`/notifications/${id}/read?variant=${getMessageVariation()}`, {method: 'PATCH'});
export async function sendSupport(id: number, text: string): Promise<SupportComment> {
  const trimmed = text.trim();
  if (!trimmed || [...trimmed].length > 2000) throw new Error('Введіть від 1 до 2000 символів');
  return apiRequest(`/notifications/${id}/support`, {method:'POST', body: JSON.stringify({text:trimmed})});
}
