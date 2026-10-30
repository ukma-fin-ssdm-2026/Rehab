import { useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { Redirect, type Href } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { takeEntryLink } from '../auth/returnEntry';
import { ScreenState } from '../components/ui/ScreenState';

export default function Index() {
  const { user, loading, restoreError, onboardingPending, retryRestore } = useAuth();
  const [entryLink, setEntryLink] = useState<string | null | undefined>(undefined);
  const consumed = useRef(false);

  useEffect(() => {
    if (!user || user.role === 'admin' || onboardingPending || consumed.current) return;
    consumed.current = true;
    setEntryLink(
      Platform.OS === 'web' && typeof window !== 'undefined'
        ? takeEntryLink(window.sessionStorage) : null
    );
  }, [user, onboardingPending]);

  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) {
    return <ScreenState state="error" message="Не вдалося перевірити сесію. Перевір підключення."
      onRetry={() => { void retryRestore(); }} />;
  }
  if (!user) return <Redirect href="/login" />;
  if (user.role === 'admin') return <Redirect href="/admin/complaints" />;
  if (onboardingPending) return <Redirect href="/onboarding" />;
  if (entryLink === undefined) return <ScreenState state="loading" />;
  return <Redirect href={entryLink ? entryLink as Href : '/(tabs)/home'} />;
}
