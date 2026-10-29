// AI-GENERATED START
import { apiRequest } from './client';

export type AdminUser = {
  user_id: number;
  name: string;
  nickname: string;
  email: string;
  role: 'user' | 'mentor' | 'admin';
  is_blocked: boolean;
};

export type AdminUserList = {
  items: AdminUser[];
  total: number;
  limit: number;
  offset: number;
};

export type TriggerCategory = 'stress' | 'holiday' | 'social' | 'other';

export type TriggerDistribution = {
  period_start: string;
  period_end: string;
  total: number;
  categories: { category: TriggerCategory; count: number; percentage: number }[];
};

export const fetchAdminUsers = (limit = 50, offset = 0) =>
  apiRequest<AdminUserList>(`/admin/users?limit=${limit}&offset=${offset}`);

export const setUserBlocked = (userId: number, isBlocked: boolean) =>
  apiRequest<AdminUser>(`/admin/users/${userId}/block`, {
    method: 'PATCH',
    body: JSON.stringify({ is_blocked: isBlocked }),
  });

export const fetchTriggerDistribution = () =>
  apiRequest<TriggerDistribution>('/admin/trigger-distribution');
// AI-GENERATED END
