const KEY = 'rehab.auth.onboarding-user';

export function isOnboardingPending(
  storage: Pick<Storage, 'getItem'>,
  userId: number,
): boolean {
  return storage.getItem(KEY) === String(userId);
}

export function saveOnboardingPending(
  storage: Pick<Storage, 'setItem' | 'removeItem'>,
  userId: number | null,
): void {
  if (userId === null) {
    storage.removeItem(KEY);
  } else {
    storage.setItem(KEY, String(userId));
  }
}
