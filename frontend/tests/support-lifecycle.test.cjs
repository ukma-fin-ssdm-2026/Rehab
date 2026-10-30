const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

// Minimal hook runtime: test production lifecycle logic, not React internals.
function harness(api) {
  const slots = [];
  let cursor = 0, effect, cleanup, value;
  const react = {
    useState(initial) {
      const index = cursor++;
      slots[index] ??= { value: typeof initial === 'function' ? initial() : initial };
      return [slots[index].value, next => {
        slots[index].value = typeof next === 'function' ? next(slots[index].value) : next;
      }];
    },
    useRef(initial) { const index = cursor++; return slots[index] ??= { current: initial }; },
    useCallback(callback, deps) {
      const index = cursor++;
      if (!slots[index] || deps.some((dep, i) => !Object.is(dep, slots[index].deps[i]))) slots[index] = { deps, callback };
      return slots[index].callback;
    },
  };
  const module = { exports: {} };
  const source = fs.readFileSync(path.join(__dirname, '../src/support/useSupportData.ts'), 'utf8');
  const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  vm.runInNewContext(output, { module, exports: module.exports, AbortController,
    require: spec => {
      if (spec === 'react') return react;
      if (spec === 'react-native') return { Platform: { OS: 'test' } };
      if (spec === 'expo-router') return { useFocusEffect: callback => { effect = callback; } };
      if (spec === '../auth/AuthProvider') return { useAuth: () => ({ user: { user_id: 17 } }) };
      if (spec === '../api/mentorship') return api;
      throw new Error(spec);
    },
  });
  function render() { cursor = 0; value = module.exports.useSupportData(); return value; }
  return { render, get value() { return value; }, focus() { render(); cleanup = effect(); render(); },
    blur() { cleanup(); render(); } };
}

async function settled(screen) { for (let i = 0; i < 12; i++) await Promise.resolve(); screen.render(); }

for (const action of ['join', 'leave', 'page']) {
  test(`${action} finishing while blurred does not leave support permanently disabled`, async () => {
    const pending = deferred();
    const page = { items: Array.from({ length: 30 }, (_, i) => ({ relationship_id: i + 1 })), total: 31, limit: 30, offset: 0 };
    const api = {
      getMyMentorCode: async () => ({ code: 'ABCDEFGHJKLM' }), getMyMentor: async () => ({ item: null }),
      getMyMentees: async (limit, offset, signal) => {
        if (!offset) return page;
        signal.addEventListener('abort', () => pending.reject(new Error('aborted')), { once: true });
        return pending.promise;
      },
      joinMentorship: () => pending.promise, endMentorship: () => pending.promise,
    };
    const screen = harness(api);
    screen.focus(); await settled(screen);
    assert.ok(screen.value.data);
    const task = action === 'join' ? screen.value.join('ABCDEFGHJKLM')
      : action === 'leave' ? screen.value.leave(1) : screen.value.loadMore();
    screen.render(); assert.equal(screen.value.busy, true);
    screen.blur();
    if (action !== 'page') pending.resolve({});
    await task;
    screen.focus(); await settled(screen);
    assert.ok(screen.value.data, 'data reloads when returning');
    assert.equal(screen.value.busy, false, 'controls must be usable after returning');
    screen.blur();
  });
}
