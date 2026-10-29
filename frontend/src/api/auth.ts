import { apiRequest } from './client';

export type UserRole = 'user' | 'mentor' | 'admin';

export interface UserAccount {
  user_id: number;
  name: string;
  nickname: string;
  email: string;
  role: UserRole;
  tracking_start_date: string;
}

export interface UserSession extends UserAccount {
  current_date: string;
}

export interface RegistrationData {
  name: string;
  nickname: string;
  email: string;
  password: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: UserAccount;
}

export function registerUser(data: RegistrationData): Promise<UserAccount> {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function loginUser(
  email: string,
  password: string,
): Promise<AccessTokenResponse> {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function getMyAccount(): Promise<UserSession> {
  return apiRequest('/auth/me');
}

export function logoutUser(): Promise<void> {
  return apiRequest('/auth/logout', { method: 'POST' });
}
