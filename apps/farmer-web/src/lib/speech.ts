import { apiPost, apiUpload } from "@/lib/api";
import { SPEECH_LOCALE } from "@/lib/i18n";
import type { Lang } from "@/lib/types";

type TtsResponse = { audio_base64: string | null; mime_type?: string; mode: "live" | "demo"; use_browser_tts?: boolean };

/** Speak text: Cloud Text-to-Speech when configured, otherwise the browser's speechSynthesis (demo). */
export async function speak(text: string, lang: Lang): Promise<"cloud" | "browser" | "unavailable"> {
  try {
    const res = await apiPost<TtsResponse>("/api/text-to-speech", { text, language: lang });
    if (res.audio_base64) {
      await new Audio(`data:${res.mime_type ?? "audio/mpeg"};base64,${res.audio_base64}`).play();
      return "cloud";
    }
  } catch {
    /* fall through to the browser voice */
  }
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = SPEECH_LOCALE[lang];
    const voice = window.speechSynthesis.getVoices().find((v) => v.lang.startsWith(SPEECH_LOCALE[lang].slice(0, 2)));
    if (voice) u.voice = voice;
    window.speechSynthesis.speak(u);
    return "browser";
  }
  return "unavailable";
}

type SttResponse = { transcript: string | null; mode: "live" | "demo"; use_browser_speech?: boolean };

export async function transcribeWithCloud(blob: Blob, lang: Lang): Promise<SttResponse> {
  const form = new FormData();
  form.append("audio", blob, "question.webm");
  form.append("language", lang);
  return apiUpload<SttResponse>("/api/speech-to-text", form);
}

// Minimal typing for the (prefixed) Web Speech recognition API.
export type Recognition = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
};

export function browserRecognition(): Recognition | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}
