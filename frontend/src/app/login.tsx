import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../auth/AuthProvider';
import { validateLogin } from '../auth/credentialForms';
import { ApiError } from '../api/client';
import { Button } from '../components/ui/Button';
import { FormField } from '../components/ui/FormField';
import { theme } from '../constants/theme';

export default function LoginScreen() {
  const { user, signIn } = useAuth();
  const { logout } = useLocalSearchParams<{ logout?: string }>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  if (user) return <Redirect href="/" />;

  async function handleLogin() {
    const validation = validateLogin(email, password);
    if (!validation.ok) {
      setError(validation.error);
      return;
    }
    setSaving(true);
    setError('');
    try {
      await signIn(validation.email, validation.password);
      router.replace('/');
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
          <Text style={styles.brand}>Rehab</Text>
          <Text style={styles.title}>Раді тебе бачити</Text>
          <Text style={styles.subtitle}>Увійди, щоб продовжити свій шлях до змін.</Text>
          {logout === 'local' ? (
            <Text style={styles.error} accessibilityRole="alert">
              Локальний вихід виконано, але сервер не підтвердив завершення сесії.
            </Text>
          ) : null}
          <View style={styles.form}>
            <FormField label="Email" value={email} onChangeText={setEmail}
              keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
              placeholder="name@example.com" />
            <FormField label="Пароль" value={password} onChangeText={setPassword}
              secureTextEntry placeholder="Введи пароль" />
            {!!error && <Text style={styles.error} accessibilityRole="alert">{error}</Text>}
            <Button title="Увійти" loading={saving} onPress={() => { void handleLogin(); }} />
            <Pressable onPress={() => router.push('/register')} disabled={saving}>
              <Text style={styles.link}>Ще немає акаунта? Зареєструватися</Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.colors.background },
  container: { flexGrow: 1, justifyContent: 'center', padding: 28, gap: 14 },
  content: { width: '100%', maxWidth: 460, alignSelf: 'center', gap: 14 },
  brand: { textAlign: 'center', fontSize: 24, fontWeight: '800', color: theme.colors.primary },
  title: { fontSize: 29, fontWeight: '800', textAlign: 'center', color: theme.colors.primaryDark },
  subtitle: { textAlign: 'center', color: theme.colors.muted, lineHeight: 22 },
  form: { marginTop: 20, gap: 14 },
  error: { color: theme.colors.danger },
  link: { color: theme.colors.primaryDark, textAlign: 'center', padding: 12, fontWeight: '600' },
});
