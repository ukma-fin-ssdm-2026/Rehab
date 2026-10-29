import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { Button } from '../../components/ui/Button';
import { theme } from '../../constants/theme';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  async function handleLogout() {
    setSaving(true);
    try {
      await signOut();
      router.replace('/login');
    } catch {
      setError('Не вдалося підтвердити вихід на сервері. Локальну сесію завершено.');
      router.replace('/login');
    } finally {
      setSaving(false);
    }
  }
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТВІЙ ПРОСТІР</Text>
      <Text style={styles.title}>Профіль</Text>
      <View style={styles.card}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.name?.charAt(0).toUpperCase() ?? 'R'}</Text>
        </View>
        <Text style={styles.name}>{user?.name ?? 'Завантаження…'}</Text>
        <Text style={styles.nickname}>@{user?.nickname ?? ''}</Text>
        <Text style={styles.email}>{user?.email ?? ''}</Text>
      </View>
      <Text style={styles.note}>Керування паролем та сповіщеннями буде доступне в наступних версіях.</Text>
      {!!error && <Text style={styles.error}>{error}</Text>}
      <Button title="Вийти з акаунта" loading={saving} onPress={() => { void handleLogout(); }} />
    </ScrollView>
  );
}
const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: theme.colors.background, padding: 24, gap: 18 },
  eyebrow: { color: theme.colors.primary, fontSize: 12, fontWeight: '700', letterSpacing: 1.5 },
  title: { fontSize: 30, fontWeight: '800', color: theme.colors.primaryDark },
  card: { alignItems: 'center', gap: 10, borderWidth: 1, borderColor: theme.colors.border,
    borderRadius: 20, backgroundColor: theme.colors.surface, padding: 24 },
  avatar: { width: 70, height: 70, borderRadius: 25, backgroundColor: theme.colors.accent,
    alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: theme.colors.primaryDark, fontSize: 30, fontWeight: '800' },
  name: { fontSize: 21, color: theme.colors.primaryDark, fontWeight: '800' },
  nickname: { color: theme.colors.primary },
  email: { color: theme.colors.text },
  note: { color: theme.colors.muted, lineHeight: 21 },
  error: { color: theme.colors.danger },
});
