const KEY = 'rehab.auth.return-entry';
const entryPath = /^\/entry\/([1-9]\d{0,9})\/?$/;

export function rememberEntryLink(
  storage: Pick<Storage, 'setItem'>,
  pathname: string,
): void {
  const match = entryPath.exec(pathname);
  if (match) storage.setItem(KEY, `/entry/${match[1]}`);
}

export function takeEntryLink(
  storage: Pick<Storage, 'getItem' | 'removeItem'>,
): string | null {
  const saved = storage.getItem(KEY);
  storage.removeItem(KEY);
  const match = saved ? entryPath.exec(saved) : null;
  return match ? `/entry/${match[1]}` : null;
}

export function discardEntryLink(
  storage: Pick<Storage, 'removeItem'>,
): void {
  storage.removeItem(KEY);
}
