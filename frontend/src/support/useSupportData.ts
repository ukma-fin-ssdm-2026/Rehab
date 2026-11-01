import { useCallback, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { endMentorship, getMyMentees, getMyMentor, getMyMentorCode, joinMentorship,
  type Relationship, type RelationshipPage } from '../api/mentorship';

type SupportData = { owner: number; code: string; mentor: Relationship | null; mentees: RelationshipPage };

export function useSupportData() {
  const { user } = useAuth();
  const owner = user?.user_id;
  const ownerRef = useRef(owner);
  const [snapshot, setSnapshot] = useState<SupportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const pendingAction = useRef<{ owner: number } | null>(null);
  const focused = useRef(false);
  const epoch = useRef(0);
  const controller = useRef<AbortController | null>(null);

  const reload = useCallback(async () => {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    const stamp = ++epoch.current;
    setLoading(true); setError(''); setSnapshot(null);
    if (!owner) { setLoading(false); return; }
    try {
      const [code, mentor, mentees] = await Promise.all([
        getMyMentorCode(request.signal), getMyMentor(request.signal), getMyMentees(30, 0, request.signal),
      ]);
      if (focused.current && stamp === epoch.current && ownerRef.current === owner) {
        setSnapshot({ owner, code: code.code, mentor: mentor.item, mentees });
      }
    } catch (cause) {
      if (!request.signal.aborted && focused.current && stamp === epoch.current) {
        setError(cause instanceof Error ? cause.message : 'Не вдалося завантажити підтримку.');
      }
    } finally {
      if (focused.current && stamp === epoch.current) setLoading(false);
    }
  }, [owner]);

  useFocusEffect(useCallback(() => {
    ownerRef.current = owner;
    focused.current = true;
    setBusy(owner !== undefined && pendingAction.current?.owner === owner);
    void reload();
    const refresh = () => { if (document.visibilityState === 'visible') void reload(); };
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.addEventListener('focus', refresh);
      document.addEventListener('visibilitychange', refresh);
    }
    return () => {
      focused.current = false; ownerRef.current = undefined; ++epoch.current; controller.current?.abort(); setSnapshot(null);
      if (Platform.OS === 'web' && typeof window !== 'undefined') {
        window.removeEventListener('focus', refresh);
        document.removeEventListener('visibilitychange', refresh);
      }
    };
  }, [reload, owner]));

  async function perform(action: () => Promise<unknown>): Promise<boolean> {
    if (!owner || pendingAction.current?.owner === owner) return false;
    const operation = { owner }; pendingAction.current = operation;
    setBusy(true); setError('');
    try {
      await action();
      if (!focused.current || ownerRef.current !== owner) return false;
      await reload();
      return focused.current && ownerRef.current === owner;
    } catch (cause) {
      if (focused.current && ownerRef.current === owner) {
        setError(cause instanceof Error ? cause.message : 'Не вдалося виконати дію.');
      }
      return false;
    } finally {
      if (pendingAction.current === operation) {
        pendingAction.current = null;
        if (ownerRef.current === owner) setBusy(false);
      }
    }
  }

  async function loadMore() {
    if (!owner || pendingAction.current?.owner === owner || !snapshot || snapshot.owner !== owner || snapshot.mentees.items.length >= snapshot.mentees.total) return;
    const operation = { owner }; pendingAction.current = operation;
    setBusy(true); setError('');
    const stamp = epoch.current;
    try {
      const page = await getMyMentees(30, snapshot.mentees.items.length, controller.current?.signal);
      if (focused.current && stamp === epoch.current && ownerRef.current === owner) {
        setSnapshot(current => current && current.owner === owner ? { ...current,
          mentees: { ...page, items: [...current.mentees.items, ...page.items.filter(row => !current.mentees.items.some(old => old.relationship_id === row.relationship_id))] },
        } : current);
      }
    } catch (cause) {
      if (focused.current && stamp === epoch.current && !controller.current?.signal.aborted) {
        setError(cause instanceof Error ? cause.message : 'Не вдалося завантажити наступну сторінку.');
      }
    } finally {
      if (pendingAction.current === operation) {
        pendingAction.current = null;
        if (ownerRef.current === owner) setBusy(false);
      }
    }
  }

  return { data: snapshot?.owner === owner ? snapshot : null, loading, error, busy, reload,
    join: (code: string) => perform(() => joinMentorship(code)),
    leave: (id: number) => perform(() => endMentorship(id)), loadMore };
}
