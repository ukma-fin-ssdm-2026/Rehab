// AI-GENERATED START
import { theme } from '../../constants/theme';
import { Stack } from 'expo-router';

export default function AdminLayout() {
  return (
    <Stack screenOptions={{ headerShown: true, headerStyle: { backgroundColor: theme.colors.background }, headerTintColor: theme.colors.text, contentStyle: { backgroundColor: theme.colors.background } }}>
      <Stack.Screen name="complaints" options={{ title: 'Скарги' }} />
      <Stack.Screen name="complaint/[complaint_id]" options={{ title: 'Скарга' }} />
      <Stack.Screen name="analytics" options={{ title: 'Статистика' }} />
      <Stack.Screen name="users" options={{ headerShown: false }} />
    </Stack>
  );
}
// AI-GENERATED END
