import { useState } from 'react';
import { Modal, Platform, Pressable, ScrollView, Text, View } from 'react-native';
import { router } from 'expo-router';
import type { Relationship } from '../api/mentorship';
import { Button } from '../components/ui/Button';
import { FormField } from '../components/ui/FormField';
import { ScreenState } from '../components/ui/ScreenState';
import { type MessageStyle } from '../messages/catalog';
import { useMessageText } from '../messages/useMessageText';
import { styles } from './styles';
import { useSupportData } from './useSupportData';

export function SupportPanel({ messageStyle = 'formal', onReport }: {
  messageStyle?: MessageStyle;
  onReport?: (relationshipId: number) => void;
}) {
  const messageText=useMessageText();
  const { data, loading, error, busy, reload, join, leave, loadMore } = useSupportData();
  const [code, setCode] = useState('');
  const [copyStatus, setCopyStatus] = useState('');
  const [ending, setEnding] = useState<Relationship | null>(null);

  async function copyCode() {
    if (!data) return;
    try {
      if (Platform.OS !== 'web' || typeof navigator === 'undefined' || !navigator.clipboard?.writeText) {
        setCopyStatus('Виділіть і скопіюйте код вручну.'); return;
      }
      await navigator.clipboard.writeText(data.code);
      setCopyStatus('Код скопійовано.');
    } catch { setCopyStatus('Виділіть і скопіюйте код вручну.'); }
  }

  return <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
    <Text style={styles.eyebrow}>ТИ НЕ САМА</Text>
    <Text style={styles.title}>Підтримка</Text>
    <Text style={styles.subtitle}>Тут можна бути поруч з іншими та отримувати підтримку на своєму шляху.</Text>
    {loading && <ScreenState state="loading" />}
    {!!error && <View style={styles.error}>
      <Text accessibilityRole="alert" style={styles.danger}>{error}</Text>
      <Pressable accessibilityRole="button" disabled={busy} onPress={() => { void reload(); }} style={styles.action}>
        <Text style={styles.link}>Спробувати ще раз</Text>
      </Pressable>
    </View>}
    {data && !loading && <>
      <View style={styles.card}>
        <Text style={styles.heading}>Мій особистий код</Text>
        <Text selectable style={styles.code}>{data.code}</Text>
        <Text style={styles.muted}>Передаючи код, ти одразу надаєш ментору доступ до свого календаря та статистики за весь період. Він зможе лише переглядати дані.</Text>
        <Button title="Скопіювати код" onPress={() => { void copyCode(); }} />
        {!!copyStatus && <Text accessibilityLiveRegion="polite" style={styles.muted}>{copyStatus}</Text>}
      </View>

      <View style={styles.card}>
        <Text style={styles.heading}>Мій ментор</Text>
        {data.mentor ? <>
          <Text style={styles.text}>@{data.mentor.mentor.nickname}</Text>
          <Text selectable style={styles.muted}>{data.mentor.mentor.email}</Text>
          <Pressable accessibilityRole="button" disabled={busy} style={styles.action} onPress={() => setEnding(data.mentor)}>
            <Text style={styles.danger}>Припинити менторство</Text>
          </Pressable>
          {onReport && <Pressable accessibilityRole="button" disabled={busy} style={styles.action}
            onPress={() => onReport(data.mentor!.relationship_id)}><Text style={styles.link}>Подати скаргу</Text></Pressable>}
        </> : <Text style={styles.muted}>Поки немає ментора. Передай свій код людині, якій довіряєш.</Text>}
      </View>

      {ending && <Modal transparent animationType="fade" onRequestClose={() => { if (!busy) setEnding(null); }}>
        <View style={styles.modalBackdrop}>
        <View accessibilityViewIsModal style={[styles.card, styles.modalCard]}>
        <Text style={styles.heading}>Завершити менторство?</Text>
        <Text style={styles.text}>З @{ending.mentor.user_id === data.owner ? ending.mentee.nickname : ending.mentor.nickname}</Text>
        <Text style={styles.text}>Доступ до даних і надсилання підтримки припиняться. Цю пару назавжди буде закрито для повторного приєднання, навіть за правильним кодом. Історія повідомлень збережеться.</Text>
        <Button title="Підтвердити завершення" loading={busy} onPress={() => {
          void leave(ending.relationship_id).then(ok => { if (ok) setEnding(null); });
        }} />
        <Pressable accessibilityRole="button" disabled={busy} style={styles.action} onPress={() => setEnding(null)}>
          <Text style={styles.link}>Скасувати</Text>
        </Pressable>
        {!!error && <Text accessibilityRole="alert" style={styles.danger}>{error}</Text>}
        </View>
        </View>
      </Modal>}

      <View style={styles.card}>
        <Text style={styles.heading}>Отримати підопічного</Text>
        <Text style={styles.muted}>Отримай код людини поза застосунком і введи його тут. Доступ відкриється відразу.</Text>
        <FormField label="Особистий код користувача" value={code} onChangeText={setCode}
          placeholder="12 літер або цифр" autoCapitalize="characters" autoCorrect={false} autoComplete="off" editable={!busy} />
        <Button title="Отримати підопічного" disabled={!code.trim()} loading={busy} onPress={() => {
          void join(code).then(ok => { if (ok) setCode(''); });
        }} />
      </View>

      <View style={styles.row}>
        <Text style={[styles.heading, styles.grow]}>Мої підопічні · {data.mentees.total}</Text>
        <Pressable accessibilityRole="button" disabled={busy} style={styles.action} onPress={() => { void reload(); }}>
          <Text style={styles.link}>Оновити</Text>
        </Pressable>
      </View>
      {data.mentees.items.length === 0 && <View style={styles.notice}>
        <Text style={styles.text}>{messageText('support.empty', messageStyle).body}</Text>
      </View>}
      {data.mentees.items.map(row => <View key={row.relationship_id} style={styles.card}>
        <Text style={styles.heading}>@{row.mentee.nickname}</Text>
        <Text selectable style={styles.muted}>{row.mentee.email}</Text>
        <Button title="Календар і статистика" disabled={busy} onPress={() => router.push({
          pathname: '/mentee/[relationship_id]', params: { relationship_id: String(row.relationship_id) },
        })} />
        <Pressable accessibilityRole="button" disabled={busy} style={styles.action} onPress={() => setEnding(row)}>
          <Text style={styles.danger}>Припинити менторство з підопічним</Text>
        </Pressable>
      </View>)}
      {data.mentees.items.length < data.mentees.total && <Button title="Показати ще" loading={busy} onPress={() => { void loadMore(); }} />}
    </>}
  </ScrollView>;
}
