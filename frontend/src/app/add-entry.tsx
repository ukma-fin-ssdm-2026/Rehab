import { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { getMyAccount, type UserSession } from '../api/auth';
import { createEntry, type DayStatus, type TriggerCategory } from '../api/calendar';
import { drinkTypes, entryPayload, type DraftDrink } from '../calendar/rules';
import { StatusFields } from '../calendar/StatusFields';
import { styles } from '../calendar/styles';

export default function AddEntryScreen() {
  const params = useLocalSearchParams<{ date?: string }>();
  const [date, setDate] = useState(typeof params.date === 'string' ? params.date : '');
  const [account, setAccount] = useState<UserSession | null>(null);
  const [status, setStatus] = useState<DayStatus>('sober');
  const [trigger, setTrigger] = useState<TriggerCategory | null>(null);
  const [drinks, setDrinks] = useState<DraftDrink[]>([]);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [attempt, setAttempt] = useState(0);

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoading(true);
    setError('');
    getMyAccount().then(user => {
      if (active) { setAccount(user); setDate(value => value || user.current_date); }
    }).catch(err => { if (active) { setAccount(null); setError(err instanceof Error ? err.message : 'Не вдалося завантажити дані.'); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // attempt changes only when the user explicitly retries loading.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt]));

  const back = () => router.replace('/(tabs)/calendar');
  async function save() {
    if (savingRef.current || !account) return;
    setError('');
    savingRef.current = true;
    setSaving(true);
    try {
      const current = await getMyAccount();
      setAccount(current);
      const payload = entryPayload({ date, status, trigger_category: trigger, drinks, comment },
        current.tracking_start_date, current.current_date);
      const entry = await createEntry(payload);
      router.replace({ pathname: '/entry/[record_id]', params: { record_id: entry.record_id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не вдалося зберегти запис.');
    } finally { savingRef.current = false; setSaving(false); }
  }

  return <ScrollView contentContainerStyle={styles.container}>
    <Text style={styles.title}>Новий запис</Text>
    {loading && <ActivityIndicator accessibilityLabel="Завантаження" />}
    {account && !loading && <>
      <View style={styles.card}>
        <Text style={styles.label}>Дата</Text>
        <TextInput accessibilityLabel="Дата запису" value={date} onChangeText={setDate} editable={!saving}
          placeholder="РРРР-ММ-ДД" style={styles.input} maxLength={10} autoCapitalize="none" />
        <Text style={styles.hint}>Від {account.tracking_start_date} до {account.current_date} включно.</Text>
      </View>
      <StatusFields status={status} trigger={trigger} disabled={saving} onStatus={setStatus} onTrigger={setTrigger} />
      {status === 'relapse' && <>
        <View style={styles.sectionHeader}>
          <Text style={styles.label}>Напої (необов’язково)</Text>
          <Pressable disabled={saving} style={styles.addSmall} onPress={() => setDrinks(items => [...items,
            { id: Date.now(), type: 'beer', volume: '' }])}><Text style={styles.addSmallText}>＋ Додати напій</Text></Pressable>
        </View>
        {drinks.map((drink, index) => <View style={styles.card} key={drink.id}>
          <Text style={styles.label}>Напій {index + 1}</Text>
          <Pressable disabled={saving} accessibilityLabel={`Видалити напій ${index + 1}`}
            onPress={() => setDrinks(items => items.filter(item => item.id !== drink.id))}><Text style={styles.removeText}>Видалити</Text></Pressable>
          <View style={styles.typeList}>{drinkTypes.map(item => <Pressable key={item.value} disabled={saving}
            accessibilityRole="radio" accessibilityState={{ checked: drink.type === item.value }}
            style={[styles.typeOption, drink.type === item.value && styles.typeActive]}
            onPress={() => setDrinks(items => items.map(value => value.id === drink.id ? { ...value, type: item.value } : value))}>
            <Text style={styles.typeText}>{item.label}</Text>
          </Pressable>)}</View>
          <TextInput accessibilityLabel={`Об’єм напою ${index + 1} (мл)`} placeholder="Об’єм (мл)"
            keyboardType="number-pad" value={drink.volume} editable={!saving} style={styles.input}
            onChangeText={volume => setDrinks(items => items.map(item => item.id === drink.id ? { ...item, volume } : item))} />
        </View>)}
      </>}
      <View style={styles.card}><Text style={styles.label}>Коментар (необов’язково)</Text>
        <TextInput accessibilityLabel="Коментар" value={comment} onChangeText={setComment} editable={!saving}
          placeholder="Що хочеш зафіксувати?" multiline maxLength={2000} style={styles.commentInput} />
        <Text style={styles.hint}>До 2000 символів.</Text>
      </View>
    </>}
    {!!error && <View style={styles.errorBox}><Text accessibilityRole="alert" style={styles.errorText}>{error}</Text>
      {!account && <Pressable onPress={() => setAttempt(value => value + 1)}><Text>Спробувати ще раз</Text></Pressable>}
    </View>}
    <Pressable disabled={saving || loading || !account} onPress={save}
      style={[styles.button, (saving || loading || !account) && styles.buttonDisabled]}>
      {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Зберегти запис</Text>}
    </Pressable>
    <Pressable disabled={saving} onPress={back}><Text style={styles.cancelText}>Скасувати</Text></Pressable>
  </ScrollView>;
}
