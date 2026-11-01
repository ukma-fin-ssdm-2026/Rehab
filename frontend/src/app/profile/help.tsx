import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useState } from 'react';
import { Linking, Pressable, Text, View } from 'react-native';
import { profileStyles as styles } from '../../profile/styles';

const questions = [
  {
    title: 'Як рахуються тверезі дні?',
    answer: 'Після початку відстеження день без явного запису в календарі вважається тверезим. Дні до початку відстеження й майбутні дні не рахуються.',
  },
  {
    title: 'Як позначити зрив?',
    answer: 'Відкрий календар, вибери день і додай запис зі статусом «Зрив». Якщо запис уже є, його можна змінити лише в межах дозволеного часу.',
  },
  {
    title: 'Коли дозволено редагувати запис?',
    answer: 'Протягом 48 годин від створення запису, включно з точною межею. Після цього змінити запис не можна.',
  },
  {
    title: 'Як працюють етапи?',
    answer: 'Автоматичні етапи становлять 7, 30, 90, 180 і 365 днів. Досягнуті етапи залишаються виконаними навіть після зриву.',
  },
  {
    title: 'Що дозволяє особистий код?',
    answer: 'Людина, якій ти передала код, може приєднатися як ментор і читати твій календар та статистику за весь період, але не редагувати записи. Код не відкриває твій акаунт.',
  },
  {
    title: 'Чи можна завершити менторство?',
    answer: 'Так, будь-яка сторона може завершити зв’язок. Після цього читання даних блокується, а та сама пара більше не може відновити цей зв’язок у тому самому напрямку.',
  },
  {
    title: 'Як працюють скарги?',
    answer: 'У вкладці «Підтримка» можна поскаржитися на власного теперішнього або колишнього ментора, за потреби додавши його коментар. Рішення адміністратора стосується конкретного зв’язку.',
  },
  {
    title: 'Які повідомлення надходять?',
    answer: 'У застосунку доступні щоденні нагадування, повідомлення ментору про зрив підопічного та коментарі підтримки. Сповіщення можна прочитати в окремому екрані.',
  },
  {
    title: 'Що надходить на пошту?',
    answer: 'Тільки копія щоденного нагадування за твоєю згодою. Повідомлення про зрив і коментарі підтримки на email не дублюються.',
  },
  {
    title: 'Навіщо обирати стиль?',
    answer: 'Формальний, гумористичний, дзен або суворий стиль змінює автоматичні тексти. Особисті коментарі інших людей залишаються без змін.',
  },
];

export default function HelpScreen() {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Питання та відповіді</Text>
      <Text style={styles.subtitle}>Короткі пояснення про можливості Rehab.</Text>
      <GlassCard style={styles.card}>
        {questions.map((item, index) => (
          <View key={item.title} style={{ gap: 9 }}>
            <Pressable accessibilityRole="button"
              accessibilityState={{ expanded: open === index }}
              onPress={() => setOpen(open === index ? null : index)}>
              <Text style={styles.field}>{open === index ? '−' : '+'} {item.title}</Text>
            </Pressable>
            {open === index && <Text style={styles.text}>{item.answer}</Text>}
          </View>
        ))}
      </GlassCard>
      <Pressable accessibilityRole="link"
        onPress={() => { void Linking.openURL('mailto:rehab.support.web@gmail.com'); }}>
        <Text style={styles.link}>rehab.support.web@gmail.com</Text>
      </Pressable>
      <Text style={styles.muted}>
        Якщо поштову програму не налаштовано, адресу можна скопіювати вручну.
      </Text>
    </ScrollView>
  );
}
