const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

function load(relative, imports = {}) {
  const file = path.join(__dirname, '../src', relative);
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, Date, Intl,
    require: name => { assert.ok(name in imports, name); return imports[name]; },
  });
  return module.exports;
}
const plain = value => JSON.parse(JSON.stringify(value));

test('calendar client keeps the API contract for list, detail, create and patch', async () => {
  const requests = [];
  const api = load('api/calendar.ts', { '../progress/changes': { notifyProgressChanged() {} }, './client': { apiRequest: async (...args) => {
    requests.push(args); return { record_id: 8 };
  } } });
  await api.listEntries('2026-10-01', '2026-10-31');
  await api.getEntry(8);
  await api.createEntry({ date: '2026-10-29', status: 'sober', drinks: [], trigger_category: null, comment: null });
  await api.updateEntry(8, { status: 'relapse', trigger_category: 'stress' });
  assert.equal(requests[0][0], '/calendar/entries?from=2026-10-01&to=2026-10-31&limit=100&offset=0');
  assert.equal(requests[1][0], '/calendar/entries/8');
  assert.equal(requests[2][1].method, 'POST');
  assert.equal(requests[3][1].method, 'PATCH');
  assert.deepEqual(JSON.parse(requests[3][1].body), { status: 'relapse', trigger_category: 'stress' });
});

test('form allows sober and relapse without drinks, strips alcohol fields for sober', () => {
  const { entryPayload } = load('calendar/rules.ts');
  const draft = { date: '2026-10-29', status: 'sober', trigger_category: 'stress',
    drinks: [{ type: 'beer', volume: '330' }], comment: ' note ' };
  assert.deepEqual(plain(entryPayload(draft, '2026-10-01', '2026-10-29')),
    { date: draft.date, status: 'sober', trigger_category: null, drinks: [], comment: 'note' });
  assert.deepEqual(plain(entryPayload({ ...draft, status: 'relapse', drinks: [] }, '2026-10-01', '2026-10-29')).drinks, []);
});

test('form rejects impossible, future and pre-tracking dates, invalid volumes and long comments', () => {
  const { entryPayload } = load('calendar/rules.ts');
  const draft = { date: '2026-10-29', status: 'relapse', trigger_category: null, drinks: [], comment: '' };
  for (const date of ['2026-02-30', '2026-10-30', '2026-09-30', 'wrong']) {
    assert.throws(() => entryPayload({ ...draft, date }, '2026-10-01', '2026-10-29'));
  }
  for (const volume of ['', '0', '-1', '1.5', '1e3', 'abc']) {
    assert.throws(() => entryPayload({ ...draft, drinks: [{ type: 'beer', volume }] }, '2026-10-01', '2026-10-29'));
  }
  assert.throws(() => entryPayload({ ...draft, comment: 'x'.repeat(2001) }, '2026-10-01', '2026-10-29'));
});

test('48 hours is inclusive and a second later editing is forbidden', () => {
  const { canEdit } = load('calendar/rules.ts');
  const created = '2026-10-27T12:00:00Z';
  assert.equal(canEdit(created, Date.parse('2026-10-29T12:00:00Z')), true);
  assert.equal(canEdit(created, Date.parse('2026-10-29T12:00:01Z')), false);
  assert.equal(canEdit('invalid', Date.now()), false);
});

test('dates use Kyiv and missing records are calculated only inside tracking range', () => {
  const { kyivDate, dayStatus } = load('calendar/rules.ts');
  assert.equal(kyivDate(new Date('2026-10-29T22:30:00Z')), '2026-10-30');
  assert.equal(dayStatus('2026-10-29', undefined, '2026-10-01', '2026-10-29'), 'sober');
  assert.equal(dayStatus('2026-09-30', undefined, '2026-10-01', '2026-10-29'), 'empty');
  assert.equal(dayStatus('2026-10-30', undefined, '2026-10-01', '2026-10-29'), 'empty');
  assert.equal(dayStatus('2026-10-29', { status: 'relapse' }, '2026-10-01', '2026-10-29'), 'relapse');
});

