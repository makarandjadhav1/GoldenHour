import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { Footer, TopBar, TrustBar } from "./components/Chrome";
import { Ledger } from "./components/Ledger";
import { useT } from "./i18n/useT";
import { LANG_TAG } from "./i18n";
import Ask from "./routes/Ask";
import Check from "./routes/Check";
import Design from "./routes/Design";
import Info from "./routes/Info";
import Lost from "./routes/Lost";
import Welcome from "./routes/Welcome";
import { useStore } from "./store";

export default function App() {
  const { t, lang } = useT();
  const { theme, contrast, motion, textScale, react } = useStore();
  const { pathname } = useLocation();

  useEffect(() => {
    const r = document.documentElement;
    r.lang = LANG_TAG[lang];
    r.dataset.contrast = contrast;
    r.dataset.motion = motion === "system" ? "" : motion;
    if (theme === "system") delete r.dataset.theme;
    else r.dataset.theme = theme;
    r.style.setProperty("--text-scale", String(textScale));
  }, [lang, theme, contrast, motion, textScale]);

  // move focus to the new page heading on navigation (a11y)
  useEffect(() => { const h = document.querySelector<HTMLElement>("main h1"); h?.setAttribute("tabindex", "-1"); h?.focus({ preventScroll: false }); }, [pathname]);

  // one gentle nudge after 60 s without interaction
  useEffect(() => {
    let done = false;
    let id = setTimeout(nudge, 60000);
    function nudge() { if (!done) { done = true; react("idle"); } }
    const reset = () => { clearTimeout(id); if (!done) id = setTimeout(nudge, 60000); };
    const evs = ["pointerdown", "keydown"] as const;
    evs.forEach((e) => addEventListener(e, reset));
    return () => { clearTimeout(id); evs.forEach((e) => removeEventListener(e, reset)); };
  }, [react]);

  return (
    <div className="app">
      <a className="skip" href="#main">{t("top.skip")}</a>
      <TopBar />
      <TrustBar />
      <main id="main">
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/check" element={<Check />} />
          <Route path="/lost" element={<Lost />} />
          <Route path="/lost/:step" element={<Lost />} />
          <Route path="/ask" element={<Ask />} />
          <Route path="/design" element={<Design />} />
          <Route path="/:page" element={<Info />} />
        </Routes>
      </main>
      <Footer />
      <Ledger />
    </div>
  );
}
