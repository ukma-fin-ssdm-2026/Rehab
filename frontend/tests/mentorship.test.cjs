const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

function loader(transport) {
  const cache = new Map();
  function load(relative) {
    const file = path.resolve(__dirname, '../src', relative);
    if (cache.has(file)) return cache.get(file).exports;
    const module = { exports: {} };
    cache.set(file, module);
    const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    }).outputText;
    vm.runInNewContext(code, { module, exports: module.exports, Headers, URLSearchParams, AbortController,
      Date, Intl, fetch: transport, process: { env: { EXPO_PUBLIC_API_URL: 'https://api.example.test' } },
      require: spec => load(path.relative(path.join(__dirname, '../src'), path.resolve(path.dirname(file), spec + '.ts'))),
    }, { filename: file });
    return module.exports;
  }
  return load;
}

test('mentorship API uses the real signed-token client and normalized code', async () => {
  const requests = [];
  const load = loader(async (url, init) => {
    requests.push([url, init]);
    return new Response(JSON.stringify({ code: 'ABCDEFGHJKLM' }), { headers: { 'Content-Type': 'application/json' } });
  });
  load('api/client.ts').setAccessToken('signed-token');
  const api = load('api/mentorship.ts');
  await api.getMyMentorCode();
  await api.joinMentorship('  abcdefghjklm  ');
  await api.getMyMentor();
  await api.getMyMentees(30, 30);
  assert.equal(requests[0][0], 'https://api.example.test/api/v1/mentorships/code');
  assert.equal(requests[0][1].headers.get('Authorization'), 'Bearer signed-token');
  assert.deepEqual(JSON.parse(requests[1][1].body), { code: 'ABCDEFGHJKLM' });
  assert.equal(requests[1][1].method, 'POST');
  assert.ok(requests[2][0].endsWith('/mentorships/my-mentor'));
  assert.ok(requests[3][0].endsWith('/mentorships/my-mentees?limit=30&offset=30'));
  const before = requests.length;
  await assert.rejects(api.joinMentorship('invalid'));
  assert.equal(requests.length, before);
});

test('mentee data uses relationship-scoped read paths and cancellation signal', async () => {
  const requests=[];
  const load=loader(async (url,init)=>{
    requests.push([url,init]);
    if(init.method==='DELETE') return new Response(null,{status:204});
    return new Response('{}',{headers:{'Content-Type':'application/json'}});
  });
  const api=load('api/mentorship.ts');
  const signal=new AbortController().signal;
  await api.getMentorship(7,signal);
  await api.getMenteeEntries(7,'2026-10-01','2026-10-31',signal);
  await api.getMenteeEntry(7,19,signal);
  await api.getMenteeStatistics(7,'month',signal);
  await api.endMentorship(7);
  assert.ok(requests[0][0].endsWith('/mentorships/7'));
  assert.ok(requests[1][0].endsWith('/mentorships/7/calendar/entries?from=2026-10-01&to=2026-10-31&limit=100&offset=0'));
  assert.ok(requests[2][0].endsWith('/mentorships/7/calendar/entries/19'));
  assert.ok(requests[3][0].endsWith('/mentorships/7/statistics?period=month'));
  assert.equal(requests[3][1].signal,signal);
  assert.equal(requests[4][1].method,'DELETE');
  await assert.rejects(api.getMentorship(NaN));
  await assert.rejects(api.getMenteeEntry(7,-1));
  assert.equal(requests.length,5);
});

test('calendar month has correct leap-day and Monday offsets',()=>{
  const {calendarMonth}=loader()('support/calendar.ts');
  const feb=calendarMonth(2028,1);
  assert.equal(feb.days.filter(Boolean).length,29);
  assert.equal(feb.days[0],null);
  assert.equal(feb.days[1],'2028-02-01');
  assert.equal(feb.to,'2028-02-29');
  assert.equal(feb.days.length%7,0);
});

test('direct mentee route waits for restore and rejects guest/admin/onboarding',()=>{
  let auth={loading:true,user:null,restoreError:false,onboardingPending:false};
  function ScreenState() {}
  function Redirect() {}
  function Stack() {}
  const module={exports:{}};
  const file=path.join(__dirname,'../src/app/mentee/_layout.tsx');
  const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,require:spec=>{
    if(spec==='react/jsx-runtime') return {jsx:(type,props)=>({type,props})};
    if(spec==='expo-router') return {Stack,Redirect};
    if(spec==='../../auth/AuthProvider') return {useAuth:()=>auth};
    if(spec==='../../components/ui/ScreenState') return {ScreenState};
    throw new Error(spec);
  }});
  const render=module.exports.default;
  assert.equal(render().type,ScreenState);
  auth={...auth,loading:false};
  assert.equal(render().props.href,'/login');
  auth={...auth,user:{role:'admin'}};
  assert.equal(render().props.href,'/');
  auth={...auth,user:{role:'user'},onboardingPending:true};
  assert.equal(render().props.href,'/onboarding');
  auth={...auth,onboardingPending:false};
  assert.equal(render().type,Stack);
  auth={...auth,user:null,restoreError:true};
  assert.equal(render().props.state,'error');
});
