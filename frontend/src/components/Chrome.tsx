import { Lock, Moon, Phone, ShieldCheck, Sun } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useT } from "../i18n/useT";
import type { Lang } from "../i18n";
import { useStore } from "../store";

export const IndependentChip = () => {
  const { t } = useT();
  return <span className="chip" data-testid="independent-chip"><ShieldCheck size={14} aria-hidden="true" /> {t("disclaimer.chip")}</span>;
};

export function TopBar() {
  const { t, lang, guide } = useT();
  const { set, textScale, theme, setLedgerOpen, ledger } = useStore();
  const langs: [Lang, string][] = [["en", "EN"], ["hi", "हिं"], ["mr", "मरा"]];
  const next = theme === "dark" ? "light" : "dark";
  return (
    <header className="topbar">
      <Link to="/" className="logo"><span className="logo-dot" aria-hidden="true" />{t("app.name")}</Link>
      <nav className="seg" aria-label={t("top.guide")}>
        {(["asha", "kabir"] as const).map((g) => (
          <button key={g} aria-pressed={guide === g} onClick={() => set({ guide: g })}>{g === "asha" ? "Asha" : "Kabir"}</button>
        ))}
      </nav>
      <div className="seg" role="group" aria-label={t("top.language")}>
        {langs.map(([l, label]) => <button key={l} aria-pressed={lang === l} lang={l} onClick={() => set({ lang: l })}>{label}</button>)}
      </div>
      <div className="seg textsize" role="group" aria-label={t("top.textSize")}>
        {([1, 1.25, 1.5] as const).map((s, i) => <button key={s} aria-pressed={textScale === s} onClick={() => set({ textScale: s })} aria-label={`${s * 100}%`}>{"A" + "+".repeat(i)}</button>)}
      </div>
      <button className="btn icon" onClick={() => set({ theme: next })} aria-label={t("top.theme")}>{theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}</button>
      <button className="btn icon" onClick={() => setLedgerOpen(true)} aria-label={`${t("top.ledger")} (${ledger.length})`}><Lock size={20} /></button>
    </header>
  );
}

export const TrustBar = () => {
  const { t } = useT();
  return <div className="trustbar"><Lock size={16} aria-hidden="true" /> {t("trust.line")} <IndependentChip /></div>;
};

export const CallButton = () => {
  const { t } = useT();
  return <a className="call" href="tel:1930"><Phone size={20} aria-hidden="true" /> {t("call.cta")}</a>;
};

export function Footer() {
  const { t, lang } = useT();
  return (
    <footer>
      <nav className="row" style={{ justifyContent: "center", marginBottom: 8 }}>
        {(["about", "privacy", "settings"] as const).map((p) => <NavLink key={p} to={`/${p}`}>{t(`nav.${p}`)}</NavLink>)}
        <Link to="/report">{t("footer.report")}</Link>
      </nav>
      <p>{t("footer.disclaimer")}</p>
      <p>{t("footer.sources")}</p>
      {lang !== "en" && <p>{t("footer.review")}</p>}
    </footer>
  );
}
