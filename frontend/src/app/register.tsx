import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { ApiError } from '../api/client';
import { Button } from '../components/ui/Button';
import { FormField } from '../components/ui/FormField';
import { theme } from '../constants/theme';

export default function RegisterScreen() {
  const { user, signUp } = useAuth();
  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  if (user) return <Redirect href="/" />;

  async function handleRegister() {
    if (!name.trim() || !nickname.trim() || !email.trim() || password.length < 8) {
      setError('Заповни всі поля, пароль має містити щонайменше 8 символів.');
      return;
    }
    setError('');
    setSaving(true);
    try {
      await signUp({ name, nickname, email, password });
      router.replace('/onboarding');
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Не вдалося зв’язатися із сервером.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.content}>
          <Pressable disabled={saving} onPress={() => router.replace('/login')}>
            <Text style={styles.back}>← Назад до входу</Text>
          </Pressable>
          <Text style={styles.title}>Створити акаунт</Text>
          <Text style={styles.subtitle}>Почни свій шлях у власному темпі.</Text>
          <View style={styles.form}>
            <FormField label="Ім’я" value={name} onChangeText={setName} maxLength={100} />
            <FormField label="Нікнейм" value={nickname} onChangeText={setNickname} maxLength={50}
              autoCapitalize="none" />
            <FormField label="Email" value={email} onChangeText={setEmail} maxLength={254}
              autoCapitalize="none" autoCorrect={false} keyboardType="email-address" />
            <FormField label="Пароль" value={password} onChangeText={setPassword}
              secureTextEntry maxLength={128} />
            {!!error && <Text style={styles.error} accessibilityRole="alert">{error}</Text>}
            <Button title="Зареєструватися" loading={saving} onPress={() => { void handleRegister(); }} />
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.colors.background },
  container: { flexGrow: 1, justifyContent: 'center', padding: 26, gap: 14 },
  content: { width: '100%', maxWidth: 460, alignSelf: 'center', gap: 14 },
  back: { color: theme.colors.primaryDark, fontWeight: '600' },
  title: { textAlign: 'center', fontSize: 28, fontWeight: '800', color: theme.colors.primaryDark },
  subtitle: { textAlign: 'center', color: theme.colors.muted },
  form: { marginTop: 16, gap: 13 },
  error: { color: theme.colors.danger },
});
