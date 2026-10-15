
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

export default function RegisterScreen() {
  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  function handleRegister() {
    if (
      !name.trim() ||
      !nickname.trim() ||
      !email.trim() ||
      !password.trim()
    ) {
      setError('Заповни всі поля.');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError('Введи коректну email-адресу.');
      return;
    }

    setError('');
    router.push('/onboarding');
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <Pressable onPress={() => router.replace('/login')}>
          <Text style={styles.back}>← Назад до входу</Text>
        </Pressable>

        <View style={styles.logo}>
          <Text style={styles.logoText}>R</Text>
        </View>

        <Text style={styles.title}>Створити акаунт</Text>
        <Text style={styles.subtitle}>
          Почни свій шлях у власному темпі.
        </Text>

        <View style={styles.form}>
          <Text style={styles.label}>Ім’я</Text>
          <TextInput
            value={name}
            onChangeText={setName}
            placeholder="Як до тебе звертатися?"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
          />

          <Text style={styles.label}>Нікнейм</Text>
          <TextInput
            value={nickname}
            onChangeText={setNickname}
            placeholder="Твоє ім’я в застосунку"
            placeholderTextColor={theme.colors.muted}
            autoCapitalize="none"
            style={styles.input}
          />

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
            placeholder="Створи пароль"
            placeholderTextColor={theme.colors.muted}
            secureTextEntry
            style={styles.input}
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable style={styles.button} onPress={handleRegister}>
            <Text style={styles.buttonText}>Продовжити</Text>
          </Pressable>
        </View>

        <Text style={styles.note}>
          Демонстраційна реєстрація. Дані не надсилаються на сервер.
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
  back: {
    color: theme.colors.primaryDark,
    fontWeight: '600',
    marginBottom: 8,
  },
  logo: {
    width: 54,
    height: 54,
    borderRadius: 19,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
  },
  logoText: {
    fontSize: 30,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  title: {
    marginTop: 12,
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    textAlign: 'center',
    fontSize: 14,
    color: theme.colors.muted,
  },
  form: {
    marginTop: 16,
    gap: 10,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.text,
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 13,
    backgroundColor: theme.colors.surface,
    paddingHorizontal: 14,
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
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  error: {
    color: theme.colors.danger,
    fontSize: 14,
  },
  note: {
    marginTop: 12,
    textAlign: 'center',
    color: theme.colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
});
