
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { theme } from '../../constants/theme';

export default function FriendsSupportScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТИ НЕ САМА</Text>
      <Text style={styles.title}>Підтримка друзів</Text>
      <Text style={styles.subtitle}>
        Підтримка може зробити шлях легшим. Тут згодом можна буде ділитися
        прогресом і знаходити людей, які розуміють тебе.
      </Text>

      <View style={styles.hero}>
        <View style={styles.icon}>
          <Text style={styles.iconText}>♡</Text>
        </View>
        <Text style={styles.heroTitle}>Простір підтримки</Text>
        <Text style={styles.heroText}>
          Твої досягнення, переживання та особисті межі заслуговують на повагу.
        </Text>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Що буде доступно?</Text>
        <View style={styles.feature}>
          <Text style={styles.featureIcon}>✓</Text>
          <Text style={styles.featureText}>Запрошення друзів</Text>
        </View>
        <View style={styles.feature}>
          <Text style={styles.featureIcon}>✓</Text>
          <Text style={styles.featureText}>Підтримка та слова заохочення</Text>
        </View>
        <View style={styles.feature}>
          <Text style={styles.featureIcon}>✓</Text>
          <Text style={styles.featureText}>Обмін досягненнями за власним бажанням</Text>
        </View>
      </View>

      <View style={styles.notice}>
        <Text style={styles.noticeTitle}>Функція буде доступна пізніше</Text>
        <Text style={styles.noticeText}>
          Це демонстраційний екран. Додавання друзів і обмін даними поки не
          реалізовані.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: 22,
    paddingTop: 32,
    paddingBottom: 36,
    gap: 18,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
    color: theme.colors.primary,
  },
  title: {
    fontSize: 29,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 23,
    color: theme.colors.muted,
  },
  hero: {
    alignItems: 'center',
    backgroundColor: theme.colors.primaryDark,
    borderRadius: 23,
    padding: 25,
    gap: 13,
  },
  icon: {
    width: 64,
    height: 64,
    borderRadius: 23,
    backgroundColor: '#477C66',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 37,
    color: '#FFFFFF',
  },
  heroTitle: {
    fontSize: 21,
    fontWeight: '800',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  heroText: {
    fontSize: 14,
    lineHeight: 22,
    color: '#E1F1E7',
    textAlign: 'center',
  },
  infoCard: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 20,
    padding: 19,
    gap: 15,
  },
  infoTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: theme.colors.primaryDark,
    marginBottom: 2,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
  },
  featureIcon: {
    fontSize: 17,
    fontWeight: '800',
    color: theme.colors.primary,
  },
  featureText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    color: theme.colors.text,
  },
  notice: {
    backgroundColor: theme.colors.accent,
    borderRadius: 17,
    padding: 17,
    gap: 8,
  },
  noticeTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  noticeText: {
    fontSize: 13,
    lineHeight: 20,
    color: theme.colors.text,
  },
});
