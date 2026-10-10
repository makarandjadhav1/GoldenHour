import { Link } from "react-router-dom";
import { useEffect } from "react";
import { Guide } from "../guides/Guide";
import { GuideStage } from "../components/GuideStage";
import { useT } from "../i18n/useT";
import { useStore } from "../store";

export default function Welcome() {
  const { t, guide } = useT();
  const { set, react, say } = useStore();
  useEffect(() => { react("load"); const id = setTimeout(() => say("g.rules"), 2800); return () => clearTimeout(id); }, [react, say]);
  return (
    <div className="hero page-in">
      <div className="duo" aria-label={t("welcome.who")}>
        <Guide who="asha" mood="welcome" />
        <Guide who="kabir" mood="idle" />
      </div>
      <h1>{t("welcome.title")}</h1>
      <p style={{ margin: "0 auto" }}>{t("welcome.notyourfault")}</p>
      <div className="choices">
        <Link to="/lost" className="choice main"><h2>{t("welcome.lost.t")}</h2><p>{t("welcome.lost.d")}</p></Link>
        <Link to="/check" className="choice"><h2>{t("welcome.check.t")}</h2><p>{t("welcome.check.d")}</p></Link>
        <Link to="/ask" className="choice"><h2>{t("welcome.ask.t")}</h2><p>{t("welcome.ask.d")}</p></Link>
      </div>
      <div className="row" style={{ justifyContent: "center", marginTop: 24 }}>
        <span id="who">{t("welcome.who")}</span>
        <div className="seg" role="group" aria-labelledby="who">
          {(["asha", "kabir"] as const).map((g) => <button key={g} aria-pressed={guide === g} onClick={() => { set({ guide: g }); say("g.pick"); }}>{g === "asha" ? "Asha" : "Kabir"}</button>)}
        </div>
      </div>
      <div style={{ maxWidth: 480, margin: "24px auto 0" }}><GuideStage compact /></div>
    </div>
  );
}
