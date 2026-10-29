
import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { getMyAccount } from '../../api/auth';
import { listEntries, type CalendarEntry } from '../../api/calendar';
import { dayStatus, kyivDate, shiftedMonth, triggers } from '../../calendar/rules';
import { theme } from '../../constants/theme';

const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];

function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getMonthDays(year: number, month: number): (string | null)[] {
  const firstDay = new Date(year, month, 1);
  const offset = (firstDay.getDay() + 6) % 7;
  const count = new Date(year, month + 1, 0).getDate();
  const days: (string | null)[] = Array(offset).fill(null);

  for (let day = 1; day <= count; day++) {
    days.push(formatDate(new Date(year, month, day)));
  }

  while (days.length % 7 !== 0) {
    days.push(null);
  }

  return days;
}

export default function CalendarScreen() {
  const [today, setToday] = useState(kyivDate());
  const [monthDate, setMonthDate] = useState(
    () => new Date(Number(today.slice(0, 4)), Number(today.slice(5, 7)) - 1, 1),
  );
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [trackingStart, setTrackingStart] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(today);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const monthStart = formatDate(new Date(year, month, 1));
  const monthEnd = formatDate(new Date(year, month + 1, 0));
  const monthDays = getMonthDays(year, month);

  const [attempt, setAttempt] = useState(0);
  useFocusEffect(useCallback(() => {
    let active = true;
    setLoading(true); setError(null); setEntries([]); setTrackingStart(null); setTotal(0);
    Promise.all([listEntries(monthStart, monthEnd), getMyAccount()]).then(([result, account]) => {
      if (active) {
        setEntries(result.items); setTotal(result.total); setTrackingStart(account.tracking_start_date);
        setToday(account.current_date);
      }
    }).catch(err => {
      if (active) setError(err instanceof Error ? err.message : 'Не вдалося завантажити календар');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // attempt changes only when the user explicitly retries loading.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthStart, monthEnd, attempt]));

  const entryByDate = new Map(entries.map(entry => [entry.date, entry]));
  const selectedEntry = entryByDate.get(selectedDate);
  const available = !loading && !error && trackingStart !== null;
  const mayCreate = available && selectedDate >= trackingStart! && selectedDate <= today;
  function getDayStatus(date: string) {
    return available ? dayStatus(date, entryByDate.get(date), trackingStart, today) : 'empty';
  }

  function changeMonth(offset: number) {
    const next = shiftedMonth(year, month, offset);
    setMonthDate(next.value);
    setSelectedDate(next.selectedDate);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Календар</Text>
      <Text style={styles.subtitle}>
        Відстежуй свій прогрес день за днем
      </Text>

      <View style={styles.monthHeader}>
        <Pressable
          accessibilityLabel="Попередній місяць"
          style={styles.monthButton}
          onPress={() => changeMonth(-1)}
        >
          <Text style={styles.arrow}>‹</Text>
        </Pressable>

        <Text style={styles.monthTitle}>
          {monthDate.toLocaleDateString('uk-UA', {
            month: 'long',
            year: 'numeric',
          })}
        </Text>

        <Pressable
          accessibilityLabel="Наступний місяць"
          style={styles.monthButton}
          onPress={() => changeMonth(1)}
        >
          <Text style={styles.arrow}>›</Text>
        </Pressable>
      </View>

      <View style={styles.calendar}>
        <View style={styles.weekRow}>
          {weekdays.map((day) => (
            <View key={day} style={styles.dayCell}>
              <Text style={styles.weekday}>{day}</Text>
            </View>
          ))}
        </View>

        <View style={styles.daysGrid}>
          {monthDays.map((date, index) => {
            if (!date) {
              return <View key={`empty-${index}`} style={styles.dayCell} />;
            }

            const status = getDayStatus(date);
            const isToday = date === today;
            const isSelected = date === selectedDate;

            return (
              <View key={date} style={styles.dayCell}>
                <Pressable
                  accessibilityLabel={`${date}, ${
                    status === 'relapse'
                      ? 'зрив'
                      : status === 'sober'
                        ? 'тверезий день'
                        : 'без позначки'
                  }`}
                  onPress={() => setSelectedDate(date)}
                  style={[
                    styles.dayButton,
                    status === 'sober' && styles.soberDay,
                    status === 'relapse' && styles.relapseDay,
                    isToday && styles.today,
                    isSelected && styles.selectedDay,
                  ]}
                >
                  <Text
                    style={[
                      styles.dayNumber,
                      status !== 'empty' && styles.markedDayText,
                      isSelected && styles.selectedDayText,
                    ]}
                  >
                    {Number(date.slice(-2))}
                  </Text>
                  {isToday && <View style={styles.todayDot} />}
                </Pressable>
              </View>
            );
          })}
        </View>
      </View>

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, styles.soberDay]} />
          <Text style={styles.legendText}>Тверезість</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, styles.relapseDay]} />
          <Text style={styles.legendText}>Зрив</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, styles.emptyDot]} />
          <Text style={styles.legendText}>Без позначки</Text>
        </View>
      </View>

      {available && <View style={styles.card}>
        <Text style={styles.cardTitle}>Обраний день</Text>
        <Text style={styles.selectedDate}>{selectedDate}</Text>

        {(() => {
          const status = getDayStatus(selectedDate);

          if (selectedEntry) {
            return (
              <>
                <Text style={styles.statusText}>
                  Статус: {status === 'relapse' ? 'Зрив' : 'Тверезість'}
                </Text>
                <Text style={styles.secondary}>
                  Тригер: {triggers.find(item => item.value === selectedEntry.trigger_category)?.label ?? 'Не вказано'}
                </Text>
              </>
            );
          }

          if (status === 'sober') {
            return (
              <Text style={styles.statusText}>
                Тверезий день за правилами відстеження. Окремий запис не створено.
              </Text>
            );
          }

          return (
            <Text style={styles.secondary}>
              Для цього дня немає позначки.
            </Text>
          );
        })()}
        {selectedEntry ? <Pressable style={styles.retryButton} onPress={() => router.push({
          pathname: '/entry/[record_id]', params: { record_id: selectedEntry.record_id },
        })}><Text style={styles.retryText}>Відкрити запис</Text></Pressable>
          : mayCreate ? <Pressable style={styles.retryButton} onPress={() => router.push({
            pathname: '/add-entry', params: { date: selectedDate },
          })}><Text style={styles.retryText}>Додати запис на цей день</Text></Pressable>
          : <Text style={styles.secondary}>Запис можна додати лише від {trackingStart} до {today}.</Text>}
      </View>}

      {available && <View style={styles.summary}>
        <Text style={styles.summaryTitle}>Записи за місяць</Text>
        <Text style={styles.summaryNumber}>{total}</Text>
      </View>}

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.secondary}>Завантаження записів...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити записи</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable
            style={styles.retryButton}
            onPress={() => setAttempt(value => value + 1)}
          >
            <Text style={styles.retryText}>Спробувати ще раз</Text>
          </Pressable>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 20,
    paddingTop: 48,
    paddingBottom: 36,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    marginTop: 6,
    marginBottom: 24,
    color: theme.colors.muted,
    fontSize: 15,
  },
  monthHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  monthTitle: {
    color: theme.colors.text,
    fontSize: 19,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  monthButton: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrow: {
    color: theme.colors.primary,
    fontSize: 30,
    lineHeight: 34,
  },
  calendar: {
    backgroundColor: theme.colors.surface,
    borderRadius: 20,
    padding: 10,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  weekRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  daysGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  dayCell: {
    width: `${100 / 7}%`,
    aspectRatio: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  weekday: {
    color: theme.colors.muted,
    fontSize: 12,
    fontWeight: '600',
  },
  dayButton: {
    width: '86%',
    height: '86%',
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
    position: 'relative',
  },
  dayNumber: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '500',
  },
  soberDay: {
    backgroundColor: theme.colors.accent,
  },
  relapseDay: {
    backgroundColor: '#F8DADA',
  },
  markedDayText: {
    fontWeight: '700',
  },
  today: {
    borderColor: theme.colors.primary,
    borderWidth: 2,
  },
  selectedDay: {
    borderColor: theme.colors.primaryDark,
    borderWidth: 2,
  },
  selectedDayText: {
    color: theme.colors.primaryDark,
    fontWeight: '800',
  },
  todayDot: {
    position: 'absolute',
    bottom: 3,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.colors.primaryDark,
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 14,
    marginTop: 16,
    marginBottom: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 4,
  },
  emptyDot: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  legendText: {
    color: theme.colors.muted,
    fontSize: 12,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 18,
    gap: 8,
  },
  cardTitle: {
    color: theme.colors.muted,
    fontSize: 14,
  },
  selectedDate: {
    color: theme.colors.primaryDark,
    fontSize: 20,
    fontWeight: '700',
  },
  statusText: {
    color: theme.colors.text,
    fontSize: 15,
  },
  secondary: {
    color: theme.colors.muted,
    fontSize: 14,
  },
  summary: {
    marginTop: 16,
    padding: 18,
    borderRadius: 18,
    backgroundColor: theme.colors.accent,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  summaryTitle: {
    color: theme.colors.primaryDark,
    fontSize: 15,
    fontWeight: '600',
  },
  summaryNumber: {
    color: theme.colors.primaryDark,
    fontSize: 24,
    fontWeight: '800',
  },
  message: {
    alignItems: 'center',
    gap: 12,
    padding: 24,
  },
  errorBox: {
    marginTop: 16,
    backgroundColor: '#FDECEC',
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.danger,
  },
  errorText: {
    fontSize: 14,
    color: theme.colors.danger,
  },
  retryButton: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.surface,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginTop: 4,
  },
  retryText: {
    color: theme.colors.primaryDark,
    fontWeight: '700',
  },
});
