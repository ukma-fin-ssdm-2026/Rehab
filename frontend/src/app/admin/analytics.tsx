// AI-GENERATED START
import { useCallback, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import { useFocusEffect } from 'expo-router';
import {
  fetchOverview, fetchTriggerDistribution,
  type AdminOverview, type TriggerCategory, type TriggerDistribution,
} from '../../api/admin';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';

const LABELS: Record<TriggerCategory, string> = {
  stress: 'Стрес', holiday: 'Свято', social: 'Соціальний тиск', other: 'Інше',
};
// Колір не єдиний носій інформації: легенда завжди показує назву, кількість і відсоток.
const COLORS: Record<TriggerCategory, string> = {
  stress: '#ACB866', holiday: '#C4A6D8', social: '#7FAE9D', other: '#D7A3B4',
};
const SIZE = 220;
const R = 100;
const C = SIZE / 2;

function arcPath(startAngle: number, endAngle: number): string {
  const pt = (a: number) => `${C + R * Math.cos(a)} ${C + R * Math.sin(a)}`;
  const large = endAngle - startAngle > Math.PI ? 1 : 0;
  return `M ${C} ${C} L ${pt(startAngle)} A ${R} ${R} 0 ${large} 1 ${pt(endAngle)} Z`;
}

export default function AdminAnalytics() {
  const [data, setData] = useState<TriggerDistribution | null>(null);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<TriggerCategory | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [counts, chart] = await Promise.all([fetchOverview(), fetchTriggerDistribution()]);
      setOverview(counts);
      setData(chart);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити дані');
    }
  }, []);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  const slices = useMemo(() => {
    if (!data || data.total === 0) return [];
    let angle = -Math.PI / 2;
    return data.categories.filter((c) => c.count > 0).map((c) => {
      const sweep = (c.count / data.total) * 2 * Math.PI;
      const slice = { ...c, start: angle, end: angle + sweep };
      angle += sweep;
      return slice;
    });
  }, [data]);

  if ((!data || !overview) && !error) return <ScreenState state="loading" />;
  if (!data || !overview) {
    return <ScreenState state="error" message={error ?? undefined} onRetry={() => { void load(); }} />;
  }

  const chosen = data.categories.find((c) => c.category === selected);
  const counters = [
    { label: 'Реєстрацій за 30 днів', value: overview.registrations_last_30_days },
    { label: 'Активних менторів', value: overview.active_mentors },
    { label: 'Активних зв\'язків', value: overview.active_relationships },
    { label: 'Скарг на розгляді', value: overview.pending_complaints },
  ];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.counters}>
        {counters.map((c) => (
          <View key={c.label} style={styles.counter}>
            <Text style={styles.counterValue}>{c.value}</Text>
            <Text style={styles.counterLabel}>{c.label}</Text>
          </View>
        ))}
      </View>
      <Text style={styles.note}>Станом на {overview.current_date} (Київ). Без персональних даних.</Text>
      {data.total === 0 ? (
        <ScreenState state="empty" message="За останні 30 днів немає зривів із вказаною категорією." />
      ) : (
      <>
      <Text style={styles.title}>Тригери зривів, {data.period_start} — {data.period_end}</Text>
      <Text style={styles.note}>
        Анонімні дані: лише зриви з вказаною категорією ({data.total}). Відсотки округлено до 0,1,
        тому сума може відрізнятися від 100.
      </Text>
      <Svg width={SIZE} height={SIZE} accessibilityLabel="Кругова діаграма тригерів">
        {slices.length === 1 ? (
          <Circle cx={C} cy={C} r={R} fill={COLORS[slices[0].category]} onPress={() => setSelected(slices[0].category)} />
        ) : (
          slices.map((s) => (
            <Path
              key={s.category}
              d={arcPath(s.start, s.end)}
              fill={COLORS[s.category]}
              stroke={s.category === selected ? theme.colors.text : theme.colors.surface}
              strokeWidth={s.category === selected ? 3 : 1}
              onPress={() => setSelected(s.category)}
            />
          ))
        )}
      </Svg>
      {chosen && (
        <Text style={styles.selected}>
          {LABELS[chosen.category]}: {chosen.count} ({chosen.percentage}%)
        </Text>
      )}
      <View style={styles.legend}>
        {data.categories.map((c) => (
          <Pressable key={c.category} style={styles.row} onPress={() => setSelected(c.category)}>
            <View style={[styles.dot, { backgroundColor: COLORS[c.category] }]} />
            <Text style={styles.rowText}>{LABELS[c.category]} — {c.count} ({c.percentage}%)</Text>
          </Pressable>
        ))}
      </View>
      </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: theme.colors.background, alignItems: 'center', padding: 16, gap: 14 },
  link: { alignSelf: 'flex-start', color: theme.colors.highlight, fontWeight: '500', fontSize: 16 },
  counters: { alignSelf: 'stretch', flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  counter: {
    flexGrow: 1, flexBasis: '45%', backgroundColor: theme.colors.surface, borderColor: theme.colors.border,
    borderWidth: 1, borderRadius: 14, padding: 12, gap: 4,
  },
  counterValue: { color: theme.colors.text, fontSize: 24, fontWeight: '500' },
  counterLabel: { color: theme.colors.muted },
  title: { color: theme.colors.text, fontWeight: '500', fontSize: 16, textAlign: 'center' },
  note: { color: theme.colors.muted, textAlign: 'center' },
  selected: { color: theme.colors.text, fontWeight: '500' },
  legend: { alignSelf: 'stretch', gap: 8 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 44 },
  dot: { width: 16, height: 16, borderRadius: 8 },
  rowText: { color: theme.colors.text },
});
// AI-GENERATED END
