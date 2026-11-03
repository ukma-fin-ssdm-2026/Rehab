import { GlassCard } from './visual/GlassCard';

import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { theme } from '../constants/theme';

type Props = {
  title: string;
  subtitle?: string;
};

export default function ScreenPlaceholder({
  title,
  subtitle = 'Функція буде доступна пізніше.',
}: Props) {
  return (
    <View style={styles.container}>
      <Pressable style={styles.back} onPress={() => router.replace('/(tabs)/profile')}>
        <Text style={styles.backText}>← До профілю</Text>
      </Pressable>

      <GlassCard style={styles.card}>
        <View style={styles.icon}>
          <Text style={styles.iconText}>✦</Text>
        </View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>СКОРО</Text>
        </View>
      </GlassCard>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
    padding: 24,
  },
  back: {
    position: 'absolute',
    top: 28,
    left: 24,
    zIndex: 1,
    paddingVertical: 10,
  },
  backText: {
    color: theme.colors.text,
    fontSize: 15,
    fontWeight: '500',
  },
  card: { ...theme.effects.card,
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: 24,
    padding: 28,
    gap: 14,
  },
  icon: {
    width: 58,
    height: 58,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.accent,
  },
  iconText: {
    fontSize: 29,
    color: theme.colors.text,
  },
  title: {
    fontSize: 25,
    fontWeight: '400',
    color: theme.colors.text,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: theme.colors.muted,
    textAlign: 'center',
  },
  badge: {
    backgroundColor: theme.colors.accent,
    borderRadius: 10,
    paddingVertical: 7,
    paddingHorizontal: 12,
    marginTop: 4,
  },
  badgeText: {
    fontSize: 11,
    letterSpacing: 1.2,
    fontWeight: '400',
    color: theme.colors.text,
  },
});
