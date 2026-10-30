/** One instance per detail screen; never share pending requests between accounts. */
export function createSupportSender<T>(send: (id: number, text: string) => Promise<T>) {
  const pending = new Map<number, Promise<T>>();
  return (id: number, text: string): Promise<T> => {
    const current = pending.get(id);
    if (current) return current;
    const request = send(id, text).finally(() => { pending.delete(id); });
    pending.set(id, request);
    return request;
  };
}
