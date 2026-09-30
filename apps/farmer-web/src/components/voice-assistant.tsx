"use client";

import { useRef, useState } from "react";
import { Loader2, Mic, MicOff, Send, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { AiBadge } from "@/components/mode-badge";
import { apiPost } from "@/lib/api";
import { EXAMPLE_QUESTIONS, SPEECH_LOCALE, useI18n } from "@/lib/i18n";
import { browserRecognition, speak, transcribeWithCloud, type Recognition } from "@/lib/speech";
import type { AskAnswer } from "@/lib/types";

/** Voice loop (PRD §18): speech -> text -> farm-context answer -> speech. Cloud STT/TTS when configured, browser otherwise. */
export function VoiceAssistant({ fieldId, useSample, cloudSpeech }: { fieldId: string; useSample: boolean; cloudSpeech: boolean }) {
  const { t, lang } = useI18n();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskAnswer | null>(null);
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [engine, setEngine] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);

  async function ask(q: string) {
    if (!q.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const a = await apiPost<AskAnswer>("/api/ask", { field_id: fieldId, question: q, language: lang, use_sample: useSample });
      setAnswer(a);
      const mode = await speak(a.answer, lang);
      setEngine((e) => `${e ? `${e} → ` : ""}${mode === "cloud" ? "Cloud TTS" : mode === "browser" ? "browser voice (demo)" : "no voice"}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function startCloud() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const rec = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach((tr) => tr.stop());
      setListening(false);
      const res = await transcribeWithCloud(new Blob(chunks, { type: "audio/webm" }), lang);
      if (res.transcript) {
        setQuestion(res.transcript);
        setEngine("Cloud Speech-to-Text");
        await ask(res.transcript);
      } else {
        setError("No speech recognised - please try again.");
      }
    };
    mediaRef.current = rec;
    rec.start();
    setListening(true);
  }

  function startBrowser() {
    const rec = browserRecognition();
    if (!rec) {
      setError("Speech recognition is not available in this browser - type the question instead.");
      return;
    }
    rec.lang = SPEECH_LOCALE[lang];
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const text = e.results[0]?.[0]?.transcript ?? "";
      setQuestion(text);
      setEngine("Browser speech recognition (demo)");
      void ask(text);
    };
    rec.onerror = (e) => setError(`Speech error: ${e.error}`);
    rec.onend = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  }

  function toggleMic() {
    setError(null);
    setEngine(null);
    if (listening) {
      recRef.current?.stop();
      mediaRef.current?.stop();
      return;
    }
    if (cloudSpeech && typeof MediaRecorder !== "undefined") {
      startCloud().catch((e: Error) => setError(e.message));
    } else {
      startBrowser();
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          {t("step_voice")}
          {answer ? <AiBadge mode={answer.ai.mode} model={answer.ai.model_name} /> : null}
        </CardTitle>
        <CardDescription>
          {cloudSpeech ? "Google Cloud Speech-to-Text / Text-to-Speech" : "Demo mode: browser speech recognition and voice (set GOOGLE_CLOUD_API_KEY for Cloud Speech)"}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Button variant={listening ? "destructive" : "default"} onClick={toggleMic} aria-label={listening ? t("stop") : t("speak")}>
            {listening ? <MicOff /> : <Mic />} {listening ? t("stop") : t("speak")}
          </Button>
          <Textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={t("ask_placeholder")} rows={2} />
          <Button variant="outline" onClick={() => ask(question)} disabled={busy || !question.trim()} aria-label={t("ask")}>
            {busy ? <Loader2 className="animate-spin" /> : <Send />}
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="text-muted-foreground">{t("example_questions")}:</span>
          {EXAMPLE_QUESTIONS[lang].map((q) => (
            <button key={q} className="rounded-full border px-2 py-0.5 hover:bg-muted" onClick={() => { setQuestion(q); void ask(q); }}>
              {q}
            </button>
          ))}
        </div>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {answer ? (
          <div className="rounded-lg bg-muted/50 p-3 text-sm">
            <p className="text-base">{answer.answer}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Grounded on: {answer.grounded_on.join(", ")} · {answer.follow_up_suggestion}
              {answer.requires_expert_review ? " · please confirm with the agriculture officer" : ""}
            </p>
            <Button size="sm" variant="ghost" className="mt-1" onClick={() => speak(answer.answer, lang)}>
              <Volume2 /> {t("listen")}
            </Button>
          </div>
        ) : null}
        {engine ? <p className="text-xs text-muted-foreground">Voice path: {engine}</p> : null}
      </CardContent>
    </Card>
  );
}
