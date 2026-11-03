import type { Notification, NotificationPage } from '../api/notifications';

/** Refresh every loaded page so new arrivals do not leave stale offset pages. */
export async function loadInboxPages(fetchPage: (limit: number, offset: number) => Promise<NotificationPage>, visible = 30) {
  const items = new Map<number, Notification>();
  let total = 0;
  for (let offset = 0; offset < Math.max(30, visible); offset += 30) {
    const page = await fetchPage(30, offset);
    if (offset === 0) total = page.total;
    for (const item of page.items) if (!items.has(item.notification_id)) items.set(item.notification_id, item);
    if (!page.items.length || offset + page.items.length >= total) break;
  }
  return { items: Array.from(items.values()), total };
}
