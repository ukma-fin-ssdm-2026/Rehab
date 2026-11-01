import { StyleSheet } from 'react-native';
import { profileStyles } from '../profile/styles';
import { theme } from '../constants/theme';
export const messageStyles = {...profileStyles, ...StyleSheet.create({
  input: {borderWidth:1,borderColor:theme.colors.border,borderRadius:12,padding:14,color:theme.colors.text,minHeight:100,textAlignVertical:'top'},
  button: {backgroundColor:theme.colors.primary,borderRadius:12,padding:16,alignItems:'center'},
  buttonText: {color:theme.colors.text,fontWeight: '500'},
})};
