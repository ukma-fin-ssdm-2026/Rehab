const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function transpile(filename, jsx = false) {
  return ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: jsx ? ts.JsxEmit.ReactJSX : undefined,
    },
  }).outputText;
}

const sourceRoot = path.join(__dirname, '..', 'src');
const returnModule = {};
vm.runInNewContext(transpile(path.join(sourceRoot, 'auth', 'returnEntry.ts')), {
  exports: returnModule, module: { exports: returnModule },
});

function createNavigation(user, onboardingPending = false, returnPath = null) {
  const entries = new Map();
  if (returnPath) entries.set('rehab.auth.return-entry', returnPath);
  const storage = {
    getItem: key => entries.get(key) ?? null,
    setItem: (key, value) => { entries.set(key, value); },
    removeItem: key => { entries.delete(key); },
  };
  const slots = [];
  let cursor = 0;
  let effects = [];
  const react = {
    useState(initial) {
      const index = cursor++;
      if (!slots[index]) slots[index] = { value: initial };
      return [slots[index].value, value => { slots[index].value = value; }];
    },
    useRef(initial) {
      const index = cursor++;
      if (!slots[index]) slots[index] = { current: initial };
      return slots[index];
    },
    useEffect(effect) { effects.push(effect); },
  };
  function Redirect() {}
  function ScreenState() {}
  const exports = {};
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(transpile(path.join(sourceRoot, 'app', 'index.tsx'), true), {
    exports, module: { exports }, window: { sessionStorage: storage },
    require: name => {
      if (name === 'react') return react;
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === 'react-native') return { Platform: { OS: 'web' } };
      if (name === 'expo-router') return { Redirect };
      if (name === '../auth/AuthProvider') {
        return { useAuth: () => ({
          user, onboardingPending, loading: false, restoreError: false,
          retryRestore: async () => undefined,
        }) };
      }
      if (name === '../auth/returnEntry') return returnModule;
      if (name === '../components/ui/ScreenState') return { ScreenState };
      throw new Error(name);
    },
  });
  return {
    Redirect,
    ScreenState,
    render() { cursor = 0; effects = []; return exports.default(); },
    runEffects() { for (const effect of effects) effect(); },
    getStored: key => entries.get(key) ?? null,
  };
}

test('signed-in users return to the requested record once', () => {
  const page = createNavigation({ user_id: 42, role: 'user' }, false, '/entry/31');
  assert.equal(page.render().type, page.ScreenState);
  page.runEffects();
  const result = page.render();
  assert.equal(result.type, page.Redirect);
  assert.equal(result.props.href, '/entry/31');
  assert.equal(page.getStored('rehab.auth.return-entry'), null);
});

test('ordinary sign-in without saved link opens the home screen', () => {
  const page = createNavigation({ user_id: 42, role: 'user' });
  assert.equal(page.render().type, page.ScreenState);
  page.runEffects();
  assert.equal(page.render().props.href, '/(tabs)/home');
});

test('guests reach login instead of private routes', () => {
  const page = createNavigation(null, false, '/entry/31');
  assert.equal(page.render().props.href, '/login');
  assert.equal(page.getStored('rehab.auth.return-entry'), '/entry/31');
});

test('pending onboarding takes precedence over saved links', () => {
  const page = createNavigation({ user_id: 42, role: 'user' }, true, '/entry/31');
  assert.equal(page.render().props.href, '/onboarding');
  assert.equal(page.getStored('rehab.auth.return-entry'), '/entry/31');
});

test('administrator routing cannot consume an entry destination', () => {
  const page = createNavigation({ user_id: 1, role: 'admin' }, false, '/entry/31');
  assert.equal(page.render().props.href, '/admin/complaints');
  assert.equal(page.getStored('rehab.auth.return-entry'), '/entry/31');
});
