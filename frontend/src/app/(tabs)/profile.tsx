
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { theme } from '../../constants/theme';

const menuItems = [
  { title: 'Редагувати профіль', subtitle: 'Ім’я та нікнейм', icon: '✎', route: '/placeholders/edit-profile' },
  { title: 'Змінити пароль', subtitle: 'Налаштування доступу', icon: '⌑', route: '/placeholders/change-password' },
  { title: 'Сповіщення', subtitle: 'Керування нагадуваннями', icon: '♧', route: '/placeholders/notifications' },
  { title: 'Стиль сповіщень', subtitle: 'Обери свій настрій', icon: '✦', route: '/placeholders/notification-vibe' },
  { title: 'Допомога', subtitle: 'Відповіді на запитання', icon: '?', route: '/placeholders/help' },
  { title: 'Конфіденційність', subtitle: 'Твої дані та приватність', icon: '◇', route: '/placeholders/privacy' },
];

export default function ProfileScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>ТВІЙ ПРОСТІР</Text>
      <Text style={styles.title}>Профіль</Text>

      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>R</Text>
        </View>
        <Text style={styles.name}>Користувач Rehab</Text>
        <Text style={styles.nickname}>@rehab_user</Text>
        <Text style={styles.profileNote}>
          Твій шлях — твої правила. Рухайся у власному темпі.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Налаштування</Text>

      <View style={styles.menu}>
        {menuItems.map((item) => (
          <Pressable
            key={item.route}
            style={styles.menuItem}
            onPress={() => router.push(item.route as never)}
          >
            <View style={styles.menuIcon}>
              <Text style={styles.menuIconText}>{item.icon}</Text>
            </View>
            <View style={styles.menuText}>
              <Text style={styles.menuTitle}>{item.title}</Text>
              <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
            </View>
            <Text style={styles.arrow}>›</Text>
          </Pressable>
        ))}
      </View>

      <Pressable
        style={styles.logout}
        onPress={() => router.replace('/login')}
      >
        <Text style={styles.logoutText}>Вийти з акаунта</Text>
      </Pressable>

      <Text style={styles.version}>REHAB · ДЕМОПРОТОТИП</Text>
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
    fontSize: 30,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  profileCard: {
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 22,
    padding: 24,
    gap: 9,
  },
  avatar: {
    width: 76,
    height: 76,
    borderRadius: 28,
    backgroundColor: theme.colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 36,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  name: {
    fontSize: 21,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  nickname: {
    fontSize: 14,
    color: theme.colors.primary,
  },
  profileNote: {
    textAlign: 'center',
    fontSize: 13,
    lineHeight: 20,
    color: theme.colors.muted,
    marginTop: 5,
  },
  sectionTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: theme.colors.primaryDark,
  },
  menu: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 19,
    paddingHorizontal: 14,
  },
  menuItem: {
    minHeight: 76,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    paddingVertical: 12,
  },
  menuIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
  },
  menuIconText: {
    fontSize: 21,
    fontWeight: '700',
    color: theme.colors.primaryDark,
  },
  menuText: {
    flex: 1,
    gap: 4,
  },
  menuTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.text,
  },
  menuSubtitle: {
    fontSize: 12,
    color: theme.colors.muted,
  },
  arrow: {
    fontSize: 25,
    color: theme.colors.muted,
  },
  logout: {
    minHeight: 50,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.colors.danger,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoutText: {
    fontWeight: '700',
    color: theme.colors.danger,
  },
  version: {
    textAlign: 'center',
    fontSize: 10,
    letterSpacing: 1.5,
    color: theme.colors.muted,
  },
});
