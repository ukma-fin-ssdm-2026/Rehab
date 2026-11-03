import { StyleSheet } from 'react-native';
import { theme } from '../constants/theme';

export const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: theme.colors.background, padding: 22, paddingTop: 32, paddingBottom: 40, gap: 18 },
  eyebrow: { color: theme.colors.highlight, fontSize: 12, letterSpacing: 1.5, fontWeight: '500' },
  title: { color: theme.colors.text, fontSize: 29, fontWeight: '400' },
  subtitle: { color: theme.colors.muted, fontSize: 15, lineHeight: 23 },
  card: { ...theme.effects.card, backgroundColor: theme.colors.surface, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 20, padding: 18, gap: 12 },
  heading: { fontSize: 19, fontWeight: '400', color: theme.colors.text },
  text: { color: theme.colors.text, fontSize: 15, lineHeight: 23 },
  muted: { color: theme.colors.muted, fontSize: 14, lineHeight: 21 },
  code: { fontSize: 24, letterSpacing: 2, fontWeight: '400', color: theme.colors.text },
  row: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 12 },
  grow: { flex: 1, minWidth: 130 },
  link: { color: theme.colors.text, fontWeight: '500', fontSize: 15 },
  action: { minHeight: 44, justifyContent: 'center', paddingVertical: 10 },
  danger: { color: theme.colors.danger, fontWeight: '500', fontSize: 15 },
  error: { backgroundColor: theme.colors.dangerSurface, padding: 16, borderRadius: 16, gap: 10 },
  notice: { ...theme.effects.card, backgroundColor: theme.colors.accent, padding: 18, borderRadius: 18, gap: 10 },
  disabled: { opacity: 0.5 },
  segmented: { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: theme.colors.accent, borderRadius: 14, padding: 5, gap: 4 },
  segment: { flex: 1, minWidth: 60, minHeight: 44, justifyContent: 'center', alignItems: 'center', borderRadius: 10, paddingHorizontal: 5 },
  selected: { backgroundColor: theme.colors.surface },
  modalBackdrop: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 22, backgroundColor: theme.colors.backdrop },
  modalCard: { width: '100%', maxWidth: 430 },
});
