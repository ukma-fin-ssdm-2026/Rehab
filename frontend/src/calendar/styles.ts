import { StyleSheet } from 'react-native';
import { theme } from '../constants/theme';

export const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 22,
    paddingTop: 32,
    gap: 16,
  },
  back: {
    color: theme.colors.primaryDark,
    fontSize: 15,
    fontWeight: '600',
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    color: theme.colors.muted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: -10,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: 18,
    padding: 17,
    gap: 11,
  },
  label: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '700',
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    color: theme.colors.text,
    paddingHorizontal: 13,
    fontSize: 15,
  },
  hint: {
    fontSize: 12,
    lineHeight: 18,
    color: theme.colors.muted,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  addSmall: {
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderRadius: 12,
    backgroundColor: theme.colors.accent,
  },
  addSmallText: {
    fontWeight: '700',
    color: theme.colors.primaryDark,
  },
  drinkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  removeText: {
    color: theme.colors.danger,
    fontWeight: '600',
  },
  typeList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeOption: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 12,
    paddingVertical: 9,
    paddingHorizontal: 11,
    backgroundColor: '#FFFFFF',
  },
  typeActive: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.accent,
  },
  typeText: {
    fontSize: 13,
    color: theme.colors.text,
  },
  typeTextActive: {
    fontWeight: '700',
    color: theme.colors.primaryDark,
  },
  commentInput: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 12,
    padding: 13,
    fontSize: 15,
    color: theme.colors.text,
  },
  errorBox: {
    padding: 14,
    borderRadius: 12,
    backgroundColor: '#FDECEC',
  },
  errorText: {
    color: theme.colors.danger,
    fontSize: 14,
    lineHeight: 20,
  },
  button: {
    minHeight: 53,
    borderRadius: 15,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
  },
  buttonDisabled: {
    opacity: 0.65,
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 16,
  },
  cancelButton: {
    alignItems: 'center',
    padding: 12,
  },
  cancelText: {
    color: theme.colors.muted,
    fontWeight: '600',
  },
});
