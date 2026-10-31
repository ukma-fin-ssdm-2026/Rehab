const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const test=require('node:test');const ts=require('typescript');
test('humorous style requires confirmation, and cancellation does not change preferences',async()=>{
 const states=[];let cursor=0;const changes=[];
 const jsx=(type,props)=>({type,props});
 const imports={
  react:{useState:initial=>{const i=cursor++;if(!(i in states))states[i]=initial;return[states[i],v=>{states[i]=v;}];}},
  'react/jsx-runtime':{jsx,jsxs:jsx},
  'react-native':{Modal:'Modal',Pressable:'Pressable',ScrollView:'ScrollView',Text:'Text',View:'View'},
  '../../api/profile':{updateProfilePreferences:async value=>{changes.push(value.message_style);}},
  '../../components/ui/Button':{Button:'Button'},'../../components/ui/ScreenState':{ScreenState:'ScreenState'},
  '../../constants/theme':{theme:{colors:{}}},'../../profile/styles':{profileStyles:{}},
  '../../profile/ProfileProvider':{useProfile:()=>({profile:{message_style:'formal'},loading:false,refreshProfile:async()=>{}})},
 };
 const file=path.join(__dirname,'../src/app/profile/style.tsx');const module={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require:name=>{assert.ok(name in imports,name);return imports[name];}});
 function render(){cursor=0;return module.exports.default();}
 function all(node,out=[]){if(!node||typeof node!=='object')return out;if(Array.isArray(node)){node.forEach(x=>all(x,out));return out;}out.push(node);all(node.props?.children,out);return out;}
 const flush=()=>new Promise(resolve=>setImmediate(resolve));
 let tree=render();all(tree).filter(x=>x.props?.accessibilityRole==='radio')[1].props.onPress();await flush();
 assert.equal(changes.length,0);tree=render();assert.equal(all(tree).find(x=>x.type==='Modal').props.visible,true);
 all(tree).find(x=>x.props?.title==='Скасувати').props.onPress();tree=render();assert.equal(all(tree).find(x=>x.type==='Modal').props.visible,false);assert.equal(changes.length,0);
 all(tree).filter(x=>x.props?.accessibilityRole==='radio')[1].props.onPress();tree=render();
 all(tree).find(x=>x.props?.title==='Обрати гумористичний').props.onPress();await flush();assert.deepEqual(changes,['humorous']);
});
