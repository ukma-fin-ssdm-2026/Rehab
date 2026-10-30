import { useEffect, useState } from 'react';
import { Image, Text, View } from 'react-native';
import { getProfileAvatar } from '../api/profile';
import { theme } from '../constants/theme';
import type { ProfileOut } from './types';

type AvatarState = {
  userId: number;
  version: number;
  dataUrl: string;
};

export function AvatarView({ profile, size = 82 }: { profile: ProfileOut; size?: number }) {
  const [avatar, setAvatar] = useState<AvatarState | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (profile.has_avatar && profile.avatar_version !== null) {
      getProfileAvatar().then(result => {
        if (!cancelled && result.avatar_version === profile.avatar_version) {
          setAvatar({
            userId: profile.user_id,
            version: result.avatar_version,
            dataUrl: result.data_url,
          });
        }
      }).catch(() => {
        if (!cancelled) setAvatar(null);
      });
    }
    return () => { cancelled = true; };
  }, [profile.user_id, profile.has_avatar, profile.avatar_version]);

  const valid = profile.has_avatar && avatar?.userId === profile.user_id &&
    avatar.version === profile.avatar_version;
  const frame = {
    width: size,
    height: size,
    borderRadius: size / 3,
    backgroundColor: theme.colors.accent,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    overflow: 'hidden' as const,
  };

  return (
    <View style={frame}>
      {valid && avatar ? (
        <Image source={{ uri: avatar.dataUrl }}
          style={{ width: size, height: size }} accessibilityLabel="Фото профілю" />
      ) : (
        <Text style={{
          color: theme.colors.primaryDark,
          fontSize: size * 0.4,
          fontWeight: '800',
        }}>
          {profile.name.charAt(0).toUpperCase() || 'R'}
        </Text>
      )}
    </View>
  );
}
