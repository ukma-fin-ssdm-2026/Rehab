import * as ImagePicker from 'expo-image-picker';
import { Platform } from 'react-native';

const MAX_AVATAR_BYTES = 5 * 1024 * 1024;

export type PickedAvatar = {
  uri: string;
  image: Blob;
  mimeType: string;
};

function imageMimeType(uri: string, declared?: string | null): string {
  if (declared && ['image/jpg', 'image/pjpeg'].includes(declared.toLowerCase())) return 'image/jpeg';
  const accepted = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/avif'];
  if (declared && accepted.includes(declared.toLowerCase())) return declared.toLowerCase();
  const path = uri.toLowerCase().split('?')[0];
  if (/\.jpe?g$/.test(path)) return 'image/jpeg';
  if (/\.png$/.test(path)) return 'image/png';
  if (/\.webp$/.test(path)) return 'image/webp';
  if (/\.heic$/.test(path)) return 'image/heic';
  if (/\.heif$/.test(path)) return 'image/heif';
  if (/\.avif$/.test(path)) return 'image/avif';
  throw new Error('Формат фото не підтримується. Обери JPEG, PNG, WebP, HEIC/HEIF або AVIF.');
}

async function signatureMime(image: Blob): Promise<string | null> {
  if (typeof image.slice(0,64).arrayBuffer !== 'function') return null;
  const bytes = new Uint8Array(await image.slice(0, 64).arrayBuffer());
  if (bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if ([137,80,78,71,13,10,26,10].every((value,i) => bytes[i] === value)) return 'image/png';
  const ascii = (start: number, end: number) => String.fromCharCode(...bytes.slice(start,end));
  if (ascii(0,4) === 'RIFF' && ascii(8,12) === 'WEBP') return 'image/webp';
  if (ascii(4,8) === 'ftyp') {
    const brands = Array.from({length: Math.floor((bytes.length-8)/4)},(_,i)=>ascii(8+i*4,12+i*4));
    if (brands.some(brand=>['avif','avis'].includes(brand))) return 'image/avif';
    if (brands.some(brand=>['heic','heix','hevc','hevx','heim','heis','mif1','msf1'].includes(brand))) return 'image/heic';
  }
  return null;
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
  const image = webFile ?? await fetch(asset.uri).then(response => {
    if (!response.ok) throw new Error('Не вдалося прочитати вибране фото.');
    return response.blob();
  });
  if (!image) throw new Error('Не вдалося прочитати вибране фото.');
  if (image.size > MAX_AVATAR_BYTES) {
    throw new Error('Фото перевищує 5 МіБ. Обери менше зображення.');
  }
  if (!image.size) throw new Error('Обране фото порожнє.');
  const mimeType = await signatureMime(image) ?? imageMimeType(
    asset.fileName ?? asset.uri,
    asset.mimeType ?? webFile?.type ?? image.type,
  );
  return { uri: asset.uri, image, mimeType };
}
