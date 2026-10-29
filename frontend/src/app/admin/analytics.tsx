// AI-GENERATED START
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import { fetchTriggerDistribution, type TriggerCategory, type TriggerDistribution } from '../../api/admin';
import { ScreenState } from '../../components/ui/ScreenState';
import { theme } from '../../constants/theme';

const LABELS: Record<TriggerCategory, string> = {
  stress: 'Стрес', holiday: 'Свято', social: 'Соціальний тиск', other: 'Інше',
};
// Колір не єдиний носій інформації: легенда завжди показує назву, кількість і відсоток.
const COLORS: Record<TriggerCategory, string> = {
  stress: '#3C8D72', holiday: '#E0A23B', social: '#5B7DB1', other: '#9A8C98',
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
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<TriggerCategory | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await fetchTriggerDistribution());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не вдалося завантажити дані');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

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

  if (!data && !error) return <ScreenState state="loading" />;
  if (!data) return <ScreenState state="error" message={error ?? undefined} onRetry={() => { void load(); }} />;
  if (data.total === 0) {
    return <ScreenState state="empty" message="За останні 30 днів немає зривів із вказаною категорією." />;
  }

  const chosen = data.categories.find((c) => c.category === selected);

  return (
    <ScrollView contentContainerStyle={styles.container}>
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
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', padding: 16, gap: 14 },
  title: { color: theme.colors.text, fontWeight: '700', fontSize: 16, textAlign: 'center' },
  note: { color: theme.colors.muted, textAlign: 'center' },
  selected: { color: theme.colors.primaryDark, fontWeight: '700' },
  legend: { alignSelf: 'stretch', gap: 8 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 44 },
  dot: { width: 16, height: 16, borderRadius: 8 },
  rowText: { color: theme.colors.text },
});
// AI-GENERATED END
