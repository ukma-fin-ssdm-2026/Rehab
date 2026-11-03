import { useId } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

/** Decorative local assets, excluded from input and accessibility. */
export function BotanicalBackdrop() {
  const glowId = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  return <View pointerEvents="none" accessible={false} style={styles.backdrop}>
    <Svg width="100%" height="100%" aria-hidden={true}>
      <Defs>
        <RadialGradient id={glowId} cx="50%" cy="30%" rx="65%" ry="55%">
          <Stop offset="0" stopColor="#745084" stopOpacity="0.24" />
          <Stop offset="1" stopColor="#0B0A10" stopOpacity="0" />
        </RadialGradient>
      </Defs>
      <Rect width="100%" height="100%" fill={`url(#${glowId})`} />
    </Svg>
    <Image source={require('../../../assets/visual/olive-branch.png')} accessible={false}
      resizeMode="contain" style={styles.leftLeaf} />
    <Image source={require('../../../assets/visual/olive-branch.png')} accessible={false}
      resizeMode="contain" style={styles.rightLeaf} />
  </View>;
}
const styles = StyleSheet.create({
  backdrop: { position: 'absolute', top: 0, left: 0, right: 0, height: 650, overflow: 'hidden' },
  leftLeaf: { position: 'absolute', width: 210, height: 210, top: -115, left: -65,
    opacity: 0.58, transform: [{ rotate: '20deg' }] },
  rightLeaf: { position: 'absolute', width: 155, height: 260, right: -93, top: 180,
    opacity: 0.32, transform: [{ rotate: '-25deg' }] },
});
