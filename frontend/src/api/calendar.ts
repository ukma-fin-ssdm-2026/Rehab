import { notifyProgressChanged } from '../progress/changes';
import { ApiError, apiRequest } from './client';

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

// AI-GENERATED START
// R3 (Лаб 9): apiRequest лише приводить JSON до типу, тому відповідь читання
// перевіряється тут. Некоректна структура дає контрольовану помилку (fail fast),
// а не null у стані екрана, де рендер падає на entries.map.
const STATUSES: readonly unknown[] = ['sober', 'relapse'];
const TRIGGERS: readonly unknown[] = ['stress', 'holiday', 'social', 'other'];
const DRINK_TYPES: readonly unknown[] = ['beer', 'wine', 'spirits', 'cocktail', 'other'];
const DATE = /^\d{4}-\d{2}-\d{2}$/;

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
const isCount = (value: unknown) => Number.isInteger(value) && (value as number) >= 0;

function isDrink(value: unknown): boolean {
  return isObject(value) && DRINK_TYPES.includes(value.type)
    && Number.isInteger(value.volume_ml) && (value.volume_ml as number) > 0;
}

export function isCalendarEntry(value: unknown): value is CalendarEntry {
  return isObject(value)
    && Number.isInteger(value.record_id) && Number.isInteger(value.user_id)
    && typeof value.date === 'string' && DATE.test(value.date)
    && STATUSES.includes(value.status)
    && (value.trigger_category === null || TRIGGERS.includes(value.trigger_category))
    && Array.isArray(value.drinks) && value.drinks.every(isDrink)
    && (value.comment === null || typeof value.comment === 'string')
    && typeof value.created_at === 'string';
}

export function isEntryPage(value: unknown): value is EntryPage {
  return isObject(value) && Array.isArray(value.items) && value.items.every(isCalendarEntry)
    && isCount(value.total) && isCount(value.limit) && isCount(value.offset);
}

function invalidCalendarResponse(): ApiError {
  console.warn('Calendar API returned an unexpected response shape');
  return new ApiError(200, 'INVALID_RESPONSE', 'Сервер повернув некоректні дані календаря. Спробуй пізніше.');
}

export async function listEntries(from: string, to: string): Promise<EntryPage> {
  const page: unknown = await apiRequest(
    `/calendar/entries?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&limit=100&offset=0`,
  );
  if (!isEntryPage(page)) throw invalidCalendarResponse();
  return page;
}

export async function getEntry(id: number): Promise<CalendarEntry> {
  const entry: unknown = await apiRequest(`/calendar/entries/${id}`);
  if (!isCalendarEntry(entry)) throw invalidCalendarResponse();
  return entry;
}
// AI-GENERATED END
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
