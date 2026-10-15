
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { theme } from '../constants/theme';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  function handleLogin() {
    if (!email.trim() || !password.trim()) {
      setError('Заповни email і пароль.');
      return;
    }

    setError('');
    router.replace('/(tabs)/home');
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>R</Text>
        </View>

        <Text style={styles.brand}>Rehab</Text>
        <Text style={styles.title}>Раді тебе бачити</Text>
        <Text style={styles.subtitle}>
          Увійди, щоб продовжити свій шлях до змін.
        </Text>

        <View style={styles.form}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="name@example.com"
            placeholderTextColor={theme.colors.muted}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            style={styles.input}
          />

          <Text style={styles.label}>Пароль</Text>
          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Введи пароль"
            placeholderTextColor={theme.colors.muted}
            secureTextEntry
            style={styles.input}
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>Увійти</Text>
          </Pressable>

          <View style={styles.registerRow}>
            <Text style={styles.subtitle}>Ще немає акаунта? </Text>
            <Pressable onPress={() => router.push('/register')}>
              <Text style={styles.link}>Зареєструватися</Text>
            </Pressable>
          </View>
        </View>

        <Text style={styles.note}>
          Демонстраційний вхід. Справжня авторизація ще не підключена.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 28,
    gap: 12,
  },
  logo: {
    width: 64,
    height: 64,
    borderRadius: 22,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
  },
  logoText: {
    fontSize: 34,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  brand: {
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  title: {
    marginTop: 16,
    textAlign: 'center',
    fontSize: 29,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 21,
    color: theme.colors.muted,
    textAlign: 'center',
  },
  form: {
    marginTop: 22,
    gap: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.text,
  },
  input: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 14,
    backgroundColor: theme.colors.surface,
    paddingHorizontal: 16,
    fontSize: 15,
    color: theme.colors.text,
  },
  button: {
    minHeight: 52,
    borderRadius: 14,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  error: {
    color: theme.colors.danger,
    fontSize: 14,
  },
  registerRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  link: {
    color: theme.colors.primaryDark,
    fontWeight: '700',
  },
  note: {
    marginTop: 24,
    textAlign: 'center',
    color: theme.colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
});
