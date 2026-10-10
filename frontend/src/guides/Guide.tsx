import { useEffect, useState, type CSSProperties } from "react";
import { useStore } from "../store";
import { MOODS, MOUTHS, type Hand, type Mood } from "./moods";

export type Who = "asha" | "kabir";
interface Props { who: Who; mood: Mood; speaking?: boolean; lookAt?: "input" | "none"; className?: string }

const LOOK: Record<Who, { name: string; skin: string; shade: string; hair: string; top: string; sleeve: string }> = {
  asha: { name: "Asha", skin: "#B9794D", shade: "#A5683F", hair: "#2A1B17", top: "#0E6E7E", sleeve: "#0E6E7E" },
  kabir: { name: "Kabir", skin: "#8E5A3A", shade: "#7B4A2E", hair: "#1F1A17", top: "#C98F2B", sleeve: "#3A3F45" },
};

// Arm pivots at the elbow (332,500). Each pose is a transform on the arm group (DRD 4.6 "Hand" column).
const ARM: Record<Hand, string> = {
  rest: "translate(46px, 96px) rotate(32deg)",
  wave: "translate(0px, -34px) rotate(0deg)",
  chest: "translate(-4px, -8px) rotate(-54deg)",
  palm: "translate(10px, -48px) rotate(8deg)",
  point: "translate(-8px, -58px) rotate(-22deg)",
  chin: "translate(-26px, -124px) rotate(-38deg)",
};

export function useReducedMotion(): boolean {
  const pref = useStore((s) => s.motion);
  const [sys, setSys] = useState(() => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    if (typeof matchMedia !== "function") return;
    const m = matchMedia("(prefers-reduced-motion: reduce)");
    const f = () => setSys(m.matches);
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, []);
  return pref === "reduce" || (pref === "system" && sys);
}

