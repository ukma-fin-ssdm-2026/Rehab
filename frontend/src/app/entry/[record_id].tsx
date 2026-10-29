import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { getEntry, updateEntry, type CalendarEntry, type DayStatus, type TriggerCategory } from '../../api/calendar';
import { ApiError } from '../../api/client';
import { canEdit, drinkTypes, triggers } from '../../calendar/rules';
import { StatusFields } from '../../calendar/StatusFields';
import { styles } from '../../calendar/styles';

export default function EntryDetailsScreen() {
  const { record_id } = useLocalSearchParams<{ record_id: string }>();
  const id = Number(record_id);
  const [entry, setEntry] = useState<CalendarEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState<DayStatus>('sober');
  const [trigger, setTrigger] = useState<TriggerCategory | null>(null);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [now, setNow] = useState(() => Date.now());
  const [expired, setExpired] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoading(true); setError(''); setEntry(null); setEditing(false); setExpired(false);
    if (!Number.isSafeInteger(id) || id < 1) {
      setError('Запис не знайдено.'); setLoading(false);
      return () => { active = false; };
    }
    getEntry(id).then(value => {
      if (active) { setEntry(value); setStatus(value.status); setTrigger(value.trigger_category); setNow(Date.now()); }
    }).catch(err => { if (active) setError(err instanceof Error ? err.message : 'Не вдалося завантажити запис.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // attempt changes only when the user explicitly retries loading.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, attempt]));

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const editable = !!entry && !expired && canEdit(entry.created_at, now);

  async function save() {
    if (!entry || savingRef.current || !editable) return;
    savingRef.current = true; setSaving(true); setError('');
    try {
      const value = await updateEntry(entry.record_id, {
        status, trigger_category: status === 'sober' ? null : trigger,
      });
      setEntry(value); setStatus(value.status); setTrigger(value.trigger_category); setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не вдалося зберегти зміни.');
      if (err instanceof ApiError && err.code === 'EDIT_WINDOW_EXPIRED') {
        setExpired(true); setEditing(false); setNow(Date.now());
      }
    } finally { savingRef.current = false; setSaving(false); }
  }

  return <ScrollView contentContainerStyle={styles.container}>
    <Pressable disabled={saving} onPress={() => router.replace('/(tabs)/calendar')}>
      <Text style={styles.back}>← Календар</Text>
    </Pressable>
    <Text style={styles.title}>Деталі запису</Text>
    {loading && <ActivityIndicator accessibilityLabel="Завантаження запису" />}
    {!!error && <View style={styles.errorBox}><Text accessibilityRole="alert" style={styles.errorText}>{error}</Text>
      {!entry && <Pressable onPress={() => setAttempt(value => value + 1)}><Text>Спробувати ще раз</Text></Pressable>}
    </View>}
    {entry && !loading && <>
      <View style={styles.card}>
        <Text style={styles.label}>Дата: {entry.date}</Text>
        <Text>Статус: {entry.status === 'sober' ? 'Тверезість' : 'Зрив'}</Text>
        <Text>Тригер: {triggers.find(item => item.value === entry.trigger_category)?.label ?? 'Не вказано'}</Text>
        <Text style={styles.label}>Напої</Text>
        {entry.drinks.length ? entry.drinks.map((drink, index) => <Text key={index}>
          {drinkTypes.find(item => item.value === drink.type)?.label ?? drink.type}: {drink.volume_ml} мл
        </Text>) : <Text>Не вказано</Text>}
        <Text style={styles.label}>Коментар</Text>
        <Text>{entry.comment || 'Не вказано'}</Text>
        <Text style={styles.hint}>Збережений запис. Створено: {new Date(entry.created_at).toLocaleString('uk-UA', { timeZone: 'Europe/Kyiv' })} (Київ).</Text>
      </View>
      {editing && <>
        <StatusFields status={status} trigger={trigger} disabled={saving || !editable}
          onStatus={setStatus} onTrigger={setTrigger} />
        <Text style={styles.hint}>Можна змінити лише статус і тригер. Дата, напої та коментар не редагуються.
          Перехід на тверезість видалить напої й тригер. Для зриву напої необов’язкові.</Text>
        <Pressable onPress={save} disabled={saving || !editable}
          style={[styles.button, (saving || !editable) && styles.buttonDisabled]}>
          {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Зберегти зміни</Text>}
        </Pressable>
        <Pressable disabled={saving} onPress={() => {
          setEditing(false); setStatus(entry.status); setTrigger(entry.trigger_category); setError('');
        }}><Text style={styles.cancelText}>Скасувати редагування</Text></Pressable>
      </>}
      {!editing && <Pressable disabled={!editable} onPress={() => setEditing(true)}
        style={[styles.button, !editable && styles.buttonDisabled]}>
        <Text style={styles.buttonText}>Редагувати запис</Text>
      </Pressable>}
      <Text style={styles.hint}>{editable ? 'Редагування доступне протягом 48 годин від створення запису.'
        : 'Час на редагування минув: дозволено лише протягом 48 годин від створення.'}</Text>
    </>}
  </ScrollView>;
}
