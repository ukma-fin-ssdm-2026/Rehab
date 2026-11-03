import { useSyncExternalStore } from 'react';
import { messageText, type MessageKey, type MessageStyle } from './catalog';
import { getMessageVariation, subscribeCopy } from './rotation';

export function useMessageVariation() {
  return useSyncExternalStore(subscribeCopy, getMessageVariation, () => 0);
}
export function useMessageText() {
  const variation = useMessageVariation();
  return (key: MessageKey, style: MessageStyle, context: Record<string,string> = {}) =>
    messageText(key,style,context,variation);
}
