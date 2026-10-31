const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const test=require('node:test');const ts=require('typescript');
function load(file,imports={},globals={}) {
 const module={exports:{}};
 const code=ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
 vm.runInNewContext(code,{module,exports:module.exports,...globals,require:name=>{assert.ok(name in imports,name);return imports[name];}});
 return module.exports;
}
test('pagination refreshes loaded pages and avoids duplicate arrivals',async()=>{
 const {loadInboxPages}=load('messages/inbox.ts');const calls=[];
 const result=await loadInboxPages(async(limit,offset)=>{
   calls.push([limit,offset]);
   return {items:offset===0?Array.from({length:30},(_,i)=>({notification_id:60-i})):Array.from({length:30},(_,i)=>({notification_id:31-i})),total:59,limit,offset};
 },60);
 assert.deepEqual(calls,[[30,0],[30,30]]);assert.equal(result.items.length,59);
 assert.equal(result.items[0].notification_id,60);assert.equal(result.total,59);
 await assert.rejects(loadInboxPages(async()=>{throw new Error('offline');}));
 const empty=await loadInboxPages(async()=>({items:[],total:0,limit:30,offset:0}));assert.equal(empty.items.length,0);
});
test('inbox lifecycle polls while focused, drops old owners and cancels on blur',async()=>{
 let states=[],refs=[],cursor=0,refCursor=0,focus,cleanup,owner=1,events={},timer;
 const deferred=()=>{let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};};
 const calls=[];const loader=()=>{const next=deferred();calls.push(next);return next.promise;};
 const browser={addEventListener:(key,fn)=>{events[key]=fn;},removeEventListener:key=>{delete events[key];}};
 const document={...browser,visibilityState:'visible'};
 const request=load('progress/request.ts');const inbox=load('messages/inbox.ts');
 const hooks=load('messages/useMessages.ts',{
  react:{useCallback:fn=>fn,useRef:initial=>{const i=refCursor++;refs[i]??={current:initial};return refs[i];},useState:initial=>{const i=cursor++;if(!(i in states))states[i]=initial;return [states[i],value=>{states[i]=value;}];}},
  'expo-router':{useFocusEffect:fn=>{focus=fn;}},'../auth/AuthProvider':{useAuth:()=>({user:{user_id:owner}})},
  '../profile/ProfileProvider':{useProfile:()=>({profile:{message_style:'formal'}})},
  '../api/notifications':{markNotificationRead:loader,getUnreadCount:loader,listNotifications:loader},
  '../progress/request':request,'./inbox':inbox,
 },{window:browser,document,setInterval:fn=>{timer=fn;return 1;},clearInterval:()=>{timer=null;}});
 function render(){cursor=0;refCursor=0;return hooks.useMessageResource(loader,true);}
 const flush=()=>new Promise(resolve=>setImmediate(resolve));
 render();cleanup=focus();assert.equal(calls.length,1);
 calls[0].resolve({count:3});await flush();assert.equal(render().data.count,3);
 timer();assert.equal(calls.length,2);
 owner=2;assert.equal(render().data,null);cleanup();render();cleanup=focus();assert.equal(calls.length,3);
 calls[2].resolve({count:1});await flush();calls[1].resolve({count:99});await flush();assert.equal(render().data.count,1);
 document.visibilityState='hidden';timer();assert.equal(calls.length,3);
 document.visibilityState='visible';events.visibilitychange();assert.equal(calls.length,4);
 cleanup();calls[3].resolve({count:99});await flush();assert.equal(render().data.count,1);
 assert.equal(timer,null);assert.equal(Object.keys(events).length,0);
});
test('messages navigation rejects guest, admin and pending onboarding',()=>{
 let auth={user:null,loading:false,onboardingPending:false};
 const screen=load('app/messages/_layout.tsx',{
  'expo-router':{Redirect:'Redirect',Stack:'Stack'},'../../auth/AuthProvider':{useAuth:()=>auth},
  '../../components/ui/ScreenState':{ScreenState:'ScreenState'},'react/jsx-runtime':{jsx:(type,props)=>({type,props})},
 }).default;
 assert.equal(screen().type,'Redirect');
 auth={...auth,user:{role:'admin'}};assert.equal(screen().type,'Redirect');
 auth={...auth,user:{role:'user'},onboardingPending:true};assert.equal(screen().props.href,'/onboarding');
 auth={...auth,onboardingPending:false};assert.equal(screen().type,'Stack');
});
