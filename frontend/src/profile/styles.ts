import { StyleSheet } from 'react-native';
import { theme } from '../constants/theme';

export const profileStyles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 24,
    paddingBottom: 40,
    gap: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '400',
    color: theme.colors.text,
  },
  subtitle: {
    color: theme.colors.muted,
    fontSize: 15,
    lineHeight: 23,
  },
  card: { ...theme.effects.card,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 18,
    padding: 20,
    gap: 14,
  },
  field: {
    color: theme.colors.text,
    fontSize: 17,
    fontWeight: '500',
  },
  text: {
    color: theme.colors.text,
    lineHeight: 22,
  },
  muted: {
    color: theme.colors.muted,
    lineHeight: 21,
  },
  error: {
    color: theme.colors.danger,
    lineHeight: 21,
  },
  link: {
    paddingVertical: 10,
    color: theme.colors.highlight,
    fontWeight: '500',
  },
});
