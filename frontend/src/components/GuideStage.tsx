import { Volume2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Guide, useReducedMotion } from "../guides/Guide";
import { useT } from "../i18n/useT";
import { speak, stopSpeaking } from "../tts";
import { useStore } from "../store";
import type { Mood } from "../guides/moods";

const CPS = 35; // typed characters per second (DRD 4.7)

/** The guide, the speech bubbles (typed, skippable) and the one live region screen readers hear. */
export function GuideStage({ compact = false, lookAt = "none" }: { compact?: boolean; lookAt?: "input" | "none" }) {
  const { t, lang, guide } = useT();
  const { lines, mood, readAloud } = useStore();
  const reduced = useReducedMotion();
  const last = lines[lines.length - 1];
  const full = last ? t(last.key, last.vars) : "";
  const [shown, setShown] = useState(full);
  const [noVoice, setNoVoice] = useState(false);
  const spoken = useRef(0);

  useEffect(() => {
    if (reduced || !full) return setShown(full);
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(full.slice(0, i));
      if (i >= full.length) clearInterval(id);
    }, 1000 / CPS);
    return () => clearInterval(id);
  }, [full, reduced]);

  useEffect(() => {
    if (readAloud && last && spoken.current !== last.id) {
      spoken.current = last.id;
      setNoVoice(!speak(full, lang));
    }
    return () => void stopSpeaking();
  }, [last, readAloud, full, lang]);

  const typing = shown.length < full.length;
  const prev = lines.length > 1 ? lines[lines.length - 2] : undefined;
  return (
    <div className={`guide-stage ${compact ? "compact" : ""}`}>
      <Guide who={guide} mood={mood as Mood} speaking={typing} lookAt={lookAt} />
      <div className="guide-label">{t("guide.label")}</div>
      <div className="bubble-wrap">
        {prev && !compact && <div className="bubble old" aria-hidden="true"><p>{t(prev.key, prev.vars)}</p></div>}
        {last && (
          <div className="bubble">
            <p aria-hidden="true">{shown}</p>
            <button className="btn ghost icon speak" onClick={(e) => { e.stopPropagation(); setNoVoice(!speak(full, lang)); }} aria-label={t("speak")}>
              <Volume2 size={18} aria-hidden="true" />
            </button>
          </div>
        )}
        {typing && <button className="btn ghost" onClick={() => setShown(full)}>{t("skip.anim")}</button>}
        {noVoice && <p className="warn" role="status">{t("settings.noVoice")}</p>}
        <div className="sr-only" aria-live="polite" role="status">{full}</div>
      </div>
    </div>
  );
}
