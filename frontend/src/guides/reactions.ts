import type { Mood } from "./moods";

export type GuideEvent =
  | "load" | "typing" | "utrValid" | "amountFound" | "missingUtr" | "verdictScam" | "verdictSuspicious" | "verdictLow"
  | "idle" | "secretTyped" | "packReady" | "lostMoney" | "analysing" | "reviewReady" | "cantRead" | "modeStep" | "afterStep";

export interface Reaction { mood: Mood; ms: number; line?: string; then?: Mood }

// DRD §4.8. A pure table: event -> mood, how long to hold it, an optional i18n key for the guide's line.
const TABLE: Record<GuideEvent, Reaction> = {
  load: { mood: "welcome", ms: 2400, line: "g.welcome", then: "idle" },
  typing: { mood: "listening", ms: 1800 },
  analysing: { mood: "thinking", ms: 600 },
  utrValid: { mood: "nod", ms: 900, line: "g.field.utrOk", then: "idle" },
  amountFound: { mood: "idle", ms: 800, line: "g.field.amount" },
  missingUtr: { mood: "reassure", ms: 2600, line: "g.field.missingUtr", then: "idle" },
  verdictScam: { mood: "alert", ms: 1000, line: "g.check.scam", then: "reassure" },
  verdictSuspicious: { mood: "alert", ms: 800, line: "g.check.suspicious", then: "reassure" },
  verdictLow: { mood: "relief", ms: 2400, line: "g.check.low", then: "idle" },
  idle: { mood: "idle", ms: 0, line: "g.idle" },
  secretTyped: { mood: "concerned", ms: 3000, line: "g.secret", then: "idle" },
  lostMoney: { mood: "concerned", ms: 2400, line: "g.lost.concerned", then: "reassure" },
  reviewReady: { mood: "reassure", ms: 2000, line: "g.lost.review", then: "idle" },
  cantRead: { mood: "reassure", ms: 2600, line: "g.lost.cantRead", then: "idle" },
  modeStep: { mood: "reassure", ms: 2400, line: "g.mode", then: "idle" },
  packReady: { mood: "relief", ms: 1600, line: "g.pack", then: "reassure" },
  afterStep: { mood: "reassure", ms: 2400, line: "g.after", then: "idle" },
};

export const moodFor = (event: GuideEvent): Reaction => TABLE[event];
