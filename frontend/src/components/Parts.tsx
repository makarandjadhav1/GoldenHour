import { AlertTriangle, Check, ChevronRight, Copy, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import type { Detection, FieldKey, Hit, Meta } from "../api";
import { useT } from "../i18n/useT";
import type { Elapsed } from "../store";

export function downloadBlob(name: string, text: string, mime: string) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------- Sun-Clock (DRD 7.1) ----------
const MINUTES: Record<Elapsed, number> = { lt15: 10, m30: 30, h1to2: 90, sameDay: 360, earlier: 2000 };
const pos = (m: number) => (m <= 120 ? (m / 120) * 0.3 : m <= 1440 ? 0.3 + ((m - 120) / 1320) * 0.5 : 0.8 + Math.min((m - 1440) / 1440, 1) * 0.18);
const CX = 180, CY = 170, R = 140;
const pt = (t: number) => [CX + R * Math.cos(Math.PI * (1 - t)), CY - R * Math.sin(Math.PI * (1 - t))] as const;
const arc = (a: number, b: number) => { const [x1, y1] = pt(a), [x2, y2] = pt(b); return `M${x1} ${y1} A${R} ${R} 0 0 1 ${x2} ${y2}`; };

export function SunClock({ bucket }: { bucket: Elapsed }) {
  const { t } = useT();
  const m = MINUTES[bucket];
  const zone = m <= 120 ? "first2h" : m <= 1440 ? "day" : "later";
  const [x, y] = pt(pos(m));
  const label = `${t(`zone.${zone}`)}. ${t(`zone.msg.${zone}`)}`;
  return (
    <div className="sunclock">
      <svg viewBox="0 0 360 190" role="img" aria-label={label}>
        <path d={arc(0, 0.3)} stroke="var(--sun)" strokeWidth="14" strokeLinecap="round" fill="none" />
        <path d={arc(0.3, 0.8)} stroke="var(--caution)" strokeWidth="10" strokeDasharray="12 8" fill="none" />
        <path d={arc(0.8, 1)} stroke="var(--ink-soft)" strokeWidth="8" strokeDasharray="2 10" strokeLinecap="round" fill="none" />
        <line x1="20" y1={CY} x2="340" y2={CY} stroke="var(--line)" strokeWidth="2" />
        <circle cx={x} cy={y} r="22" fill="var(--sun-soft)" /><circle cx={x} cy={y} r="13" fill="var(--sun)" />
        <text x="40" y="186" fontSize="11" fill="var(--ink-soft)" textAnchor="middle">0</text>
        <text x="320" y="186" fontSize="11" fill="var(--ink-soft)" textAnchor="middle">24h</text>
      </svg>
      <p><strong>{t(`zone.${zone}`)}.</strong> {t(`zone.msg.${zone}`)}</p>
    </div>
  );
}

// ---------- Field card (DRD 7.2) ----------
const LIST: FieldKey[] = ["utrs", "scamPhones", "scamUpi", "scamLinks"];
const split = (s: string) => s.split(/[,\n;]+/).map((x) => x.trim()).filter(Boolean);
const group4 = (s: string) => s.replace(/\s/g, "").replace(/(.{4})(?=.)/g, "$1 ");

export function FieldCard({ k, value, meta, onChange }: { k: FieldKey; value: string | string[]; meta?: Meta[FieldKey]; onChange: (v: string | string[]) => void }) {
  const { t } = useT();
  const isList = LIST.includes(k);
  const joined = Array.isArray(value) ? value.join(", ") : value;
  const [text, setText] = useState(joined);
  useEffect(() => { if (isList ? split(text).join("|") !== (value as string[]).join("|") : text !== value) setText(joined); }, [value]);
  const tier = meta?.tier ?? 1;
  const ok = !!joined && !meta?.warn;
  const id = `f-${k}`;
  return (
    <div className="card fieldcard" data-field={k}>
      <header>
        <label htmlFor={id}>{t(`f.${k}`)}</label>
        <span className={`chip t${tier}`}>{t(`tier.${tier}`)}</span>
      </header>
      <div className="val">
        {k === "description" ? (
          <textarea id={id} className="field" rows={3} value={text} onChange={(e) => { setText(e.target.value); onChange(e.target.value); }} aria-describedby={`${id}-w`} />
        ) : (
          <input id={id} className={`field ${k === "utrs" ? "mono" : ""}`} value={text} inputMode={k === "mobile" ? "tel" : undefined} aria-invalid={!!meta?.warn}
            aria-describedby={`${id}-w`} onChange={(e) => { setText(e.target.value); onChange(isList ? split(e.target.value) : e.target.value); }} />
        )}
        {ok && <span className="tick" role="img" aria-label="OK"><Check /></span>}
      </div>
      {k === "utrs" && Array.isArray(value) && value.length > 0 && <p className="mono hint" style={{ margin: "4px 0 0" }}>{value.map(group4).join("  ·  ")}</p>}
      <p id={`${id}-w`} className="warn" style={{ margin: "4px 0 0" }}>{meta?.warn}</p>
      <div className="row" style={{ gap: 8 }}>
        {meta?.auto && <span className="tag-auto">{t("f.auto")}</span>}
        {isList && <span className="tag-auto">{t("f.listHint")}</span>}
      </div>
      <details><summary>{t("f.howto")}</summary><p>{t(`howto.${k}`)}</p></details>
    </div>
  );
}

// ---------- Copy blocks (DRD 7.3) ----------
export function CopyButton({ text, label }: { text: string; label?: string }) {
  const { t } = useT();
  const [state, setState] = useState<"idle" | "ok" | "fail">("idle");
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setState("ok"); }
    catch {
      const ta = Object.assign(document.createElement("textarea"), { value: text });
      document.body.append(ta); ta.select();
      setState(document.execCommand("copy") ? "ok" : "fail"); ta.remove();
    }
    setTimeout(() => setState("idle"), 1600);
  };
  return (
    <>
      <button className="btn" onClick={copy}>{state === "ok" ? <Check size={18} /> : <Copy size={18} />} {state === "ok" ? t("copied") : label ?? t("copy")}</button>
      {state === "fail" && <span className="warn" role="status">{t("copyFail")}</span>}
    </>
  );
}

