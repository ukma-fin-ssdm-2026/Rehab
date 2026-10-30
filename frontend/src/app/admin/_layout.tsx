// AI-GENERATED START
import { Stack } from 'expo-router';

export default function AdminLayout() {
  return (
    <Stack screenOptions={{ headerShown: true }}>
      <Stack.Screen name="complaints" options={{ title: 'Скарги' }} />
      <Stack.Screen name="complaint/[complaint_id]" options={{ title: 'Скарга' }} />
      <Stack.Screen name="analytics" options={{ title: 'Статистика' }} />
      <Stack.Screen name="users" options={{ headerShown: false }} />
    </Stack>
  );
}
// AI-GENERATED END
