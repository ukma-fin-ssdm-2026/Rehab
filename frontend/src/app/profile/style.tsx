import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useState } from 'react';
import { Modal, Pressable, Text, View } from 'react-native';
import { updateProfilePreferences } from '../../api/profile';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';
import { useProfile } from '../../profile/ProfileProvider';
import { profileStyles as styles } from '../../profile/styles';
import type { MessageStyle } from '../../profile/types';

const choices: { key: MessageStyle; title: string; detail: string }[] = [
  { key: 'formal', title: 'Формальний', detail: 'Спокійно та конкретно.' },
  { key: 'humorous', title: 'Гумористичний', detail: 'Зухвалий гумор і ненормативна лексика. Лише за твоєю згодою.' },
  { key: 'zen', title: 'Дзен', detail: 'Спокій і цитати східної філософії українською.' },
  { key: 'strict', title: 'Суворий', detail: 'Різко й вимогливо, наче сувора мама. Без мату.' },
];

export default function MessageStyleScreen() {
  const { profile, loading, error: loadError, refreshProfile } = useProfile();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState(false);

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
      <GlassCard style={styles.card}>
        {choices.map(item => (
          <Pressable key={item.key} accessibilityRole="radio"
            accessibilityState={{ selected: profile.message_style === item.key, disabled: saving }}
            disabled={saving} onPress={() => { if (item.key==='humorous' && profile.message_style!=='humorous') setWarning(true); else void choose(item.key); }}
            style={{ borderWidth: 1, borderColor: profile.message_style === item.key
              ? theme.colors.buttonBorder : theme.colors.border, padding: 14, borderRadius: 12 }}>
            <Text style={styles.field}>{item.title} {profile.message_style === item.key ? '✓' : ''}</Text>
            <Text style={styles.muted}>{item.detail}</Text>
          </Pressable>
        ))}
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Оновити" disabled={saving} onPress={() => { void refreshProfile(); }} />
      </GlassCard>
      <Modal visible={warning} transparent animationType="fade" onRequestClose={()=>setWarning(false)}>
        <View style={{flex:1,backgroundColor:theme.colors.backdrop,justifyContent:'center',padding:24}}>
          <GlassCard accessibilityViewIsModal style={[styles.card,{backgroundColor:theme.colors.background}]}>
            <Text style={styles.title}>Ненормативна лексика</Text>
            <Text style={styles.subtitle}>Гумористичний стиль містить матюки й грубі жарти в автоматичних текстах застосунку та поштових нагадуваннях. Обирай його, лише якщо тобі комфортний такий тон.</Text>
            <Button title="Обрати гумористичний" onPress={()=>{setWarning(false);void choose('humorous');}} />
            <Button title="Скасувати" onPress={()=>setWarning(false)} />
          </GlassCard>
        </View>
      </Modal>
    </ScrollView>
  );
}
