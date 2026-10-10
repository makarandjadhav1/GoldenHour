import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { useT } from "../i18n/useT";
import { useStore } from "../store";

export default function Info() {
  const { page } = useParams();
  const { t } = useT();
  const s = useStore();
  const [note, setNote] = useState("");
  const [sent, setSent] = useState(false);
  if (page === "settings") {
    return (
      <div className="page-in" style={{ display: "grid", gap: 16, maxWidth: 560 }}>
        <h1>{t("settings.title")}</h1>
        <label className="row"><input type="checkbox" checked={s.contrast === "high"} onChange={(e) => s.set({ contrast: e.target.checked ? "high" : "normal" })} /> {t("settings.contrast")}</label>
        <label className="row"><input type="checkbox" checked={s.motion === "reduce"} onChange={(e) => s.set({ motion: e.target.checked ? "reduce" : "system" })} /> {t("settings.motion")}</label>
        <label className="row"><input type="checkbox" checked={s.readAloud} onChange={(e) => s.set({ readAloud: e.target.checked })} /> {t("settings.readAloud")}</label>
        <div className="seg" role="group" aria-label={t("top.textSize")}>
          {([1, 1.25, 1.5] as const).map((x) => <button key={x} aria-pressed={s.textScale === x} onClick={() => s.set({ textScale: x })}>{x * 100}%</button>)}
        </div>
        <div className="seg" role="group" aria-label={t("top.theme")}>
          {(["system", "light", "dark"] as const).map((x) => <button key={x} aria-pressed={s.theme === x} onClick={() => s.set({ theme: x })}>{t(`theme.${x}`)}</button>)}
        </div>
        <button className="btn" onClick={s.wipeAll}>{t("after.delete")}</button>
      </div>
    );
  }
  if (page === "report") {
    return (
      <form className="page-in" style={{ display: "grid", gap: 12, maxWidth: 560 }} onSubmit={async (e) => { e.preventDefault(); try { await api.report("", note); setSent(true); setNote(""); } catch { s.say("g.error"); } }}>
        <h1>{t("report.title")}</h1>
        <label htmlFor="note" className="sr-only">{t("report.placeholder")}</label>
        <textarea id="note" className="big" style={{ minHeight: 120 }} value={note} maxLength={500} placeholder={t("report.placeholder")} onChange={(e) => setNote(e.target.value)} />
        <button className="btn primary" disabled={!note.trim()} style={{ justifySelf: "start" }}>{t("report.send")}</button>
        {sent && <p role="status">{t("report.thanks")}</p>}
      </form>
    );
  }
  const key = page === "privacy" ? "privacy" : "about";
  return <div className="page-in"><h1>{t(`${key}.title`)}</h1><p>{t(`${key}.body`)}</p></div>;
}
