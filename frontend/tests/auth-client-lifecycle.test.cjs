const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const sourceRoot = path.join(__dirname, '..', 'src');

function createClient(transport) {
  function load(file) {
    const module = { exports: {} };
    const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
    }).outputText;
    vm.runInNewContext(output, {
      module,
      exports: module.exports,
      Headers,
      fetch: transport,
      process: { env: { EXPO_PUBLIC_API_URL: 'https://api.example.test' } },
      require: specifier => {
        assert.equal(specifier, '../config/api');
        return load(path.join(sourceRoot, 'config', 'api.ts'));
      },
    }, { filename: file });
    return module.exports;
  }

  return load(path.join(sourceRoot, 'api', 'client.ts'));
}

function errorResponse(status, code) {
  return new Response(JSON.stringify({ code, message: code, details: null }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('late 401 from previous JWT does not revoke a newer login', async () => {
  let finishOldRequest;
  const oldResponse = new Promise(resolve => { finishOldRequest = resolve; });
  const sentTokens = [];
  const client = createClient(async (url, options) => {
    sentTokens.push(options.headers.get('Authorization'));
    if (sentTokens.length === 1) return oldResponse;
    return new Response('{"user_id":2}', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });

  let invalidations = 0;
  client.setSessionInvalidHandler(() => { invalidations += 1; });
  client.setAccessToken('old-signed-token');
  const pending = client.apiRequest('/auth/me');
  client.setAccessToken('new-signed-token');
  finishOldRequest(errorResponse(401, 'UNAUTHORIZED'));

  await assert.rejects(pending, error => error.status === 401);
  assert.equal(invalidations, 0);

  const profile = await client.apiRequest('/auth/me');
  assert.equal(profile.user_id, 2);
  assert.deepEqual(sentTokens, [
    'Bearer old-signed-token',
    'Bearer new-signed-token',
  ]);
});

test('late account block from another session does not revoke current JWT', async () => {
  let finishOldRequest;
  const oldResponse = new Promise(resolve => { finishOldRequest = resolve; });
  const client = createClient(async () => oldResponse);
  let invalidations = 0;
  client.setSessionInvalidHandler(() => { invalidations += 1; });
  client.setAccessToken('earlier-token');
  const pending = client.apiRequest('/auth/me');
  client.setAccessToken('current-token');
  finishOldRequest(errorResponse(403, 'ACCOUNT_BLOCKED'));

  await assert.rejects(pending, error => error.status === 403);
  assert.equal(invalidations, 0);
});

test('401 and account block still revoke the active JWT', async () => {
  for (const [status, code] of [
    [401, 'UNAUTHORIZED'],
    [403, 'ACCOUNT_BLOCKED'],
  ]) {
    const client = createClient(async () => errorResponse(status, code));
    let invalidations = 0;
    client.setSessionInvalidHandler(() => { invalidations += 1; });
    client.setAccessToken('current-signed-token');

    await assert.rejects(client.apiRequest('/auth/me'), error =>
      error.status === status && error.code === code
    );
    assert.equal(invalidations, 1);
  }
});

test('invalid public login does not invalidate a concurrently restored session', async () => {
  let finishLogin;
  const delayedLogin = new Promise(resolve => { finishLogin = resolve; });
  const client = createClient(async () => delayedLogin);
  let invalidations = 0;
  client.setSessionInvalidHandler(() => { invalidations += 1; });
  const pending = client.apiRequest('/auth/login', { method: 'POST' });
  client.setAccessToken('restored-signed-token');
  finishLogin(errorResponse(401, 'UNAUTHORIZED'));

  await assert.rejects(pending, error => error.status === 401);
  assert.equal(invalidations, 0);
});
