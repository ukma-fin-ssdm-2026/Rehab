
import { StyleSheet, Text, View } from 'react-native';

type Props = {
  title: string;
};

export default function ScreenPlaceholder({ title }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>Твій шлях до змін починається тут.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F5FAF7',
    padding: 24,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#245C4A',
  },
  subtitle: {
    marginTop: 10,
    fontSize: 15,
    color: '#718078',
    textAlign: 'center',
  },
});
