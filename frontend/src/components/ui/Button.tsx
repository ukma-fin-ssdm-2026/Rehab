import { Pressable, Text, StyleSheet } from 'react-native';
import { theme } from '../../constants/theme';

export function Button({
  title, onPress, disabled = false, loading = false,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={[styles.button, (disabled || loading) && styles.disabled]}
    >
      <Text style={styles.text}>{loading ? 'Зачекайте…' : title}</Text>
    </Pressable>
  );
}
const styles = StyleSheet.create({
  button: {
    backgroundColor: theme.colors.primary,
    borderRadius: 14,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  disabled: { opacity: 0.55 },
  text: { color: '#FFFFFF', fontWeight: '700', fontSize: 16 },
});
