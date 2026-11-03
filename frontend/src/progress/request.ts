/** Ignore obsolete responses after a newer request, blur, or account change. */
export function createLatestRequest() {
  let version = 0;
  return {
    cancel() { version += 1; },
    async run<T>(load: () => Promise<T>, success: (data: T) => void, failure: (error: unknown) => void) {
      const current = ++version;
      try {
        const data = await load();
        if (current === version) success(data);
      } catch (error) {
        if (current === version) failure(error);
      }
    },
  };
}
