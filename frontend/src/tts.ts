import { LANG_TAG, type Lang } from "./i18n";

export const ttsSupported = () => typeof window !== "undefined" && "speechSynthesis" in window;

/** Speak with the browser's own voices. Returns false if no voice exists for the language. */
export function speak(text: string, lang: Lang): boolean {
  if (!ttsSupported()) return false;
  const tag = LANG_TAG[lang];
  const voice = speechSynthesis.getVoices().find((v) => v.lang.replace("_", "-").toLowerCase().startsWith(tag.slice(0, 2)));
  if (!voice && lang !== "en") return false;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = tag;
  if (voice) u.voice = voice;
  speechSynthesis.speak(u);
  return true;
}

export const stopSpeaking = () => ttsSupported() && speechSynthesis.cancel();
