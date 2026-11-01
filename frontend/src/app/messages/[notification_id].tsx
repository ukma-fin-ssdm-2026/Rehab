import { ScreenScrollView as ScrollView } from '../../components/visual/ScreenScrollView';
import { GlassCard } from '../../components/visual/GlassCard';
import { useRef, useState } from 'react';
import { ActivityIndicator, Pressable, Text, TextInput } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ApiError } from '../../api/client';
import { sendSupport } from '../../api/notifications';
import { useAuth } from '../../auth/AuthProvider';
import { useMessage } from '../../messages/useMessages';
import { createSupportSender } from '../../messages/support';
import { messageStyles as styles } from '../../messages/styles';

export default function MessageScreen() {
  const {notification_id}=useLocalSearchParams<{notification_id:string}>();
  const {user}=useAuth();
  const id=/^[1-9]\d*$/.test(notification_id ?? '') ? Number(notification_id) : Number.NaN;
  return <Message key={`${user?.user_id}:${notification_id}`} id={id} />;
}
function Message({id}:{id:number}) {
  const {data,loading,error,reload}=useMessage(id);
  const [text,setText]=useState('');
  const [busy,setBusy]=useState(false);
  const [sendError,setSendError]=useState('');
  const sender=useRef(createSupportSender(sendSupport)).current;
  const submit=async()=>{
    if (busy || !data?.can_support) return;
    setBusy(true);setSendError('');
    try { await sender(id,text);setText('');await reload(); }
    catch(cause) {
      if (cause instanceof ApiError && ['SUPPORT_ALREADY_SENT','MENTORSHIP_INACTIVE','RELAPSE_NO_LONGER_ACTIVE'].includes(cause.code)) await reload();
      setSendError(cause instanceof Error ? cause.message : 'Не вдалося надіслати підтримку');
    } finally {setBusy(false);}
  };
  return <ScrollView contentContainerStyle={styles.container}>
    {loading && <ActivityIndicator accessibilityLabel="Завантаження повідомлення" />}
    {!!error && <GlassCard style={styles.card}><Text style={styles.error}>{error}</Text><Pressable onPress={()=>void reload()}><Text style={styles.link}>Спробувати ще раз</Text></Pressable></GlassCard>}
    {data && !error && <>
      <Text style={styles.title}>{data.title}</Text><Text style={styles.text}>{data.body}</Text>
      <Text style={styles.muted}>{new Date(data.created_at).toLocaleString('uk-UA')}</Text>
      {data.sender && <Text style={styles.text}>{data.sender.nickname} · {data.sender.email}</Text>}
      {data.support_comment && <GlassCard style={styles.card}>
        <Text style={styles.field}>Коментар підтримки</Text>
        <Text style={styles.text}>{data.support_comment.text}</Text>
        <Text style={styles.muted}>{data.support_comment.author.nickname} · {data.support_comment.author.email}</Text>
        <Text style={styles.muted}>{new Date(data.support_comment.created_at).toLocaleString('uk-UA')}</Text>
      </GlassCard>}
      {data.can_view_mentee && <Pressable onPress={()=>router.push({pathname:'/mentee/[relationship_id]',params:{relationship_id:String(data.relationship_id)}})}><Text style={styles.link}>Статистика підопічного</Text></Pressable>}
      {data.can_support && <GlassCard style={styles.card}>
        <Text style={styles.field}>Підтримати</Text>
        <TextInput accessibilityLabel="Текст підтримки" multiline style={styles.input} value={text} onChangeText={setText} editable={!busy} placeholder="Напишіть слова підтримки" />
        <Text style={styles.muted}>{[...text.trim()].length} / 2000</Text>
        <Pressable style={styles.button} disabled={busy || !text.trim() || [...text.trim()].length>2000} onPress={()=>void submit()}><Text style={styles.buttonText}>{busy ? 'Надсилання…' : 'Надіслати підтримку'}</Text></Pressable>
      </GlassCard>}
      {!!sendError && <Text style={styles.error}>{sendError}</Text>}
      {data.can_report_mentor && data.support_comment && <Pressable onPress={()=>router.push({pathname:'/support/report',params:{relationship_id:String(data.relationship_id),notification_id:String(data.notification_id)}})}><Text style={styles.link}>Поскаржитися</Text></Pressable>}
    </>}
  </ScrollView>;
}
