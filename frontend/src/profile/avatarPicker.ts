import * as ImagePicker from 'expo-image-picker';
import { Platform } from 'react-native';

const MAX_AVATAR_BYTES = 5 * 1024 * 1024;

export type PickedAvatar = {
  uri: string;
  image: Blob;
  mimeType: string;
};

function imageMimeType(uri: string, declared?: string | null): string {
  const accepted = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
  if (declared && accepted.includes(declared.toLowerCase())) return declared.toLowerCase();
  const path = uri.toLowerCase().split('?')[0];
  if (/\.jpe?g$/.test(path)) return 'image/jpeg';
  if (/\.png$/.test(path)) return 'image/png';
  if (/\.webp$/.test(path)) return 'image/webp';
  if (/\.heic$/.test(path)) return 'image/heic';
  if (/\.heif$/.test(path)) return 'image/heif';
  throw new Error('Формат фото не підтримується. Обери JPEG, PNG, WebP або HEIC.');
}

export async function pickProfileAvatar(): Promise<PickedAvatar | null> {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsMultipleSelection: false,
    allowsEditing: false,
    quality: 0.85,
  });
  if (result.canceled || !result.assets?.length) return null;

  const asset = result.assets[0];
  if (asset.fileSize !== undefined && asset.fileSize > MAX_AVATAR_BYTES) {
    throw new Error('Фото перевищує 5 МіБ. Обери менше зображення.');
  }
  const webFile = Platform.OS === 'web' ? asset.file : undefined;
  const mimeType = imageMimeType(
    asset.fileName ?? asset.uri,
    asset.mimeType ?? webFile?.type,
  );
  const image = webFile ?? await fetch(asset.uri).then(response => {
    if (!response.ok) throw new Error('Не вдалося прочитати вибране фото.');
    return response.blob();
  });
  if (image.size > MAX_AVATAR_BYTES) {
    throw new Error('Фото перевищує 5 МіБ. Обери менше зображення.');
  }
  if (!image.size) throw new Error('Обране фото порожнє.');
  return { uri: asset.uri, image, mimeType };
}
