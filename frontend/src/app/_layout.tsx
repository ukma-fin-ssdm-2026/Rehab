import { Stack } from 'expo-router';
import { AuthProvider, useAuth } from '../auth/AuthProvider';
import { ScreenState } from '../components/ui/ScreenState';
import { ProfileProvider } from '../profile/ProfileProvider';

function ProtectedNavigation() {
  const { user, loading, restoreError, retryRestore, onboardingPending } = useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) {
    return <ScreenState state="error" message="Не вдалося перевірити сесію. Перевір підключення."
      onRetry={() => { void retryRestore(); }} />;
  }
  const isUser = !!user && user.role !== 'admin';
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Protected guard={!loading && !user}>
        <Stack.Screen name="login" />
        <Stack.Screen name="register" />
      </Stack.Protected>
      <Stack.Protected guard={!loading && isUser && onboardingPending}>
        <Stack.Screen name="onboarding" />
      </Stack.Protected>
      <Stack.Protected guard={!loading && isUser && !onboardingPending}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="add-entry" />
        <Stack.Screen name="entry/[record_id]" />
        <Stack.Screen name="messages" />
        <Stack.Screen name="placeholders" />
        <Stack.Screen name="profile/edit" />
        <Stack.Screen name="profile/password" />
        <Stack.Screen name="profile/notifications" />
        <Stack.Screen name="profile/style" />
        <Stack.Screen name="profile/privacy" />
        <Stack.Screen name="profile/help" />
        <Stack.Screen name="support/report" />
        <Stack.Screen name="mentee" />
      </Stack.Protected>
      <Stack.Protected guard={!loading && !!user && user.role === 'admin'}>
        <Stack.Screen name="admin" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <ProfileProvider>
        <ProtectedNavigation />
      </ProfileProvider>
    </AuthProvider>
  );
}
