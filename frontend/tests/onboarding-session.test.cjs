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

test('onboarding does not leak into another tab', () => {
  const firstTab = createStorage();
  const secondTab = createStorage();
  saveOnboardingPending(firstTab, 42);
  assert.equal(isOnboardingPending(firstTab, 42), true);
  assert.equal(isOnboardingPending(secondTab, 42), false);
});

test('finishing onboarding removes the pending flag', () => {
  const storage = createStorage();
  saveOnboardingPending(storage, 42);
  saveOnboardingPending(storage, null);
  assert.equal(isOnboardingPending(storage, 42), false);
});
