import { apiRequest } from './client';
import type {
  AvatarDataOut, AvatarUploadOut, ProfileOut, ProfilePasswordUpdate,
  ProfilePreferencesUpdate, ProfileUpdate,
} from '../profile/types';

export function getProfile(): Promise<ProfileOut> {
  return apiRequest<ProfileOut>('/profile');
}

export function updateProfile(data: ProfileUpdate): Promise<ProfileOut> {
  return apiRequest<ProfileOut>('/profile', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function changeProfilePassword(data: ProfilePasswordUpdate): Promise<void> {
  return apiRequest<void>('/profile/password', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export function updateProfilePreferences(
  data: ProfilePreferencesUpdate,
): Promise<ProfileOut> {
  return apiRequest<ProfileOut>('/profile/preferences', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function uploadProfileAvatar(
  image: Blob,
  mimeType: string,
): Promise<AvatarUploadOut> {
  return apiRequest<AvatarUploadOut>('/profile/avatar', {
    method: 'PUT',
    headers: { 'Content-Type': mimeType },
    body: image,
  });
}

export function getProfileAvatar(): Promise<AvatarDataOut> {
  return apiRequest<AvatarDataOut>('/profile/avatar');
}

export function deleteProfileAvatar(): Promise<void> {
  return apiRequest<void>('/profile/avatar', { method: 'DELETE' });
}
