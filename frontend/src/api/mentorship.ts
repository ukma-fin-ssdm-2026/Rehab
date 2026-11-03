import type { CalendarEntry, EntryPage } from './calendar';
import { apiRequest } from './client';
import type { Statistics, StatisticsPeriod } from './statistics';

export type RelationshipContact = { user_id: number; nickname: string; email: string };
export type Relationship = {
  relationship_id: number; status: 'active' | 'ended';
  mentor: RelationshipContact; mentee: RelationshipContact;
  created_at: string; ended_at: string | null;
  ended_reason: 'mentor_left' | 'mentee_left' | 'complaint' | null;
};
export type RelationshipPage = { items: Relationship[]; total: number; limit: number; offset: number };
export type MenteeStatistics = Statistics & { tracking_start_date: string; period: StatisticsPeriod };

function relationshipPath(id: number): string {
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error('Некоректний ідентифікатор менторства.');
  return `/mentorships/${id}`;
}

export async function getMyMentorCode(signal?: AbortSignal): Promise<{ code: string }> {
  return apiRequest('/mentorships/code', { signal });
}
export async function getMyMentor(signal?: AbortSignal): Promise<{ item: Relationship | null }> {
  return apiRequest('/mentorships/my-mentor', { signal });
}
export async function getMyMentees(limit = 30, offset = 0, signal?: AbortSignal): Promise<RelationshipPage> {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100 || !Number.isInteger(offset) || offset < 0) {
    throw new Error('Некоректна сторінка підопічних.');
  }
  return apiRequest(`/mentorships/my-mentees?limit=${limit}&offset=${offset}`, { signal });
}
export async function joinMentorship(value: string): Promise<Relationship> {
  const code = value.trim().toUpperCase();
  if (!/^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{12}$/.test(code)) {
    throw new Error('Код має містити 12 літер або цифр. Перевір його й спробуй ще раз.');
  }
  return apiRequest('/mentorships', { method: 'POST', body: JSON.stringify({ code }) });
}
export async function endMentorship(id: number): Promise<void> {
  return apiRequest(relationshipPath(id), { method: 'DELETE' });
}
export async function getMentorship(id: number, signal?: AbortSignal): Promise<Relationship> {
  return apiRequest(relationshipPath(id), { signal });
}
export async function getMenteeEntries(id: number, from: string, to: string, signal?: AbortSignal): Promise<EntryPage> {
  const query = new URLSearchParams({ from, to, limit: '100', offset: '0' });
  return apiRequest(`${relationshipPath(id)}/calendar/entries?${query}`, { signal });
}
export async function getMenteeEntry(id: number, recordId: number, signal?: AbortSignal): Promise<CalendarEntry> {
  if (!Number.isSafeInteger(recordId) || recordId <= 0) throw new Error('Некоректний ідентифікатор запису.');
  return apiRequest(`${relationshipPath(id)}/calendar/entries/${recordId}`, { signal });
}
export async function getMenteeStatistics(id: number, period: StatisticsPeriod, signal?: AbortSignal): Promise<MenteeStatistics> {
  return apiRequest(`${relationshipPath(id)}/statistics?period=${period}`, { signal });
}
