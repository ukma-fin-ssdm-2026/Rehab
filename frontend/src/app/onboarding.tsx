
import { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { theme } from '../constants/theme';
import { useAuth } from '../auth/AuthProvider';

const options = [
  'Хочу краще розуміти свої звички',
  'Хочу зробити паузу в алкоголі',
  'Хочу відновити контроль',
  'Поки просто досліджую себе',
];

export default function OnboardingScreen() {
  const { finishOnboarding } = useAuth();
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState('');

  function handleContinue() {
    if (!selected) {
      setError('Обери один варіант, щоб продовжити.');
      return;
    }

    finishOnboarding();
    router.replace('/(tabs)/home');
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.progressTrack}>
          <View style={styles.progressFill} />
        </View>
        <Text style={styles.step}>1 з 1</Text>
      </View>

      <Text style={styles.eyebrow}>ТВОЯ ВІДПРАВНА ТОЧКА</Text>
      <Text style={styles.title}>Що привело тебе до Rehab?</Text>
      <Text style={styles.subtitle}>
        Тут немає правильних чи неправильних відповідей. Обери те, що найближче
        тобі зараз.
      </Text>

      <View style={styles.options}>
        {options.map((option) => {
          const active = selected === option;

          return (
            <Pressable
              key={option}
              accessibilityRole="radio"
              accessibilityState={{ checked: active }}
              onPress={() => {
                setSelected(option);
                setError('');
              }}
              style={[styles.option, active && styles.optionActive]}
            >
              <View style={[styles.radio, active && styles.radioActive]}>
                {active ? <View style={styles.radioDot} /> : null}
              </View>
              <Text style={[styles.optionText, active && styles.optionTextActive]}>
                {option}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.button} onPress={handleContinue}>
        <Text style={styles.buttonText}>Почати</Text>
      </Pressable>

      <Text style={styles.note}>
        Ти можеш рухатися у власному темпі.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
    padding: 24,
    paddingTop: 36,
    gap: 18,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 18,
  },
  progressTrack: {
    flex: 1,
    height: 6,
    backgroundColor: theme.colors.accent,
    borderRadius: 8,
    overflow: 'hidden',
  },
  progressFill: {
    width: '100%',
    height: '100%',
    backgroundColor: theme.colors.primary,
  },
  step: {
    color: theme.colors.muted,
    fontSize: 12,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
    color: theme.colors.primary,
  },
  title: {
    fontSize: 30,
    lineHeight: 37,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 23,
    color: theme.colors.muted,
  },
  options: {
    gap: 12,
    marginTop: 8,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    padding: 17,
    minHeight: 68,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 17,
    backgroundColor: theme.colors.surface,
  },
  optionActive: {
    borderColor: theme.colors.primary,
    backgroundColor: '#EAF5EE',
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: theme.colors.muted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioActive: {
    borderColor: theme.colors.primary,
  },
  radioDot: {
    width: 11,
    height: 11,
    borderRadius: 6,
    backgroundColor: theme.colors.primary,
  },
  optionText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 21,
    color: theme.colors.text,
  },
  optionTextActive: {
    fontWeight: '600',
    color: theme.colors.primaryDark,
  },
  error: {
    color: theme.colors.danger,
    fontSize: 14,
  },
  button: {
    minHeight: 54,
    borderRadius: 15,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 6,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  note: {
    textAlign: 'center',
    color: theme.colors.muted,
    fontSize: 13,
  },
});
