// AI-GENERATED START
import { useCallback, useRef, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Link, useFocusEffect } from 'expo-router';
import { fetchComplaints, type AdminComplaint, type ComplaintFilter } from '../../api/admin';
import { formatDate, STATUS_LABELS } from '../../admin/labels';
import { useAuth } from '../../auth/AuthProvider';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';

const FILTERS: { value: ComplaintFilter; label: string }[] = [
  { value: 'pending', label: 'Нові' },
  { value: 'approved', label: 'Схвалені' },
  { value: 'rejected', label: 'Відхилені' },
  { value: 'all', label: 'Усі' },
];

export default function AdminComplaints() {
  const { signOut } = useAuth();
  const [filter, setFilter] = useState<ComplaintFilter>('pending');
  const [items, setItems] = useState<AdminComplaint[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  // Відповідь для попереднього фільтра не повинна перезаписати новий список.
  const request = useRef(0);

  const load = useCallback(async (status: ComplaintFilter) => {
    const id = ++request.current;
    setError(null);
    try {
      const page = await fetchComplaints(status);
      if (id !== request.current) return;
      setItems(page.items);
      setTotal(page.total);
    } catch (e) {
      if (id !== request.current) return;
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити скарги');
    }
  }, []);

  useFocusEffect(useCallback(() => {
    void load(filter);
  }, [load, filter]));

  const choose = (value: ComplaintFilter) => {
    if (value === filter) return;
    setItems(null);
    setFilter(value);
  };

  const loadMore = async () => {
    if (!items || loadingMore || items.length >= total) return;
    const id = request.current;
    setLoadingMore(true);
    try {
      const page = await fetchComplaints(filter, items.length);
      if (id === request.current) {
        setItems((prev) => [...(prev ?? []), ...page.items]);
        setTotal(page.total);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити скарги');
    } finally {
      setLoadingMore(false);
    }
  };

  const header = (
    <View style={styles.header}>
      <Link href="/admin/analytics" style={styles.link}>Статистика →</Link>
      <View style={styles.filters}>
        {FILTERS.map((f) => (
          <Pressable
            key={f.value}
            accessibilityRole="button"
            accessibilityState={{ selected: f.value === filter }}
            onPress={() => choose(f.value)}
            style={[styles.chip, f.value === filter && styles.chipActive]}
          >
            <Text style={[styles.chipText, f.value === filter && styles.chipTextActive]}>{f.label}</Text>
          </Pressable>
        ))}
      </View>
      {error && items && <Text style={styles.error}>{error}</Text>}
    </View>
  );

  let body = null;
  if (!items && !error) body = <ScreenState state="loading" />;
  else if (!items) {
    body = <ScreenState state="error" message={error ?? undefined} onRetry={() => { void load(filter); }} />;
  }

  return (
    <FlatList
      contentContainerStyle={styles.list}
      data={items ?? []}
      keyExtractor={(c) => String(c.complaint_id)}
      ListHeaderComponent={<>{header}{body}</>}
      ListEmptyComponent={items ? <ScreenState state="empty" message="Скарг у цьому розділі немає." /> : null}
      renderItem={({ item }) => (
        <Link href={`/admin/complaint/${item.complaint_id}`} asChild>
          <Pressable accessibilityRole="button" style={styles.card}>
            <Text style={item.status === 'pending' ? styles.pending : styles.meta}>
              {STATUS_LABELS[item.status]} · {formatDate(item.created_at)}
            </Text>
            <Text style={styles.party}>Скаржник: {item.reporter.nickname} · {item.reporter.email}</Text>
            <Text style={styles.party}>Ментор: {item.reported.nickname} · {item.reported.email}</Text>
            <Text style={styles.reason} numberOfLines={3}>{item.reason}</Text>
          </Pressable>
        </Link>
      )}
      ListFooterComponent={
        <View style={styles.footer}>
          {items && items.length < total && (
            <Button title="Показати ще" loading={loadingMore} onPress={() => { void loadMore(); }} />
          )}
          <Button title="Вийти" onPress={() => { void signOut().catch(() => {}); }} />
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, gap: 12, backgroundColor: theme.colors.background, flexGrow: 1 },
  header: { gap: 12 },
  link: { color: theme.colors.primary, fontWeight: '700', fontSize: 16 },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    borderWidth: 1, borderColor: theme.colors.border, borderRadius: 999,
    paddingHorizontal: 14, minHeight: 40, justifyContent: 'center', backgroundColor: theme.colors.surface,
  },
  chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  chipText: { color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#FFFFFF' },
  error: { color: theme.colors.danger },
  card: {
    backgroundColor: theme.colors.surface, borderColor: theme.colors.border,
    borderWidth: 1, borderRadius: 14, padding: 14, gap: 6,
  },
  pending: { color: theme.colors.danger, fontWeight: '700' },
  meta: { color: theme.colors.muted, fontWeight: '600' },
  party: { color: theme.colors.text },
  reason: { color: theme.colors.text, fontStyle: 'italic' },
  footer: { gap: 12, marginTop: 8 },
});
// AI-GENERATED END
