
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { getCalendarEntriesUrl } from "../../config/api";

type CalendarEntry = {
  record_id: number;
  user_id: number;
  date: string;
  status: string;
  trigger_category: string | null;
  created_at: string;
};

type CalendarResponse = {
  items: CalendarEntry[];
  total: number;
  limit: number;
  offset: number;
};


export default function CalendarScreen() {
  const [data, setData] = useState<CalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadEntries() {
      try {
        const response = await fetch(getCalendarEntriesUrl(), {
          method: 'GET',
          headers: {
            Authorization: 'Bearer user-42',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result: CalendarResponse = await response.json();
        setData(result);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Не вдалося завантажити календар',
        );
      } finally {
        setLoading(false);
      }
    }

    loadEntries();
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Календар</Text>

      {loading && (
        <View style={styles.message}>
          <ActivityIndicator size="large" color="#3C8D72" />
          <Text style={styles.secondary}>Завантаження записів...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Не вдалося завантажити записи</Text>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {data && !loading && !error && (
        <View style={styles.content}>
          <Text style={styles.total}>Усього записів: {data.total}</Text>

          {data.items.length === 0 ? (
            <Text style={styles.secondary}>Записів поки немає.</Text>
          ) : (
            data.items.map((item) => (
              <View key={item.record_id} style={styles.card}>
                <Text style={styles.date}>{item.date}</Text>
                <Text style={styles.status}>
                  Статус: {item.status === 'relapse' ? 'Зрив' : 'Тверезість'}
                </Text>
                <Text style={styles.secondary}>
                  Тригер: {item.trigger_category ?? 'Не вказано'}
                </Text>
              </View>
            ))
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#F5FAF7',
    padding: 24,
    paddingTop: 48,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#245C4A',
    marginBottom: 20,
  },
  content: {
    gap: 12,
  },
  message: {
    alignItems: 'center',
    gap: 12,
    padding: 24,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DCE8E0',
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    gap: 6,
  },
  date: {
    fontSize: 17,
    fontWeight: '700',
    color: '#245C4A',
  },
  status: {
    fontSize: 15,
    color: '#20352D',
  },
  total: {
    fontSize: 16,
    fontWeight: '600',
    color: '#20352D',
  },
  secondary: {
    fontSize: 14,
    color: '#718078',
  },
  errorBox: {
    backgroundColor: '#FDECEC',
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#A52A2A',
  },
  errorText: {
    fontSize: 14,
    color: '#A52A2A',
  },
});
