function dateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

/** Calendar cells use business-date strings, never UTC serialization of local midnight. */
export function calendarMonth(year: number, month: number) {
  const first = new Date(year, month, 1);
  const count = new Date(year, month + 1, 0).getDate();
  const days: (string | null)[] = Array((first.getDay() + 6) % 7).fill(null);
  for (let day = 1; day <= count; day++) days.push(dateKey(year, month, day));
  while (days.length % 7) days.push(null);
  return { days, from: dateKey(year, month, 1), to: dateKey(year, month, count) };
}
