const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'profile', 'avatarPicker.ts'), 'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function setup({ os = 'web', result, getFile } = {}) {
  let opened = 0;
  let downloaded = 0;
  const picker = {
    launchImageLibraryAsync: async options => {
      opened++;
      assert.deepEqual(Array.from(options.mediaTypes), ['images']);
      assert.equal(options.allowsMultipleSelection, false);
      return result;
    },
  };
  const exports = {};
  vm.runInNewContext(compiled, {
    exports,
    module: { exports },
    Blob,
    require: name => {
      if (name === 'expo-image-picker') return picker;
      if (name === 'react-native') return { Platform: { OS: os } };
      throw new Error(name);
    },
    fetch: async uri => {
      downloaded++;
      assert.equal(uri, result.assets[0].uri);
      return { ok: true, blob: async () => getFile };
    },
  });
  return { picker: exports, opened: () => opened, downloaded: () => downloaded };
}

test('gallery cancellation does not upload or download', async () => {
  const h = setup({ result: { canceled: true, assets: null } });
  assert.equal(await h.picker.pickProfileAvatar(), null);
  assert.equal(h.opened(), 1);
  assert.equal(h.downloaded(), 0);
});

test('web uploads the actual selected file without fetching a URI', async () => {
  const file = new Blob(['jpeg'], { type: 'image/jpeg' });
  const h = setup({
    result: { canceled: false, assets: [{
      uri: 'blob:photo', fileName: 'photo.jpg', mimeType: 'image/jpeg',
      file, fileSize: file.size,
    }] },
  });
  const avatar = await h.picker.pickProfileAvatar();
  assert.equal(avatar.image, file);
  assert.equal(avatar.mimeType, 'image/jpeg');
  assert.equal(avatar.uri, 'blob:photo');
  assert.equal(h.downloaded(), 0);
});

test('native loads the picked HEIC file before passing to the API client', async () => {
  const file = new Blob(['heic']);
  const h = setup({
    os: 'ios',
    result: { canceled: false, assets: [{
      uri: 'file:///tmp/IMG_0123.HEIC', fileName: 'IMG_0123.HEIC',
      fileSize: file.size,
    }] },
    getFile: file,
  });
  const avatar = await h.picker.pickProfileAvatar();
  assert.equal(avatar.image, file);
  assert.equal(avatar.mimeType, 'image/heic');
  assert.equal(h.downloaded(), 1);
});

test('oversized image is rejected before reading its contents', async () => {
  const h = setup({ result: { canceled: false, assets: [{
    uri: 'file:///big.jpg', mimeType: 'image/jpeg',
    fileSize: 5 * 1024 * 1024 + 1,
  }] } });
  await assert.rejects(h.picker.pickProfileAvatar(), /5 МіБ/);
  assert.equal(h.downloaded(), 0);
});

test('unknown and empty files cannot be saved', async () => {
  const invalid = setup({ result: { canceled: false, assets: [{
    uri: 'blob:invalid', fileName: 'photo.gif', mimeType: 'image/gif',
    file: new Blob(['gif']), fileSize: 3,
  }] } });
  await assert.rejects(invalid.picker.pickProfileAvatar(), /Формат фото/);
  const empty = setup({ result: { canceled: false, assets: [{
    uri: 'blob:empty', fileName: 'photo.png', mimeType: 'image/png',
    file: new Blob([]), fileSize: 0,
  }] } });
  await assert.rejects(empty.picker.pickProfileAvatar(), /порожнє/);
});

test('actual file size is checked even if metadata reports a smaller file', async () => {
  const huge = new Blob([new Uint8Array(5 * 1024 * 1024 + 1)]);
  const h = setup({ result: { canceled: false, assets: [{
    uri: 'blob:huge', fileName: 'photo.jpg', mimeType: 'image/jpeg',
    file: huge, fileSize: 100,
  }] } });
  await assert.rejects(h.picker.pickProfileAvatar(), /5 МіБ/);
});
