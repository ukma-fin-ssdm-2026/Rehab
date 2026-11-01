import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
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
      <GlassCard style={styles.card}>
        {profile ? <AvatarView profile={profile} /> : (
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.name?.charAt(0).toUpperCase() ?? 'R'}</Text>
          </View>
        )}
        <Text style={styles.name}>{profile?.name ?? user?.name ?? 'Завантаження…'}</Text>
        <Text style={styles.nickname}>@{profile?.nickname ?? user?.nickname ?? ''}</Text>
        <Text style={styles.email}>{profile?.email ?? user?.email ?? ''}</Text>
      </GlassCard>
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
        <GlassCard style={styles.menu}>
          <Text style={styles.note}>Дійсно видалити фото?</Text>
          <Button title="Підтвердити видалення" loading={saving}
            onPress={() => { void removeAvatar(); }} />
          <Pressable onPress={() => setDeleteRequested(false)}>
            <Text style={styles.link}>Скасувати</Text>
          </Pressable>
        </GlassCard>
      )}
      {!!loadError && <Text style={styles.error}>{loadError}</Text>}
      {!!error && <Text style={styles.error}>{error}</Text>}
      {!!loadError && <Button title="Повторити"
        onPress={() => { void refreshProfile(); }} />}
      <GlassCard style={styles.menu}>
        {([
          ['Редагувати профіль', '/profile/edit'],
          ['Змінити пароль', '/profile/password'],
          ['Сповіщення та пошта', '/profile/notifications'],
          ['Стиль повідомлень', '/profile/style'],
          ['Приватність і доступ', '/profile/privacy'],
          ['Питання та відповіді', '/profile/help'],
        ] as const).map(([title, route]) => (
          <Pressable key={route} accessibilityRole="button" accessibilityLabel={title} disabled={!profile || saving}
            style={styles.menuItem} onPress={() => router.push(route)}>
            <View style={styles.menuLabel}>
              <Ionicons name={route === '/profile/edit' ? 'create-outline' : route === '/profile/password' ? 'lock-closed-outline' : route === '/profile/notifications' ? 'notifications-outline' : route === '/profile/style' ? 'chatbubble-outline' : route === '/profile/privacy' ? 'shield-checkmark-outline' : 'help-circle-outline'} size={22} color={theme.colors.muted} />
              <Text style={styles.link}>{title}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.muted} />
          </Pressable>
        ))}
      </GlassCard>
      <Button variant="outline" title="Вийти з акаунта" loading={saving} onPress={() => { void handleLogout(); }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: theme.colors.background, padding: 24, gap: 18 },
  eyebrow: { color: theme.colors.highlight, fontSize: 12, fontWeight: '500', letterSpacing: 1.5 },
  title: { fontSize: 30, fontWeight: '400', color: theme.colors.text },
  card: { ...theme.effects.card, alignItems: 'center', gap: 10, borderWidth: 1, borderColor: theme.colors.border,
    borderRadius: 20, backgroundColor: theme.colors.surface, padding: 24 },
  avatar: { width: 70, height: 70, borderRadius: 25, backgroundColor: theme.colors.accent,
    alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: theme.colors.text, fontSize: 30, fontWeight: '400' },
  name: { fontSize: 21, color: theme.colors.text, fontWeight: '400' },
  nickname: { color: theme.colors.highlight },
  email: { color: theme.colors.text },
  note: { color: theme.colors.muted, lineHeight: 21 },
  error: { color: theme.colors.danger },
  photoActions: { gap: 12 },
  preview: { alignItems: 'center', gap: 12, padding: 12 },
  previewImage: { width: 112, height: 112, borderRadius: 32 },
  remove: { color: theme.colors.danger, fontWeight: '500' },
  link: { color: theme.colors.text, fontWeight: '500' },
  menu: { ...theme.effects.card, backgroundColor: theme.colors.surface, borderRadius: 16, padding: 16, gap: 12 },
  menuLabel: { flexDirection: 'row', alignItems: 'center', gap: 12, flexShrink: 1 },
  menuItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, borderBottomWidth: 1, borderBottomColor: theme.colors.border, padding: 8 },
});
