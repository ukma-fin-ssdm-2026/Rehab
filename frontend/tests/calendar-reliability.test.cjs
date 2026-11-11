// AI-GENERATED START
// Лаб 9, R3: тести надійності контракту відповіді календаря.
// Тестовий дублер apiRequest підміняє сервер, що повертає 200 з неправильною структурою.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

class ApiError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code; }
}

function loadCalendar(response) {
  const file = path.join(__dirname, '../src/api/calendar.ts');
  const module = { exports: {} };
  const warnings = [];
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const imports = {
    './client': { ApiError, apiRequest: async () => structuredClone(response) },
    '../progress/changes': { notifyProgressChanged() {} },
  };
  vm.runInNewContext(code, {
    module, exports: module.exports, console: { warn: message => warnings.push(message) },
    require: name => { assert.ok(name in imports, name); return imports[name]; },
  });
  return { api: module.exports, warnings };
}

const entry = {
  record_id: 8, user_id: 1, date: '2026-10-29', status: 'relapse', trigger_category: 'stress',
  drinks: [{ type: 'beer', volume_ml: 330 }], comment: null, created_at: '2026-10-29T10:00:00Z',
};
const page = items => ({ items, total: Array.isArray(items) ? items.length : 0, limit: 100, offset: 0 });

async function rejectsAsInvalid(response, call = api => api.listEntries('2026-10-01', '2026-10-31')) {
  const { api, warnings } = loadCalendar(response);
  await assert.rejects(call(api), error => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.code, 'INVALID_RESPONSE');
    assert.doesNotMatch(error.message, /items|null|TypeError/);
    return true;
  });
  assert.equal(warnings.length, 1, 'the contract violation must be logged');
}

test('R3: valid calendar page passes unchanged', async () => {
  const { api, warnings } = loadCalendar(page([entry, { ...entry, record_id: 9, status: 'sober', trigger_category: null, drinks: [] }]));
  const result = await api.listEntries('2026-10-01', '2026-10-31');
  assert.equal(result.items.length, 2);
  assert.equal(result.items[0].drinks[0].volume_ml, 330);
  assert.equal(warnings.length, 0);
});

test('R3 boundary: empty month is a valid page, not an error', async () => {
  const { api } = loadCalendar(page([]));
  assert.equal((await api.listEntries('2026-10-01', '2026-10-31')).items.length, 0);
});

test('R3 fault injection: items null gives a controlled error instead of a render crash', async () => {
  await rejectsAsInvalid({ items: null, total: 0, limit: 100, offset: 0 });
});

test('R3 fault injection: missing items or non-object body gives a controlled error', async () => {
  await rejectsAsInvalid({ total: 0, limit: 100, offset: 0 });
  await rejectsAsInvalid(null);
  await rejectsAsInvalid('<html>proxy error</html>');
});

test('R3: entry with wrong field types is rejected', async () => {
  const broken = [
    { ...entry, record_id: '8' },
    { ...entry, date: 29 },
    { ...entry, status: 'unknown' },
    { ...entry, drinks: null },
    { ...entry, drinks: [{ type: 'beer', volume_ml: -1 }] },
    { ...entry, comment: 5 },
  ];
  for (const item of broken) await rejectsAsInvalid(page([item]));
  await rejectsAsInvalid({ ...page([entry]), total: '1' });
});

test('R3: single entry response is validated too', async () => {
  const { api } = loadCalendar(entry);
  assert.equal((await api.getEntry(8)).record_id, 8);
  await rejectsAsInvalid({ record_id: 8 }, api => api.getEntry(8));
});
// AI-GENERATED END
