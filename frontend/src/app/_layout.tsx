import { Stack } from 'expo-router';
import { AuthProvider, useAuth } from '../auth/AuthProvider';
import { ScreenState } from '../components/ui/ScreenState';

function ProtectedNavigation() {
  const { user, loading, restoreError, retryRestore } = useAuth();
  // Keep the requested URL until session restore finishes; otherwise protected
  // detail routes are removed before the saved JWT can be checked.
  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) {
    return <ScreenState state="error" message="Не вдалося перевірити сесію. Перевір підключення."
      onRetry={() => { void retryRestore(); }} />;
  }
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Protected guard={!loading && !user}>
        <Stack.Screen name="login" />
        <Stack.Screen name="register" />
      </Stack.Protected>
      <Stack.Protected guard={!loading && !!user && user.role !== 'admin'}>
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="add-entry" />
        <Stack.Screen name="entry/[record_id]" />
        <Stack.Screen name="placeholders" />
      </Stack.Protected>
      {/* AI-GENERATED START */}
      <Stack.Protected guard={!loading && !!user && user.role === 'admin'}>
        <Stack.Screen name="admin" />
      </Stack.Protected>
      {/* AI-GENERATED END */}
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <ProtectedNavigation />
    </AuthProvider>
  );
}
