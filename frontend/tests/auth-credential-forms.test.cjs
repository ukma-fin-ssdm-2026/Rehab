const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const filepath = path.join(__dirname, '..', 'src', 'auth', 'credentialForms.ts');
const compiled = ts.transpileModule(fs.readFileSync(filepath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const output = {};
vm.runInNewContext(compiled, { exports: output, module: { exports: output } });
const { validateRegistration, validateLogin } = output;
const valid = { name: 'Анна', nickname: 'anna', email: 'anna@example.com', password: '12345678' };

test('registration normalizes fields without changing the password', () => {
  const result = validateRegistration({ ...valid, name: '  Анна  ', nickname: ' anna ', email: '  ANNA@Example.Com ', password: ' 12345678 ' });
  assert.equal(result.ok, true);
  assert.equal(result.data.name, 'Анна');
  assert.equal(result.data.nickname, 'anna');
  assert.equal(result.data.email, 'anna@example.com');
  assert.equal(result.data.password, ' 12345678 ');
});

test('registration rejects empty or whitespace names and nicknames', () => {
  assert.equal(validateRegistration({ ...valid, name: '  ' }).ok, false);
  assert.equal(validateRegistration({ ...valid, nickname: '\t ' }).ok, false);
});

test('registration accepts 100-character name and 50-character nickname', () => {
  assert.equal(validateRegistration({ ...valid, name: 'a'.repeat(100), nickname: 'b'.repeat(50) }).ok, true);
  assert.equal(validateRegistration({ ...valid, name: 'a'.repeat(101) }).ok, false);
  assert.equal(validateRegistration({ ...valid, nickname: 'a'.repeat(51) }).ok, false);
});

test('registration checks email syntax and length', () => {
  for (const email of ['missing-at.example.com', 'a@example', 'a @example.com', '', 'a@' + 'x'.repeat(250) + '.com']) {
    assert.equal(validateRegistration({ ...valid, email }).ok, false, email);
  }
  assert.equal(validateRegistration({ ...valid, email: 'test+tag@example.co.uk' }).ok, true);
});

test('registration accepts passwords of exactly 8 and 128 characters', () => {
  assert.equal(validateRegistration({ ...valid, password: 'x'.repeat(8) }).ok, true);
  assert.equal(validateRegistration({ ...valid, password: 'x'.repeat(128) }).ok, true);
  assert.equal(validateRegistration({ ...valid, password: 'x'.repeat(7) }).ok, false);
  assert.equal(validateRegistration({ ...valid, password: 'x'.repeat(129) }).ok, false);
});

test('login normalizes email but preserves exact password', () => {
  const result = validateLogin(' A@EXAMPLE.COM ', ' password ');
  assert.equal(result.ok, true);
  assert.equal(result.email, 'a@example.com');
  assert.equal(result.password, ' password ');
});

test('login refuses empty credentials and invalid email before API request', () => {
  assert.equal(validateLogin(' ', 'password').ok, false);
  assert.equal(validateLogin('a@example.com', '').ok, false);
  assert.equal(validateLogin('a@example', 'password').ok, false);
});
