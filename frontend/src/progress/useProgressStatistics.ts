import { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { getStatistics, type Statistics, type StatisticsPeriod } from '../api/statistics';
import { subscribeProgressChanges } from './changes';
import { createLatestRequest } from './request';

export function useProgressStatistics(period: StatisticsPeriod = 'all') {
  const { user } = useAuth();
  const owner = user?.user_id;
  const [snapshot, setSnapshot] = useState<{ owner: number; period: StatisticsPeriod; data: Statistics } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const request = useRef(createLatestRequest()).current;
  const load = useCallback(() => {
    if (owner === undefined) return;
    setLoading(true);
    setError('');
    void request.run(() => getStatistics(period), data => {
      setSnapshot({ owner, period, data });
      setLoading(false);
    }, reason => {
      setSnapshot(null);
      setError(reason instanceof Error ? reason.message : 'Не вдалося завантажити прогрес');
      setLoading(false);
    });
  }, [owner, period, request]);

  useFocusEffect(useCallback(() => {
    setSnapshot(null);
    load();
    const unsubscribe = subscribeProgressChanges(load);
    const visible = () => { if (document.visibilityState === 'visible') load(); };
    if (typeof window !== 'undefined') {
      window.addEventListener('focus', load);
      document.addEventListener('visibilitychange', visible);
    }
    return () => {
      request.cancel();
      unsubscribe();
      if (typeof window !== 'undefined') {
        window.removeEventListener('focus', load);
        document.removeEventListener('visibilitychange', visible);
      }
    };
  }, [load, request]));

  const data = snapshot?.owner === owner && snapshot?.period === period ? snapshot.data : null;
  return { data, loading, error, reload: load };
}
