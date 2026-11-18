// AI-GENERATED START
// Перевірка контракту відповіді повідомлень (продовження R3 з Лаб 9).
// Тестовий дублер apiRequest імітує сервер, що повертає 200 з неправильною структурою.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

class ApiError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code; }
}

function compile(relative) {
  return ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src', relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
}

function loadNotifications(response) {
  const module = { exports: {} };
  const warnings = [];
  const imports = {
    './client': { ApiError, apiRequest: async () => structuredClone(response) },
    '../messages/rotation': { getMessageVariation: () => 1 },
  };
  vm.runInNewContext(compile('api/notifications.ts'), {
    module, exports: module.exports, console: { warn: message => warnings.push(message) },
    require: name => { assert.ok(name in imports, name); return imports[name]; },
  });
  return { api: module.exports, warnings };
}

function loadInbox() {
  const module = { exports: {} };
  vm.runInNewContext(compile('messages/inbox.ts'), { module, exports: module.exports, require: () => ({}) });
  return module.exports;
}

const notification = {
  notification_id: 5, kind: 'relapse', created_at: '2026-11-18T10:00:00Z', read_at: null,
  business_date: '2026-11-18', relationship_id: 2, record_id: 7,
  sender: { nickname: 'mentee', email: 'mentee@example.test' }, title: 'Зрив', body: 'Підтримай',
  support_comment: null, can_support: true, can_view_mentee: true, can_report_mentor: false,
};
const page = items => ({ items, total: Array.isArray(items) ? items.length : 0, limit: 30, offset: 0 });

async function rejectsAsInvalid(response, call = api => api.listNotifications()) {
  const { api, warnings } = loadNotifications(response);
  await assert.rejects(call(api), error => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.code, 'INVALID_RESPONSE');
    assert.doesNotMatch(error.message, /items|iterable|TypeError|undefined/);
    return true;
  });
  assert.equal(warnings.length, 1, 'the contract violation must be logged');
}

test('valid notification page and unread count pass unchanged', async () => {
  const { api, warnings } = loadNotifications(page([notification, { ...notification, notification_id: 6, kind: 'daily_reminder', sender: null, relationship_id: null, record_id: null }]));
  assert.equal((await api.listNotifications()).items.length, 2);
  assert.equal((await loadNotifications({ count: 3 }).api.getUnreadCount()).count, 3);
  assert.equal(warnings.length, 0);
});

test('boundary: empty inbox and zero unread are valid', async () => {
  assert.equal((await loadNotifications(page([])).api.listNotifications()).items.length, 0);
  assert.equal((await loadNotifications({ count: 0 }).api.getUnreadCount()).count, 0);
});

test('fault injection: items null gives a readable error instead of "not iterable"', async () => {
  await rejectsAsInvalid({ items: null, total: 0, limit: 30, offset: 0 });
  const { api } = loadNotifications({ items: null, total: 0, limit: 30, offset: 0 });
  await assert.rejects(loadInbox().loadInboxPages(api.listNotifications), error => error.code === 'INVALID_RESPONSE');
});

test('fault injection: missing items, null body or HTML instead of JSON', async () => {
  await rejectsAsInvalid({ total: 0, limit: 30, offset: 0 });
  await rejectsAsInvalid(null);
  await rejectsAsInvalid('<html>proxy error</html>');
});

test('notification with wrong field types is rejected', async () => {
  for (const item of [
    { ...notification, notification_id: '5' },
    { ...notification, kind: 'unknown' },
    { ...notification, title: null },
    { ...notification, read_at: 5 },
    { ...notification, sender: 'mentee' },
  ]) await rejectsAsInvalid(page([item]));
  await rejectsAsInvalid({ ...page([notification]), total: '1' });
});

test('unread count must be a non-negative integer', async () => {
  for (const body of [{}, { count: '3' }, { count: -1 }, { count: 1.5 }, null]) {
    await rejectsAsInvalid(body, api => api.getUnreadCount());
  }
});
// AI-GENERATED END
