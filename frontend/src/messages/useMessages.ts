import { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { useProfile } from '../profile/ProfileProvider';
import { listNotifications, getUnreadCount, markNotificationRead } from '../api/notifications';
import { createLatestRequest } from '../progress/request';
import { loadInboxPages } from './inbox';

export function useMessageResource<T>(loader: () => Promise<T>, poll = false) {
  const { user } = useAuth();
  const owner = user?.user_id;
  const request = useRef(createLatestRequest()).current;
  const [snapshot, setSnapshot] = useState<{owner: number; data: T} | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const reload = useCallback(async () => {
    if (owner === undefined) return;
    setLoading(true); setError('');
    await request.run(loader, data => { setSnapshot({owner,data}); setLoading(false); }, cause => {
      setSnapshot(null); setError(cause instanceof Error ? cause.message : 'Не вдалося завантажити повідомлення'); setLoading(false);
    });
  }, [loader, owner, request]);
  useFocusEffect(useCallback(() => {
    void reload();
    const visible = () => { if (typeof document === 'undefined' || document.visibilityState === 'visible') void reload(); };
    const timer = poll ? setInterval(visible,60000) : null;
    if (typeof window !== 'undefined') {
      window.addEventListener('focus',visible); document.addEventListener('visibilitychange',visible);
    }
    return () => {
      request.cancel(); if (timer !== null) clearInterval(timer);
      if (typeof window !== 'undefined') { window.removeEventListener('focus',visible); document.removeEventListener('visibilitychange',visible); }
    };
  }, [reload,poll,request]));
  return {data:snapshot && snapshot.owner === owner ? snapshot.data : null,loading,error,reload};
}

export function useUnreadMessages() {
  const load=useCallback(()=>getUnreadCount(),[]);
  return useMessageResource(load);
}

export function useInbox(visible: number) {
  const {profile}=useProfile();
  const style=profile?.message_style;
  const load=useCallback(()=>{
    void style;
    return loadInboxPages(listNotifications,visible);
  },[visible,style]);
  return useMessageResource(load,true);
}

export function useMessage(id: number) {
  const {profile}=useProfile();
  const style=profile?.message_style;
  const load=useCallback(()=>{
    void style;
    return Number.isInteger(id) && id > 0 ? markNotificationRead(id) : Promise.reject(new Error('Некоректний номер повідомлення'));
  },[id,style]);
  return useMessageResource(load,true);
}
