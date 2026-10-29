const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const src = path.join(__dirname, '..', 'src', 'auth');

function loadHelper(filename) {
  const exports = {};
  const source = fs.readFileSync(path.join(src, filename), 'utf8');
  const output = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(output, { exports, module: { exports } });
  return exports;
}

function createSession(pathname, token = 'expired-token') {
  const values = new Map();
  if (token) values.set('rehab.auth.token', token);
  const storage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, String(value)); },
    removeItem: key => { values.delete(key); },
  };
  const effects = [];
  const react = {
    createContext: () => ({ Provider() {} }),
    useCallback: fn => fn,
    useContext: () => null,
    useRef: value => ({ current: value }),
    useState: initial => {
      let value = typeof initial === 'function' ? initial() : initial;
      return [value, next => { value = next; }];
    },
    useEffect: fn => { effects.push(fn); },
  };
  let invalidate = null;
  let activeToken = null;
  const helpers = {
    './onboardingSession': loadHelper('onboardingSession.ts'),
    './returnEntry': loadHelper('returnEntry.ts'),
  };
  const output = ts.transpileModule(
    fs.readFileSync(path.join(src, 'AuthProvider.tsx'), 'utf8'), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.ReactJSX,
      },
    }
  ).outputText;
  const exports = {};
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(output, {
    exports, module: { exports },
    window: { location: { pathname }, sessionStorage: storage },
    require: name => {
      if (name === 'react') return react;
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === 'react-native') return { Platform: { OS: 'web' } };
      if (name === '../api/auth') return {
        getMyAccount: () => new Promise(() => {}),
        loginUser: async () => ({
          access_token: 'new-token', user: { user_id: 12, role: 'user' },
        }),
        logoutUser: async () => undefined,
        registerUser: async () => undefined,
      };
      if (name === '../api/client') return {
        ApiError: class ApiError extends Error {},
        setAccessToken: value => { activeToken = value; },
        setSessionInvalidHandler: handler => { invalidate = handler; },
      };
      if (helpers[name]) return helpers[name];
      throw new Error(name);
    },
  });
  const auth = exports.AuthProvider({ children: null }).props.value;
  effects[0]();
  return {
    auth, storage, invalidate: () => invalidate(),
    savedToken: () => storage.getItem('rehab.auth.token'),
    currentToken: () => activeToken,
    takeEntry: () => helpers['./returnEntry'].takeEntryLink(storage),
  };
}

test('expired JWT on a record URL retains the record destination', () => {
  const session = createSession('/entry/42');
  session.invalidate();
  assert.equal(session.savedToken(), null);
  assert.equal(session.currentToken(), null);
  assert.equal(session.takeEntry(), '/entry/42');
});

test('relogin after expiration can consume the stored record once', async () => {
  const session = createSession('/entry/7');
  session.invalidate();
  const account = await session.auth.signIn('user@example.com', 'password');
  assert.equal(account.user_id, 12);
  assert.equal(session.savedToken(), 'new-token');
  assert.equal(session.takeEntry(), '/entry/7');
  assert.equal(session.takeEntry(), null);
});

test('an explicit logout discards the record destination', async () => {
  const session = createSession('/entry/17');
  session.storage.setItem('rehab.auth.return-entry', '/entry/17');
  await session.auth.signOut();
  assert.equal(session.savedToken(), null);
  assert.equal(session.takeEntry(), null);
});

test('invalidating a session on another screen clears a stale destination', () => {
  const session = createSession('/(tabs)/home');
  session.storage.setItem('rehab.auth.return-entry', '/entry/55');
  session.invalidate();
  assert.equal(session.takeEntry(), null);
});

test('invalidating on an unsafe path never stores external navigation', () => {
  const session = createSession('//example.com');
  session.invalidate();
  assert.equal(session.takeEntry(), null);
});
