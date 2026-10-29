const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'auth', 'returnEntry.ts'), 'utf8'
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const functions = {};
vm.runInNewContext(compiled, { exports: functions, module: { exports: functions } });
const { rememberEntryLink, takeEntryLink, discardEntryLink } = functions;

function storage() {
  const values = new Map();
  return {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, String(value)); },
    removeItem: key => { values.delete(key); },
  };
}

test('a direct record link can be restored once after authentication', () => {
  const tab = storage();
  rememberEntryLink(tab, '/entry/42');
  assert.equal(takeEntryLink(tab), '/entry/42');
  assert.equal(takeEntryLink(tab), null);
});

test('a record path with a trailing slash is normalized', () => {
  const tab = storage();
  rememberEntryLink(tab, '/entry/123/');
  assert.equal(takeEntryLink(tab), '/entry/123');
});

test('login ignores arbitrary URLs and unsafe target paths', () => {
  for (const unsafe of [
    'https://example.com/entry/42', '//example.com', '/admin/users',
    '/entry/0', '/entry/001', '/entry/42?redirect=evil',
    '/entry/1/other', '/entry/12345678901',
  ]) {
    const tab = storage();
    rememberEntryLink(tab, unsafe);
    assert.equal(takeEntryLink(tab), null, unsafe);
  }
});

test('tampered destinations are discarded instead of opened', () => {
  const tab = storage();
  tab.setItem('rehab.auth.return-entry', 'https://example.com');
  assert.equal(takeEntryLink(tab), null);
  tab.setItem('rehab.auth.return-entry', '/entry/1?next=//example.com');
  assert.equal(takeEntryLink(tab), null);
});

test('registration or logout can discard a pending record link', () => {
  const tab = storage();
  rememberEntryLink(tab, '/entry/17');
  discardEntryLink(tab);
  assert.equal(takeEntryLink(tab), null);
});

test('a different browser tab cannot consume another independent tab link', () => {
  const first = storage();
  const other = storage();
  rememberEntryLink(first, '/entry/23');
  assert.equal(takeEntryLink(other), null);
  assert.equal(takeEntryLink(first), '/entry/23');
});
