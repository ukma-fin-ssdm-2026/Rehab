// Regression checks for the session used by production screen requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const src = path.join(__dirname, '..', 'src');

function sources(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? sources(file) : /\.tsx?$/.test(file) ? [file] : [];
  });
}

function clientWith(transport) {
  function load(file) {
    const module = { exports: {} };
    const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    }).outputText;
    vm.runInNewContext(output, {
      module, exports: module.exports, Headers, fetch: transport,
      process: { env: { EXPO_PUBLIC_API_URL: 'https://api.example.test/' } },
      require: specifier => {
        assert.equal(specifier, '../config/api');
        return load(path.join(src, 'config', 'api.ts'));
      },
    }, { filename: file });
    return module.exports;
  }
  return load(path.join(src, 'api', 'client.ts'));
}

test('production UI never sends demo session tokens', () => {
  const offenders = sources(src).filter(file =>
    /Bearer\s+(?:user|mentor|admin)-\d+/.test(fs.readFileSync(file, 'utf8')),
  ).map(file => path.relative(src, file));
  assert.deepEqual(offenders, [], 'Screens must use the signed session from apiRequest');
});

test('calendar write uses current JWT, one API prefix and JSON headers', async () => {
  let request;
  const client = clientWith(async (url, options) => {
    request = { url, ...options };
    return new Response('{"record_id":7}', { status: 201, headers: { 'Content-Type': 'application/json' } });
  });
  client.setAccessToken('signed-session-one');
  const result = await client.apiRequest('/calendar/entries', { method: 'POST', body: '{"status":"sober"}' });
  assert.equal(request.url, 'https://api.example.test/api/v1/calendar/entries');
  assert.equal(request.headers.get('Authorization'), 'Bearer signed-session-one');
  assert.equal(request.headers.get('Content-Type'), 'application/json');
  assert.equal(request.method, 'POST');
  assert.equal(result.record_id, 7);
  client.setAccessToken('signed-session-two');
  await client.apiRequest('/statistics?period=month');
  assert.equal(request.headers.get('Authorization'), 'Bearer signed-session-two');
});

test('expired session invokes invalidation and displays the server message', async () => {
  const client = clientWith(async () => new Response(JSON.stringify({
    code: 'UNAUTHORIZED', message: 'Сесія завершилася', details: null,
  }), { status: 401, headers: { 'Content-Type': 'application/json' } }));
  let invalidated = 0;
  client.setAccessToken('expired-signed-session');
  client.setSessionInvalidHandler(() => invalidated++);
  await assert.rejects(client.apiRequest('/calendar/entries'), error =>
    error.status === 401 && error.code === 'UNAUTHORIZED' && error.message === 'Сесія завершилася',
  );
  assert.equal(invalidated, 1);
});

test('a role restriction does not clear an otherwise valid session', async () => {
  const client = clientWith(async () => new Response('{"code":"FORBIDDEN","message":"No access"}', {
    status: 403, headers: { 'Content-Type': 'application/json' },
  }));
  let invalidated = 0;
  client.setAccessToken('valid-signed-session');
  client.setSessionInvalidHandler(() => invalidated++);
  await assert.rejects(client.apiRequest('/admin/users'), error => error.status === 403);
  assert.equal(invalidated, 0);
});
