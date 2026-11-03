import { ImageBackground, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';
import { LotusMark } from './LotusMark';
import { theme } from '../../constants/theme';

/** Illustration around the existing total; the ring is decorative, not goal progress. */
export function JourneyOrb({ total }: { total: number }) {
  return <View style={styles.frame}>
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" viewBox="0 0 320 320" aria-hidden={true}>
      <Defs>
        <LinearGradient id="rehab-orb-rim" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor="#77588C" />
          <Stop offset="0.48" stopColor="#C4D56C" />
          <Stop offset="0.75" stopColor="#88944C" />
          <Stop offset="1" stopColor="#58416D" />
        </LinearGradient>
      </Defs>
      <Circle cx="160" cy="160" r="154" fill="none" stroke="url(#rehab-orb-rim)" strokeWidth="2" />
    </Svg>
    <ImageBackground source={require('../../../assets/visual/night-mountains.png')}
      style={styles.landscape} imageStyle={styles.image} accessible={false}>
      <View style={styles.shade} />
      <LotusMark size={42} />
      <Text style={styles.label}>Усього тверезих днів</Text>
      <Text style={styles.number}>{total}</Text>
      <Text style={styles.caption}>Твій прогрес має значення</Text>
    </ImageBackground>
  </View>;
}

const styles = StyleSheet.create({
  frame: { width: '100%', maxWidth: 280, aspectRatio: 1, alignSelf: 'center',
    padding: 15, marginVertical: 4, borderRadius: 999,
    boxShadow: '0 0 38px rgba(130,85,157,0.18), 0 0 22px rgba(170,190,89,0.07)' },
  landscape: { flex: 1, borderRadius: 999, overflow: 'hidden', justifyContent: 'center',
    alignItems: 'center', gap: 7, backgroundColor: theme.colors.surface,
    borderWidth: 1, borderColor: 'rgba(210,182,230,0.3)' },
  image: { width: '100%', height: '100%', borderRadius: 999 },
  shade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(8,6,16,0.35)' },
  label: { color: theme.colors.heroMuted, fontSize: 13, textAlign: 'center' },
  number: { fontSize: 68, lineHeight: 78, fontWeight: '300', color: theme.colors.text },
  caption: { color: theme.colors.heroMuted, fontSize: 12, textAlign: 'center', paddingHorizontal: 12 },
});
