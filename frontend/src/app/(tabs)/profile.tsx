import { useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { Button } from '../../components/ui/Button';
import { useProfile } from '../../profile/ProfileProvider';
import { AvatarView } from '../../profile/AvatarView';
import { deleteProfileAvatar, uploadProfileAvatar } from '../../api/profile';
import { pickProfileAvatar, type PickedAvatar } from '../../profile/avatarPicker';
import { theme } from '../../constants/theme';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [saving, setSaving] = useState(false);
  const [deleteRequested, setDeleteRequested] = useState(false);
  const [selected, setSelected] = useState<PickedAvatar | null>(null);
  const [error, setError] = useState('');
  const { profile, error: loadError, refreshProfile } = useProfile();

  async function handleLogout() {
    setSaving(true);
    try {
      await signOut();
      router.replace('/login');
    } catch {
      router.replace('/login?logout=local');
    } finally {
      setSaving(false);
    }
  }

  async function selectPhoto() {
    setError('');
    try {
      const photo = await pickProfileAvatar();
      if (photo) setSelected(photo);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося вибрати фото.');
    }
  }

  async function savePhoto() {
    if (!selected || saving) return;
    setSaving(true);
    setError('');
    try {
      await uploadProfileAvatar(selected.image, selected.mimeType);
      await refreshProfile();
      setSelected(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося зберегти фото.');
    } finally {
      setSaving(false);
    }
  }

  async function removeAvatar() {
    setSaving(true);
    setError('');
    try {
      await deleteProfileAvatar();
      await refreshProfile();
      setDeleteRequested(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося видалити фото.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТВІЙ ПРОСТІР</Text>
      <Text style={styles.title}>Профіль</Text>
      <View style={styles.card}>
        {profile ? <AvatarView profile={profile} /> : (
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.name?.charAt(0).toUpperCase() ?? 'R'}</Text>
          </View>
        )}
        <Text style={styles.name}>{profile?.name ?? user?.name ?? 'Завантаження…'}</Text>
        <Text style={styles.nickname}>@{profile?.nickname ?? user?.nickname ?? ''}</Text>
        <Text style={styles.email}>{profile?.email ?? user?.email ?? ''}</Text>
      </View>
      <View style={styles.photoActions}>
        <Button title="Обрати фото з галереї" disabled={saving || !profile}
          onPress={() => { void selectPhoto(); }} />
        {selected && (
          <View style={styles.preview}>
            <Image source={{ uri: selected.uri }} style={styles.previewImage}
              accessibilityLabel="Попередній перегляд нового фото" />
            <Text style={styles.note}>Фото ще не збережено.</Text>
            <Button title="Зберегти фото" loading={saving}
              onPress={() => { void savePhoto(); }} />
            <Pressable accessibilityRole="button" disabled={saving}
              onPress={() => setSelected(null)}>
              <Text style={styles.link}>Скасувати вибір</Text>
            </Pressable>
          </View>
        )}
      </View>
      {profile?.has_avatar && (
        <Pressable accessibilityRole="button" disabled={saving}
          onPress={() => setDeleteRequested(true)}>
          <Text style={styles.remove}>Видалити фото</Text>
        </Pressable>
      )}
      {deleteRequested && (
        <View style={styles.menu}>
          <Text style={styles.note}>Дійсно видалити фото?</Text>
          <Button title="Підтвердити видалення" loading={saving}
            onPress={() => { void removeAvatar(); }} />
          <Pressable onPress={() => setDeleteRequested(false)}>
            <Text style={styles.link}>Скасувати</Text>
          </Pressable>
        </View>
      )}
      {!!loadError && <Text style={styles.error}>{loadError}</Text>}
      {!!error && <Text style={styles.error}>{error}</Text>}
      {!!loadError && <Button title="Повторити"
        onPress={() => { void refreshProfile(); }} />}
      <View style={styles.menu}>
        {([
          ['Редагувати профіль', '/profile/edit'],
          ['Змінити пароль', '/profile/password'],
          ['Сповіщення та пошта', '/profile/notifications'],
          ['Стиль повідомлень', '/profile/style'],
          ['Приватність і доступ', '/profile/privacy'],
          ['Питання та відповіді', '/profile/help'],
        ] as const).map(([title, route]) => (
          <Pressable key={route} accessibilityRole="button" disabled={!profile || saving}
            style={styles.menuItem} onPress={() => router.push(route)}>
            <Text style={styles.link}>{title}</Text>
          </Pressable>
        ))}
      </View>
      <Button title="Вийти з акаунта" loading={saving} onPress={() => { void handleLogout(); }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: theme.colors.background, padding: 24, gap: 18 },
  eyebrow: { color: theme.colors.primary, fontSize: 12, fontWeight: '700', letterSpacing: 1.5 },
  title: { fontSize: 30, fontWeight: '800', color: theme.colors.primaryDark },
  card: { alignItems: 'center', gap: 10, borderWidth: 1, borderColor: theme.colors.border,
    borderRadius: 20, backgroundColor: theme.colors.surface, padding: 24 },
  avatar: { width: 70, height: 70, borderRadius: 25, backgroundColor: theme.colors.accent,
    alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: theme.colors.primaryDark, fontSize: 30, fontWeight: '800' },
  name: { fontSize: 21, color: theme.colors.primaryDark, fontWeight: '800' },
  nickname: { color: theme.colors.primary },
  email: { color: theme.colors.text },
  note: { color: theme.colors.muted, lineHeight: 21 },
  error: { color: theme.colors.danger },
  photoActions: { gap: 12 },
  preview: { alignItems: 'center', gap: 12, padding: 12 },
  previewImage: { width: 112, height: 112, borderRadius: 32 },
  remove: { color: theme.colors.danger, fontWeight: '700' },
  link: { color: theme.colors.primaryDark, fontWeight: '600' },
  menu: { backgroundColor: theme.colors.surface, borderRadius: 16, padding: 16, gap: 12 },
  menuItem: { borderBottomWidth: 1, borderBottomColor: theme.colors.border, padding: 8 },
});
