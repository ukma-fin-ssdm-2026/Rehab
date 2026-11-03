const listeners = new Set<() => void>();
export function subscribeProgressChanges(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function notifyProgressChanged(): void {
  for (const listener of listeners) listener();
}
