const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'auth', 'onboardingSession.ts'),
  'utf8',
);
const transformed = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const runtimeExports = {};
vm.runInNewContext(transformed, {
  exports: runtimeExports,
  module: { exports: runtimeExports },
});
const { isOnboardingPending, saveOnboardingPending } = runtimeExports;

function createStorage() {
  const items = new Map();
  return {
    getItem: key => items.get(key) ?? null,
    setItem: (key, value) => { items.set(key, String(value)); },
    removeItem: key => { items.delete(key); },
  };
}

test('new accounts have no pending onboarding', () => {
  const storage = createStorage();
  assert.equal(isOnboardingPending(storage, 42), false);
});

test('pending onboarding belongs only to the registering account', () => {
  const storage = createStorage();
  saveOnboardingPending(storage, 42);
  assert.equal(isOnboardingPending(storage, 42), true);
  assert.equal(isOnboardingPending(storage, 43), false);
});

test('a same-tab reload can restore the pending onboarding', () => {
  const storage = createStorage();
  saveOnboardingPending(storage, 42);
  assert.equal(isOnboardingPending(storage, 42), true);
  assert.equal(isOnboardingPending(storage, 42), true);
});

test('independently opened tabs have separate onboarding state', () => {
  const firstTab = createStorage();
  const secondTab = createStorage();
  saveOnboardingPending(firstTab, 42);
  assert.equal(isOnboardingPending(firstTab, 42), true);
  assert.equal(isOnboardingPending(secondTab, 42), false);
});

test('copied session storage has an independent pending marker', () => {
  const firstTab = createStorage();
  saveOnboardingPending(firstTab, 42);
  const secondTab = createStorage();
  const initialMarker = firstTab.getItem('rehab.auth.onboarding-user');
  secondTab.setItem('rehab.auth.onboarding-user', initialMarker);
  assert.equal(isOnboardingPending(secondTab, 42), true);
  saveOnboardingPending(firstTab, null);
  assert.equal(isOnboardingPending(firstTab, 42), false);
  assert.equal(isOnboardingPending(secondTab, 42), true);
});

test('finishing onboarding removes the pending flag', () => {
  const storage = createStorage();
  saveOnboardingPending(storage, 42);
  saveOnboardingPending(storage, null);
  assert.equal(isOnboardingPending(storage, 42), false);
});

test('private calendar details survive session restoration and stay protected', () => {
  const layoutFile = path.join(__dirname, '..', 'src', 'app', '_layout.tsx');
  const layoutSource = fs.readFileSync(layoutFile, 'utf8');
  const output = ts.transpileModule(layoutSource, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
  function Stack() {}
  Stack.Screen = function Screen() {};
  Stack.Protected = function Protected() {};
  function ScreenState() {}
  const jsx = (type, props) => ({ type, props });
  let auth = { user: null, loading: true, restoreError: false };
  const exports = {};
  vm.runInNewContext(output, {
    module: { exports },
    exports,
    require: name => {
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === 'expo-router') return { Stack };
      if (name === '../auth/AuthProvider') {
        return { AuthProvider() {}, useAuth: () => auth };
      }
      if (name === '../components/ui/ScreenState') return { ScreenState };
      throw new Error(name);
    },
  }, { filename: layoutFile });

  const navigation = exports.default().props.children.type;
  const waiting = navigation();
  assert.equal(waiting.type, ScreenState);
  assert.equal(waiting.props.state, 'loading');

  auth = { user: { user_id: 42, role: 'user' }, loading: false, restoreError: false };
  const root = navigation();
  assert.equal(root.type, Stack);
  const privateRoutes = root.props.children.find(child =>
    child.type === Stack.Protected && child.props.guard === true
  );
  const names = privateRoutes.props.children.map(child => child.props.name);
  assert.ok(names.includes('entry/[record_id]'));
  assert.ok(names.includes('onboarding'));

  auth = { user: null, loading: false, restoreError: false };
  const loggedOut = navigation();
  assert.equal(loggedOut.type, Stack);
  const privateGroup = loggedOut.props.children.find(child =>
    child.type === Stack.Protected && child.props.children.some(route =>
      route.props.name === 'entry/[record_id]'
    )
  );
  assert.equal(privateGroup.props.guard, false);
});
