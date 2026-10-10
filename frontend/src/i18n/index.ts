import en from "./en.json";
import hi from "./hi.json";
import mr from "./mr.json";

export type Lang = "en" | "hi" | "mr";
export type Guide = "asha" | "kabir";
const dict: Record<Lang, Record<string, string>> = { en, hi, mr };

/** Translate a key. Guide lines try a masculine `.m` variant for Kabir. Falls back to English, then the key. */
export function translate(lang: Lang, key: string, vars: Record<string, string | number> = {}, guide?: Guide): string {
  const d = dict[lang];
  const raw = (guide === "kabir" && d[key + ".m"]) || d[key] || en[key as keyof typeof en] || key;
  return raw.replace(/\{(\w+)\}/g, (_, k: string) => String(vars[k] ?? ""));
}

export const hasKey = (lang: Lang, key: string) => key in dict[lang];
export const LANG_TAG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };
