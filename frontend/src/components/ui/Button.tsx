import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, Text, StyleSheet } from 'react-native';
import { theme } from '../../constants/theme';

export function Button({
  title, onPress, disabled = false, loading = false, variant = 'primary',
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'outline';
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={[styles.button, variant === 'outline' && styles.outline, (disabled || loading) && styles.disabled]}
    >
      <LinearGradient pointerEvents="none" colors={variant === 'outline' ? theme.gradients.outline : theme.gradients.button}
        start={{x:0,y:0}} end={{x:1,y:1}} style={styles.gradient} />
      <Text style={[styles.text, variant === 'outline' && styles.outlineText]}>{loading ? 'Зачекайте…' : title}</Text>
    </Pressable>
  );
}
const styles = StyleSheet.create({
  gradient: { ...StyleSheet.absoluteFill, borderRadius: 25 },
  button: {
    ...theme.effects.button,
    backgroundColor: theme.colors.primary,
    borderRadius: 26,
    borderWidth: 1,
    borderColor: theme.colors.buttonBorder,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  outline: { backgroundColor: theme.colors.surface, borderColor: theme.colors.danger },
  outlineText: { color: theme.colors.danger },
  disabled: { opacity: 0.55 },
  text: { color: theme.colors.text, fontWeight: '500', fontSize: 16 },
});
