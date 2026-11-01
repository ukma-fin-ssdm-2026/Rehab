import { StyleSheet, View } from 'react-native';
import Svg, { Defs, G, LinearGradient, Path, Rect, Stop } from 'react-native-svg';
import { theme } from '../../constants/theme';

/** Vector foliage inspired by the saved Figma reference, not an exported asset. */
export function BotanicalBackdrop() {
  return (
    <View pointerEvents="none" accessible={false} style={styles.backdrop}>
      <Svg width="100%" height="100%" viewBox="0 0 430 230" preserveAspectRatio="xMidYMin slice">
        <Defs>
          <LinearGradient id="rehab-foliage-fade" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={theme.colors.background} stopOpacity="0" />
            <Stop offset="1" stopColor={theme.colors.background} stopOpacity="1" />
          </LinearGradient>
        </Defs>
        <G fill={theme.colors.hero} stroke={theme.colors.progressTrack} strokeWidth="0.7">
          <Path d="M-30 130Q-20 42 48 16Q69 81-30 130Z" />
          <Path d="M8 76Q27 8 95-12Q105 47 8 76Z" />
          <Path d="M58 36Q89-13 146-5Q137 46 58 36Z" />
          <Path d="M-8 181Q12 102 75 82Q85 147-8 181Z" />
          <Path d="M440 172Q383 114 366 36Q430 36 440 172Z" />
          <Path d="M412 96Q340 60 332-7Q400-1 412 96Z" />
          <Path d="M369 37Q301 47 270-9Q322-39 369 37Z" />
        </G>
        <G fill="none" stroke={theme.colors.highlight} strokeWidth="0.6" opacity="0.45">
          <Path d="M0 118L48 16M15 72L95 0M0 169L75 82M430 156L366 36M409 88L332 0" />
          <Path d="M13 93L9 65M26 72L52 72M27 57L27 36M44 42L75 39M406 108L379 107M393 77L405 47M378 58L355 59" />
        </G>
        <Rect width="430" height="230" fill="url(#rehab-foliage-fade)" />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: { position: 'absolute', top: 0, left: 0, right: 0, height: 230, opacity: 0.65 },
});
