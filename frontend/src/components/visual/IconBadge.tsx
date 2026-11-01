import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';
import { StyleSheet } from 'react-native';

export function IconBadge({name}: {name:ComponentProps<typeof Ionicons>['name']}) {
  return <LinearGradient accessible={false} colors={['#493451','#291F34']}
    start={{x:0,y:0}} end={{x:1,y:1}} style={styles.badge}>
    <Ionicons name={name} size={23} color="#D9B4EC" accessible={false} />
  </LinearGradient>;
}
const styles=StyleSheet.create({
  badge:{width:42,height:42,borderRadius:15,alignItems:'center',justifyContent:'center',
    borderWidth:1,borderColor:'#695075',boxShadow:'inset 0 1px 0 rgba(245,220,255,0.15)'},
});
