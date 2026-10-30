import { useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { router } from 'expo-router';
import { changeProfilePassword } from '../../api/profile';
import { useAuth } from '../../auth/AuthProvider';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { profileStyles as styles } from '../../profile/styles';

export default function PasswordScreen() {
  const { finishPasswordChange } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function save() {
    if (next.length < 8 || next.length > 128 || !current) {
      setError('Новий пароль має містити 8–128 символів.');
      return;
    }
    if (next !== confirm) {
      setError('Підтвердження пароля не збігається.');
      return;
    }
    if (current === next) {
      setError('Новий пароль має відрізнятися від поточного.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await changeProfilePassword({ current_password: current, new_password: next });
      finishPasswordChange();
      router.replace('/login?password=changed');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Не вдалося змінити пароль.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Змінити пароль</Text>
      <Text style={styles.subtitle}>
        Після зміни всі попередні сеанси завершаться. Увійди з новим паролем.
      </Text>
      <View style={styles.card}>
        <FormField label="Поточний пароль" value={current} onChangeText={setCurrent}
          secureTextEntry autoCapitalize="none" />
        <FormField label="Новий пароль" value={next} onChangeText={setNext}
          secureTextEntry autoCapitalize="none" />
        <FormField label="Повтори новий пароль" value={confirm} onChangeText={setConfirm}
          secureTextEntry autoCapitalize="none" />
        {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
        <Button title="Змінити пароль" disabled={saving} loading={saving}
          onPress={() => { void save(); }} />
      </View>
    </ScrollView>
  );
}
