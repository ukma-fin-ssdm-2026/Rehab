import Svg, { G, Path } from 'react-native-svg';
import { theme } from '../../constants/theme';

/** Decorative mark; it carries no state or action. */
export function LotusMark({ size = 44 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 80 80" aria-hidden={true}>
      <G fill="none" stroke={theme.colors.highlight} strokeWidth={1.7}
        strokeLinecap="round" strokeLinejoin="round">
        <Path d="M40 64C24 51 27 27 40 10C53 27 56 51 40 64Z" />
        <Path d="M40 64C20 61 11 43 12 23C30 28 40 43 40 64Z" />
        <Path d="M40 64C60 61 69 43 68 23C50 28 40 43 40 64Z" />
        <Path d="M40 64C23 70 10 60 5 45C22 43 34 48 40 64Z" />
        <Path d="M40 64C57 70 70 60 75 45C58 43 46 48 40 64Z" />
        <Path d="M40 64V28" />
      </G>
    </Svg>
  );
}
