import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useState } from 'react';
import { Text } from 'react-native';
import { router } from 'expo-router';
import { updateProfile } from '../../api/profile';
import { useAuth } from '../../auth/AuthProvider';
import { FormField } from '../../components/ui/FormField';
import { Button } from '../../components/ui/Button';
import { ScreenState } from '../../components/ui/ScreenState';
import { useProfile } from '../../profile/ProfileProvider';
import type { ProfileOut } from '../../profile/types';
import { profileStyles as styles } from '../../profile/styles';

function EditProfileForm({ profile, refreshProfile }: {
  profile: ProfileOut;
  refreshProfile: () => Promise<void>;
}) {
  const { refresh } = useAuth();
  const [name, setName] = useState(profile.name);
  const [nickname, setNickname] = useState(profile.nickname);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function save() {
    const nextName = name.trim();
    const nextNickname = nickname.trim();
    if (!nextName || nextName.length > 100 || !nextNickname || nextNickname.length > 50) {
      setError('Ім’я має містити 1–100 символів, нікнейм — 1–50.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await updateProfile({ name: nextName, nickname: nextNickname });
      await Promise.all([refreshProfile(), refresh()]);
      router.back();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося зберегти профіль.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Редагувати профіль</Text>
      <Text style={styles.subtitle}>Email і права доступу тут не змінюються.</Text>
      <GlassCard style={styles.card}>
        <FormField label="Ім’я" value={name} onChangeText={setName} maxLength={110} />
        <FormField label="Нікнейм" value={nickname} onChangeText={setNickname}
          maxLength={60} autoCapitalize="none" />
        <Text style={styles.muted}>Email: {profile.email}</Text>
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Зберегти" disabled={saving} loading={saving}
          onPress={() => { void save(); }} />
      </GlassCard>
    </ScrollView>
  );
}

export default function EditProfileScreen() {
  const { profile, loading, error, refreshProfile } = useProfile();
  if (!profile) {
    return <ScreenState state={loading ? 'loading' : 'error'}
      message={error ?? undefined} onRetry={() => { void refreshProfile(); }} />;
  }
  return <EditProfileForm key={profile.user_id} profile={profile}
    refreshProfile={refreshProfile} />;
}
