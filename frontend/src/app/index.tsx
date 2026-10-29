import { Redirect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { ScreenState } from '../components/ui/ScreenState';

export default function Index() {
  const { user, loading, restoreError, onboardingPending, retryRestore } = useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) {
    return <ScreenState state="error" message="Не вдалося перевірити сесію. Перевір підключення."
      onRetry={() => { void retryRestore(); }} />;
  }
  if (!user) return <Redirect href="/login" />;
  // AI-GENERATED START
  if (user.role === 'admin') return <Redirect href="/admin/users" />;
  // AI-GENERATED END
  if (onboardingPending) return <Redirect href="/onboarding" />;
  return <Redirect href="/(tabs)/home" />;
}
