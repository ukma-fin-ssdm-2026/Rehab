const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.join(__dirname, '..', 'src', 'api', 'profile.ts');
const source = fs.readFileSync(filename, 'utf8');
const transformed = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function createClient() {
  const requests = [];
  const exports = {};
  vm.runInNewContext(transformed, {
    exports,
    module: { exports },
    require: name => {
      if (name === './client') {
        return {
          apiRequest: (url, options = {}) => {
            requests.push({ url, options });
            return Promise.resolve(undefined);
          },
        };
      }
      throw new Error(name);
    },
  });
  return { client: exports, requests };
}

test('profile data uses one authenticated client and the agreed path', async () => {
  const { client, requests } = createClient();
  await client.getProfile();
  assert.equal(requests[0].url, '/profile');
  assert.equal(requests[0].options.method, undefined);
});

test('profile editing only sends permitted fields', async () => {
  const { client, requests } = createClient();
  const data = { name: 'Anna', nickname: 'anna' };
  await client.updateProfile(data);
  assert.equal(requests[0].url, '/profile');
  assert.equal(requests[0].options.method, 'PATCH');
  assert.equal(requests[0].options.body, JSON.stringify(data));
});

test('password change sends old and new password without trimming', async () => {
  const { client, requests } = createClient();
  const data = { current_password: ' old pass ', new_password: ' new pass123 ' };
  await client.changeProfilePassword(data);
  assert.equal(requests[0].url, '/profile/password');
  assert.equal(requests[0].options.method, 'PUT');
  assert.equal(requests[0].options.body, JSON.stringify(data));
});

test('preferences use the shared profile endpoint', async () => {
  const { client, requests } = createClient();
  await client.updateProfilePreferences({
    email_reminders_enabled: false, message_style: 'zen',
  });
  assert.equal(requests[0].url, '/profile/preferences');
  assert.equal(requests[0].options.method, 'PATCH');
  assert.equal(JSON.parse(requests[0].options.body).message_style, 'zen');
});

test('binary avatar upload explicitly sets image content type', async () => {
  const { client, requests } = createClient();
  const image = new Blob(['image-data'], { type: 'image/jpeg' });
  await client.uploadProfileAvatar(image, 'image/jpeg');
  assert.equal(requests[0].url, '/profile/avatar');
  assert.equal(requests[0].options.method, 'PUT');
  assert.equal(requests[0].options.headers['Content-Type'], 'image/jpeg');
  assert.equal(requests[0].options.body, image);
});

test('avatar read and delete use the agreed private endpoint', async () => {
  const { client, requests } = createClient();
  await client.getProfileAvatar();
  await client.deleteProfileAvatar();
  assert.equal(requests[0].url, '/profile/avatar');
  assert.equal(requests[1].url, '/profile/avatar');
  assert.equal(requests[1].options.method, 'DELETE');
});
