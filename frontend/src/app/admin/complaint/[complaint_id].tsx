// AI-GENERATED START
import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams } from 'expo-router';
import { decideComplaint, fetchComplaint, type AdminComplaint } from '../../../api/admin';
import { formatDate, STATUS_LABELS } from '../../../admin/labels';
import { Button } from '../../../components/ui/Button';
import { ScreenState } from '../../../components/ui/ScreenState';
import { theme } from '../../../constants/theme';

type Decision = 'approved' | 'rejected';

export default function AdminComplaintDetail() {
  const params = useLocalSearchParams<{ complaint_id: string }>();
  const complaintId = Number(params.complaint_id);
  const [complaint, setComplaint] = useState<AdminComplaint | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<Decision | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setComplaint(await fetchComplaint(complaintId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити скаргу');
    }
  }, [complaintId]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  const decide = async (decision: Decision) => {
    setBusy(true);
    setError(null);
    try {
      await decideComplaint(complaintId, decision);
      setConfirm(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося зберегти рішення');
      await load();
    } finally {
      setBusy(false);
    }
  };

  if (!Number.isInteger(complaintId) || complaintId < 1) {
    return <ScreenState state="error" message="Некоректне посилання на скаргу" />;
  }
  if (!complaint && !error) return <ScreenState state="loading" />;
  if (!complaint) {
    return <ScreenState state="error" message={error ?? undefined} onRetry={() => { void load(); }} />;
  }

  const pair = `${complaint.reporter.nickname} і ментора ${complaint.reported.nickname}`;
  const consequence = confirm === 'approved'
    ? `Менторство між ${pair} буде завершено назавжди: повторно приєднати цю пару неможливо. Інші зв'язки, вхід і власні записи обох не зміняться.`
    : `Скаргу буде закрито без змін для зв'язку ${pair}. Якщо менторство вже завершене, відхилення його не відновлює.`;

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.card}>
        <Text style={complaint.status === 'pending' ? styles.pending : styles.meta}>
          {STATUS_LABELS[complaint.status]}
        </Text>
        <Text style={styles.meta}>Подано: {formatDate(complaint.created_at)}</Text>
        {complaint.reviewed_at && (
          <Text style={styles.meta}>Розглянуто: {formatDate(complaint.reviewed_at)}</Text>
        )}
        <Text style={styles.label}>Скаржник (підопічний)</Text>
        <Text selectable style={styles.text}>{complaint.reporter.nickname} · {complaint.reporter.email}</Text>
        <Text style={styles.label}>Ментор</Text>
        <Text selectable style={styles.text}>{complaint.reported.nickname} · {complaint.reported.email}</Text>
        <Text style={styles.label}>Причина</Text>
        <Text selectable style={styles.text}>{complaint.reason}</Text>
        <Text style={styles.label}>Доданий коментар ментора</Text>
        {complaint.evidence ? (
          <View style={styles.evidence}>
            <Text selectable style={styles.text}>{complaint.evidence.text}</Text>
            {complaint.evidence.created_at && (
              <Text style={styles.meta}>{formatDate(complaint.evidence.created_at)}</Text>
            )}
          </View>
        ) : (
          <Text style={styles.meta}>Не додано</Text>
        )}
      </View>

      {error && <Text style={styles.error}>{error}</Text>}

      {complaint.status === 'pending' && !confirm && (
        <View style={styles.actions}>
          <Button title="Схвалити скаргу" disabled={busy} onPress={() => setConfirm('approved')} />
          <Button title="Відхилити" disabled={busy} onPress={() => setConfirm('rejected')} />
        </View>
      )}
      {complaint.status === 'pending' && confirm && (
        <View style={styles.card}>
          <Text style={styles.text}>{consequence}</Text>
          <Button
            title={confirm === 'approved' ? 'Так, схвалити' : 'Так, відхилити'}
            loading={busy}
            onPress={() => { void decide(confirm); }}
          />
          <Pressable accessibilityRole="button" disabled={busy} onPress={() => setConfirm(null)} style={styles.cancel}>
            <Text style={styles.cancelText}>Скасувати</Text>
          </Pressable>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { padding: 16, gap: 12, backgroundColor: theme.colors.background, flexGrow: 1 },
  card: {
    backgroundColor: theme.colors.surface, borderColor: theme.colors.border,
    borderWidth: 1, borderRadius: 14, padding: 14, gap: 6,
  },
  pending: { color: theme.colors.danger, fontWeight: '500' },
  meta: { color: theme.colors.muted },
  label: { color: theme.colors.muted, fontWeight: '500', marginTop: 8 },
  text: { color: theme.colors.text, fontSize: 16 },
  evidence: { backgroundColor: theme.colors.accent, borderRadius: 10, padding: 10, gap: 4 },
  error: { color: theme.colors.danger },
  actions: { gap: 12 },
  cancel: { minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  cancelText: { color: theme.colors.text, fontWeight: '500', fontSize: 16 },
});
// AI-GENERATED END
