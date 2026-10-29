import {
  createContext, useCallback, useContext, useEffect, useState,
  type ReactNode,
} from 'react';
import { Platform } from 'react-native';
import {
  type UserAccount, type RegistrationData, getMyAccount,
  loginUser, logoutUser, registerUser,
} from '../api/auth';
import { setAccessToken, setSessionInvalidHandler } from '../api/client';

const KEY = 'rehab.auth.token';

type AuthContextValue = {
  user: UserAccount | null;
  loading: boolean;
  signIn(email: string, password: string): Promise<UserAccount>;
  signUp(data: RegistrationData): Promise<UserAccount>;
  signOut(): Promise<void>;
  refresh(): Promise<void>;
};

const Context = createContext<AuthContextValue | null>(null);

function getSavedToken(): string | null {
  return Platform.OS === 'web' && typeof window !== 'undefined'
    ? window.sessionStorage.getItem(KEY) : null;
}
function saveToken(value: string | null): void {
  if (Platform.OS !== 'web' || typeof window === 'undefined') return;
  if (value) window.sessionStorage.setItem(KEY, value);
  else window.sessionStorage.removeItem(KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [loading, setLoading] = useState(true);

  const clear = useCallback(() => {
    setAccessToken(null);
    saveToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    if (!getSavedToken()) return;
    const account = await getMyAccount();
    setUser(account);
  }, []);

  useEffect(() => {
    let active = true;
    setSessionInvalidHandler(clear);
    const saved = getSavedToken();
    if (saved) {
      setAccessToken(saved);
      getMyAccount().then(account => {
        if (active) setUser(account);
      }).catch(() => {
        // Тимчасова мережева помилка не скидає токен.
      }).finally(() => {
        if (active) setLoading(false);
      });
    } else setLoading(false);
    return () => {
      active = false;
      setSessionInvalidHandler(null);
    };
  }, [clear]);

  useEffect(() => {
    if (Platform.OS !== 'web' || !user || typeof window === 'undefined') return;
    const check = () => { void refresh().catch(() => {}); };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') check();
    };
    window.addEventListener('focus', check);
    document.addEventListener('visibilitychange', onVisibility);
    const interval = window.setInterval(check, 30000);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('focus', check);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [user, refresh]);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await loginUser(email, password);
    setAccessToken(result.access_token);
    saveToken(result.access_token);
    setUser(result.user);
    return result.user;
  }, []);

  const signUp = useCallback(async (data: RegistrationData) => {
    await registerUser(data);
    return signIn(data.email, data.password);
  }, [signIn]);

  const signOut = useCallback(async () => {
    try { await logoutUser(); }
    finally { clear(); }
  }, [clear]);

  return (
    <Context.Provider value={{ user, loading, signIn, signUp, signOut, refresh }}>
      {children}
    </Context.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(Context);
  if (!context) throw new Error('useAuth потребує AuthProvider');
  return context;
}
