// AI-GENERATED START
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ApiError } from '../../api/client';
import {
  COMPLAINT_REASON_MAX, fetchEvidence, submitComplaint, type ComplaintEvidence,
} from '../../api/complaints';
import { formatDate } from '../../admin/labels';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';
import { useAuth } from '../../auth/AuthProvider';

function positiveId(value: string | undefined): number | null {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
}

// Відкривається з картки ментора (relationship_id) або з повідомлення підтримки
// (relationship_id + notification_id): тоді доказ підставляється автоматично.
export default function ReportMentorRoute() {
  const { user } = useAuth();
  const params = useLocalSearchParams<{ relationship_id?: string; notification_id?: string }>();
  return <ReportMentor key={`${user?.user_id}:${params.relationship_id}:${params.notification_id}`} />;
}

function ReportMentor() {
  const params = useLocalSearchParams<{ relationship_id?: string; notification_id?: string }>();
  const relationshipId = positiveId(params.relationship_id);
  const notificationId = positiveId(params.notification_id);
  const [evidence, setEvidence] = useState<ComplaintEvidence | null>(null);
  const [evidenceState, setEvidenceState] = useState<'idle' | 'loading' | 'error'>(
    notificationId ? 'loading' : 'idle',
  );
  const [reason, setReason] = useState('');
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const loadEvidence = useCallback(async () => {
    if (!notificationId) return;
    setEvidenceState('loading');
    try {
      const comment = await fetchEvidence(notificationId);
      if (!comment) throw new Error('Коментар недоступний');
      setEvidence(comment);
      setEvidenceState('idle');
    } catch {
      setEvidenceState('error');
    }
  }, [notificationId]);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) return loadEvidence(); });
    return () => { active = false; };
  }, [loadEvidence]);

  const send = async () => {
    if (busy || (notificationId && evidenceState !== 'idle')) return;
    const text = reason.trim();
    if (!text) return setFieldError('Опиши причину скарги.');
    if (text.length > COMPLAINT_REASON_MAX) {
      return setFieldError(`Не більше ${COMPLAINT_REASON_MAX} символів.`);
    }
    setFieldError(undefined);
    setError(null);
    setBusy(true);
    try {
      await submitComplaint({
        relationship_id: relationshipId as number,
        reason: text,
        ...(evidence ? { support_comment_id: evidence.support_comment_id } : {}),
      });
      setDone(true);
    } catch (e) {
      if (e instanceof ApiError && e.code === 'COMPLAINT_ALREADY_PENDING') {
        setError('Скарга на цього ментора вже розглядається. Дочекайся рішення адміністратора.');
      } else {
        setError(e instanceof Error ? e.message : 'Не вдалося надіслати скаргу');
      }
    } finally {
      setBusy(false);
    }
  };

  if (!relationshipId) {
    return <ScreenState state="error" message="Не вказано менторство для скарги." />;
  }
  if (done) {
    return (
      <View style={styles.page}>
        <ScreenState state="empty" message="Скаргу надіслано. Адміністратор розгляне її; до рішення менторство не змінюється." />
        <Button title="Назад" onPress={() => router.back()} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={styles.title}>Скарга на ментора</Text>
      <Text style={styles.note}>
        Адміністратор побачить ваші нікнейми й email, причину та доданий коментар.
        Скарга сама не завершує менторство: це можна зробити окремо у «Підтримці».
      </Text>
      {evidenceState === 'loading' && <ScreenState state="loading" message="Завантажуємо коментар…" />}
      {evidenceState === 'error' && (
        <ScreenState state="error" message="Не вдалося завантажити коментар." onRetry={() => { void loadEvidence(); }} />
      )}
      {evidence && (
        <View style={styles.evidence}>
          <Text style={styles.label}>Коментар, на який скаржитесь</Text>
          <Text style={styles.text}>{evidence.text}</Text>
          <Text style={styles.note}>{formatDate(evidence.created_at)}</Text>
        </View>
      )}
      <FormField
        label="Причина"
        value={reason}
        onChangeText={setReason}
        multiline
        maxLength={COMPLAINT_REASON_MAX}
        placeholder="Що сталося?"
        error={fieldError}
        style={[styles.input, !!fieldError && styles.invalid]}
      />
      <Text style={styles.note}>{reason.trim().length}/{COMPLAINT_REASON_MAX}</Text>
      {error && <Text style={styles.error}>{error}</Text>}
      <Button
        title="Надіслати скаргу"
        loading={busy}
        disabled={!!notificationId && evidenceState !== 'idle'}
        onPress={() => { void send(); }}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { padding: 16, gap: 12, backgroundColor: theme.colors.background, flexGrow: 1 },
  title: { color: theme.colors.text, fontSize: 22, fontWeight: '700' },
  note: { color: theme.colors.muted },
  label: { color: theme.colors.muted, fontWeight: '700' },
  text: { color: theme.colors.text, fontSize: 16 },
  evidence: { backgroundColor: theme.colors.accent, borderRadius: 12, padding: 12, gap: 6 },
  input: {
    backgroundColor: theme.colors.surface, borderColor: theme.colors.border, borderWidth: 1,
    borderRadius: 12, minHeight: 120, padding: 14, color: theme.colors.text, textAlignVertical: 'top',
  },
  invalid: { borderColor: theme.colors.danger },
  error: { color: theme.colors.danger },
});
// AI-GENERATED END
