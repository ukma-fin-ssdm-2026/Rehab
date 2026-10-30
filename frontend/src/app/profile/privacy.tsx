import { Pressable, ScrollView, Text, View } from 'react-native';
import { router } from 'expo-router';
import { profileStyles as styles } from '../../profile/styles';

export default function PrivacyScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Приватність і доступ</Text>
      <View style={styles.card}>
        <Text style={styles.field}>Твої дані належать тобі</Text>
        <Text style={styles.text}>
          Календар і статистика приватні. Лише твій активний ментор може читати їх
          після того, як самостійно введе твій особистий код.
        </Text>
        <Text style={styles.field}>Особистий код</Text>
        <Text style={styles.text}>
          Код показується лише тобі у вкладці «Підтримка». Це не пароль.
          Передавай його лише людині, якій хочеш надати доступ до календаря
          та статистики за весь період. Код не дає права редагувати твої записи.
        </Text>
        <Text style={styles.field}>Завершення менторства</Text>
        <Text style={styles.text}>
          Кожна сторона може завершити зв’язок. Після завершення читання
          календаря й статистики припиняється. Ця сама пара не зможе знову
          приєднатися в тому самому напрямку, а вже отримані повідомлення
          та коментарі зберігаються.
        </Text>
        <Text style={styles.field}>Коментарі</Text>
        <Text style={styles.text}>
          Коментар підтримки бачать його отримувач і автор у межах власних
          повідомлень. Адміністратор отримує текст лише тоді, коли його
          додають до скарги як доказ.
        </Text>
        <Pressable accessibilityRole="button"
          onPress={() => router.push('/(tabs)/friends-support')}>
          <Text style={styles.link}>Перейти до підтримки та керування менторством</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}
