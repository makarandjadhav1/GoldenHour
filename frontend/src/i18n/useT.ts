import { useCallback } from "react";
import { useStore } from "../store";
import { translate } from "./index";

/** t(key, vars). Re-renders when the language or guide changes. */
export function useT() {
  const lang = useStore((s) => s.lang);
  const guide = useStore((s) => s.guide);
  const t = useCallback((key: string, vars?: Record<string, string | number>) => translate(lang, key, vars, guide), [lang, guide]);
  return { t, lang, guide };
}
