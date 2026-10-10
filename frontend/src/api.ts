// The ONLY module allowed to touch the network. Every request is recorded in the Privacy Ledger. No bodies are kept.
import { useStore } from "./store";

const BASE = import.meta.env.VITE_API_BASE ?? "";

export interface Hit { ruleId: string; label: string; why: string; weight: number; evidence: string; start: number; end: number; critical: boolean }
export interface Detection {
  score: number; verdict: "scam" | "suspicious" | "low"; scamType: string; scamTypeName: string; critical: boolean;
  hits: Hit[]; urls: string[]; advice: string[]; redactedText: string; maskedCount: number; truncated: boolean;
}
export type FieldKey = "amount" | "utrs" | "bank" | "account" | "when" | "mobile" | "scamPhones" | "scamUpi" | "scamLinks" | "description" | "name" | "location";
export interface Fields {
  amount: string; bank: string; account: string; when: string; mobile: string; name: string; location: string; description: string;
  utrs: string[]; scamPhones: string[]; scamUpi: string[]; scamLinks: string[];
}
export type Meta = Record<FieldKey, { tier: 1 | 2 | 3; warn: string | null; auto: boolean }>;
export interface Missing { key: string; howToFind: string }
export interface Extracted { incident: { amounts: string[]; possibleUtrs: string[]; banks: string[] }; fields: Fields; meta: Meta; missing: Missing[]; maskedCount: number; truncated: boolean; redactedText: string }
export interface Pack {
  mode: "A" | "B"; callScript: string[] | null; portalSheet: { section: string; key: string; label: string; tier: number; value: string }[] | null;
  portalVerified: boolean; complaint: string; bankLetter: string; checklist: { id: string; title: string; detail: string }[]; missing: Missing[];
  banner: { zone: "first2h" | "day" | "later"; message: string }; packTxt: string; ics: string;
}
export interface AskResult {
  fallback: boolean; message: string | null;
  results: { id: string; q: string; a: string; sources: { title: string; url: string; publisher: string }[]; verifiedOn: string; score: number; translationPending: boolean }[];
}

async function call<T>(label: string, path: string, body?: unknown): Promise<T> {
  const payload = body === undefined ? undefined : JSON.stringify(body);
  const entry = { id: crypto.randomUUID(), t: Date.now(), label, path, method: payload ? "POST" : "GET", bytesOut: payload ? new Blob([payload]).size : 0 };
  try {
    const res = await fetch(BASE + path, { method: entry.method, headers: payload ? { "Content-Type": "application/json" } : undefined, body: payload });
    const text = res.status === 204 ? "" : await res.text();
    useStore.getState().addLedger({ ...entry, bytesIn: new Blob([text]).size, status: res.status });
    if (!res.ok) throw new Error(String(res.status));
    return (text ? JSON.parse(text) : undefined) as T;
  } catch (e) {
    if (!(e instanceof Error && /^\d+$/.test(e.message))) useStore.getState().addLedger({ ...entry, bytesIn: 0, status: "error" });
    throw e;
  }
}

export const api = {
  check: (text: string, lang: string) => call<Detection>("Check message", "/v1/check", { text, lang }),
  extract: (text: string, lang: string) => call<Extracted>("Find details", "/v1/extract", { text, lang }),
  validate: (fields: Fields) => call<{ meta: Meta; missing: Missing[] }>("Check fields", "/v1/validate", { fields }),
  pack: (fields: Fields, mode: "A" | "B", lang: string, elapsed: string) => call<Pack>("Build pack", "/v1/pack", { fields, mode, lang, elapsed }),
  ask: (question: string, lang: string) => call<AskResult>("Ask", "/v1/ask", { question, lang }),
  report: (page: string, note: string) => call<void>("Report an error", "/v1/report-error", { page, note }),
};
