import { useEffect, useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { router } from 'expo-router';
import { updateProfile } from '../../api/profile';
import { useAuth } from '../../auth/AuthProvider';
import { FormField } from '../../components/ui/FormField';
import { Button } from '../../components/ui/Button';
import { useProfile } from '../../profile/ProfileProvider';
import { profileStyles as styles } from '../../profile/styles';

export default function EditProfileScreen() {
  const { profile, refreshProfile } = useProfile();
  const { refresh } = useAuth();
  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setName(profile?.name ?? '');
    setNickname(profile?.nickname ?? '');
  }, [profile?.user_id, profile?.name, profile?.nickname]);

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
      <View style={styles.card}>
        <FormField label="Ім’я" value={name} onChangeText={setName} maxLength={110} />
        <FormField label="Нікнейм" value={nickname} onChangeText={setNickname}
          maxLength={60} autoCapitalize="none" />
        <Text style={styles.muted}>Email: {profile?.email ?? ''}</Text>
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Зберегти" disabled={!profile || saving} loading={saving}
          onPress={() => { void save(); }} />
      </View>
    </ScrollView>
  );
}
