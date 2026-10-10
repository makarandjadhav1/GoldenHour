import { ArrowLeft, ArrowRight, Download, Printer } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { api, type FieldKey, type Pack } from "../api";
import { CallButton } from "../components/Chrome";
import { GuideStage } from "../components/GuideStage";
import { CopyBlock, CopyButton, downloadBlob, FieldCard, ModeCard, ScriptBlock, Stepper, SunClock } from "../components/Parts";
import { useT } from "../i18n/useT";
import { useStore, type Elapsed } from "../store";

const STEPS = ["tell", "review", "mode", "pack", "after"] as const;
type Step = (typeof STEPS)[number];
const ELAPSED: Elapsed[] = ["lt15", "m30", "h1to2", "sameDay", "earlier"];
const TIER1: FieldKey[] = ["amount", "utrs", "bank", "when", "mobile", "account", "scamPhones", "scamUpi", "scamLinks"];
const TIER2: FieldKey[] = ["description", "name", "location"];
const QUICK: FieldKey[] = ["amount", "utrs", "bank", "when", "mobile"];

export default function Lost() {
  const { step: raw } = useParams();
  const step = (STEPS as readonly string[]).includes(raw ?? "") ? (raw as Step) : "tell";
  const { t } = useT();
  const { lost } = useStore();
  const idx = STEPS.indexOf(step);
  if (!raw) return <Navigate to="/lost/tell" replace />;
  if (step !== "tell" && !lost.extracted) return <Navigate to="/lost/tell" replace state={{ redirected: true }} />;
  return (
    <div className="stage-grid page-in">
      <div className="guide-col"><GuideStage lookAt={step === "tell" ? "input" : "none"} /></div>
      <div>
        <h1 tabIndex={-1} id="flow-h">{t("lost.title")}</h1>
        <Stepper steps={[...STEPS]} current={idx} />
        <SunClock bucket={lost.elapsed} />
        {step === "tell" && <Tell />}
        {step === "review" && <Review />}
        {step === "mode" && <Mode />}
        {step === "pack" && <PackStep />}
        {step === "after" && <After />}
      </div>
      <CallButton />
    </div>
  );
}

function Nav({ back, next, nextLabel, nextDisabled }: { back?: () => void; next?: () => void; nextLabel?: string; nextDisabled?: boolean }) {
  const { t } = useT();
  return (
    <div className="nav-row">
      {back ? <button className="btn" onClick={back}><ArrowLeft size={18} aria-hidden="true" /> {t("lost.back")}</button> : <span />}
      {next && <button className="btn primary" onClick={next} disabled={nextDisabled}>{nextLabel ?? t("lost.next")} <ArrowRight size={18} aria-hidden="true" /></button>}
    </div>
  );
}

const maskUtr = (u: string) => `UTR ···· ${u.slice(-4)}`;

function Tell() {
  const { t, lang } = useT();
  const nav = useNavigate();
  const { lost, setLost, react, say, setMood } = useStore();
  const [chips, setChips] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const seen = useRef({ amount: false, utr: false });
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => { say("g.lost.start"); setMood("concerned", 2200, "reassure"); }, [say, setMood]);

  const preview = useCallback(async (text: string) => {
    if (text.trim().length < 6) return setChips([]);
    try {
      const r = await api.extract(text, lang);
      const f = r.fields;
      setChips([...r.incident.amounts, ...f.utrs.map(maskUtr), ...f.scamUpi, ...f.scamPhones, ...(f.bank ? [f.bank] : [])]);
      if (r.maskedCount) { react("secretTyped"); setLost({ narrative: r.redactedText }); }
      if (r.incident.amounts.length && !seen.current.amount) { seen.current.amount = true; say("g.field.amount"); }
      if (f.utrs.length && !seen.current.utr) { seen.current.utr = true; react("utrValid"); }
    } catch { /* preview is best-effort */ }
  }, [lang, react, say, setLost]);

  const onChange = (v: string) => {
    setLost({ narrative: v });
    setMood("listening");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => { preview(v); setMood("idle"); }, 600);
  };

  const next = async () => {
    setBusy(true);
    try {
      const r = await api.extract(lost.narrative, lang);
      const fields = { ...r.fields, description: lost.extracted ? lost.fields.description : r.redactedText.slice(0, 1500) };
      setLost({ fields: lost.extracted ? keepEdited(lost.fields, r.fields) : fields, meta: r.meta, missing: r.missing, possibleUtrs: r.incident.possibleUtrs, extracted: true,
        narrative: r.maskedCount ? r.redactedText : lost.narrative });
      const found = r.fields.utrs.length || r.incident.amounts.length;
      if (!found) say("g.lost.cantRead"); else react("reviewReady");
      nav("/lost/review");
    } catch { say("g.error"); } finally { setBusy(false); }
  };

  return (
    <section>
      <label htmlFor="narr"><strong>{t("lost.tell.label")}</strong></label>
      <textarea id="narr" className="big" value={lost.narrative} maxLength={5000} placeholder={t("lost.tell.placeholder")} onChange={(e) => onChange(e.target.value)} />
      <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
        <legend><strong>{t("lost.when")}</strong></legend>
        <div className="radios">
          {ELAPSED.map((e) => (
            <label key={e} className="radio-card"><input type="radio" name="when" checked={lost.elapsed === e} onChange={() => setLost({ elapsed: e })} /> {t(`when.${e}`)}</label>
          ))}
        </div>
      </fieldset>
      <h3>{t("lost.found")}</h3>
      <div className="chips-found" aria-live="polite">{chips.length ? chips.map((c, i) => <span key={c + i} className="chip">{c}</span>) : <span className="hint">{t("lost.foundNone")}</span>}</div>
      <Nav next={next} nextDisabled={busy || !lost.narrative.trim()} />
    </section>
  );
}

