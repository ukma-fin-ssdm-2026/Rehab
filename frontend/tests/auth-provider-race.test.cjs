const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.join(__dirname, '..', 'src', 'auth', 'AuthProvider.tsx');
const source = fs.readFileSync(filename, 'utf8');
const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX,
  },
}).outputText;

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

function createAuth(loginUser, registerUser = async () => undefined) {
  const stored = new Map();
  const sessionStorage = {
    getItem: key => stored.get(key) ?? null,
    setItem: (key, value) => { stored.set(key, value); },
    removeItem: key => { stored.delete(key); },
  };
  const state = [];
  const react = {
    createContext: () => ({ Provider() {} }),
    useCallback: callback => callback,
    useContext: () => null,
    useEffect: () => undefined,
    useRef: initial => ({ current: initial }),
    useState(initial) {
      const item = { current: typeof initial === 'function' ? initial() : initial };
      state.push(item);
      return [item.current, value => { item.current = value; }];
    },
  };
  const exported = {};
  let accessToken = null;
  const jsx = (type, props) => ({ type, props });
  vm.runInNewContext(transpiled, {
    exports: exported,
    module: { exports: exported },
    window: { sessionStorage },
    require: name => {
      if (name === 'react') return react;
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === 'react-native') return { Platform: { OS: 'web' } };
      if (name === '../api/auth') return {
        loginUser, registerUser,
        getMyAccount: async () => null,
        logoutUser: async () => undefined,
      };
      if (name === '../api/client') return {
        ApiError: class ApiError extends Error {},
        setAccessToken: token => { accessToken = token; },
        setSessionInvalidHandler: () => undefined,
      };
      throw new Error(name);
    },
  }, { filename });
  const auth = exported.AuthProvider({ children: null }).props.value;
  return {
    auth,
    state,
    getToken: () => accessToken,
    getSavedToken: () => sessionStorage.getItem('rehab.auth.token'),
  };
}

test('a delayed first login cannot replace a newer login', async () => {
  const oldLogin = deferred();
  const newLogin = deferred();
  const { auth, getToken, getSavedToken, state } = createAuth(email =>
    email === 'first@example.com' ? oldLogin.promise : newLogin.promise
  );
  const first = auth.signIn('first@example.com', 'first-password');
  const second = auth.signIn('second@example.com', 'second-password');
  newLogin.resolve({ access_token: 'new-token', user: { user_id: 2 } });
  assert.equal((await second).user_id, 2);
  oldLogin.resolve({ access_token: 'old-token', user: { user_id: 1 } });
  await assert.rejects(first, error => /перервано/.test(error.message));
  assert.equal(getToken(), 'new-token');
  assert.equal(getSavedToken(), 'new-token');
  assert.equal(state[0].current.user_id, 2);
});

test('a completed login after logout does not restore a session', async () => {
  const delayed = deferred();
  const { auth, getToken, getSavedToken, state } = createAuth(() => delayed.promise);
  const pending = auth.signIn('user@example.com', 'password');
  await auth.signOut();
  delayed.resolve({ access_token: 'late-token', user: { user_id: 3 } });
  await assert.rejects(pending, error => /перервано/.test(error.message));
  assert.equal(getToken(), null);
  assert.equal(getSavedToken(), null);
  assert.equal(state[0].current, null);
});

test('registration completed after logout does not start an implicit login', async () => {
  const registration = deferred();
  let logins = 0;
  const { auth, getToken, state } = createAuth(async () => {
    logins += 1;
    return { access_token: 'late-token', user: { user_id: 4 } };
  }, () => registration.promise);
  const pending = auth.signUp({
    name: 'Test', nickname: 'user', email: 'user@example.com', password: 'password',
  });
  await auth.signOut();
  registration.resolve({ user_id: 4 });
  await assert.rejects(pending, error => /перервано/.test(error.message));
  assert.equal(logins, 0);
  assert.equal(getToken(), null);
  assert.equal(state[3].current, false);
});

test('ordinary registration still signs in and enables onboarding', async () => {
  const { auth, getToken, state } = createAuth(async () => ({
    access_token: 'valid-token', user: { user_id: 5 },
  }));
  const user = await auth.signUp({
    name: 'Test', nickname: 'user', email: 'user@example.com', password: 'password',
  });
  assert.equal(user.user_id, 5);
  assert.equal(getToken(), 'valid-token');
  assert.equal(state[3].current, true);
});
