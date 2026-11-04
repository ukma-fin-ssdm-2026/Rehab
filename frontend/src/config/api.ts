
const configuredUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

// AI-GENERATED START: Substitute Algorithm for SonarQube typescript:S8786.
function removeTrailingSlashes(value: string): string {
  let end = value.length;
  while (end > 0 && value[end - 1] === "/") {
    end -= 1;
  }
  return value.slice(0, end);
}

export const API_BASE_URL = removeTrailingSlashes(configuredUrl ?? "");
// AI-GENERATED END

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
