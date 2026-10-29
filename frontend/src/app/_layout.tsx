import { Stack } from 'expo-router';
import { AuthProvider, useAuth } from '../auth/AuthProvider';
import { ScreenState } from '../components/ui/ScreenState';

function ProtectedNavigation() {
  const { user, loading } = useAuth();
  if (loading) return <ScreenState state="loading" message="Перевіряємо сесію…" />;
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Protected guard={!user}>
        <Stack.Screen name="login" />
        <Stack.Screen name="register" />
      </Stack.Protected>
      <Stack.Protected guard={!!user && user.role !== 'admin'}>
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="add-entry" />
        <Stack.Screen name="placeholders" />
      </Stack.Protected>
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
