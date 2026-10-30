import {
  createContext, useCallback, useContext, useEffect, useRef, useState,
  type ReactNode,
} from 'react';
import { useAuth } from '../auth/AuthProvider';
import { getProfile } from '../api/profile';
import type { ProfileContextValue, ProfileOut } from './types';

const Context = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const userId = user && user.role !== 'admin' ? user.user_id : null;
  const [profile, setProfile] = useState<ProfileOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);

  const refreshProfile = useCallback(async () => {
    const version = ++requestVersion.current;
    if (userId === null) {
      setProfile(null);
      setError(null);
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const current = await getProfile();
      if (version === requestVersion.current && current.user_id === userId) {
        setProfile(current);
      }
    } catch (cause) {
      if (version === requestVersion.current) {
        setError(cause instanceof Error ? cause.message : 'Не вдалося завантажити профіль.');
      }
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (userId !== null) {
      void refreshProfile();
    }
    const versionRef = requestVersion;
    return () => {
      versionRef.current += 1;
    };
  }, [userId, refreshProfile]);

  const currentProfile = profile?.user_id === userId ? profile : null;

  return (
    <Context.Provider value={{
      profile: currentProfile,
      loading: userId !== null && loading,
      error: userId !== null ? error : null,
      refreshProfile,
    }}>
      {children}
    </Context.Provider>
  );
}

export function useProfile(): ProfileContextValue {
  const context = useContext(Context);
  if (!context) throw new Error('useProfile потребує ProfileProvider');
  return context;
}
