import { LinearGradient } from 'expo-linear-gradient';
import { Image, View, StyleSheet, type ViewProps } from 'react-native';
import { theme } from '../../constants/theme';

/** One native view, preserving the caller's layout and accessibility props. */
export function GlassCard({ style, children, illustrated = false, ...props }: ViewProps & { illustrated?: boolean }) {
  return <LinearGradient colors={theme.gradients.card} start={{ x: 0, y: 0 }}
    end={{ x: 1, y: 1 }} style={[styles.glass, style]} {...props}>
    {illustrated && <View pointerEvents="none" accessible={false} style={styles.art}>
      <Image source={require('../../../assets/visual/night-mountains.png')}
        accessible={false} resizeMode="cover" style={{width:'100%',height:'100%'}} />
    </View>}
    {children}
  </LinearGradient>;
}

const styles = StyleSheet.create({
  glass: {
    borderWidth: 1, borderColor: theme.colors.border, borderRadius: 24,
    ...theme.effects.card, overflow: 'hidden',
  },
  art: { position: 'absolute', bottom: 0, right: 0, width: '65%', height: '100%', opacity: 0.22 },
});
