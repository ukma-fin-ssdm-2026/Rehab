const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');
function load(relative, imports = {}, globals = {}) {
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src', relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, Set, ...globals,
    require: name => { assert.ok(name in imports, name); return imports[name]; },
  });
  return module.exports;
}
const deferred = () => { let resolve; let reject; const promise = new Promise((a,b) => { resolve=a; reject=b; }); return { promise, resolve, reject }; };
test('latest period wins; stale success and failure cannot overwrite it', async () => {
  const { createLatestRequest } = load('progress/request.ts');
  const request = createLatestRequest(); const values=[]; const errors=[];
  const old=deferred(); const current=deferred();
  const a=request.run(() => old.promise, x=>values.push(x), e=>errors.push(e));
  const b=request.run(() => current.promise, x=>values.push(x), e=>errors.push(e));
  current.resolve('month'); await b; old.resolve('week'); await a;
  assert.deepEqual(values, ['month']);
  const stale=deferred(); const c=request.run(()=>stale.promise, x=>values.push(x), e=>errors.push(e));
  await request.run(async ()=>'year', x=>values.push(x), e=>errors.push(e));
  stale.reject(new Error('old failure')); await c;
  assert.deepEqual(values, ['month','year']); assert.equal(errors.length,0);
});
test('leaving screen ignores pending result and current errors are delivered', async () => {
  const { createLatestRequest } = load('progress/request.ts');
  const request=createLatestRequest(); const pending=deferred(); const values=[]; const errors=[];
  const run=request.run(()=>pending.promise, x=>values.push(x), e=>errors.push(e));
  request.cancel(); pending.resolve('private data'); await run; assert.equal(values.length,0);
  await request.run(async()=>{throw new Error('offline');}, x=>values.push(x), e=>errors.push(e.message));
  assert.deepEqual(errors,['offline']);
});
test('calendar mutations notify only after success and unsubscribe stops refresh', async () => {
  const changes=load('progress/changes.ts'); let count=0;
  const unsubscribe=changes.subscribeProgressChanges(()=>count++);
  let fail=false;
  const api=load('api/calendar.ts', {'../progress/changes':changes,'./client':{apiRequest:async()=>{if(fail)throw new Error('offline'); return {record_id:1};}}});
  await api.createEntry({}); await api.updateEntry(1,{}); assert.equal(count,2);
  fail=true; await assert.rejects(api.createEntry({})); assert.equal(count,2);
  unsubscribe(); fail=false; await api.updateEntry(1,{}); assert.equal(count,2);
});

test('focused statistics refresh on writes and period changes; blur blocks late data', async () => {
  const changes = load('progress/changes.ts');
  const request = load('progress/request.ts');
  let owner=1; let states=[]; let cursor=0; let refs=[]; let refCursor=0;
  let focus; let cleanup; let calls=[]; const events={};
  const browser={addEventListener:(name,fn)=>{events[name]=fn;},removeEventListener:name=>{delete events[name];}};
  const document={...browser,visibilityState:'hidden'};
  const hooks = load('progress/useProgressStatistics.ts', {
    react: {
      useState: initial => { const i=cursor++; if (!(i in states)) states[i]=initial; return [states[i], value=>{states[i]=value;}]; },
      useRef: initial => { const i=refCursor++; refs[i] ??= {current:initial}; return refs[i]; },
      useCallback: fn=>fn,
    },
    'expo-router': {useFocusEffect: fn=>{focus=fn;}},
    '../auth/AuthProvider': {useAuth: ()=>({user:{user_id:owner}})},
    '../api/statistics': {getStatistics: period=>{const d=deferred();calls.push({period,...d});return d.promise;}},
    './changes': changes, './request':request,
  }, {window:browser,document});
  function render(period='all') {cursor=0;refCursor=0;return hooks.useProgressStatistics(period);}
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  render(); cleanup=focus(); assert.equal(calls.length,1);
  calls[0].resolve({current_streak:7}); await flush(); assert.equal(render().data.current_streak,7);
  changes.notifyProgressChanged(); assert.equal(calls.length,2);
  calls[1].resolve({current_streak:0}); await flush(); assert.equal(render().data.current_streak,0);
  cleanup(); render('month'); cleanup=focus(); assert.equal(calls[2].period,'month');
  cleanup(); calls[2].resolve({current_streak:99}); await flush(); assert.equal(render('month').data,null);
  owner=2; render('month'); cleanup=focus(); assert.equal(render('month').data,null);
  calls[3].resolve({current_streak:1}); await flush(); assert.equal(render('month').data.current_streak,1);
  events.visibilitychange(); assert.equal(calls.length,4);
  document.visibilityState='visible'; events.visibilitychange(); assert.equal(calls.length,5);
  calls[4].resolve({current_streak:2}); await flush(); assert.equal(render('month').data.current_streak,2);
  cleanup(); changes.notifyProgressChanged(); assert.equal(calls.length,5); assert.equal(Object.keys(events).length,0);
});
