import {
  createContext, useCallback, useContext, useEffect, useRef, useState,
  type ReactNode,
} from 'react';
import { Platform } from 'react-native';
import {
  type UserAccount, type RegistrationData, getMyAccount,
  loginUser, logoutUser, registerUser,
} from '../api/auth';
import { ApiError, setAccessToken, setSessionInvalidHandler } from '../api/client';

const KEY = 'rehab.auth.token';

type AuthContextValue = {
  user: UserAccount | null;
  loading: boolean;
  restoreError: boolean;
  onboardingPending: boolean;
  finishOnboarding(): void;
  signIn(email: string, password: string): Promise<UserAccount>;
  signUp(data: RegistrationData): Promise<UserAccount>;
  signOut(): Promise<void>;
  refresh(): Promise<void>;
  retryRestore(): Promise<void>;
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
  const [loading, setLoading] = useState(() => getSavedToken() !== null);
  const [restoreError, setRestoreError] = useState(false);
  const [onboardingPending, setOnboardingPending] = useState(false);
  const sessionVersion = useRef(0);

  const clear = useCallback(() => {
    sessionVersion.current += 1;
    setAccessToken(null);
    saveToken(null);
    setUser(null);
    setRestoreError(false);
    setOnboardingPending(false);
  }, []);

  const refresh = useCallback(async () => {
    const saved = getSavedToken();
    if (!saved) {
      clear();
      return;
    }
    const version = sessionVersion.current;
    setAccessToken(saved);
    const account = await getMyAccount();
    if (version === sessionVersion.current && getSavedToken() === saved) {
      setUser(account);
      setRestoreError(false);
    }
  }, [clear]);

  const retryRestore = useCallback(async () => {
    setLoading(true);
    try {
      await refresh();
    } catch (cause) {
      if (!(cause instanceof ApiError &&
        (cause.status === 401 || cause.code === 'ACCOUNT_BLOCKED'))) {
        setRestoreError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  useEffect(() => {
    let active = true;
    setSessionInvalidHandler(clear);
    const saved = getSavedToken();
    if (saved) {
      const version = sessionVersion.current;
      setAccessToken(saved);
      getMyAccount().then(account => {
        if (active && version === sessionVersion.current && getSavedToken() === saved) {
          setUser(account);
        }
      }).catch(cause => {
        if (active && version === sessionVersion.current &&
          !(cause instanceof ApiError &&
          (cause.status === 401 || cause.code === 'ACCOUNT_BLOCKED'))) {
          setRestoreError(true);
        }
      }).finally(() => {
        if (active) setLoading(false);
      });
    }
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
    sessionVersion.current += 1;
    setAccessToken(result.access_token);
    saveToken(result.access_token);
    setRestoreError(false);
    setOnboardingPending(false);
    setUser(result.user);
    return result.user;
  }, []);

  const signUp = useCallback(async (data: RegistrationData) => {
    await registerUser(data);
    const account = await signIn(data.email, data.password);
    setOnboardingPending(true);
    return account;
  }, [signIn]);

  const signOut = useCallback(async () => {
    const logoutRequest = logoutUser();
    clear();
    await logoutRequest;
  }, [clear]);

  return (
    <Context.Provider value={{
      user, loading, restoreError, onboardingPending,
      finishOnboarding: () => setOnboardingPending(false),
      signIn, signUp, signOut, refresh, retryRestore,
    }}>
      {children}
    </Context.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(Context);
  if (!context) throw new Error('useAuth потребує AuthProvider');
  return context;
}