// keep what the user already corrected when they come back and re-extract
const isEmpty = (v: unknown) => (Array.isArray(v) ? v.length === 0 : !v);
const keepEdited = <T extends object>(old: T, fresh: T): T =>
  Object.fromEntries(Object.entries(fresh).map(([k, v]) => [k, isEmpty(v) ? old[k as keyof T] : v])) as T;

function Review() {
  const { t } = useT();
  const nav = useNavigate();
  const { lost, setLost, setField, react, say } = useStore();
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const keys = lost.quick ? QUICK : [...TIER1, ...TIER2];

  const edit = (k: FieldKey, v: string | string[]) => {
    setField(k, v);
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      try {
        const r = await api.validate(useStore.getState().lost.fields);
        setLost({ meta: r.meta, missing: r.missing });
        if (k === "utrs" && Array.isArray(v) && v.length && !r.meta.utrs.warn) react("utrValid");
      } catch { /* validation is best-effort */ }
    }, 400);
  };
  const missingNow = lost.missing.filter((m) => !lost.quick || (QUICK as string[]).includes(m.key));

  return (
    <section>
      <h2>{t("lost.review.title")}</h2>
      <label className="row" style={{ marginBottom: 12 }}><input type="checkbox" checked={lost.quick} onChange={(e) => setLost({ quick: e.target.checked })} /> {t("lost.quick")}</label>
      {lost.possibleUtrs.filter((p) => !lost.fields.utrs.includes(p)).map((p) => (
        <div key={p} className="card row" style={{ justifyContent: "space-between" }}>
          <span>{t("lost.possible", { n: p })}</span>
          <button className="btn" onClick={() => edit("utrs", [...lost.fields.utrs, p])}>{t("lost.usePossible")}</button>
        </div>
      ))}
      {keys.map((k) => <FieldCard key={k} k={k} value={lost.fields[k]} meta={lost.meta?.[k]} onChange={(v) => edit(k, v)} />)}
      {missingNow.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>{t("lost.missing")}</h3>
          <ul>{missingNow.map((m) => <li key={m.key}>{t(`howto.${m.key}`)}</li>)}</ul>
          <p className="hint">{t("lost.fillLater")}</p>
        </div>
      )}
      <Nav back={() => nav("/lost/tell")} next={() => { if (!lost.fields.utrs.length) react("missingUtr"); else say("g.mode"); nav("/lost/mode"); }} />
    </section>
  );
}

function Mode() {
  const { t } = useT();
  const nav = useNavigate();
  const { lost, setLost, say, setMood } = useStore();
  useEffect(() => { say("g.mode"); setMood("reassure", 2200); const id = setTimeout(() => say("g.cantFile"), 1400); return () => clearTimeout(id); }, [say, setMood]);
  return (
    <section>
      <h2>{t("lost.mode.title")}</h2>
      <div className="modes">
        <ModeCard mode="A" selected={lost.mode === "A"} onSelect={() => setLost({ mode: "A" })} />
        <ModeCard mode="B" selected={lost.mode === "B"} onSelect={() => setLost({ mode: "B" })} />
        <ModeCard mode="C" disabled />
      </div>
      <Nav back={() => nav("/lost/review")} next={() => nav("/lost/pack")} />
    </section>
  );
}