export function Guide({ who, mood, speaking = false, lookAt = "none", className }: Props) {
  const L = LOOK[who];
  const reduced = useReducedMotion();
  const p = MOODS[mood];
  const [blink, setBlink] = useState(false);
  const [talk, setTalk] = useState(false);

  // blink every 4-6 s; paused while the tab is hidden or motion is reduced
  useEffect(() => {
    if (reduced) return;
    let t: ReturnType<typeof setTimeout>;
    const loop = () => {
      t = setTimeout(() => {
        if (!document.hidden) { setBlink(true); setTimeout(() => setBlink(false), 130); }
        loop();
      }, 4000 + Math.random() * 2000);
    };
    loop();
    return () => clearTimeout(t);
  }, [reduced]);

  useEffect(() => {
    if (!speaking || reduced) return setTalk(false);
    const i = setInterval(() => setTalk((v) => !v), 150);
    return () => clearInterval(i);
  }, [speaking, reduced]);

  const mouth = speaking && !reduced ? (talk ? "open" : "open2") : p.mouth;
  const gaze: [number, number] = lookAt === "input" ? [0, 5] : p.gaze;
  const tr = (css: CSSProperties) => ({ style: { transformBox: "fill-box" as const, transformOrigin: "center", ...css } });
  const eye = (cx: number) => (
    <g key={cx} {...tr({ transform: `scaleY(${p.eyes})` })} className="part">
      <ellipse cx={cx} cy={244} rx={14} ry={10} fill="#fff" />
      <circle cx={cx + gaze[0]} cy={244 + gaze[1] * 0.6} r={6.5} fill="#2B1D14" className="part" />
      <circle cx={cx + gaze[0] + 2} cy={242 + gaze[1] * 0.6} r={2} fill="#fff" />
      <ellipse cx={cx} cy={244} rx={15.5} ry={11.5} fill={L.skin} style={{ transformBox: "fill-box", transformOrigin: "top", transform: `scaleY(${blink ? 1 : 0})`, transition: "transform 80ms" }} />
    </g>
  );

  return (
    <svg viewBox="0 0 400 500" role="img" aria-label={`${L.name}, virtual guide`} className={`guide-svg ${className ?? ""}`}>
      <g id="halo" aria-hidden="true" className={reduced ? "" : "halo-shimmer"}>
        <circle cx="200" cy="235" r="188" fill="var(--sun-soft)" />
      </g>
      <g id="body" aria-hidden="true" className={reduced ? "" : "breathe"}>
        <g id="torso">
          <g id="clothing">
            <path d="M30 500 C30 430 90 392 150 380 L250 380 C310 392 370 430 370 500Z" fill={who === "asha" ? L.top : L.top} />
            {who === "asha" ? (
              <path d="M112 392 C150 440 250 440 288 392 L300 412 C250 462 150 462 100 412Z" fill="var(--sun-soft)" stroke="#F3D79B" strokeWidth="2" />
            ) : (
              <>
                <path d="M30 500 C30 430 90 392 150 380 L184 380 L178 500Z" fill={L.sleeve} />
                <path d="M370 500 C370 430 310 392 250 380 L216 380 L222 500Z" fill={L.sleeve} />
                <path d="M172 380 L200 416 L228 380 L214 376 L200 394 L186 376Z" fill="#E9B04C" />
              </>
            )}
          </g>
          <g id="neck"><path d="M176 316 L176 392 Q200 414 224 392 L224 316Z" fill={L.shade} /></g>
        </g>
        <g id="arm-right" className="part" style={{ transformOrigin: "332px 500px", transform: ARM[p.hand] }}>
          <g className={p.hand === "wave" && !reduced ? "hand-wave" : ""} id="hand-right">
            <line x1="332" y1="760" x2="332" y2="410" stroke={who === "asha" ? L.top : L.sleeve} strokeWidth="46" strokeLinecap="round" />
            <ellipse cx="332" cy="388" rx="22" ry="26" fill={L.skin} />
            <ellipse cx="309" cy="398" rx="9" ry="16" fill={L.skin} transform="rotate(-28 309 398)" />
            {(p.hand === "wave" || p.hand === "palm") && [317, 327, 337, 347].map((x) => <rect key={x} x={x - 5} y="358" width="10" height="26" rx="5" fill={L.skin} />)}
            {p.hand === "point" && <rect x="326" y="338" width="12" height="46" rx="6" fill={L.skin} />}
          </g>
        </g>
      </g>
      <g id="head" aria-hidden="true" className={`part ${p.nod && !reduced ? "nod" : ""}`} style={{ transformOrigin: "200px 336px", transform: `rotate(${p.tilt}deg)` }}>
        <g id="hair-back">
          {who === "asha" && <path d="M116 232 C98 120 302 120 284 232 C304 300 298 384 270 416 C254 394 252 340 258 300 L142 300 C148 340 146 394 130 416 C102 384 96 300 116 232Z" fill={L.hair} />}
        </g>
        <g id="ears">
          <circle cx="124" cy="250" r="15" fill={L.skin} /><circle cx="276" cy="250" r="15" fill={L.skin} />
          {who === "asha" && <><circle cx="124" cy="262" r="3.5" fill="#E8B64D" /><circle cx="276" cy="262" r="3.5" fill="#E8B64D" /></>}
        </g>
        <g id="face">
          <ellipse cx="200" cy="238" rx="78" ry="92" fill={L.skin} />
          <ellipse cx="150" cy="278" rx="16" ry="9" fill="#D9604C" opacity="0.16" /><ellipse cx="250" cy="278" rx="16" ry="9" fill="#D9604C" opacity="0.16" />
          {who === "kabir" && <path d="M128 262 C132 312 170 326 200 326 C230 326 268 312 272 262 C260 294 238 308 200 308 C162 308 140 294 128 262Z" fill={L.hair} opacity="0.3" />}
        </g>
        <g id="nose"><path d="M200 258 Q193 274 203 278" stroke={L.shade} strokeWidth="3.5" fill="none" strokeLinecap="round" /></g>
        <g id="eyes">{eye(168)}{eye(232)}</g>
        <g id="brows">
          <path id="brow-left" d="M146 220 Q166 210 188 220" stroke={L.hair} strokeWidth="6" strokeLinecap="round" fill="none" className="part" {...tr({ transform: `translateY(${p.browY}px) rotate(${-p.browTilt}deg)` })} />
          <path id="brow-right" d="M212 220 Q234 210 254 220" stroke={L.hair} strokeWidth="6" strokeLinecap="round" fill="none" className="part" {...tr({ transform: `translateY(${p.browY}px) rotate(${p.browTilt}deg)` })} />
        </g>
        <path id="mouth" d={MOUTHS[mouth]} stroke="#7A3B2E" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill={mouth.startsWith("open") ? "#7A3B2E" : "none"} />
        {who === "kabir" && (
          <g id="glasses" fill="none" stroke="#26282B" strokeWidth="4">
            <circle cx="168" cy="244" r="27" /><circle cx="232" cy="244" r="27" /><path d="M195 242 Q200 238 205 242" /><path d="M141 242 L124 238" /><path d="M259 242 L276 238" />
          </g>
        )}
        <g id="hair-front">
          {who === "asha" ? (
            <path d="M118 236 C108 140 200 98 264 134 C296 154 294 206 284 238 C272 200 242 178 206 176 C170 176 134 196 118 236Z" fill={L.hair} />
          ) : (
            <path d="M120 230 C114 128 286 128 280 230 C270 192 242 170 200 170 C158 170 130 192 120 230Z" fill={L.hair} />
          )}
        </g>
      </g>
    </svg>
  );
}
