import { Stack } from 'expo-router';
import { AuthProvider, useAuth } from '../auth/AuthProvider';

function ProtectedNavigation() {
  const { user, loading } = useAuth();
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
