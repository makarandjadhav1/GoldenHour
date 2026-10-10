export type Mood = "idle" | "welcome" | "listening" | "concerned" | "reassure" | "thinking" | "nod" | "alert" | "relief";
export type Hand = "rest" | "wave" | "chest" | "palm" | "point" | "chin";
export type Mouth = "smile" | "warm" | "neutral" | "small" | "down" | "pursed" | "flat" | "open" | "open2";

export interface MoodParams {
  browY: number;      // px, negative = raised
  browTilt: number;   // deg, inner ends raised when positive
  eyes: number;       // vertical scale of the eyes
  gaze: [number, number];
  mouth: Mouth;
  tilt: number;       // head tilt in degrees
  hand: Hand;
  nod?: boolean;
}

// DRD §4.6
export const MOODS: Record<Mood, MoodParams> = {
  idle: { browY: 0, browTilt: 0, eyes: 1, gaze: [0, 0], mouth: "smile", tilt: 0, hand: "rest" },
  welcome: { browY: -2, browTilt: 0, eyes: 1, gaze: [0, 0], mouth: "warm", tilt: 3, hand: "wave" },
  listening: { browY: -3, browTilt: 4, eyes: 1, gaze: [-3, 3], mouth: "neutral", tilt: 4, hand: "rest" },
  concerned: { browY: -4, browTilt: 8, eyes: 1.12, gaze: [0, 0], mouth: "down", tilt: 3, hand: "chest" },
  reassure: { browY: -2, browTilt: 3, eyes: 0.92, gaze: [0, 0], mouth: "warm", tilt: 0, hand: "palm" },
  thinking: { browY: -3, browTilt: 2, eyes: 1, gaze: [4, -4], mouth: "pursed", tilt: 6, hand: "chin" },
  nod: { browY: 0, browTilt: 0, eyes: 1, gaze: [0, 0], mouth: "smile", tilt: 0, hand: "rest", nod: true },
  alert: { browY: -5, browTilt: 0, eyes: 1.18, gaze: [0, 0], mouth: "flat", tilt: 0, hand: "point" },
  relief: { browY: -1, browTilt: 0, eyes: 0.9, gaze: [0, 0], mouth: "small", tilt: 0, hand: "rest" },
};

export const MOUTHS: Record<Mouth, string> = {
  smile: "M176 290 Q200 306 224 290",
  warm: "M172 288 Q200 312 228 288",
  neutral: "M180 296 Q200 300 220 296",
  small: "M184 294 Q200 303 216 294",
  down: "M182 300 Q200 291 218 300",
  pursed: "M188 297 Q200 292 212 297",
  flat: "M180 297 L220 297",
  open: "M180 290 Q200 318 220 290 Q200 296 180 290Z",
  open2: "M184 292 Q200 306 216 292 Q200 296 184 292Z",
};

export const MOOD_LIST = Object.keys(MOODS) as Mood[];
