import { GlassCard } from '../components/visual/GlassCard';
import { useProfile } from '../profile/ProfileProvider';
import { relapseLabel } from '../messages/catalog';
import { Pressable, Text, View } from 'react-native';
import type { DayStatus, TriggerCategory } from '../api/calendar';
import { triggers } from './rules';
import { styles } from './styles';

export function StatusFields({ status, trigger, disabled, onStatus, onTrigger }: {
  status: DayStatus; trigger: TriggerCategory | null; disabled: boolean;
  onStatus: (value: DayStatus) => void; onTrigger: (value: TriggerCategory | null) => void;
}) {
  const {profile}=useProfile();
  return <GlassCard style={styles.card}>
    <Text style={styles.label}>Статус дня</Text>
    <View style={styles.typeList}>
      {(['sober', 'relapse'] as const).map(value => <Pressable key={value}
        accessibilityRole="radio" accessibilityState={{ checked: status === value, disabled }}
        disabled={disabled} onPress={() => onStatus(value)}
        style={[styles.typeOption, status === value && styles.typeActive]}>
        <Text style={styles.typeText}>{value === 'sober' ? 'Тверезість' : relapseLabel(profile?.message_style ?? 'formal')}</Text>
      </Pressable>)}
    </View>
    {status === 'relapse' && <>
      <Text style={styles.label}>Тригер (необов’язково)</Text>
      <View style={styles.typeList}>{triggers.map(item => <Pressable key={item.value ?? 'none'}
        accessibilityRole="radio" accessibilityState={{ checked: trigger === item.value, disabled }}
        disabled={disabled} onPress={() => onTrigger(item.value)}
        style={[styles.typeOption, trigger === item.value && styles.typeActive]}>
        <Text style={styles.typeText}>{item.label}</Text>
      </Pressable>)}</View>
    </>}
  </GlassCard>;
}
