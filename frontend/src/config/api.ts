
const configuredUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

export const API_BASE_URL =
  configuredUrl?.replace(/\/+$/, "") ?? "";

function getApiUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error(
      "Не налаштовано EXPO_PUBLIC_API_URL. Перевір frontend/.env.local."
    );
  }

  return `${API_BASE_URL}${path}`;
}

export function getCalendarEntriesUrl(): string {
  return getApiUrl("/api/v1/calendar/entries");
}

export function getStatisticsUrl(
  period: "all" | "week" | "month" | "year"
): string {
  return getApiUrl(`/api/v1/statistics?period=${period}`);
}
