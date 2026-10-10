import { useEffect, useState } from "react";
import { api } from "../api";
import { GuideStage } from "../components/GuideStage";
import { useT } from "../i18n/useT";
import { useStore } from "../store";

export default function Ask() {
  const { t, lang } = useT();
  const { ask, pushAsk, say, setMood, react } = useStore();
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { setMood("idle"); say("g.ask.start"); }, [say, setMood]);

  const submit = async (question: string) => {
    if (!question.trim() || busy) return;
    setBusy(true); setQ(""); setMood("thinking");
    try {
      const a = await api.ask(question, lang);
      pushAsk({ q: question, a });
      if (a.fallback) { say("g.ask.none"); setMood("reassure", 2000); } else react("amountFound");
    } catch { say("g.error"); } finally { setBusy(false); }
  };
  return (
    <div className="stage-grid page-in">
      <div className="guide-col"><GuideStage lookAt="input" /></div>
      <div>
        <h1>{t("ask.title")}</h1>
        <div className="row" style={{ marginBottom: 12 }}>
          {[1, 2, 3].map((n) => <button key={n} className="chip" onClick={() => submit(t(`ask.sugg${n}`))}>{t(`ask.sugg${n}`)}</button>)}
        </div>
        <div className="chat" aria-live="polite">
          {ask.map((x, i) => (
            <div key={i} className="chat">
              <div className="q">{x.q}</div>
              {x.a?.fallback ? <div className="card">{t("g.ask.none")}</div> : x.a?.results.slice(0, 1).map((r) => (
                <div key={r.id} className="card">
                  <p><strong>{r.q}</strong></p>
                  <p>{r.a}</p>
                  {r.translationPending && <p className="hint">{t("ask.pending")}</p>}
                  <div className="src">
                    {r.sources.map((s) => <a key={s.url} className="chip" href={s.url} target="_blank" rel="noreferrer noopener">{t("ask.source")}: {s.publisher}</a>)}
                    <span className="hint">{t("ask.verified", { date: r.verifiedOn })}</span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
        <form className="row" style={{ marginTop: 16 }} onSubmit={(e) => { e.preventDefault(); submit(q); }}>
          <label htmlFor="q" className="sr-only">{t("ask.placeholder")}</label>
          <input id="q" className="field" style={{ flex: 1, minWidth: 200 }} value={q} maxLength={300} placeholder={t("ask.placeholder")} onChange={(e) => setQ(e.target.value)} />
          <button className="btn primary" disabled={busy}>{t("ask.button")}</button>
        </form>
      </div>
    </div>
  );
}
