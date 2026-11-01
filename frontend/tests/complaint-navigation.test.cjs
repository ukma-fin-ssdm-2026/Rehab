const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const ts = require('typescript');

test('reporting a received comment passes the private notification ID to evidence lookup', () => {
  const routes = [];
  const data = {notification_id: 9, relationship_id: 4, can_report_mentor: true,
    can_support: false, can_view_mentee: false, created_at: '2026-10-31T12:00:00Z',
    support_comment: {support_comment_id: 15, text: 'Support', author:{nickname:'mentor',email:'mentor@example.test'}, created_at: '2026-10-31T12:00:00Z'}};
  const jsx = (type, props) => ({type, props});
  const imports = {
    'react': {useRef: value => ({current:value}), useState: value => [value,()=>{}]},
    '../../components/visual/ScreenScrollView':{ScreenScrollView:'ScrollView'},
  '../../components/visual/GlassCard':{GlassCard:'View'},
  'react/jsx-runtime': {jsx, jsxs:jsx, Fragment:'Fragment'},
    'react-native': Object.fromEntries(['ActivityIndicator','Pressable','ScrollView','Text','TextInput','View'].map(x=>[x,x])),
    'expo-router': {router:{push:route=>routes.push(route),back(){}},useLocalSearchParams:()=>({notification_id:'9'})},
    '../../api/client': {ApiError: class extends Error {}},
    '../../api/notifications': {sendSupport(){}},
    '../../auth/AuthProvider': {useAuth:()=>({user:{user_id:2}})},
    '../../messages/useMessages': {useMessage:()=>({data,loading:false,error:null,reload(){}})},
    '../../messages/support': {createSupportSender:()=>()=>{}},
    '../../messages/styles': {messageStyles:{}},
  };
  const module = {exports:{}};
  const source = fs.readFileSync(path.join(__dirname,'../src/app/messages/[notification_id].tsx'),'utf8');
  const code = ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,require:name=>{assert.ok(name in imports,name);return imports[name];}});
  const screen = module.exports.default();
  const tree = screen.type(screen.props);
  function visit(node) {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) return node.forEach(visit);
    if (node.type === 'Pressable' && node.props.children?.props.children === 'Поскаржитися') node.props.onPress();
    visit(node.props?.children);
  }
  visit(tree);
  assert.equal(routes.length,1);
  assert.equal(routes[0].pathname,'/support/report');
  assert.equal(routes[0].params.relationship_id,'4');
  assert.equal(routes[0].params.notification_id,'9');
  assert.equal(routes[0].params.support_comment_id,undefined);
});
