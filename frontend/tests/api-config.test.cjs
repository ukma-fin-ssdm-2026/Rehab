const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'config', 'api.ts'), 'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function configuration(value) {
  const exports = {};
  const env = value === undefined ? {} : { EXPO_PUBLIC_API_URL: value };
  vm.runInNewContext(compiled, { exports, module: { exports }, process: { env } });
  return exports;
}

const cases = [
  ['unset', undefined, ''],
  ['empty', '', ''],
  ['whitespace only', ' \t\r\n\uFEFF', ''],
  ['one slash', '/', ''],
  ['slashes only', '////', ''],
  ['plain base', 'https://api.example.test', 'https://api.example.test'],
  ['one trailing slash', 'https://api.example.test/', 'https://api.example.test'],
  ['many trailing slashes', 'https://api.example.test////', 'https://api.example.test'],
  ['outer whitespace', ' \thttps://api.example.test/// \n', 'https://api.example.test'],
  ['internal slashes', 'https://api.example.test/a//b///', 'https://api.example.test/a//b'],
  ['internal whitespace', 'https://api.example.test/a /b/', 'https://api.example.test/a /b'],
  ['backslash is retained', 'https://api.example.test/\\', 'https://api.example.test/\\'],
  ['unicode path', 'https://api.example.test/шлях///', 'https://api.example.test/шлях'],
  ['unvalidated text', 'relative///', 'relative'],
];

for (const [name, input, expected] of cases) {
  test(`API configuration preserves existing normalization: ${name}`, () => {
    const api = configuration(input);
    assert.equal(api.API_BASE_URL, expected);
    if (!expected) {
      const message = 'Не налаштовано EXPO_PUBLIC_API_URL. Перевір frontend/.env.local.';
      assert.throws(() => api.getCalendarEntriesUrl(), { name: 'Error', message });
      assert.throws(() => api.getStatisticsUrl('all'), { name: 'Error', message });
    }
  });
}

test('a long internal slash run followed by text is preserved', () => {
  const input = `https://api.example.test/${'/'.repeat(4000)}x`;
  assert.equal(configuration(input).API_BASE_URL, input);
});

test('calendar URL keeps its exact route after trimming the base', () => {
  const api = configuration(' https://api.example.test/prefix/// ');
  assert.equal(api.getCalendarEntriesUrl(), 'https://api.example.test/prefix/api/v1/calendar/entries');
});

for (const period of ['all', 'week', 'month', 'year']) {
  test(`statistics URL keeps its route and period: ${period}`, () => {
    const api = configuration('https://api.example.test///');
    assert.equal(api.getStatisticsUrl(period), `https://api.example.test/api/v1/statistics?period=${period}`);
  });
}