test('changing months selects the first day of the new month, including year rollover', () => {
  const { shiftedMonth } = load('calendar/rules.ts');
  assert.equal(shiftedMonth(2026, 9, 1).selectedDate, '2026-11-01');
  assert.equal(shiftedMonth(2026, 11, 1).selectedDate, '2027-01-01');
  assert.equal(shiftedMonth(2026, 0, -1).selectedDate, '2025-12-01');
});

test('navigation waits for session restore before mounting protected routes', () => {
  function ScreenState() {}
  function Stack() {}
  Stack.Screen = function Screen() {};
  Stack.Protected = function Protected() {};
  const jsx = (type, props) => ({ type, props });
  let auth = { user: null, loading: true, restoreError: false };
  const root = load('app/_layout.tsx', {
    'react/jsx-runtime': { jsx, jsxs: jsx },
    'expo-router': { Stack, usePathname:()=>'/home' },
    '../components/navigation/BackButton': {BackButton(){}},
    '../navigation/back': {showBack:()=>false},
    '../constants/theme': {theme:{colors:{background:'#141210'}}},
    '../auth/AuthProvider': { AuthProvider() {}, useAuth: () => auth },
    '../components/ui/ScreenState': { ScreenState },
    '../profile/ProfileProvider': { ProfileProvider() {} },
  });
  const navigation = root.default().props.children.props.children.type;
  assert.equal(navigation().type, ScreenState);
  assert.equal(navigation().props.state, 'loading');
  auth = { user: { role: 'user' }, loading: false, restoreError: false };
  assert.equal(navigation().type, Stack);
  auth = { user: null, loading: false, restoreError: true, retryRestore: async () => {} };
  assert.equal(navigation().props.state, 'error');
  const activeScreens = node => {
    if (!node) return [];
    if (Array.isArray(node)) return node.flatMap(activeScreens);
    if (node.type === Stack.Protected && !node.props.guard) return [];
    return node.props?.name ? [node.props.name] : activeScreens(node.props?.children);
  };
  auth = { user: { role: 'user' }, loading: false, restoreError: false, onboardingPending: false };
  assert.equal(activeScreens(navigation()).filter(name => name === 'messages').length, 1);
  auth = { ...auth, onboardingPending: true };
  assert.ok(!activeScreens(navigation()).includes('messages'));
  auth = { ...auth, user: { role: 'admin' }, onboardingPending: false };
  assert.ok(!activeScreens(navigation()).includes('messages'));
  auth = { ...auth, user: null };
  assert.ok(!activeScreens(navigation()).includes('messages'));

});

test('entry details do not fall back to black text', () => {
  const detail = fs.readFileSync(
    path.join(__dirname, '../src/app/entry/[record_id].tsx'), 'utf8',
  );
  const styles = fs.readFileSync(
    path.join(__dirname, '../src/calendar/styles.ts'), 'utf8',
  );
  assert.match(styles, /detailValue:\s*\{[^}]*color:\s*'#D9B8ED'/);
  assert.equal((detail.match(/style=\{styles\.detailValue\}/g) ?? []).length, 6);
  assert.doesNotMatch(detail, /<Text\b(?![^>]*\bstyle=)[^>]*>/);
});

test('sober days use mint backgrounds and readable dark numbers', () => {
  const calendar = fs.readFileSync(
    path.join(__dirname, '../src/app/(tabs)/calendar.tsx'), 'utf8',
  );
  assert.match(calendar, /soberDay:\s*\{\s*backgroundColor:\s*'#A8E2CB'/);
  assert.match(calendar, /soberDayText:\s*\{\s*color:\s*'#163A2E'/);
  assert.match(calendar, /status === 'sober' && styles\.soberDay,/);
  assert.match(calendar, /isSelected && styles\.selectedDayText,\s*status === 'sober' && styles\.soberDayText/);
  assert.match(calendar, /style=\{\[styles\.legendDot, styles\.soberDay\]\}/);
});
