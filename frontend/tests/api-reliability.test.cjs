const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function setup(fetch) {
  const timers = new Map();
  let next = 0;
  const module = { exports: {} };
  const file = path.join(__dirname, '../src/api/client.ts');
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, {
    module, exports: module.exports, Headers, AbortController, fetch,
    setTimeout: callback => { timers.set(++next, callback); return next; },
    clearTimeout: id => timers.delete(id),
    require: () => ({ API_BASE_URL: 'https://api.example.test' }),
  });
  return { client: module.exports, timers, expire: () => [...timers.values()].forEach(fn => fn()) };
}
const json = (body, status = 200) => new Response(body, {
  status, headers: { 'Content-Type': 'application/json' },
});

for (const phase of ['headers', 'body']) {
  test(`deadline bounds stalled ${phase} without retrying a write`, async () => {
    let calls = 0;
    let signal;
    const app = setup(async (_url, options) => {
      calls++; signal = options.signal;
      if (phase === 'headers') return new Promise(() => {});
      return { status: 200, ok: true, headers: new Headers(), text: () => new Promise(() => {}) };
    });
    const pending = app.client.apiRequest('/calendar/entries', { method: 'POST', body: '{}' });
    const checked = assert.rejects(pending, error => error.code === 'REQUEST_TIMEOUT');
    await Promise.resolve();
    assert.equal(app.timers.size, 1, 'request must have a deadline');
    app.expire();
    await checked;
    assert.equal(signal.aborted, true);
    assert.equal(calls, 1);
    assert.equal(app.timers.size, 0);
  });
}

test('caller cancellation ends a pending request and cleans its deadline', async () => {
  let transportSignal;
  const app = setup((_url, options) => {
    transportSignal = options.signal;
    return new Promise(() => {});
  });
  const caller = new AbortController();
  const pending = app.client.apiRequest('/profile', { signal: caller.signal });
  const checked = assert.rejects(pending, error => error.name === 'AbortError');
  caller.abort();
  await checked;
  assert.equal(transportSignal.aborted, true);
  assert.equal(app.timers.size, 0);
});

test('already cancelled request never reaches transport', async () => {
  let calls = 0;
  const app = setup(async () => { calls++; return json('{}'); });
  const caller = new AbortController(); caller.abort();
  await assert.rejects(app.client.apiRequest('/profile', { signal: caller.signal }), error => error.name === 'AbortError');
  assert.equal(calls, 0);
});

for (const status of [200, 401, 500]) {
  test(`malformed JSON at HTTP ${status} produces a controlled error`, async () => {
    const app = setup(async () => json('{broken', status));
    let invalidated = 0;
    app.client.setAccessToken('current');
    app.client.setSessionInvalidHandler(() => invalidated++);
    await assert.rejects(app.client.apiRequest('/profile'), error =>
      error instanceof app.client.ApiError && error.status === status &&
      error.code === (status === 200 ? 'INVALID_RESPONSE' : 'HTTP_ERROR'));
    assert.equal(invalidated, status === 401 ? 1 : 0);
    assert.equal(app.timers.size, 0);
  });
}

test('late malformed 401 cannot invalidate a newer session', async () => {
  let respond;
  const app = setup(() => new Promise(resolve => { respond = resolve; }));
  let invalidated = 0;
  app.client.setSessionInvalidHandler(() => invalidated++);
  app.client.setAccessToken('old');
  const pending = app.client.apiRequest('/profile');
  app.client.setAccessToken('new'); respond(json('{broken', 401));
  await assert.rejects(pending, error => error.status === 401);
  assert.equal(invalidated, 0);
});

test('a response arriving after timeout cannot invalidate the session', async () => {
  let respond;
  const app = setup(() => new Promise(resolve => { respond = resolve; }));
  let invalidated = 0;
  app.client.setAccessToken('current');
  app.client.setSessionInvalidHandler(() => invalidated++);
  const pending = app.client.apiRequest('/profile');
  const checked = assert.rejects(pending, error => error.code === 'REQUEST_TIMEOUT');
  app.expire(); await checked;
  respond(json('{}', 401));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(invalidated, 0);
});

test('network failure is preserved and clears the deadline', async () => {
  const failure = new TypeError('offline');
  const app = setup(async () => { throw failure; });
  await assert.rejects(app.client.apiRequest('/profile'), error => error === failure);
  assert.equal(app.timers.size, 0);
});

test('successful JSON and empty 204 clear deadlines and caller listeners', async () => {
  for (const response of [json('{"value":7}'), new Response(null, { status: 204 })]) {
    const app = setup(async () => response);
    const caller = new AbortController();
    let attached = 0;
    let removed = 0;
    const add = caller.signal.addEventListener.bind(caller.signal);
    const remove = caller.signal.removeEventListener.bind(caller.signal);
    caller.signal.addEventListener = (...args) => { attached++; return add(...args); };
    caller.signal.removeEventListener = (...args) => { removed++; return remove(...args); };
    const result = await app.client.apiRequest('/profile', { signal: caller.signal });
    assert.equal(response.status === 204 ? result : result.value, response.status === 204 ? undefined : 7);
    assert.equal(app.timers.size, 0);
    assert.equal(removed, attached);
  }
});
