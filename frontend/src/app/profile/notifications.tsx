import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useState } from 'react';
import { Switch, Text } from 'react-native';
import { updateProfilePreferences } from '../../api/profile';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';
import { useProfile } from '../../profile/ProfileProvider';
import { profileStyles as styles } from '../../profile/styles';

export default function NotificationSettingsScreen() {
  const { profile, loading, error: loadError, refreshProfile } = useProfile();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function change(enabled: boolean) {
    if (!profile || saving) return;
    setSaving(true);
    setError('');
    try {
      await updateProfilePreferences({ email_reminders_enabled: enabled });
      await refreshProfile();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося зберегти налаштування.');
    } finally {
      setSaving(false);
    }
  }

  if (!profile && loading) return <ScreenState state="loading" />;
  if (!profile) return <ScreenState state="error" message={loadError ?? undefined}
    onRetry={() => { void refreshProfile(); }} />;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Сповіщення та пошта</Text>
      <GlassCard style={styles.card}>
        <Text style={styles.field}>Дублювати щоденне нагадування на пошту</Text>
        <Switch value={profile.email_reminders_enabled} disabled={saving}
          accessibilityLabel="Дублювати щоденне нагадування на пошту"
          onValueChange={value => { void change(value); }}
          trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
          thumbColor={theme.colors.highlight} />
        <Text style={styles.muted}>Адреса: {profile.email}</Text>
        <Text style={styles.text}>
          Повідомлення в Rehab залишаються незалежно від цього перемикача.
          На пошту надходитимуть лише копії щоденних нагадувань, не повідомлення
          про зрив чи коментарі підтримки.
        </Text>
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Оновити" disabled={saving} onPress={() => { void refreshProfile(); }} />
      </GlassCard>
    </ScrollView>
  );
}
