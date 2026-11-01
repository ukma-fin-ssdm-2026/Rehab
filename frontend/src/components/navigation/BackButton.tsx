import { Pressable, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { goBack } from '../../navigation/back';
import { theme } from '../../constants/theme';

export function BackButton() {
  const {user}=useAuth();
  return <SafeAreaView edges={['top']} style={{backgroundColor:theme.colors.background}}>
    <Pressable accessibilityRole="button" accessibilityLabel="Повернутися на попередню сторінку"
      onPress={()=>goBack(router,user?.role??'user')} style={{paddingHorizontal:24,paddingVertical:12,minHeight:48,alignSelf:'flex-start'}}>
      <Text style={{fontSize:16,fontWeight:'600',color:theme.colors.primary}}>‹ Назад</Text>
    </Pressable>
  </SafeAreaView>;
}
