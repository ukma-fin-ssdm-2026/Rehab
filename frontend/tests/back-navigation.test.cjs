const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const test=require('node:test');const ts=require('typescript');
test('back navigation stays inside app, with safe role home when history is absent',()=>{
 const file=path.join(__dirname,'../src/navigation/back.ts');assert.ok(fs.existsSync(file),'back policy missing');
 const module={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module,exports:module.exports});
 const api=module.exports;
 for(const page of ['/home','/login','/register','/onboarding','/admin/complaints','/'])assert.equal(api.showBack(page),false);
 for(const page of ['/profile','/profile/edit','/goals','/calendar','/messages/3','/admin/analytics'])assert.equal(api.showBack(page),true);
 const calls=[];const router={canGoBack:()=>false,back:()=>calls.push('back'),replace:path=>calls.push(path)};
 api.goBack(router,'user');api.goBack(router,'admin');router.canGoBack=()=>true;api.goBack(router,'user');
 assert.deepEqual(calls,['/home','/admin/complaints','back']);
});
