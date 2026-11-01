import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useProfile } from '../../profile/ProfileProvider';
import { useMessageText } from '../../messages/useMessageText';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useProgressStatistics } from '../../progress/useProgressStatistics';
import { theme } from '../../constants/theme';
import { FIXED_GOAL_DAYS, GOAL_LABELS, GOAL_DESCRIPTIONS } from '../../constants/goals';

export default function GoalsScreen() {
  const messageText=useMessageText();
  const { profile } = useProfile();
  const motivation = profile ? messageText('goals.motivation', profile.message_style).body : '';
  const { data, loading, error, reload: loadGoals } = useProgressStatistics();

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

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.highlight} />
          <Text style={styles.muted}>Завантажуємо цілі...</Text>
        </View>
      )}

      {error ? (
        <GlassCard style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити цілі</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={loadGoals}>
            <Text style={styles.retry}>Спробувати ще раз</Text>
          </Pressable>
        </GlassCard>
      ) : null}

      {data && !loading && !error && (
        <>
          {activeGoal !== null ? (
            <GlassCard style={styles.activeCard}>
              <View style={styles.activeBadge}>
                <Text style={styles.activeBadgeText}>ПОТОЧНИЙ ЕТАП</Text>
              </View>
              <Text style={styles.activeTitle}>
                {GOAL_LABELS[activeGoal]} тверезості
              </Text>
              <Text style={styles.activeDescription}>
                {motivation}
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
            </GlassCard>
          ) : (
            <GlassCard style={styles.successCard}>
              <Text style={styles.successIcon}>★</Text>
              <Text style={styles.successTitle}>Усі етапи виконано!</Text>
              <Text style={styles.muted}>
                Ти пройшла всі доступні етапи. Продовжуй рухатися у власному
                темпі.
              </Text>
            </GlassCard>
          )}

          <Text style={styles.sectionTitle}>Етапи твого шляху</Text>

          {FIXED_GOAL_DAYS.map((days) => {
            const isCompleted = completed.includes(days);
            const isActive = activeGoal === days;

            return (
              <GlassCard
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
                  <Text style={styles.goalTitle}>{GOAL_LABELS[days]}</Text>
                  <Text style={styles.goalDescription}>
                    Прогрес: {isCompleted ? days : Math.min(data.current_streak, days)} із {days} днів
                  </Text>
                  <Text style={styles.goalDescription}>
                    {GOAL_DESCRIPTIONS[days]}
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
              </GlassCard>
            );
          })}

          <GlassCard style={styles.infoCard}>
            <Text style={styles.infoTitle}>Пам’ятай</Text>
            <Text style={styles.infoText}>
              Відзнака зберігається після нового зриву. Виправлення минулих записів може змінити рекорд і відзнаки.
            </Text>
          </GlassCard>
          <Text style={styles.muted}>Етапи 7, 30, 90, 180 і 365 днів за безперервною серією.</Text>
          <Text style={styles.muted}>Дні без записів від початку відстеження враховуються як тверезі.</Text>
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
    fontWeight: '500',
    letterSpacing: 1.5,
    color: theme.colors.highlight,
  },
  title: {
    fontSize: 30,
    fontWeight: '400',
    color: theme.colors.text,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: theme.colors.muted,
    marginTop: -10,
  },
  activeCard: { ...theme.effects.card,
    backgroundColor: theme.colors.hero,
    borderRadius: 22,
    padding: 22,
    gap: 13,
  },
  activeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.hero,
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 9,
  },
  activeBadgeText: {
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: '400',
    color: theme.colors.text,
  },
  activeTitle: {
    fontSize: 26,
    fontWeight: '400',
    color: theme.colors.text,
  },
  activeDescription: {
    fontSize: 14,
    color: theme.colors.heroMuted,
    lineHeight: 21,
  },
  progressTrack: {
    height: 9,
    backgroundColor: theme.colors.progressTrack,
    borderRadius: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: theme.colors.highlight,
    borderRadius: 8,
  },
  progressLabel: {
    color: theme.colors.text,
    fontSize: 13,
    fontWeight: '500',
  },
  successCard: { ...theme.effects.card,
    backgroundColor: theme.colors.accent,
    borderRadius: 22,
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  successIcon: {
    fontSize: 36,
    color: theme.colors.text,
  },
  successTitle: {
    fontSize: 22,
    fontWeight: '400',
    color: theme.colors.text,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '400',
    color: theme.colors.text,
  },
  goalCard: { ...theme.effects.card,
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
    borderColor: theme.colors.buttonBorder,
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
    fontWeight: '400',
    color: theme.colors.text,
  },
  goalInfo: {
    flex: 1,
    gap: 5,
  },
  goalTitle: {
    fontSize: 17,
    fontWeight: '400',
    color: theme.colors.text,
  },
  goalDescription: {
    fontSize: 13,
    lineHeight: 19,
    color: theme.colors.muted,
  },
  goalStatus: {
    fontSize: 12,
    fontWeight: '500',
    color: theme.colors.muted,
  },
  activeText: {
    color: theme.colors.highlight,
  },
  completedText: {
    color: theme.colors.text,
  },
  infoCard: { ...theme.effects.card,
    borderRadius: 18,
    padding: 18,
    backgroundColor: theme.colors.accent,
    gap: 8,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '400',
    color: theme.colors.text,
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
  errorBox: { ...theme.effects.card,
    backgroundColor: theme.colors.dangerSurface,
    borderRadius: 15,
    padding: 16,
    gap: 10,
  },
  errorTitle: {
    color: theme.colors.danger,
    fontSize: 16,
    fontWeight: '500',
  },
  errorText: {
    color: theme.colors.danger,
    fontSize: 14,
  },
  retry: {
    color: theme.colors.text,
    fontWeight: '500',
  },
});
