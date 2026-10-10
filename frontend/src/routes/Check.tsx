import { ArrowRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { CallButton } from "../components/Chrome";
import { GuideStage } from "../components/GuideStage";
import { CopyButton, HighlightedText, VerdictBanner } from "../components/Parts";
import { useT } from "../i18n/useT";
import { useStore } from "../store";

const LANG_NAME = { en: "English", hi: "Hindi", mr: "Marathi" } as const;
const EXAMPLES = ["kyc", "parcel", "job"] as const;

export default function Check() {
  const { t, lang } = useT();
  const nav = useNavigate();
  const { check, setCheck, react, say, setMood, setLost } = useStore();
  const [active, setActive] = useState<number | null>(null);
  const [error, setError] = useState(false);
  const [consent, setConsent] = useState(false);
  const [opinion, setOpinion] = useState<Awaited<ReturnType<typeof api.explain>> | "off" | null>(null);
  const typing = useRef<ReturnType<typeof setTimeout>>(undefined);
  const d = check.detection;

  useEffect(() => { setMood("idle"); say("g.check.start"); }, [setMood, say]);

  const run = async (text = check.input) => {
    if (!text.trim()) return say("g.check.empty");
    setCheck({ busy: true }); setError(false); setMood("thinking"); say("g.check.think");
    try {
      const det = await api.check(text, lang);
      setCheck({ detection: det, busy: false }); setActive(null);
      react(det.verdict === "scam" ? "verdictScam" : det.verdict === "suspicious" ? "verdictSuspicious" : "verdictLow");
      if (det.maskedCount) setTimeout(() => react("secretTyped"), 1500);
    } catch { setCheck({ busy: false }); setError(true); say("g.error"); setMood("reassure", 2000); }
  };
  const familyText = d ? t("family.text", { type: d.scamTypeName }) : "";

  return (
    <div className="stage-grid page-in">
      <div className="guide-col"><GuideStage lookAt="input" /></div>
      <div>
        <h1>{t("check.title")}</h1>
        <label htmlFor="msg" className="sr-only">{t("check.placeholder")}</label>
        <textarea id="msg" className="big" value={check.input} placeholder={t("check.placeholder")} maxLength={5000}
          onChange={(e) => { setCheck({ input: e.target.value }); setMood("listening"); clearTimeout(typing.current); typing.current = setTimeout(() => setMood("idle"), 1800); }}
          onPaste={(e) => { const txt = e.clipboardData.getData("text"); if (txt) setTimeout(() => run(txt), 0); }} />
        <div className="row" style={{ margin: "12px 0" }}>
          <button className="btn primary" disabled={check.busy} onClick={() => run()}>{t("check.button")}</button>
          <span className="hint">{t("check.examples")}:</span>
          {EXAMPLES.map((x) => <button key={x} className="chip" onClick={() => { const txt = t(`check.ex.${x}.text`); setCheck({ input: txt }); run(txt); }}>{t(`check.ex.${x}`)}</button>)}
        </div>
        {error && <p className="warn" role="alert">{t("g.error")}</p>}
        {d && (
          <section aria-live="polite" style={{ display: "grid", gap: 16 }}>
            <VerdictBanner d={d} />
            {d.maskedCount > 0 && <p className="hint">{t("check.masked", { n: d.maskedCount })}</p>}
            <div className="card">
              <h3>{t("check.msg")}</h3>
              {d.hits.length > 0 && <p className="hint">{t("check.tapHit")}</p>}
              <HighlightedText text={d.redactedText} hits={d.hits} active={active} onPick={setActive} />
            </div>
            {d.hits.length > 0 && (
              <div>
                <h3>{t("check.why")}</h3>
                {[...d.hits.map((h, i) => [h, i] as const)].sort((a, b) => b[0].weight - a[0].weight).map(([h, i]) => (
                  <div key={i} className={`card reason ${active === i ? "on" : ""}`}><strong>{h.label}</strong><span>{h.why}</span><span className="hint mono">“{h.evidence}”</span></div>
                ))}
              </div>
            )}
            <div className="card"><h3>{t("check.todo")}</h3><ul className="steps-list">{d.advice.map((a) => <li key={a}>{a}</li>)}</ul></div>
            <div className="card">
              <label className="row"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> {t("ai.consent")}</label>
              <button className="btn" disabled={!consent} style={{ marginTop: 8 }}
                onClick={async () => { try { setOpinion(await api.explain(d.redactedText, d.hits.map((h) => h.label), LANG_NAME[lang])); } catch { setOpinion("off"); } }}>{t("ai.button")}</button>
              {opinion === "off" && <p className="hint" role="status">{t("ai.unavailable")}</p>}
              {opinion && opinion !== "off" && (
                <div role="status"><h3>{t("ai.title")} <span className="chip">{opinion.confidence}</span></h3><p>{opinion.why}</p>
                  {opinion.extraRedFlags.length > 0 && <ul>{opinion.extraRedFlags.map((f) => <li key={f}>{f}</li>)}</ul>}</div>
              )}
            </div>
            <p className="hint">{t("check.heuristic")}</p>
            <div className="row">
              {d.verdict !== "low" && <CopyButton text={familyText} label={t("check.family")} />}
              <button className="btn" onClick={() => { setLost({ narrative: check.input }); nav("/lost/tell"); }}>{t("check.paid")} <ArrowRight size={18} aria-hidden="true" /></button>
            </div>
          </section>
        )}
      </div>
      {d && d.verdict !== "low" && <CallButton />}
    </div>
  );
}
