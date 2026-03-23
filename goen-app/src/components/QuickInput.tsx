"use client";

import { useState, useRef, useCallback } from "react";
import { extractPersonNames, extractTags, extractMood } from "@/lib/ai-extract";
import { addPerson, addEncounter, loadData } from "@/lib/storage";

interface QuickInputProps {
  onEncounterAdded: () => void;
}

export default function QuickInput({ onEncounterAdded }: QuickInputProps) {
  const [text, setText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const handleSubmit = useCallback(() => {
    if (!text.trim()) return;
    setIsProcessing(true);

    const input = text.trim();
    const names = extractPersonNames(input);
    const tags = extractTags(input);
    const mood = extractMood(input);

    // Ensure persons exist
    const data = loadData();
    const personIds: string[] = [];
    const personNames: string[] = [];

    for (const name of names) {
      const existing = data.persons.find(
        (p) => p.name.toLowerCase() === name.toLowerCase()
      );
      if (existing) {
        personIds.push(existing.id);
        personNames.push(existing.name);
      } else {
        const person = addPerson(name, tags);
        personIds.push(person.id);
        personNames.push(person.name);
      }
    }

    addEncounter({
      text: input,
      personIds,
      personNames,
      tags,
      mood,
      createdAt: new Date().toISOString(),
    });

    setText("");
    setIsProcessing(false);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 2000);
    onEncounterAdded();
  }, [text, onEncounterAdded]);

  const startVoiceInput = useCallback(async () => {
    // Try Web Speech API first (better for real-time transcription)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = window as any;
    const SpeechRecognitionCtor = win.webkitSpeechRecognition || win.SpeechRecognition;

    if (SpeechRecognitionCtor) {
      const recognition = new SpeechRecognitionCtor();
      recognition.lang = "ja-JP";
      recognition.interimResults = true;
      recognition.continuous = false;

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results as ArrayLike<{ 0: { transcript: string } }>)
          .map((r) => r[0].transcript)
          .join("");
        setText((prev) => prev + transcript);
      };

      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);

      recognition.start();
      setIsRecording(true);
      mediaRecorderRef.current = { stop: () => recognition.stop() } as unknown as MediaRecorder;
      return;
    }

    // Fallback: just toggle recording state (no transcription)
    setIsRecording(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        setIsRecording(false);
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
    } catch {
      setIsRecording(false);
    }
  }, []);

  const stopVoiceInput = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const detectedNames = text ? extractPersonNames(text) : [];
  const detectedTags = text ? extractTags(text) : [];

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="今日のご縁を記録... 例: 田中さんとランチ。AI事業の話で刺激を受けた"
          className="w-full bg-cosmos-surface border border-cosmos-dim/30 rounded-2xl px-5 py-4 pr-24 text-base placeholder:text-cosmos-dim/50 focus:outline-none focus:border-cosmos-accent/50 focus:glow resize-none transition-all duration-300"
          rows={2}
        />
        <div className="absolute right-3 bottom-3 flex gap-2">
          <button
            onClick={isRecording ? stopVoiceInput : startVoiceInput}
            className={`relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
              isRecording
                ? "bg-red-500/20 text-red-400 voice-pulse"
                : "bg-cosmos-surface hover:bg-cosmos-dim/30 text-cosmos-dim"
            }`}
            title="音声入力"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          </button>
          <button
            onClick={handleSubmit}
            disabled={!text.trim() || isProcessing}
            className="w-10 h-10 rounded-full bg-cosmos-accent/80 hover:bg-cosmos-accent text-white flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed"
            title="記録する"
          >
            {showSuccess ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" x2="12" y1="5" y2="19" />
                <line x1="5" x2="19" y1="12" y2="12" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Live extraction preview */}
      {text.trim() && (detectedNames.length > 0 || detectedTags.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-2 px-2 animate-[fadeIn_0.2s_ease]">
          {detectedNames.map((name) => (
            <span
              key={name}
              className="px-3 py-1 rounded-full bg-cosmos-accent/15 text-cosmos-glow text-sm border border-cosmos-accent/20"
            >
              {name}
            </span>
          ))}
          {detectedTags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1 rounded-full bg-cosmos-warm/15 text-cosmos-warm text-sm border border-cosmos-warm/20"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
