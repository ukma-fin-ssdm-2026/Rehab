import { Redirect, Stack } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { ScreenState } from '../../components/ui/ScreenState';

export default function MessagesLayout() {
  const {user,loading,onboardingPending}=useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (!user || user.role === 'admin') return <Redirect href="/" />;
  if (onboardingPending) return <Redirect href="/onboarding" />;
  return <Stack screenOptions={{headerShown:false}} />;
}
