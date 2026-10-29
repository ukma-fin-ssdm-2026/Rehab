
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { apiRequest } from '../../api/client';
import { theme } from '../../constants/theme';

type Period = 'week' | 'month' | 'year';

type Statistics = {
  sober_days: number;
  relapse_days: number;
  period_start: string;
  period_end: string;
  current_streak: number;
  longest_streak: number;
};

const periods: { label: string; value: Period }[] = [
  { label: 'Тиждень', value: 'week' },
  { label: 'Місяць', value: 'month' },
  { label: 'Рік', value: 'year' },
];

export default function StatisticsScreen() {
  const [period, setPeriod] = useState<Period>('week');
  const [data, setData] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadStatistics = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      setData(await apiRequest<Statistics>(`/statistics?period=${period}`));
    } catch (err) {
      setData(null);
      setError(
        err instanceof Error ? err.message : 'Не вдалося завантажити статистику',
      );
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void loadStatistics();
  }, [loadStatistics]);

  const maxDays = Math.max(
    data?.sober_days ?? 0,
    data?.relapse_days ?? 0,
    1,
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТВОЯ ДИНАМІКА</Text>
      <Text style={styles.title}>Статистика</Text>
      <Text style={styles.subtitle}>
        Подивись на свій шлях за обраний період.
      </Text>

      <View style={styles.periods}>
        {periods.map((item) => {
          const active = period === item.value;
          return (
            <Pressable
              key={item.value}
              onPress={() => setPeriod(item.value)}
              style={[styles.periodButton, active && styles.periodActive]}
            >
              <Text
                style={[styles.periodText, active && styles.periodTextActive]}
              >
                {item.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.muted}>Завантаження статистики...</Text>
        </View>
      )}

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити дані</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={loadStatistics}>
            <Text style={styles.retry}>Спробувати ще раз</Text>
          </Pressable>
        </View>
      ) : null}

      {data && !loading && !error && (
        <>
          <View style={styles.summary}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNumber}>{data.sober_days}</Text>
              <Text style={styles.summaryLabel}>Тверезих днів</Text>
            </View>
            <View style={styles.separator} />
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryNumber, styles.relapseNumber]}>
                {data.relapse_days}
              </Text>
              <Text style={styles.summaryLabel}>Днів зі зривом</Text>
            </View>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Порівняння днів</Text>
            <Text style={styles.muted}>
              Дані за період: {data.period_start} — {data.period_end}
            </Text>

            <View style={styles.chart}>
              <View style={styles.barGroup}>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.bar,
                      styles.soberBar,
                      {
                        height: `${(data.sober_days / maxDays) * 100}%`,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.barValue}>{data.sober_days}</Text>
                <Text style={styles.barLabel}>Тверезі</Text>
              </View>

              <View style={styles.barGroup}>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.bar,
                      styles.relapseBar,
                      {
                        height: `${(data.relapse_days / maxDays) * 100}%`,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.barValue}>{data.relapse_days}</Text>
                <Text style={styles.barLabel}>Зриви</Text>
              </View>
            </View>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Серії тверезості</Text>
            <View style={styles.streakRow}>
              <Text style={styles.streakLabel}>Поточна серія</Text>
              <Text style={styles.streakValue}>{data.current_streak} дн.</Text>
            </View>
            <View style={styles.streakRow}>
              <Text style={styles.streakLabel}>Найдовша серія</Text>
              <Text style={styles.streakValue}>{data.longest_streak} дн.</Text>
            </View>
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 22,
    paddingTop: 32,
    gap: 18,
    backgroundColor: theme.colors.background,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
    color: theme.colors.primary,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: theme.colors.muted,
    marginTop: -10,
  },
  periods: {
    flexDirection: 'row',
    gap: 8,
    padding: 5,
    borderRadius: 15,
    backgroundColor: theme.colors.accent,
  },
  periodButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 11,
  },
  periodActive: {
    backgroundColor: theme.colors.surface,
  },
  periodText: {
    fontSize: 13,
    color: theme.colors.muted,
    fontWeight: '600',
  },
  periodTextActive: {
    color: theme.colors.primaryDark,
    fontWeight: '800',
  },
  summary: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 20,
    alignItems: 'center',
  },
  summaryItem: {
    flex: 1,
    gap: 6,
  },
  summaryNumber: {
    fontSize: 34,
    fontWeight: '800',
    color: theme.colors.primary,
  },
  relapseNumber: {
    color: theme.colors.danger,
  },
  summaryLabel: {
    fontSize: 13,
    color: theme.colors.muted,
  },
  separator: {
    width: 1,
    height: 50,
    backgroundColor: theme.colors.border,
    marginHorizontal: 14,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 20,
    padding: 19,
    gap: 14,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  muted: {
    fontSize: 13,
    color: theme.colors.muted,
    lineHeight: 19,
  },
  chart: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    gap: 30,
    paddingTop: 10,
  },
  barGroup: {
    alignItems: 'center',
    width: 85,
    gap: 7,
  },
  barTrack: {
    height: 150,
    width: 42,
    borderRadius: 12,
    backgroundColor: theme.colors.background,
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  bar: {
    width: '100%',
    minHeight: 0,
    borderRadius: 12,
  },
  soberBar: {
    backgroundColor: theme.colors.primary,
  },
  relapseBar: {
    backgroundColor: theme.colors.danger,
  },
  barValue: {
    fontWeight: '800',
    color: theme.colors.text,
  },
  barLabel: {
    fontSize: 12,
    color: theme.colors.muted,
  },
  streakRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 5,
  },
  streakLabel: {
    color: theme.colors.muted,
    fontSize: 14,
  },
  streakValue: {
    color: theme.colors.primaryDark,
    fontSize: 16,
    fontWeight: '800',
  },
  message: {
    alignItems: 'center',
    padding: 24,
    gap: 12,
  },
  errorBox: {
    backgroundColor: '#FDECEC',
    borderRadius: 15,
    padding: 16,
    gap: 10,
  },
  errorTitle: {
    color: theme.colors.danger,
    fontSize: 16,
    fontWeight: '700',
  },
  errorText: {
    color: theme.colors.danger,
    fontSize: 14,
  },
  retry: {
    color: theme.colors.primaryDark,
    fontWeight: '700',
  },
});
