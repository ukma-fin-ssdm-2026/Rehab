import { SupportPanel } from '../../support/SupportPanel';
import { router } from 'expo-router';
import { useProfile } from '../../profile/ProfileProvider';

export default function FriendsSupportScreen() {
  const { profile } = useProfile();
  return <SupportPanel messageStyle={profile?.message_style ?? 'formal'}
    onReport={(id) => router.push({pathname: '/support/report', params: {relationship_id: String(id)}})} />;
}
