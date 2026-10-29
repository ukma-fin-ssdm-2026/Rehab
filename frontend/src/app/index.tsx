import { Redirect } from 'expo-router';
import { View, StyleSheet } from 'react-native';
import { useAuth } from '../auth/AuthProvider';
import { Button } from '../components/ui/Button';
import { ScreenState } from '../components/ui/ScreenState';

export default function Index() {
  const { user, loading, restoreError, refresh, onboardingPending, signOut } = useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (restoreError && !user) {
    return <ScreenState state="error" message="Не вдалося перевірити сесію. Перевір підключення."
      onRetry={() => { void refresh().catch(() => {}); }} />;
  }
  if (!user) return <Redirect href="/login" />;
  if (user.role === 'admin') {
    return (
      <View style={styles.admin}>
        <ScreenState state="empty" message="Панель адміністратора ще не підключена." />
        <Button title="Вийти" onPress={() => { void signOut().catch(() => {}); }} />
      </View>
    );
  }
  if (onboardingPending) return <Redirect href="/onboarding" />;
  return <Redirect href="/(tabs)/home" />;
}

const styles = StyleSheet.create({
  admin: { flex: 1, justifyContent: 'center', padding: 24 },
});
