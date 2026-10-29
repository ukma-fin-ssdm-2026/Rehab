
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { getStatisticsUrl } from '../../config/api';
import { theme } from '../../constants/theme';
import { FIXED_GOAL_DAYS } from '../../constants/goals';

type Statistics = {
  active_goal_days: number | null;
  completed_goal_days: number[];
  current_streak: number;
  goal_progress_days: number;
  total_sober_days: number;
};

export default function GoalsScreen() {
  const [data, setData] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadGoals = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(getStatisticsUrl('all'), {
        headers: { Authorization: 'Bearer user-42' },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      setData(await response.json());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Не вдалося завантажити цілі',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGoals();
  }, [loadGoals]);

  const completed = data?.completed_goal_days ?? [];
  const activeGoal =
    FIXED_GOAL_DAYS.find((days) => !completed.includes(days)) ?? null;
  const progress = activeGoal === null
    ? 0
    : Math.min(data?.current_streak ?? 0, activeGoal);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>МАЛЕНЬКІ КРОКИ</Text>
      <Text style={styles.title}>Мої цілі</Text>
      <Text style={styles.subtitle}>
        Не потрібно робити все одразу. Рухайся у власному темпі.
      </Text>

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.muted}>Завантажуємо цілі...</Text>
        </View>
      )}

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити цілі</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={loadGoals}>
            <Text style={styles.retry}>Спробувати ще раз</Text>
          </Pressable>
        </View>
      ) : null}

      {data && !loading && !error && (
        <>
          {activeGoal !== null ? (
            <View style={styles.activeCard}>
              <View style={styles.activeBadge}>
                <Text style={styles.activeBadgeText}>ПОТОЧНИЙ ЕТАП</Text>
              </View>
              <Text style={styles.activeTitle}>
                {activeGoal} днів тверезості
              </Text>
              <Text style={styles.activeDescription}>
                Рухайся до наступного етапу один день за раз.
              </Text>
              <View style={styles.progressTrack}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(
                        100,
                        (progress / activeGoal) * 100,
                      )}%`,
                    },
                  ]}
                />
              </View>
              <Text style={styles.progressLabel}>
                {progress} із {activeGoal} днів
              </Text>
            </View>
          ) : (
            <View style={styles.successCard}>
              <Text style={styles.successIcon}>★</Text>
              <Text style={styles.successTitle}>Усі етапи виконано!</Text>
              <Text style={styles.muted}>
                Ти пройшла всі доступні етапи. Продовжуй рухатися у власному
                темпі.
              </Text>
            </View>
          )}

          <Text style={styles.sectionTitle}>Етапи твого шляху</Text>

          {FIXED_GOAL_DAYS.map((days) => {
            const isCompleted = completed.includes(days);
            const isActive = activeGoal === days;

            return (
              <View
                key={days}
                style={[
                  styles.goalCard,
                  isActive && styles.goalCardActive,
                  isCompleted && styles.goalCardCompleted,
                ]}
              >
                <View style={styles.goalIcon}>
                  <Text style={styles.goalIconText}>
                    {isCompleted ? '✓' : isActive ? '↗' : '○'}
                  </Text>
                </View>
                <View style={styles.goalInfo}>
                  <Text style={styles.goalTitle}>{days} днів</Text>
                  <Text style={styles.goalDescription}>
                    {days === 7
                      ? 'Перший тиждень твого шляху'
                      : 'Місяць послідовності та турботи про себе'}
                  </Text>
                  <Text
                    style={[
                      styles.goalStatus,
                      isCompleted && styles.completedText,
                      isActive && styles.activeText,
                    ]}
                  >
                    {isCompleted
                      ? 'Виконано'
                      : isActive
                        ? 'Поточний етап'
                        : 'Наступний етап'}
                  </Text>
                </View>
              </View>
            );
          })}

          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Пам’ятай</Text>
            <Text style={styles.infoText}>
              Твій прогрес — це не змагання. Навіть маленькі кроки мають
              значення.
            </Text>
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 22,
    paddingTop: 32,
    gap: 18,
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
  activeCard: {
    backgroundColor: theme.colors.primaryDark,
    borderRadius: 22,
    padding: 22,
    gap: 13,
  },
  activeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#477C66',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 9,
  },
  activeBadgeText: {
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  activeTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  activeDescription: {
    fontSize: 14,
    color: '#E1F1E7',
    lineHeight: 21,
  },
  progressTrack: {
    height: 9,
    backgroundColor: '#628A78',
    borderRadius: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
  },
  progressLabel: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  successCard: {
    backgroundColor: theme.colors.accent,
    borderRadius: 22,
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  successIcon: {
    fontSize: 36,
    color: theme.colors.primaryDark,
  },
  successTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  goalCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 18,
    padding: 17,
  },
  goalCardActive: {
    borderColor: theme.colors.primary,
    borderWidth: 2,
  },
  goalCardCompleted: {
    opacity: 0.65,
  },
  goalIcon: {
    width: 44,
    height: 44,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.accent,
  },
  goalIconText: {
    fontSize: 23,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  goalInfo: {
    flex: 1,
    gap: 5,
  },
  goalTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: theme.colors.text,
  },
  goalDescription: {
    fontSize: 13,
    lineHeight: 19,
    color: theme.colors.muted,
  },
  goalStatus: {
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.muted,
  },
  activeText: {
    color: theme.colors.primary,
  },
  completedText: {
    color: theme.colors.primaryDark,
  },
  infoCard: {
    borderRadius: 18,
    padding: 18,
    backgroundColor: theme.colors.accent,
    gap: 8,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 21,
    color: theme.colors.text,
  },
  muted: {
    color: theme.colors.muted,
    fontSize: 14,
    lineHeight: 21,
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
