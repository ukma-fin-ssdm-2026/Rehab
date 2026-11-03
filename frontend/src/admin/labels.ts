// AI-GENERATED START
import type { ComplaintStatus } from '../api/admin';

export const STATUS_LABELS: Record<ComplaintStatus, string> = {
  pending: 'Очікує розгляду',
  approved: 'Схвалено',
  rejected: 'Відхилено',
};

export function formatDate(value: string): string {
  return new Date(value).toLocaleString('uk-UA', { timeZone: 'Europe/Kyiv' });
}
// AI-GENERATED END
