import { API_BASE_URL } from '../config/api';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: unknown = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

let token: string | null = null;
let sessionInvalid: (() => void) | null = null;

const REQUEST_TIMEOUT_MS = 30_000;

export function setAccessToken(value: string | null): void {
  token = value;
}

export function setSessionInvalidHandler(callback: (() => void) | null): void {
  sessionInvalid = callback;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const callerSignal = options.signal;
  const cancellationError = () => callerSignal?.reason ??
    Object.assign(new Error('Запит скасовано'), { name: 'AbortError' });
  if (callerSignal?.aborted) throw cancellationError();

  let cancel = (_error: unknown): void => {};
  const cancelled = new Promise<never>((_resolve, reject) => { cancel = reject; });
  const onAbort = () => {
    cancel(cancellationError());
    controller.abort();
  };
  callerSignal?.addEventListener('abort', onAbort, { once: true });
  const timer = setTimeout(() => {
    cancel(new ApiError(0, 'REQUEST_TIMEOUT', 'Час очікування відповіді минув. Перевір з’єднання.'));
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  try {
    // The deadline includes reading the body. Do not retry writes automatically:
    // a timeout does not prove that the server rolled back the operation.
    return await Promise.race([
      performRequest<T>(path, { ...options, signal: controller.signal }),
      cancelled,
    ]);
  } finally {
    clearTimeout(timer);
    callerSignal?.removeEventListener('abort', onAbort);
  }
}

async function performRequest<T>(path: string, options: RequestInit): Promise<T> {
  if (!path.startsWith('/') || path.startsWith('/api/v1')) {
    throw new Error('Шлях API має починатися з /, без /api/v1');
  }
  if (!API_BASE_URL) {
    throw new Error('Не налаштовано EXPO_PUBLIC_API_URL');
  }
  const headers = new Headers(options.headers);
  if (options.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const requestToken = token;
  if (requestToken) headers.set('Authorization', `Bearer ${requestToken}`);

  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    ...options,
    headers,
  });
  if (options.signal?.aborted) throw Object.assign(new Error('Запит скасовано'), { name: 'AbortError' });
  if (requestToken !== null && requestToken === token && response.status === 401) {
    sessionInvalid?.();
  }
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get('content-type') ?? '';
  const text = await response.text();
  let payload: unknown = text;
  if (contentType.includes('application/json')) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      if (response.ok) {
        throw new ApiError(response.status, 'INVALID_RESPONSE', 'Сервер повернув некоректну відповідь. Спробуй пізніше.');
      }
      // Keep the HTTP status even when the error body cannot be decoded.
      payload = null;
    }
  }
  if (!response.ok) {
    const body =
      payload && typeof payload === 'object' && !Array.isArray(payload)
        ? payload as Record<string, unknown>
        : {};
    const detail =
      body.detail && typeof body.detail === 'object' && !Array.isArray(body.detail)
        ? body.detail as Record<string, unknown>
        : {};
    const code = typeof body.code === 'string' ? body.code
      : typeof detail.code === 'string' ? detail.code : 'HTTP_ERROR';
    const message = typeof body.message === 'string' ? body.message
      : typeof detail.message === 'string' ? detail.message
      : typeof body.detail === 'string' ? body.detail
      : response.status === 422 && Array.isArray(body.detail)
        ? 'Перевір правильність заповнених полів.'
        : `Помилка сервера (${response.status})`;
    throw new ApiError(response.status, code, message, body.details ?? detail.details ?? null);
  }
  return payload as T;
}
