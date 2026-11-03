export function showBack(path: string): boolean {
  return !['/','/home','/login','/register','/onboarding','/admin','/admin/complaints'].includes(path);
}
export function goBack(router: {canGoBack():boolean;back():void;replace(path: '/home' | '/admin/complaints'):void}, role: string): void {
  if(router.canGoBack()) router.back();
  else router.replace(role==='admin' ? '/admin/complaints' : '/home');
}
