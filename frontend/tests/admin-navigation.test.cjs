const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '../src/app/index.tsx'), 'utf8'
);
const code = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX,
  },
}).outputText;

test('administrator enters complaints without accessing legacy account list', () => {
  function Redirect() {}
  function ScreenState() {}
  const jsx = (type, props) => ({ type, props });
  const exports = {};
  const account = { user_id: 1, role: 'admin' };
  vm.runInNewContext(code, {
    exports,
    module: { exports },
    require: name => {
      if (name === 'react') return {
        useEffect() {},
        useRef: value => ({ current: value }),
        useState: value => [value, () => {}],
      };
      if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx };
      if (name === 'react-native') return { Platform: { OS: 'web' } };
      if (name === 'expo-router') return { Redirect };
      if (name === '../auth/AuthProvider') {
        return { useAuth: () => ({
          user: account, loading: false,
          onboardingPending: false, restoreError: false,
        }) };
      }
      if (name === '../auth/returnEntry') {
        return { takeEntryLink() { throw new Error('Admin cannot read private saved links'); } };
      }
      if (name === '../components/ui/ScreenState') return { ScreenState };
      throw new Error(name);
    },
  });
  const element = exports.default();
  assert.equal(element.type, Redirect);
  assert.equal(element.props.href, '/admin/complaints');
});
