import type { CalendarEntry, DayStatus, DrinkType, EntryCreate, TriggerCategory } from '../api/calendar';

export const drinkTypes: { label: string; value: DrinkType }[] = [
  { label: 'Пиво', value: 'beer' }, { label: 'Вино', value: 'wine' },
  { label: 'Міцний алкоголь', value: 'spirits' }, { label: 'Коктейль', value: 'cocktail' },
  { label: 'Інше', value: 'other' },
];
export const triggers: { label: string; value: TriggerCategory | null }[] = [
  { label: 'Не вказано', value: null }, { label: 'Стрес', value: 'stress' },
  { label: 'Свято', value: 'holiday' }, { label: 'Компанія', value: 'social' },
  { label: 'Інше', value: 'other' },
];
export type DraftDrink = { id: number; type: DrinkType; volume: string };
export type EntryDraft = {
  date: string; status: DayStatus; trigger_category: TriggerCategory | null;
  drinks: Omit<DraftDrink, 'id'>[]; comment: string;
};

export function kyivDate(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Kyiv', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const value = (name: string) => parts.find(part => part.type === name)!.value;
  return `${value('year')}-${value('month')}-${value('day')}`;
}

export function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T12:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function entryPayload(draft: EntryDraft, start: string, today: string): EntryCreate {
  if (!validDate(draft.date)) throw new Error('Введи коректну дату у форматі РРРР-ММ-ДД.');
  if (draft.date < start || draft.date > today) throw new Error(`Дата має бути від ${start} до ${today}.`);
  if (Array.from(draft.comment).length > 2000) throw new Error('Коментар — не більше 2000 символів.');
  const drinks = draft.status === 'sober' ? [] : draft.drinks.map(drink => {
    const volume = Number(drink.volume);
    if (!/^\d+$/.test(drink.volume) || !Number.isSafeInteger(volume) || volume <= 0) {
      throw new Error('Для кожного напою вкажи додатний цілий об’єм у мілілітрах.');
    }
    return { type: drink.type, volume_ml: volume };
  });
  return { date: draft.date, status: draft.status,
    trigger_category: draft.status === 'sober' ? null : draft.trigger_category,
    drinks, comment: draft.comment.trim() || null };
}

export function canEdit(createdAt: string, now = Date.now()): boolean {
  const age = now - Date.parse(createdAt);
  return Number.isFinite(age) && age >= 0 && age <= 48 * 60 * 60 * 1000;
}

export function dayStatus(date: string, entry: Pick<CalendarEntry, 'status'> | undefined,
  start: string | null, today: string): DayStatus | 'empty' {
  if (entry) return entry.status;
  return start && date >= start && date <= today ? 'sober' : 'empty';
}

export function shiftedMonth(year: number, month: number, offset: number) {
  const value = new Date(year, month + offset, 1);
  const selectedDate = `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-01`;
  return { value, selectedDate };
}
