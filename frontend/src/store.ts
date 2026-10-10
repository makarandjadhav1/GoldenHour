import { create } from "zustand";
import type { AskResult, Detection, FieldKey, Fields, Meta, Missing, Pack } from "./api";
import type { Guide, Lang } from "./i18n";
import type { Mood } from "./guides/moods";
import { moodFor, type GuideEvent } from "./guides/reactions";

export type Elapsed = "lt15" | "m30" | "h1to2" | "sameDay" | "earlier";
export interface LedgerEntry { id: string; t: number; label: string; path: string; method: string; bytesOut: number; bytesIn: number; status: number | "error" }
export interface Line { id: number; key: string; vars?: Record<string, string | number> }

export const emptyFields = (): Fields => ({
  amount: "", bank: "", account: "", when: "", mobile: "", name: "", location: "", description: "",
  utrs: [], scamPhones: [], scamUpi: [], scamLinks: [],
});

interface Settings { lang: Lang; guide: Guide; textScale: 1 | 1.25 | 1.5; theme: "system" | "light" | "dark"; contrast: "normal" | "high"; motion: "system" | "reduce" | "full"; readAloud: boolean }
const SETTINGS_KEY = "gh.settings";
const defaults: Settings = { lang: "en", guide: "asha", textScale: 1, theme: "system", contrast: "normal", motion: "system", readAloud: false };

function loadSettings(): Settings {
  try { return { ...defaults, ...JSON.parse(sessionStorage.getItem(SETTINGS_KEY) ?? "{}") }; } catch { return defaults; }
}

interface State extends Settings {
  set: (s: Partial<Settings>) => void;
  mood: Mood; lines: Line[]; speaking: boolean;
  say: (key: string, vars?: Line["vars"]) => void;
  setMood: (m: Mood, holdMs?: number, then?: Mood) => void;
  react: (e: GuideEvent) => void;
  check: { input: string; detection?: Detection; busy: boolean };
  setCheck: (c: Partial<State["check"]>) => void;
  lost: { narrative: string; elapsed: Elapsed; quick: boolean; fields: Fields; meta?: Meta; missing: Missing[]; possibleUtrs: string[]; mode: "A" | "B"; pack?: Pack; extracted: boolean };
  setLost: (l: Partial<State["lost"]>) => void;
  setField: (k: FieldKey, v: string | string[]) => void;
  ask: { q: string; a?: AskResult }[];
  pushAsk: (x: { q: string; a?: AskResult }) => void;
  ledger: LedgerEntry[];
  addLedger: (e: Omit<LedgerEntry, never>) => void;
  ledgerOpen: boolean;
  setLedgerOpen: (o: boolean) => void;
  wipeAll: () => void;
}

const freshLost = (): State["lost"] => ({ narrative: "", elapsed: "m30", quick: false, fields: emptyFields(), missing: [], possibleUtrs: [], mode: "A", extracted: false });
let lineId = 0;
let moodTimer: ReturnType<typeof setTimeout> | undefined;

export const useStore = create<State>((set, get) => ({
  ...loadSettings(),
  set: (s) => {
    set(s);
    const { lang, guide, textScale, theme, contrast, motion, readAloud } = get();
    try { sessionStorage.setItem(SETTINGS_KEY, JSON.stringify({ lang, guide, textScale, theme, contrast, motion, readAloud })); } catch { /* storage may be blocked */ }
  },
  mood: "idle", lines: [], speaking: false,
  say: (key, vars) => set((s) => ({ lines: [...s.lines.slice(-2), { id: ++lineId, key, vars }] })),
  setMood: (m, holdMs, then = "idle") => {
    clearTimeout(moodTimer);
    set({ mood: m });
    if (holdMs) moodTimer = setTimeout(() => set({ mood: then }), holdMs);
  },
  react: (e) => {
    const r = moodFor(e);
    if (r.line) get().say(r.line);
    get().setMood(r.mood, r.ms || undefined, r.then ?? "idle");
  },
  check: { input: "", busy: false },
  setCheck: (c) => set((s) => ({ check: { ...s.check, ...c } })),
  lost: freshLost(),
  setLost: (l) => set((s) => ({ lost: { ...s.lost, ...l } })),
  setField: (k, v) => set((s) => ({ lost: { ...s.lost, fields: { ...s.lost.fields, [k]: v } } })),
  ask: [],
  pushAsk: (x) => set((s) => ({ ask: [...s.ask, x] })),
  ledger: [],
  addLedger: (e) => set((s) => ({ ledger: [...s.ledger, e] })),
  ledgerOpen: false,
  setLedgerOpen: (o) => set({ ledgerOpen: o }),
  wipeAll: () => {
    try { sessionStorage.clear(); localStorage.clear(); } catch { /* ignore */ }
    indexedDB?.databases?.().then((dbs) => dbs.forEach((d) => d.name && indexedDB.deleteDatabase(d.name))).catch(() => undefined);
    caches?.keys?.().then((ks) => ks.filter((k) => k.startsWith("gh-user")).forEach((k) => caches.delete(k))).catch(() => undefined);
    speechSynthesis?.cancel?.();
    set((s) => ({
      ...defaults, check: { input: "", busy: false }, lost: freshLost(), ask: [], lines: [], mood: "reassure",
      ledger: [...s.ledger, { id: crypto.randomUUID(), t: Date.now(), label: "ledger.wiped", path: "", method: "LOCAL", bytesOut: 0, bytesIn: 0, status: 200 }],
    }));
    get().say("g.wiped");
  },
}));
