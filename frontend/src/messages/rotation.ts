/** Presentation-only cursor: no tokens, calendars or authored messages are stored. */
type Cursor = { cursor: number; day: string; owner?: number };
const memory = new Map<string, string>();
let active: Cursor | null = null;
const listeners = new Set<() => void>();
let timer: ReturnType<typeof setInterval> | null = null;
let previous = 0;
const mod = (value: number) => ((value % 4) + 4) % 4;

export function copyDay(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Kyiv', year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
  const value = (key: string) => parts.find(part=>part.type===key)!.value;
  return `${value('year')}-${value('month')}-${value('day')}`;
}
function elapsed(from: string, to: string): number {
  return Math.round((Date.parse(to+'T00:00:00Z')-Date.parse(from+'T00:00:00Z'))/86400000);
}
function store(session: boolean): Storage | null {
  try { return typeof window === 'undefined' ? null : session ? window.sessionStorage : window.localStorage; }
  catch { return null; }
}
function read(key: string, session = false): Cursor | null {
  try {
    const raw = store(session)?.getItem(key) ?? memory.get(key);
    if (!raw) return null;
    const value = JSON.parse(raw);
    return Number.isInteger(value.cursor) && value.cursor >= 0 && value.cursor < 4
      && typeof value.day === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value.day)
      && Number.isFinite(Date.parse(value.day+'T00:00:00Z')) ? value : null;
  } catch { return null; }
}
function write(key: string, value: Cursor, session = false) {
  const raw = JSON.stringify(value); memory.set(key,raw);
  try { store(session)?.setItem(key,raw); } catch { /* Private mode/quota: keep in memory. */ }
}
export function getMessageVariation(): number {
  return active ? mod(active.cursor+elapsed(active.day,copyDay())) : 0;
}
function changed() {
  const value = getMessageVariation();
  if (value !== previous) { previous=value; listeners.forEach(listener=>listener()); }
}
export function beginCopySession(owner: number, fresh = false): void {
  const day = copyDay();
  const saved = read('rehab.copy.session',true);
  if (!fresh && saved?.owner === owner) active=saved;
  else if (!fresh && active?.owner === owner) return;
  else {
    const last=read(`rehab.copy.last.${owner}`);
    active={owner,day,cursor:last ? mod(last.cursor+elapsed(last.day,day)+1) : 0};
    write(`rehab.copy.last.${owner}`,active);
    write('rehab.copy.session',active,true);
  }
  changed();
}
export function clearCopySession(): void {
  active=null;memory.delete('rehab.copy.session');
  try { store(true)?.removeItem('rehab.copy.session'); } catch { /* No private data retained. */ }
  changed();
}
export function subscribeCopy(listener: () => void): () => void {
  listeners.add(listener);
  if (listeners.size === 1) {
    previous=getMessageVariation();timer=setInterval(changed,15000);
    if (typeof window !== 'undefined') window.addEventListener('focus',changed);
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange',changed);
  }
  return () => {
    listeners.delete(listener);
    if (!listeners.size) {
      if(timer!==null) clearInterval(timer);timer=null;
      if(typeof window!=='undefined') window.removeEventListener('focus',changed);
      if(typeof document!=='undefined') document.removeEventListener('visibilitychange',changed);
    }
  };
}
