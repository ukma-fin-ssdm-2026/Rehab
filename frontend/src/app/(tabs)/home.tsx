
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { apiRequest } from '../../api/client';
import { theme } from '../../constants/theme';

type Statistics = {
  total_sober_days: number;
  current_streak: number;
  longest_streak: number;
  active_goal_days: number | null;
  goal_progress_days: number;
};

export default function HomeScreen() {
  const [data, setData] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatistics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      setData(await apiRequest<Statistics>('/statistics?period=all'));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Не вдалося завантажити статистику',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStatistics();
  }, [loadStatistics]);

  useFocusEffect(
    useCallback(() => {
      void loadStatistics();
    }, [loadStatistics]),
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТВІЙ ПРОСТІР</Text>
      <Text style={styles.title}>Привіт!</Text>
      <Text style={styles.subtitle}>
        Кожен день — це твій власний крок уперед.
      </Text>

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.muted}>Завантажуємо твою статистику...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити дані</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable style={styles.retry} onPress={loadStatistics}>
            <Text style={styles.retryText}>Спробувати ще раз</Text>
          </Pressable>
        </View>
      )}

      {data && !loading && !error && (
        <>
          <View style={styles.hero}>
            <Text style={styles.heroLabel}>Усього тверезих днів</Text>
            <Text style={styles.heroNumber}>{data.total_sober_days}</Text>
            <Text style={styles.heroCaption}>Твій прогрес має значення</Text>
          </View>

          <View style={styles.grid}>
            <View style={styles.card}>
              <Text style={styles.cardIcon}>↗</Text>
              <Text style={styles.cardNumber}>{data.current_streak}</Text>
              <Text style={styles.cardLabel}>Поточна серія</Text>
            </View>
            <View style={styles.card}>
              <Text style={styles.cardIcon}>★</Text>
              <Text style={styles.cardNumber}>{data.longest_streak}</Text>
              <Text style={styles.cardLabel}>Найкраща серія</Text>
            </View>
          </View>

          <View style={styles.goalCard}>
            <Text style={styles.goalTitle}>Твоя поточна ціль</Text>
            {data.active_goal_days == null ? (
              <Text style={styles.goalText}>Усі цілі виконано!</Text>
            ) : (
              <>
                <Text style={styles.goalNumber}>
                  {data.active_goal_days} днів
                </Text>
                <Text style={styles.muted}>
                  Прогрес: {data.goal_progress_days} із {data.active_goal_days}
                </Text>
                <View style={styles.progressTrack}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${Math.min(
                          100,
                          (data.goal_progress_days / data.active_goal_days) * 100,
                        )}%`,
                      },
                    ]}
                  />
                </View>
              </>
            )}
          </View>
        </>
      )}

      <Pressable
        style={styles.button}
        onPress={() => router.push('/add-entry')}
      >
        <Text style={styles.buttonText}>＋  Додати запис</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 24,
    paddingTop: 32,
    gap: 18,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 2,
    color: theme.colors.primary,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: theme.colors.muted,
    marginTop: -12,
  },
  hero: {
    backgroundColor: theme.colors.primaryDark,
    borderRadius: 24,
    padding: 24,
    gap: 8,
  },
  heroLabel: {
    fontSize: 15,
    color: '#E1F1E7',
  },
  heroNumber: {
    fontSize: 52,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  heroCaption: {
    fontSize: 14,
    color: '#E1F1E7',
  },
  grid: {
    flexDirection: 'row',
    gap: 12,
  },
  card: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 20,
    padding: 18,
    gap: 8,
  },
  cardIcon: {
    fontSize: 24,
    color: theme.colors.primary,
  },
  cardNumber: {
    fontSize: 28,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  cardLabel: {
    fontSize: 13,
    color: theme.colors.muted,
  },
  goalCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 20,
    gap: 10,
  },
  goalTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.text,
  },
  goalText: {
  fontSize: 16,
  fontWeight: '600',
  color: theme.colors.primary,
  },
  goalNumber: {
    fontSize: 25,
    fontWeight: '800',
    color: theme.colors.primary,
  },
  progressTrack: {
    height: 8,
    backgroundColor: theme.colors.accent,
    borderRadius: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: theme.colors.primary,
    borderRadius: 8,
  },
  muted: {
    fontSize: 14,
    color: theme.colors.muted,
  },
  message: {
    alignItems: 'center',
    padding: 24,
    gap: 12,
  },
  errorBox: {
    backgroundColor: '#FDECEC',
    borderRadius: 16,
    padding: 16,
    gap: 10,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.danger,
  },
  errorText: {
    color: theme.colors.danger,
  },
  retry: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
  },
  retryText: {
    color: theme.colors.primaryDark,
    fontWeight: '700',
  },
  button: {
    backgroundColor: theme.colors.primary,
    borderRadius: 16,
    alignItems: 'center',
    padding: 17,
    marginTop: 2,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
