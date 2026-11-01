import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useEffect, useState } from 'react';
import { Pressable, Text } from 'react-native';
import { router } from 'expo-router';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../auth/AuthProvider';
import { profileStyles as styles } from '../../profile/styles';

type MentorResponse = { item: { mentor: { nickname: string; email: string } } | null };

export default function PrivacyScreen() {
  const { user } = useAuth();
  return <PrivacyContent key={user?.user_id ?? 'guest'} />;
}

function PrivacyContent() {
  const [mentor, setMentor] = useState<MentorResponse['item']>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    apiRequest<MentorResponse>('/mentorships/my-mentor').then(result => {
      if (active) setMentor(result.item);
    }).catch(() => {
      if (active) setError(true);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Приватність і доступ</Text>
      <GlassCard style={styles.card}>
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
        <Text style={styles.field}>Мій ментор</Text>
        {loading ? <Text style={styles.muted}>Завантаження…</Text> :
          error ? <Text style={styles.error}>Не вдалося завантажити дані.</Text> :
          mentor ? <Text style={styles.text}>
            {mentor.mentor.nickname} · {mentor.mentor.email}
          </Text> : <Text style={styles.muted}>Активного ментора немає.</Text>}
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
      </GlassCard>
    </ScrollView>
  );
}
