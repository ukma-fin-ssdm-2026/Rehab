import { notifyProgressChanged } from '../progress/changes';
import { apiRequest } from './client';

export type DayStatus = 'sober' | 'relapse';
export type TriggerCategory = 'stress' | 'holiday' | 'social' | 'other';
export type DrinkType = 'beer' | 'wine' | 'spirits' | 'cocktail' | 'other';
export type Drink = { type: DrinkType; volume_ml: number };
export type EntryCreate = {
  date: string;
  status: DayStatus;
  trigger_category: TriggerCategory | null;
  drinks: Drink[];
  comment: string | null;
};
export type CalendarEntry = EntryCreate & {
  record_id: number;
  user_id: number;
  created_at: string;
};
export type EntryPage = { items: CalendarEntry[]; total: number; limit: number; offset: number };
export type EntryUpdate = Pick<EntryCreate, 'status' | 'trigger_category'>;

export const listEntries = (from: string, to: string): Promise<EntryPage> =>
  apiRequest(`/calendar/entries?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&limit=100&offset=0`);
export const getEntry = (id: number): Promise<CalendarEntry> => apiRequest(`/calendar/entries/${id}`);
export async function createEntry(data: EntryCreate): Promise<CalendarEntry> {
  const entry = await apiRequest<CalendarEntry>('/calendar/entries', { method: 'POST', body: JSON.stringify(data) });
  notifyProgressChanged();
  return entry;
}
export async function updateEntry(id: number, data: EntryUpdate): Promise<CalendarEntry> {
  const entry = await apiRequest<CalendarEntry>(`/calendar/entries/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  notifyProgressChanged();
  return entry;
}