function PackStep() {
  const { t, lang } = useT();
  const nav = useNavigate();
  const { lost, react, say } = useStore();
  const [pack, setPack] = useState<Pack>();
  const [tab, setTab] = useState<"script" | "portal" | "letter" | "complaint" | "checklist">(lost.mode === "A" ? "script" : "portal");
  useEffect(() => {
    let live = true;
    api.pack(lost.fields, lost.mode, lang, lost.elapsed).then((p) => { if (live) { setPack(p); react("packReady"); } }).catch(() => say("g.error"));
    return () => { live = false; };
  }, [lost.fields, lost.mode, lost.elapsed, lang, react, say]);
  const tabs = [lost.mode === "A" ? "script" : "portal", "letter", "complaint", "checklist"] as const;
  if (!pack) return <p role="status">…</p>;
  return (
    <section>
      <h2>{t("lost.pack.title")}</h2>
      <div role="tablist" aria-label={t("lost.pack.title")}>
        {tabs.map((x) => <button key={x} role="tab" aria-selected={tab === x} onClick={() => setTab(x)}>{t(`tab.${x}`)}</button>)}
      </div>
      <div role="tabpanel">
        {tab === "script" && pack.callScript && <ScriptBlock lines={pack.callScript} />}
        {tab === "portal" && pack.portalSheet && (
          <div>
            {!pack.portalVerified && <p className="warn">{t("pack.portalWarn")}</p>}
            {pack.portalSheet.map((r) => (
              <div key={r.key} className="card row" style={{ justifyContent: "space-between" }}>
                <div><div className="hint">{r.section}</div><strong>{r.label}</strong><div className="mono">{r.value || "…"}</div></div>
                {r.value && <CopyButton text={r.value} />}
              </div>
            ))}
          </div>
        )}
        {tab === "letter" && <CopyBlock text={pack.bankLetter} />}
        {tab === "complaint" && <CopyBlock text={pack.complaint} />}
        {tab === "checklist" && (
          <ol className="card" style={{ listStyle: "none", margin: 0 }}>
            {pack.checklist.map((c) => <li key={c.id}><label className="script-line"><input type="checkbox" /><span><strong>{c.title}</strong><br />{c.detail}</span></label></li>)}
          </ol>
        )}
      </div>
      <div className="row no-print" style={{ marginTop: 16 }}>
        <button className="btn" onClick={() => downloadBlob("goldenhour_pack.txt", pack.packTxt, "text/plain")}><Download size={18} aria-hidden="true" /> {t("download.pack")}</button>
        <button className="btn" onClick={() => window.print()}><Printer size={18} aria-hidden="true" /> {t("print")}</button>
      </div>
      <Nav back={() => nav("/lost/mode")} next={() => { react("afterStep"); nav("/lost/after"); }} />
    </section>
  );
}

function After() {
  const { t, lang } = useT();
  const nav = useNavigate();
  const { lost, wipeAll, setLost } = useStore();
  const [ics, setIcs] = useState("");
  useEffect(() => { api.pack(lost.fields, lost.mode, lang, lost.elapsed).then((p) => setIcs(p.ics)).catch(() => undefined); }, [lost.fields, lost.mode, lost.elapsed, lang]);
  return (
    <section>
      <h2>{t("lost.after.title")}</h2>
      <p>{t("after.hours")}</p>
      <button className="btn" disabled={!ics} onClick={() => downloadBlob("goldenhour_reminder.ics", ics, "text/calendar")}>{t("download.ics")}</button>
      <div className="card" style={{ marginTop: 16 }}><h3>{t("after.otp")}</h3><p>{t("after.otp.d")}</p></div>
      <div className="card"><h3>{t("after.recovery")}</h3><p>{t("after.recovery.d")}</p></div>
      <div className="row" style={{ marginTop: 16 }}>
        <button className="btn" onClick={() => { wipeAll(); nav("/"); }}>{t("after.delete")}</button>
        <button className="btn ghost" onClick={() => { setLost({ extracted: false }); nav("/lost/tell"); }}>{t("flow.restart")}</button>
      </div>
      <Nav back={() => nav("/lost/pack")} />
    </section>
  );
}
