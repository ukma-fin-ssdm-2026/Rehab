import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import type { StatisticsPeriod } from '../api/statistics';
import { dayStatus, drinkTypes, shiftedMonth, triggers } from '../calendar/rules';
import { ScreenState } from '../components/ui/ScreenState';
import { theme } from '../constants/theme';
import { calendarMonth } from './calendar';
import { styles } from './styles';
import { useMenteeData } from './useMenteeData';

const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];
const periods: { value: StatisticsPeriod; label: string }[] = [
  { value: 'all', label: 'Увесь час' }, { value: 'week', label: 'Тиждень' },
  { value: 'month', label: 'Місяць' }, { value: 'year', label: 'Рік' },
];

export default function MenteeScreen() {
  const params = useLocalSearchParams<{ relationship_id?: string | string[] }>();
  const raw = params.relationship_id;
  const candidate = typeof raw === 'string' && /^[1-9]\d*$/.test(raw) ? Number(raw) : NaN;
  const id = Number.isSafeInteger(candidate) ? candidate : null;
  const [monthKey, setMonthKey] = useState<string | null>(null);
  const [period, setPeriod] = useState<StatisticsPeriod>('all');
  const [tab, setTab] = useState<'calendar' | 'statistics'>('calendar');
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const { data, loading, error, reload } = useMenteeData(id, monthKey, period);
  const month = data ? data.monthKey.split('-').map(Number) : null;
  const range = month ? calendarMonth(month[0], month[1] - 1) : null;
  const stats = data?.statistics;
  const today = stats?.period_end ?? '';
  const selected = selectedDate ?? (data?.monthKey === today.slice(0, 7) ? today : range?.from ?? '');
  const byDate = new Map(data?.entries.items.map(entry => [entry.date, entry]));
  const record = byDate.get(selected);
  const selectedStatus = stats ? dayStatus(selected, record, stats.tracking_start_date, today) : 'empty';

  function changeMonth(offset: number) {
    if (!month) return;
    const next = shiftedMonth(month[0], month[1] - 1, offset);
    setMonthKey(next.selectedDate.slice(0, 7)); setSelectedDate(null);
  }

  return <ScrollView contentContainerStyle={styles.container}>
    <Pressable accessibilityRole="button" style={styles.action} onPress={() => router.replace('/(tabs)/friends-support')}>
      <Text style={styles.link}>‹ До підтримки</Text>
    </Pressable>
    <Text style={styles.title}>Дані підопічного</Text>
    {loading && <ScreenState state="loading" />}
    {!!error && <ScreenState state="error" message={error} onRetry={() => { void reload(); }} />}
    {data && stats && month && range && <>
      <View style={styles.card}>
        <Text style={styles.heading}>@{data.relationship.mentee.nickname}</Text>
        <Text selectable style={styles.muted}>{data.relationship.mentee.email}</Text>
        <Text style={styles.muted}>Тільки перегляд. Змінювати календарні записи може лише власник.</Text>
      </View>
      <View style={styles.segmented}>
        {(['calendar', 'statistics'] as const).map(value => <Pressable key={value} accessibilityRole="button"
          accessibilityState={{ selected: tab === value }} onPress={() => setTab(value)}
          style={[styles.segment, tab === value && styles.selected]}>
          <Text style={styles.link}>{value === 'calendar' ? 'Календар' : 'Статистика'}</Text>
        </Pressable>)}
      </View>
      {tab === 'calendar' ? <>
        <View style={styles.row}>
          <Pressable accessibilityRole="button" accessibilityLabel="Попередній місяць"
            disabled={data.monthKey <= stats.tracking_start_date.slice(0, 7)} onPress={() => changeMonth(-1)}
            style={[local.monthButton, data.monthKey <= stats.tracking_start_date.slice(0, 7) && styles.disabled]}><Text style={styles.heading}>‹</Text></Pressable>
          <Text style={[styles.text, local.monthTitle]}>{new Date(month[0], month[1] - 1, 1).toLocaleDateString('uk-UA', { month: 'long', year: 'numeric' })}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Наступний місяць"
            disabled={data.monthKey >= today.slice(0, 7)} onPress={() => changeMonth(1)}
            style={[local.monthButton, data.monthKey >= today.slice(0, 7) && styles.disabled]}><Text style={styles.heading}>›</Text></Pressable>
        </View>
        <View style={styles.card}>
          <View style={local.grid}>{weekdays.map(day => <View key={day} style={local.cell}><Text style={styles.muted}>{day}</Text></View>)}</View>
          <View style={local.grid}>{range.days.map((date, index) => {
            if (!date) return <View key={`empty-${index}`} style={local.cell} />;
            const status = dayStatus(date, byDate.get(date), stats.tracking_start_date, today);
            return <View key={date} style={local.cell}>
              <Pressable accessibilityRole="button" accessibilityLabel={`${date}, ${status === 'sober' ? 'тверезий день' : status === 'relapse' ? 'зрив' : 'поза періодом відстеження'}`}
                disabled={status === 'empty'} onPress={() => setSelectedDate(date)}
                style={[local.day, status === 'sober' && local.sober, status === 'relapse' && local.relapse,
                  selected === date && local.selectedDay, status === 'empty' && styles.disabled]}>
                <Text style={local.dayText}>{Number(date.slice(-2))}</Text>
              </Pressable>
            </View>;
          })}</View>
          <Text style={styles.muted}>Зелений — тверезість · рожевий — зрив.</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.heading}>{selected}</Text>
          <Text style={styles.text}>{selectedStatus === 'relapse' ? 'Зрив' : selectedStatus === 'sober' ? 'Тверезий день' : 'Поза періодом відстеження'}</Text>
          {record ? <>
            <Text style={styles.text}>Тригер: {triggers.find(item => item.value === record.trigger_category)?.label ?? 'Не вказано'}</Text>
            <Text style={styles.heading}>Напої</Text>
            {record.drinks.length ? record.drinks.map((drink, index) => <Text key={index} style={styles.text}>
              {drinkTypes.find(item => item.value === drink.type)?.label ?? drink.type}: {drink.volume_ml} мл
            </Text>) : <Text style={styles.muted}>Не вказано</Text>}
            <Text style={styles.heading}>Коментар до запису</Text>
            <Text selectable style={styles.text}>{record.comment || 'Не вказано'}</Text>
          </> : <Text style={styles.muted}>{selectedStatus === 'sober'
            ? 'Запису немає. За замовчуванням день вважається тверезим.' : 'Для цієї дати немає даних.'}</Text>}
        </View>
      </> : <>
        <View style={styles.segmented}>{periods.map(item => <Pressable key={item.value} accessibilityRole="button"
          accessibilityState={{ selected: period === item.value }} style={[styles.segment, period === item.value && styles.selected]}
          onPress={() => setPeriod(item.value)}><Text style={styles.link}>{item.label}</Text></Pressable>)}</View>
        <Text style={styles.muted}>Період: {stats.period_start} — {stats.period_end}</Text>
        <View style={local.metrics}>
          {[['Поточна серія', stats.current_streak], ['Найкраща серія', stats.longest_streak],
            ['Тверезі дні за період', stats.sober_days], ['Дні зриву за період', stats.relapse_days],
            ['Тверезі дні за весь час', stats.total_sober_days]].map(([label, value]) => <View key={label} style={[styles.card, local.metric]}>
            <Text style={styles.muted}>{label}</Text><Text style={styles.title}>{value}</Text>
          </View>)}
        </View>
      </>}
    </>}
  </ScrollView>;
}

const local = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: { width: '14.2857%', padding: 2, alignItems: 'center', justifyContent: 'center', minHeight: 35 },
  day: { alignSelf: 'stretch', minHeight: 44, borderWidth: 2, borderColor: 'transparent', borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  dayText: { color: theme.colors.primaryDark, fontSize: 14, fontWeight: '600' },
  sober: { backgroundColor: theme.colors.accent }, relapse: { backgroundColor: '#F9DDDF' },
  selectedDay: { borderColor: theme.colors.primaryDark },
  monthTitle: { flex: 1, textAlign: 'center', fontWeight: '700' },
  monthButton: { width: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  metric: { flexGrow: 1, flexBasis: '45%', minWidth: 130 },
});
