import { Lock, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useT } from "../i18n/useT";
import { useStore } from "../store";

/** DRD 6.6: every network request, never its content. */
export function Ledger() {
  const { t } = useT();
  const { ledger, ledgerOpen, setLedgerOpen, wipeAll } = useStore();
  const head = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (!ledgerOpen) return;
    head.current?.focus();
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setLedgerOpen(false);
    addEventListener("keydown", esc);
    return () => removeEventListener("keydown", esc);
  }, [ledgerOpen, setLedgerOpen]);
  if (!ledgerOpen) return null;
  return (
    <>
      <div className="scrim" role="presentation" onClick={() => setLedgerOpen(false)} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="ledger-h">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 id="ledger-h" ref={head} tabIndex={-1}><Lock size={20} aria-hidden="true" /> {t("ledger.title")}</h2>
          <button className="btn icon ghost" onClick={() => setLedgerOpen(false)} aria-label="Close"><X /></button>
        </div>
        <p><strong>{t("ledger.summary")}</strong></p>
        <p className="hint">{t("ledger.explain")}</p>
        <ul aria-live="polite" style={{ listStyle: "none", padding: 0 }} data-testid="ledger-list">
          {ledger.length === 0 && <li>{t("ledger.empty")}</li>}
          {[...ledger].reverse().map((e) => (
            <li key={e.id} className="ledger-item">
              <time dateTime={new Date(e.t).toISOString()} className="mono">{new Date(e.t).toLocaleTimeString()}</time>
              <span>{e.label.startsWith("ledger.") ? t(e.label) : e.label} <span className="hint mono">{e.path}</span></span>
              <span className="hint">{e.status === "error" ? "error" : e.status}{e.method !== "LOCAL" && <><br />{t("ledger.bytes", { out: e.bytesOut, in: e.bytesIn })}</>}</span>
            </li>
          ))}
        </ul>
        <h3>{t("ledger.local")}</h3>
        <p className="hint">{t("ledger.localD")}</p>
        <button className="btn" onClick={() => { wipeAll(); setLedgerOpen(false); }}>{t("after.delete")}</button>
      </aside>
    </>
  );
}
