import { ScrollView, type ScrollViewProps } from 'react-native';
import { BotanicalBackdrop } from './BotanicalBackdrop';
import { theme } from '../../constants/theme';

/** A shared visual layer only; scrolling and event props are forwarded intact. */
export function ScreenScrollView({ children, style, contentContainerStyle, ...props }: ScrollViewProps) {
  return <ScrollView style={[{ backgroundColor: theme.colors.background }, style]}
    contentContainerStyle={[{ flexGrow: 1, width: '100%', maxWidth: 1040, alignSelf: 'center' }, contentContainerStyle]} {...props}>
    <BotanicalBackdrop />
    {children}
  </ScrollView>;
}
