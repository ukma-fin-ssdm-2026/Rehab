import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { updateProfilePreferences } from '../../api/profile';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';
import { useProfile } from '../../profile/ProfileProvider';
import { profileStyles as styles } from '../../profile/styles';
import type { MessageStyle } from '../../profile/types';

const choices: { key: MessageStyle; title: string; detail: string }[] = [
  { key: 'formal', title: 'Формальний', detail: 'Спокійно та конкретно.' },
  { key: 'humorous', title: 'Гумористичний', detail: 'Тепло, з м’яким гумором.' },
  { key: 'zen', title: 'Дзен', detail: 'М’яко й уважно.' },
  { key: 'strict', title: 'Суворий', detail: 'Прямо, без осуду.' },
];

export default function MessageStyleScreen() {
  const { profile, loading, error: loadError, refreshProfile } = useProfile();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function choose(value: MessageStyle) {
    if (!profile || saving || profile.message_style === value) return;
    setSaving(true);
    setError('');
    try {
      await updateProfilePreferences({ message_style: value });
      await refreshProfile();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося змінити стиль.');
    } finally {
      setSaving(false);
    }
  }

  if (!profile && loading) return <ScreenState state="loading" />;
  if (!profile) return <ScreenState state="error" message={loadError ?? undefined}
    onRetry={() => { void refreshProfile(); }} />;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Стиль повідомлень</Text>
      <Text style={styles.subtitle}>
        Стиль змінює автоматичні фрази, але не чужі особисті коментарі.
      </Text>
      <View style={styles.card}>
        {choices.map(item => (
          <Pressable key={item.key} accessibilityRole="radio"
            accessibilityState={{ selected: profile.message_style === item.key, disabled: saving }}
            disabled={saving} onPress={() => { void choose(item.key); }}
            style={{ borderWidth: 1, borderColor: profile.message_style === item.key
              ? theme.colors.primary : theme.colors.border, padding: 14, borderRadius: 12 }}>
            <Text style={styles.field}>{item.title} {profile.message_style === item.key ? '✓' : ''}</Text>
            <Text style={styles.muted}>{item.detail}</Text>
          </Pressable>
        ))}
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Оновити" disabled={saving} onPress={() => { void refreshProfile(); }} />
      </View>
    </ScrollView>
  );
}
