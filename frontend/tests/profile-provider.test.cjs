const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.join(__dirname, '..', 'src', 'profile', 'ProfileProvider.tsx');
const source = fs.readFileSync(filename, 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX,
  },
}).outputText;

function harness() {
  const slots = [];
  const pending = [];
  const requests = [];
  let cursor = 0;
  let authUser = null;
  const jsx = (type, props) => ({ type, props });

  function hook(initializer) {
    const index = cursor++;
    if (!slots[index]) slots[index] = initializer();
    return slots[index];
  }

  const react = {
    createContext: () => ({ Provider() {} }),
    useState(initial) {
      const slot = hook(() => ({
        value: typeof initial === 'function' ? initial() : initial,
      }));
      return [slot.value, value => { slot.value = value; }];
    },
    useRef(initial) {
      return hook(() => ({ current: initial }));
    },
    useCallback(fn, deps) {
      const slot = hook(() => ({ fn, deps }));
      if (!deps.every((item, i) => Object.is(item, slot.deps[i]))) {
        slot.fn = fn;
        slot.deps = deps;
      }
      return slot.fn;
    },
    useEffect(fn, deps) {
      const slot = hook(() => ({ deps: null, fn: null, cleanup: null }));
      if (slot.deps === null || !deps.every((item, i) => Object.is(item, slot.deps[i]))) {
        slot.deps = deps;
        pending.push(() => {
          if (slot.cleanup) slot.cleanup();
          slot.cleanup = fn();
        });
      }
    },
    useContext: () => null,
  };
  const exports = {};
  vm.runInNewContext(compiled, {
    exports, module: { exports },
    require: name => {
      if (name === 'react') return react;
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === '../auth/AuthProvider') {
        return { useAuth: () => ({ user: authUser }) };
      }
      if (name === '../api/profile') {
        return {
          getProfile: () => new Promise((resolve, reject) => {
            requests.push({ resolve, reject });
          }),
        };
      }
      throw new Error(name);
    },
  }, { filename });

  return {
    setUser(user) { authUser = user; },
    render() {
      cursor = 0;
      return exports.ProfileProvider({ children: null }).props.value;
    },
    runEffects() {
      const all = pending.splice(0);
      for (const fn of all) fn();
    },
    requests,
  };
}

async function settled() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

test('changing accounts hides old photo and preferences even before effects run', async () => {
  const app = harness();
  app.setUser({ user_id: 1, role: 'user' });
  app.render();
  app.runEffects();
  assert.equal(app.requests.length, 1);
  app.requests[0].resolve({
    user_id: 1, has_avatar: true, message_style: 'zen',
  });
  await settled();
  assert.equal(app.render().profile.user_id, 1);
  app.setUser({ user_id: 2, role: 'user' });
  assert.equal(app.render().profile, null);
  app.runEffects();
  assert.equal(app.requests.length, 2);
  app.requests[1].resolve({
    user_id: 2, has_avatar: false, message_style: 'formal',
  });
  await settled();
  assert.equal(app.render().profile.user_id, 2);
  app.setUser(null);
  assert.equal(app.render().profile, null);
});

test('late response for previous account never replaces current profile', async () => {
  const app = harness();
  app.setUser({ user_id: 12, role: 'user' });
  app.render();
  app.runEffects();
  app.setUser({ user_id: 13, role: 'user' });
  app.render();
  app.runEffects();
  app.requests[1].resolve({ user_id: 13, message_style: 'strict' });
  await settled();
  assert.equal(app.render().profile.user_id, 13);
  app.requests[0].resolve({ user_id: 12, message_style: 'humorous' });
  await settled();
  assert.equal(app.render().profile.user_id, 13);
});

test('admin or signed-out sessions never request private profile data', () => {
  const app = harness();
  app.render();
  app.runEffects();
  app.setUser({ user_id: 1, role: 'admin' });
  app.render();
  app.runEffects();
  assert.equal(app.requests.length, 0);
});
