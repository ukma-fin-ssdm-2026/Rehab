import { useCallback, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { getMentorship, getMenteeEntries, getMenteeStatistics,
  type MenteeStatistics, type Relationship } from '../api/mentorship';
import type { EntryPage } from '../api/calendar';
import type { StatisticsPeriod } from '../api/statistics';
import { calendarMonth } from './calendar';

type Snapshot = { owner: number; id: number; relationship: Relationship;
  statistics: MenteeStatistics; entries: EntryPage; monthKey: string; period: StatisticsPeriod };

export function useMenteeData(id: number | null, monthKey: string | null, period: StatisticsPeriod) {
  const { user } = useAuth();
  const owner = user?.user_id;
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const epoch = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const focused = useRef(false);

  const reload = useCallback(async () => {
    controller.current?.abort();
    const request = new AbortController(); controller.current = request;
    const stamp = ++epoch.current;
    setSnapshot(null); setLoading(true); setError('');
    if (!id || !owner) { setError('Некоректне посилання на підопічного.'); setLoading(false); return; }
    try {
      const [relationship, statistics] = await Promise.all([
        getMentorship(id, request.signal), getMenteeStatistics(id, period, request.signal),
      ]);
      if (relationship.status !== 'active') throw new Error('Менторство завершено. Доступ до даних закрито.');
      const currentMonth = monthKey ?? statistics.period_end.slice(0, 7);
      const [year, month] = currentMonth.split('-').map(Number);
      const range = calendarMonth(year, month - 1);
      const entries = await getMenteeEntries(id, range.from, range.to, request.signal);
      if (focused.current && stamp === epoch.current) {
        setSnapshot({ owner, id, relationship, statistics, entries, monthKey: currentMonth, period });
      }
    } catch (cause) {
      if (!request.signal.aborted && focused.current && stamp === epoch.current) {
        setError(cause instanceof Error ? cause.message : 'Не вдалося завантажити дані підопічного.');
      }
    } finally { if (focused.current && stamp === epoch.current) setLoading(false); }
  }, [id, owner, monthKey, period]);

  useFocusEffect(useCallback(() => {
    focused.current = true;
    void reload();
    const refresh = () => { if (document.visibilityState === 'visible') void reload(); };
    const interval = setInterval(() => {
      if (Platform.OS !== 'web' || typeof document === 'undefined' || document.visibilityState === 'visible') void reload();
    }, 60000);
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.addEventListener('focus', refresh);
      document.addEventListener('visibilitychange', refresh);
    }
    return () => {
      focused.current = false; ++epoch.current; controller.current?.abort(); setSnapshot(null); clearInterval(interval);
      if (Platform.OS === 'web' && typeof window !== 'undefined') {
        window.removeEventListener('focus', refresh);
        document.removeEventListener('visibilitychange', refresh);
      }
    };
  }, [reload]));

  const data = snapshot !== null && snapshot.owner === owner && snapshot.id === id && snapshot.period === period &&
    (monthKey === null || snapshot.monthKey === monthKey) ? snapshot : null;
  return { data, loading, error, reload };
}
