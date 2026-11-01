import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useState } from 'react';
import { ActivityIndicator, Pressable, Text } from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../../auth/AuthProvider';
import { useInbox } from '../../messages/useMessages';
import { messageStyles as styles } from '../../messages/styles';

export default function MessagesScreen() {
  const {user}=useAuth();
  return <Inbox key={user?.user_id ?? 'guest'} />;
}
function Inbox() {
  const [visible,setVisible]=useState(30);
  const {data,loading,error,reload}=useInbox(visible);
  return <ScrollView contentContainerStyle={styles.container}>
    <Text style={styles.title}>Повідомлення</Text>
    {loading && <ActivityIndicator accessibilityLabel="Завантаження повідомлень" />}
    {!!error && <GlassCard style={styles.card}><Text style={styles.error}>{error}</Text><Pressable onPress={()=>void reload()}><Text style={styles.link}>Спробувати ще раз</Text></Pressable></GlassCard>}
    {data && !error && <>
      {data.items.length === 0 && <Text style={styles.text}>Повідомлень поки немає.</Text>}
      {data.items.map(item=><Pressable key={item.notification_id} style={styles.card}
        accessibilityRole="button" accessibilityLabel={`${item.read_at ? 'Прочитано' : 'Непрочитано'}: ${item.title}`}
        onPress={()=>router.push({pathname:'/messages/[notification_id]',params:{notification_id:String(item.notification_id)}})}>
        <Text style={styles.field}>{item.read_at ? '' : '● '}{item.title}</Text>
        <Text style={styles.text}>{item.body}</Text>
        <Text style={styles.muted}>{new Date(item.created_at).toLocaleString('uk-UA')}</Text>
      </Pressable>)}
      {data.items.length < data.total && <Pressable disabled={loading} style={styles.button} onPress={()=>setVisible(value=>value+30)}><Text style={styles.buttonText}>Завантажити ще</Text></Pressable>}
    </>}
  </ScrollView>;
}
