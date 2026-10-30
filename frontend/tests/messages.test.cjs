const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');
function load(relative, imports = {}) {
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src', relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(code, {module, exports:module.exports, require: name=>{
    assert.ok(name in imports,name); return imports[name];
  }});
  return module.exports;
}
const catalog = require('../src/messages/catalog-data.json');
test('all four styles retain context as plain text for every key', () => {
  const {messageText} = load('messages/catalog.ts', {'./catalog-data.json':catalog});
  for (const key of Object.keys(catalog)) for (const style of ['formal','humorous','zen','strict']) {
    const value=messageText(key,style,{nickname:'<img src=x>',date:'2026-10-30'});
    assert.ok(value.title && value.body);
    if(key==='relapse') assert.ok(value.body.includes('<img src=x>'));
  }
  assert.throws(()=>messageText('relapse','formal',{}));
});
test('notification API keeps pagination, ownership and empty read body', async () => {
  const calls=[];
  const api=load('api/notifications.ts',{'./client':{apiRequest:async(...args)=>{calls.push(args);return {};}}});
  await api.listNotifications(30,60); await api.getUnreadCount(); await api.getNotification(3); await api.markNotificationRead(3);
  await api.sendSupport(3,'  <b>Поруч</b>  ');
  assert.equal(calls[0][0],'/notifications?limit=30&offset=60');
  assert.equal(calls[1][0],'/notifications/unread-count');
  assert.equal(calls[2][0],'/notifications/3');
  assert.equal(calls[3][1].method,'PATCH'); assert.equal(calls[3][1].body,undefined);
  assert.deepEqual(JSON.parse(calls[4][1].body),{text:'<b>Поруч</b>'});
  await assert.rejects(api.sendSupport(3,'   '));
});
test('screen-scoped sender prevents double submit and releases after failure', async () => {
  let resolve;let count=0;
  const {createSupportSender}=load('messages/support.ts');
  const sender=createSupportSender(()=>{count++;return new Promise(r=>{resolve=r;});});
  const first=sender(3,'hello'); const second=sender(3,'hello'); assert.equal(count,1);
  resolve({support_comment_id:8}); assert.equal(await first,await second);
  const other=createSupportSender(async()=>{count++;throw new Error('offline');});
  await assert.rejects(other(3,'text')); await assert.rejects(other(3,'text')); assert.equal(count,3);
});
test('five goal labels are explicit calendar-day milestones', () => {
  const {FIXED_GOAL_DAYS,GOAL_LABELS}=load('constants/goals.ts');
  assert.deepEqual(Array.from(FIXED_GOAL_DAYS),[7,30,90,180,365]);
  assert.equal(GOAL_LABELS[90],'90 днів (3 місяці)');
  assert.equal(GOAL_LABELS[180],'180 днів (пів року)');
  assert.equal(GOAL_LABELS[365],'365 днів (рік)');
});
