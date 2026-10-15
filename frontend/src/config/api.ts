const configuredUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

export const API_BASE_URL =
  configuredUrl?.replace(/\/+$/, "") ?? "";

export function getCalendarEntriesUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "Не налаштовано EXPO_PUBLIC_API_URL. Перевір frontend/.env.local."
    );
  }

  return `${API_BASE_URL}/api/v1/calendar/entries`;
}