import catalog from './catalog-data.json';
export type MessageStyle = 'formal' | 'humorous' | 'zen' | 'strict';
export type MessageKey = keyof typeof catalog;
export const MESSAGE_STYLES: readonly MessageStyle[] = ['formal', 'humorous', 'zen', 'strict'];

/** Plain text only; never pass the result to an HTML renderer. */
export function messageText(key: MessageKey, style: MessageStyle, context: Record<string, string> = {}): { title: string; body: string } {
  const template = catalog[key]?.[style];
  if (!template) throw new Error('Невідомий ключ або стиль повідомлення');
  const format = (text: string) => text.replace(/\{([a-z_]+)\}/g, (_, token: string) => {
    if (!Object.prototype.hasOwnProperty.call(context, token)) throw new Error(`Відсутній контекст: ${token}`);
    return context[token];
  });
  return { title: format(template[0]), body: format(template[1]) };
}
