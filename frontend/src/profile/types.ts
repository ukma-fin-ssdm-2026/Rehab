export type MessageStyle = 'formal' | 'humorous' | 'zen' | 'strict';

export interface ProfileOut {
  user_id: number;
  name: string;
  nickname: string;
  email: string;
  has_avatar: boolean;
  avatar_version: number | null;
  email_reminders_enabled: boolean;
  message_style: MessageStyle;
}

export interface ProfileContextValue {
  profile: ProfileOut | null;
  loading: boolean;
  error: string | null;
  refreshProfile(): Promise<void>;
}

export interface ProfileUpdate {
  name?: string;
  nickname?: string;
}

export interface ProfilePreferencesUpdate {
  email_reminders_enabled?: boolean;
  message_style?: MessageStyle;
}

export interface ProfilePasswordUpdate {
  current_password: string;
  new_password: string;
}

export interface AvatarUploadOut {
  has_avatar: true;
  avatar_version: number;
}

export interface AvatarDataOut {
  data_url: string;
  avatar_version: number;
}