export const CopyBlock = ({ text }: { text: string }) => (
  <div className="card copyblock">{/* scrollable text must be reachable by keyboard */}
    {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
    <pre tabIndex={0}>{text}</pre><CopyButton text={text} /></div>
);

export function ScriptBlock({ lines }: { lines: string[] }) {
  const { t } = useT();
  return (
    <div className="card">
      <p className="hint">{t("pack.scriptIntro")}</p>
      <ol style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {lines.map((l, i) => (
          <li key={i}><label className="script-line"><input type="checkbox" /><span>{i + 1}. {l}</span></label></li>
        ))}
      </ol>
      <CopyButton text={lines.map((l, i) => `${i + 1}. ${l}`).join("\n")} />
    </div>
  );
}

// ---------- Verdict + highlights (DRD 7.4, 6.3) ----------
export function VerdictBanner({ d }: { d: Detection }) {
  const { t } = useT();
  const Icon = d.verdict === "scam" ? ShieldAlert : d.verdict === "suspicious" ? AlertTriangle : ShieldCheck;
  return (
    <div className={`verdict ${d.verdict}`}>
      <Icon size={36} aria-hidden="true" color="var(--vc)" />
      <div style={{ flex: 1 }}>
        <h2>{t(`verdict.${d.verdict}`)}</h2>
        {d.verdict !== "low" && <span className="chip">{d.scamTypeName}</span>}
      </div>
      <div className="ring" style={{ ["--p" as string]: d.score }} role="img" aria-label={`${t("check.score")}: ${d.score} / 100`}><span>{d.score}</span></div>
    </div>
  );
}

export function HighlightedText({ text, hits, active, onPick }: { text: string; hits: Hit[]; active: number | null; onPick: (i: number) => void }) {
  const idx = hits.map((h, i) => [h, i] as const).filter(([h]) => h.start >= 0 && h.end > h.start).sort((a, b) => a[0].start - b[0].start);
  const out: ReactNode[] = [];
  let at = 0;
  for (const [h, i] of idx) {
    if (h.start < at) continue; // skip overlaps
    if (h.start > at) out.push(text.slice(at, h.start));
    out.push(
      <mark key={i} className={`hit ${active === i ? "active" : ""}`}>
        <button className="hit-btn" aria-pressed={active === i} onClick={() => onPick(i)}>{text.slice(h.start, h.end)}</button>
      </mark>,
    );
    at = h.end;
  }
  out.push(text.slice(at));
  return <p className="msg">{out}</p>;
}

// ---------- Mode cards, stepper ----------
export function ModeCard({ mode, selected, disabled, onSelect }: { mode: "A" | "B" | "C"; selected?: boolean; disabled?: boolean; onSelect?: () => void }) {
  const { t } = useT();
  return (
    <button className="card mode" aria-pressed={selected} aria-disabled={disabled} onClick={() => !disabled && onSelect?.()} style={disabled ? { opacity: 0.6, cursor: "not-allowed" } : undefined}>
      {mode === "A" && <span className="chip t1">{t("mode.A.tag")}</span>}
      <h3 style={{ marginTop: 8 }}>{t(`mode.${mode}.t`)}</h3>
      {mode === "C" ? <p>{t("mode.C.na")}</p> : (
        <>
          <ul><li>{t(`mode.${mode}.1`)}</li>{mode === "A" && <li>{t("mode.A.2")}</li>}{mode === "B" && <li>{t("mode.B.2")}</li>}</ul>
          <p className="hint">{t(`mode.${mode}.pro`)}</p>
        </>
      )}
    </button>
  );
}

export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  const { t } = useT();
  return (
    <ol className="stepper" aria-label={t("lost.title")}>
      {steps.map((s, i) => (
        <li key={s} aria-current={i === current ? "step" : undefined}>{i < current ? <Check size={16} aria-hidden="true" /> : <span aria-hidden="true">{i + 1}</span>} {t(`lost.step.${s}`)}</li>
      ))}
    </ol>
  );
}

export const NextIcon = ChevronRight;
