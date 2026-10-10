import { useState } from "react";
import { Guide } from "../guides/Guide";
import { MOOD_LIST } from "../guides/moods";
import { CopyBlock, FieldCard, ModeCard, ScriptBlock, SunClock, VerdictBanner } from "../components/Parts";
import { useT } from "../i18n/useT";
import type { Elapsed } from "../store";

const demo = { score: 91, verdict: "scam" as const, scamType: "kyc", scamTypeName: "Fake KYC / account-block scam", critical: true, hits: [], urls: [], advice: [], redactedText: "", maskedCount: 0, truncated: false };

/** Our "Storybook": every guide mood and component state, on one page. */
export default function Design() {
  const { t } = useT();
  const [speaking, setSpeaking] = useState(false);
  return (
    <div className="page-in" style={{ display: "grid", gap: 24 }}>
      <h1>Design</h1>
      <label className="row"><input type="checkbox" checked={speaking} onChange={(e) => setSpeaking(e.target.checked)} /> speaking</label>
      {(["asha", "kabir"] as const).map((who) => (
        <section key={who}>
          <h2>{who}</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(180px,1fr))", gap: 12 }}>
            {MOOD_LIST.map((m) => <figure key={m} style={{ margin: 0, textAlign: "center" }} data-mood={m}><Guide who={who} mood={m} speaking={speaking} /><figcaption>{t(`mood.${m}`)}</figcaption></figure>)}
          </div>
        </section>
      ))}
      <section><h2>Sun-Clock</h2><div className="row">{(["lt15", "m30", "h1to2", "sameDay", "earlier"] as Elapsed[]).map((b) => <SunClock key={b} bucket={b} />)}</div></section>
      <section>
        <h2>Verdicts</h2>
        {(["scam", "suspicious", "low"] as const).map((v) => <div key={v} style={{ marginBottom: 8 }}><VerdictBanner d={{ ...demo, verdict: v, score: v === "scam" ? 91 : v === "suspicious" ? 45 : 8 }} /></div>)}
      </section>
      <section>
        <h2>Field card</h2>
        <FieldCard k="utrs" value={["524587920123"]} meta={{ tier: 1, warn: null, auto: true }} onChange={() => undefined} />
        <FieldCard k="mobile" value="123" meta={{ tier: 1, warn: "A mobile number has 10 digits.", auto: false }} onChange={() => undefined} />
        <FieldCard k="name" value="" meta={{ tier: 2, warn: null, auto: false }} onChange={() => undefined} />
      </section>
      <section><h2>Modes</h2><div className="modes"><ModeCard mode="A" selected /><ModeCard mode="B" /><ModeCard mode="C" disabled /></div></section>
      <section><h2>Copy</h2><CopyBlock text={"Sample text\nsecond line"} /><ScriptBlock lines={["Say: I want to report a fraud.", "Amount lost: ₹49,999"]} /></section>
    </div>
  );
}
