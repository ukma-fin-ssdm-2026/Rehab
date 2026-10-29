// AI-GENERATED START
import { useCallback, useEffect, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Link } from 'expo-router';
import { fetchAdminUsers, setUserBlocked, type AdminUser } from '../../api/admin';
import { useAuth } from '../../auth/AuthProvider';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';

export default function AdminUsers() {
  const { signOut } = useAuth();
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  // Two-step action: Alert buttons are not shown by react-native-web.
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setUsers((await fetchAdminUsers()).items);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити користувачів');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const toggle = async (user: AdminUser) => {
    setConfirmId(null);
    setBusyId(user.user_id);
    setError(null);
    try {
      const updated = await setUserBlocked(user.user_id, !user.is_blocked);
      setUsers((prev) => prev?.map((u) => (u.user_id === updated.user_id ? updated : u)) ?? prev);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося змінити статус');
    } finally {
      setBusyId(null);
    }
  };

  if (!users && !error) return <ScreenState state="loading" />;
  if (!users) return <ScreenState state="error" message={error ?? undefined} onRetry={() => { void load(); }} />;

  return (
    <FlatList
      contentContainerStyle={styles.list}
      data={users}
      keyExtractor={(u) => String(u.user_id)}
      ListHeaderComponent={
        <View style={styles.header}>
          <Link href="/admin/analytics" style={styles.link}>Діаграма тригерів →</Link>
          {error && <Text style={styles.error}>{error}</Text>}
        </View>
      }
      ListEmptyComponent={<ScreenState state="empty" message="Користувачів поки немає." />}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.name}>{item.name} (@{item.nickname})</Text>
          <Text style={styles.meta}>{item.email} · {item.role}</Text>
          <Text style={item.is_blocked ? styles.blocked : styles.active}>
            {item.is_blocked ? 'Заблоковано' : 'Активний'}
          </Text>
          {item.role !== 'admin' && confirmId !== item.user_id && (
            <Button
              title={item.is_blocked ? 'Розблокувати' : 'Заблокувати'}
              loading={busyId === item.user_id}
              onPress={() => setConfirmId(item.user_id)}
            />
          )}
          {item.role !== 'admin' && confirmId === item.user_id && (
            <View style={styles.confirm}>
              <Text style={styles.confirmText}>
                {item.is_blocked
                  ? `Розблокувати ${item.email}? Старі сесії не відновляться, потрібен новий вхід.`
                  : `Заблокувати ${item.email}? Користувач одразу втратить доступ.`}
              </Text>
              <Button
                title={item.is_blocked ? 'Так, розблокувати' : 'Так, заблокувати'}
                onPress={() => { void toggle(item); }}
              />
              <Pressable accessibilityRole="button" onPress={() => setConfirmId(null)} style={styles.cancel}>
                <Text style={styles.cancelText}>Скасувати</Text>
              </Pressable>
            </View>
          )}
        </View>
      )}
      ListFooterComponent={<View style={styles.footer}><Button title="Вийти" onPress={() => { void signOut().catch(() => {}); }} /></View>}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, gap: 12 },
  header: { gap: 8 },
  link: { color: theme.colors.primary, fontWeight: '700', fontSize: 16 },
  error: { color: theme.colors.danger },
  card: {
    backgroundColor: theme.colors.surface, borderColor: theme.colors.border,
    borderWidth: 1, borderRadius: 14, padding: 14, gap: 6,
  },
  name: { color: theme.colors.text, fontWeight: '700', fontSize: 16 },
  meta: { color: theme.colors.muted },
  blocked: { color: theme.colors.danger, fontWeight: '700' },
  active: { color: theme.colors.primaryDark, fontWeight: '700' },
  footer: { marginTop: 8 },
  confirm: { gap: 8 },
  confirmText: { color: theme.colors.text },
  cancel: { minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  cancelText: { color: theme.colors.primaryDark, fontWeight: '700', fontSize: 16 },
});
// AI-GENERATED END
