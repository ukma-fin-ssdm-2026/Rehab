import { View, Text, TextInput, StyleSheet, type TextInputProps } from 'react-native';
import { theme } from '../../constants/theme';

export function FormField({
  label, error, ...props
}: TextInputProps & { label: string; error?: string }) {
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        accessibilityHint={error}
        placeholderTextColor={theme.colors.muted}
        style={[styles.input, !!error && styles.invalid]}
        {...props}
      />
      {!!error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}
const styles = StyleSheet.create({
  wrapper: { gap: 6 },
  label: { fontSize: 14, fontWeight: '500', color: theme.colors.text },
  input: { ...theme.effects.input,
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: 18,
    minHeight: 48,
    paddingHorizontal: 14,
    color: theme.colors.text,
  },
  invalid: { borderColor: theme.colors.danger },
  error: { color: theme.colors.danger, fontSize: 12 },
});
