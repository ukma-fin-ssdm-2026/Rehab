export type RegistrationFields = {
  name: string;
  nickname: string;
  email: string;
  password: string;
};

export type RegistrationValidation =
  | { ok: true; data: RegistrationFields }
  | { ok: false; error: string };

export type LoginValidation =
  | { ok: true; email: string; password: string }
  | { ok: false; error: string };

const emailPattern = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/;

export function validateRegistration(fields: RegistrationFields): RegistrationValidation {
  const name = fields.name.trim();
  const nickname = fields.nickname.trim();
  const email = fields.email.trim().toLowerCase();
  const password = fields.password;

  if (!name || name.length > 100) {
    return { ok: false, error: 'Ім’я має містити від 1 до 100 символів.' };
  }
  if (!nickname || nickname.length > 50) {
    return { ok: false, error: 'Нікнейм має містити від 1 до 50 символів.' };
  }
  if (email.length < 3 || email.length > 254 || !emailPattern.test(email)) {
    return { ok: false, error: 'Введи коректну email-адресу.' };
  }
  if (password.length < 8 || password.length > 128) {
    return { ok: false, error: 'Пароль має містити від 8 до 128 символів.' };
  }
  return { ok: true, data: { name, nickname, email, password } };
}

export function validateLogin(emailValue: string, password: string): LoginValidation {
  const email = emailValue.trim().toLowerCase();
  if (!email || !password) {
    return { ok: false, error: 'Заповни email і пароль.' };
  }
  if (!emailPattern.test(email)) {
    return { ok: false, error: 'Введи коректну email-адресу.' };
  }
  return { ok: true, email, password };
}
