
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { apiRequest } from '../api/client';
import { theme } from '../constants/theme';

const drinkTypes = [
  { label: 'Пиво', value: 'beer' },
  { label: 'Вино', value: 'wine' },
  { label: 'Міцний алкоголь', value: 'spirits' },
  { label: 'Коктейль', value: 'cocktail' },
  { label: 'Інше', value: 'other' },
] as const;

type Drink = {
  id: number;
  type: (typeof drinkTypes)[number]['value'];
  volume: string;
};

function todayString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function AddEntryScreen() {
  const [date, setDate] = useState(todayString());
  const [drinks, setDrinks] = useState<Drink[]>([
    { id: 1, type: 'beer', volume: '' },
  ]);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function updateDrink(id: number, changes: Partial<Drink>) {
    setDrinks((current) =>
      current.map((drink) =>
        drink.id === id ? { ...drink, ...changes } : drink,
      ),
    );
  }

  function addDrink() {
    setDrinks((current) => [
      ...current,
      { id: Date.now(), type: 'beer', volume: '' },
    ]);
  }

  function removeDrink(id: number) {
    setDrinks((current) => current.filter((drink) => drink.id !== id));
  }

  async function saveEntry() {
    setError('');

    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      setError('Введи дату у форматі РРРР-ММ-ДД.');
      return;
    }

    const [year, month, day] = date.split('-').map(Number);
    const parsedDate = new Date(year, month - 1, day);
    const validDate =
      parsedDate.getFullYear() === year &&
      parsedDate.getMonth() === month - 1 &&
      parsedDate.getDate() === day;

    if (!validDate) {
      setError('Введи коректну дату.');
      return;
    }

    if (date > todayString()) {
      setError('Не можна додати запис на майбутню дату.');
      return;
    }

    if (drinks.length === 0) {
      setError('Додай хоча б один напій.');
      return;
    }

    const parsedDrinks = drinks.map((drink) => ({
      type: drink.type,
      volume_ml: Number(drink.volume),
    }));

    if (
      parsedDrinks.some(
        (drink) =>
          !Number.isInteger(drink.volume_ml) || drink.volume_ml <= 0,
      )
    ) {
      setError('Для кожного напою вкажи цілий об’єм у мілілітрах більше нуля.');
      return;
    }

    setSaving(true);

    try {
      await apiRequest('/calendar/entries', {
        method: 'POST',
        body: JSON.stringify({
          date,
          status: 'relapse',
          trigger_category: null,
          drinks: parsedDrinks,
          comment: comment.trim() || null,
        }),
      });

      router.replace('/(tabs)/home');
    } catch (err) {
      setError(
        err instanceof Error
          ? `Не вдалося зберегти запис: ${err.message}`
          : 'Не вдалося зберегти запис.',
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()}>
        <Text style={styles.back}>← Назад</Text>
      </Pressable>

      <Text style={styles.title}>Новий запис</Text>
      <Text style={styles.subtitle}>
        Заповни інформацію без осуду до себе.
      </Text>

      <View style={styles.card}>
        <Text style={styles.label}>Дата</Text>
        <TextInput
          value={date}
          onChangeText={setDate}
          placeholder="РРРР-ММ-ДД"
          style={styles.input}
          maxLength={10}
          autoCapitalize="none"
        />
        <Text style={styles.hint}>Формат: 2026-10-15. Не пізніше сьогодні.</Text>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Напої</Text>
        <Pressable onPress={addDrink} style={styles.addSmall}>
          <Text style={styles.addSmallText}>＋ Додати</Text>
        </Pressable>
      </View>

      {drinks.map((drink, index) => (
        <View key={drink.id} style={styles.card}>
          <View style={styles.drinkHeader}>
            <Text style={styles.label}>Напій {index + 1}</Text>
            {drinks.length > 1 && (
              <Pressable onPress={() => removeDrink(drink.id)}>
                <Text style={styles.removeText}>Видалити</Text>
              </Pressable>
            )}
          </View>

          <Text style={styles.label}>Тип напою</Text>
          <View style={styles.typeList}>
            {drinkTypes.map((item) => {
              const active = drink.type === item.value;
              return (
                <Pressable
                  key={item.value}
                  onPress={() => updateDrink(drink.id, { type: item.value })}
                  style={[styles.typeOption, active && styles.typeActive]}
                >
                  <Text
                    style={[styles.typeText, active && styles.typeTextActive]}
                  >
                    {item.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={styles.label}>Об’єм (мл)</Text>
          <TextInput
            value={drink.volume}
            onChangeText={(value) =>
              updateDrink(drink.id, {
                volume: value.replace(/[^0-9]/g, ''),
              })
            }
            placeholder="Наприклад, 330"
            keyboardType="number-pad"
            style={styles.input}
          />
        </View>
      ))}

      <View style={styles.card}>
        <Text style={styles.label}>Коментар (необов’язково)</Text>
        <TextInput
          value={comment}
          onChangeText={setComment}
          placeholder="Що хочеш зафіксувати?"
          multiline
          textAlignVertical="top"
          style={styles.commentInput}
        />
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <Pressable
        style={[styles.button, saving && styles.buttonDisabled]}
        onPress={saveEntry}
        disabled={saving}
      >
        {saving ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.buttonText}>Зберегти запис</Text>
        )}
      </Pressable>

      <Pressable
        style={styles.cancelButton}
        onPress={() => router.back()}
        disabled={saving}
      >
        <Text style={styles.cancelText}>Скасувати</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
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
