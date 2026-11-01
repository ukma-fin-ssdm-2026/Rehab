import { LotusMark } from '../../components/visual/LotusMark';
import { useUnreadMessages } from '../../messages/useMessages';
import { useProfile } from '../../profile/ProfileProvider';
import { useMessageText } from '../../messages/useMessageText';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { useProgressStatistics } from '../../progress/useProgressStatistics';
import { theme } from '../../constants/theme';
import { FIXED_GOAL_DAYS, GOAL_LABELS } from '../../constants/goals';

export default function HomeScreen() {
  const messageText=useMessageText();
  const unread = useUnreadMessages();
  const { profile } = useProfile();
  const motivation = profile ? messageText('home.motivation', profile.message_style).body : '';
  const { data, loading, error, reload: loadStatistics } = useProgressStatistics();
  const completedGoals = data?.completed_goal_days ?? [];
  const activeGoal = FIXED_GOAL_DAYS.find(days => !completedGoals.includes(days)) ?? null;
  const goalProgress = activeGoal === null ? 0 : Math.min(data?.current_streak ?? 0, activeGoal);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.brandRow}><LotusMark size={26} /><Text style={styles.eyebrow}>ТВІЙ ПРОСТІР</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel={unread.error ? 'Повідомлення. Не вдалося оновити лічильник' : `Повідомлення. Непрочитаних: ${unread.data?.count ?? 'завантаження'}`} onPress={()=>router.push('/messages')}>
          <Text style={styles.retryText}>✉{unread.data ? ` ${unread.data.count}` : unread.error ? ' !' : '…'}</Text>
        </Pressable>
      </View>
      <Text style={styles.title}>{profile && profile.message_style !== 'formal' ? messageText('home.motivation',profile.message_style).title : 'Привіт!'}</Text>
      <Text style={styles.subtitle}>
        {motivation}
      </Text>

      <Text style={styles.muted}>Дні без записів від початку відстеження враховуються як тверезі.</Text>

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.highlight} />
          <Text style={styles.muted}>Завантажуємо твою статистику...</Text>
        </View>
      )}

      {!!error && (
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
            <Text style={styles.goalTitle}>Твій поточний етап</Text>
            {activeGoal === null ? (
              <Text style={styles.goalText}>Усі етапи виконано!</Text>
            ) : (
              <>
                <Text style={styles.goalNumber}>
                  {GOAL_LABELS[activeGoal]}
                </Text>
                <Text style={styles.muted}>
                  Прогрес: {goalProgress} із {activeGoal}
                </Text>
                <View style={styles.progressTrack}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${Math.min(
                          100,
                          (goalProgress / activeGoal) * 100,
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
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerRow: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap'},
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 24,
    paddingTop: 32,
    gap: 18,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 2,
    color: theme.colors.highlight,
  },
  title: {
    fontSize: 32,
    fontWeight: '400',
    color: theme.colors.text,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: theme.colors.muted,
    marginTop: -12,
  },
  hero: {
    backgroundColor: theme.colors.hero,
    borderRadius: 24,
    padding: 24,
    gap: 8,
  },
  heroLabel: {
    fontSize: 15,
    color: theme.colors.heroMuted,
  },
  heroNumber: {
    fontSize: 52,
    fontWeight: '400',
    color: theme.colors.text,
  },
  heroCaption: {
    fontSize: 14,
    color: theme.colors.heroMuted,
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
    color: theme.colors.highlight,
  },
  cardNumber: {
    fontSize: 28,
    fontWeight: '400',
    color: theme.colors.text,
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
    fontWeight: '500',
    color: theme.colors.text,
  },
  goalText: {
  fontSize: 16,
  fontWeight: '500',
  color: theme.colors.highlight,
  },
  goalNumber: {
    fontSize: 25,
    fontWeight: '400',
    color: theme.colors.highlight,
  },
  progressTrack: {
    height: 8,
    backgroundColor: theme.colors.accent,
    borderRadius: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: theme.colors.highlight,
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
    backgroundColor: theme.colors.dangerSurface,
    borderRadius: 16,
    padding: 16,
    gap: 10,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '500',
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
    color: theme.colors.text,
    fontWeight: '500',
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
    fontWeight: '500',
    color: theme.colors.text,
  },
});
