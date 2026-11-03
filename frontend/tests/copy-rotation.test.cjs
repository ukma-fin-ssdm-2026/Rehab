const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const test=require('node:test');const ts=require('typescript');
function storage(){const items=new Map();return {getItem:key=>items.get(key)??null,setItem:(key,value)=>items.set(key,value),removeItem:key=>items.delete(key)};}
test('copy changes on login and Kyiv midnight, survives reload and isolates accounts',()=>{
 const file=path.join(__dirname,'../src/messages/rotation.ts');
 assert.ok(fs.existsSync(file),'rotation module missing');
 let now=new Date('2026-10-31T21:59:00Z');
 const localStorage=storage(),sessionStorage=storage();
 function load(){
  const module={exports:{}};
  class Clock extends Date {constructor(...args){super(...(args.length?args:[now]));}static now(){return +now;}}
  const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,Date:Clock,Intl,window:{localStorage,sessionStorage}});
  return module.exports;
 }
 let api=load();api.beginCopySession(1,true);assert.equal(api.getMessageVariation(),0);
 api=load();api.beginCopySession(1,false);assert.equal(api.getMessageVariation(),0);
 api.beginCopySession(1,true);assert.equal(api.getMessageVariation(),1);
 now=new Date('2026-10-31T22:00:01Z');assert.equal(api.getMessageVariation(),2);
 api=load();api.beginCopySession(1,false);assert.equal(api.getMessageVariation(),2);
 api.beginCopySession(1,true);assert.equal(api.getMessageVariation(),3);
 api.clearCopySession();assert.equal(api.getMessageVariation(),0);
 api.beginCopySession(2,true);assert.equal(api.getMessageVariation(),0);
 api.beginCopySession(1,true);assert.equal(api.getMessageVariation(),0);
});
