import { Redirect } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { ScreenState } from '../components/ui/ScreenState';

export default function Index() {
  const { user, loading } = useAuth();
  if (loading) return <ScreenState state="loading" />;
  if (!user) return <Redirect href="/login" />;
  if (user.role === 'admin') return <Redirect href={'/admin/users' as never} />;
  return <Redirect href="/(tabs)/home" />;
}
