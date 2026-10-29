import { ActivityIndicator, Pressable, Text, View, StyleSheet } from 'react-native';
import { theme } from '../../constants/theme';

type ScreenStateProps = {
  state: 'loading' | 'empty' | 'error';
  message?: string;
  onRetry?: () => void;
};

export function ScreenState({ state, message, onRetry }: ScreenStateProps) {
  return (
    <View style={styles.container}>
      {state === 'loading' && <ActivityIndicator color={theme.colors.primary} />}
      <Text style={styles.text}>
        {message ?? (state === 'loading' ? 'Завантаження…' :
          state === 'empty' ? 'Поки немає даних' : 'Не вдалося завантажити дані')}
      </Text>
      {state === 'error' && onRetry && (
        <Pressable accessibilityRole="button" onPress={onRetry}>
          <Text style={styles.retry}>Спробувати знову</Text>
        </Pressable>
      )}
    </View>
  );
}
const styles = StyleSheet.create({
  container: { alignItems: 'center', padding: 24, gap: 12 },
  text: { color: theme.colors.text, textAlign: 'center' },
  retry: { color: theme.colors.primary, fontWeight: '700' },
});
