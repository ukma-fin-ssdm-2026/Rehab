import { Redirect, Stack } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { ScreenState } from '../../components/ui/ScreenState';

/** Independent guard until this subtree is also registered in the shared root. */
export default function MenteeLayout() {
  const { user, loading, restoreError, retryRestore, onboardingPending } = useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) return <ScreenState state="error" message="Не вдалося перевірити сесію."
    onRetry={() => { void retryRestore(); }} />;
  if (!user) return <Redirect href="/login" />;
  if (user.role === 'admin') return <Redirect href="/" />;
  if (onboardingPending) return <Redirect href="/onboarding" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
