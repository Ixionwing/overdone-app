"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { evaluatePrompt } from "@/lib/api";
import { requirePrompt } from "@/lib/prompt";
import {
  alert,
  button,
  col,
  displayHeading,
  field,
  label,
  promptArea,
  textarea,
} from "@/theme/layout";
import type { EvaluationResult } from "@/lib/types";

type PromptPanelProps = {
  onResult: (result: EvaluationResult | null) => void;
};

export function PromptPanel({ onResult }: PromptPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const errorRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (error) {
      errorRef.current?.focus();
    }
  }, [error]);

  async function evaluate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    let trimmed: string;
    try {
      trimmed = requirePrompt(prompt);
    } catch (err) {
      onResult(null);
      setError(
        err instanceof Error
          ? err.message
          : "Enter a proposed increment, then try Evaluate Increment again.",
      );
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await evaluatePrompt(trimmed);
      onResult(result);
    } catch (err) {
      onResult(null);
      setError(
        err instanceof Error
          ? `${err.message} Then try Evaluate Increment again.`
          : "Evaluate failed. Then try Evaluate Increment again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className={col} aria-label="Proposed Change" onSubmit={evaluate}>
      <h2 className={displayHeading}>Proposed Change</h2>
      <div className={field}>
        <label className={label} htmlFor="prompt-draft">
          One-Shot Prompt
        </label>
        <textarea
          className={`${textarea} ${promptArea}`}
          id="prompt-draft"
          name="prompt-draft"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={4}
          autoComplete="off"
          placeholder="I want to add 20 lb to my bench press tomorrow…"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "prompt-error" : undefined}
        />
      </div>
      <div>
        <button className={button} type="submit" disabled={busy}>
          {busy ? "Evaluating…" : "Evaluate Increment"}
        </button>
      </div>
      {error ? (
        <p
          ref={errorRef}
          className={alert}
          id="prompt-error"
          role="alert"
          tabIndex={-1}
        >
          {error}
        </p>
      ) : null}
    </form>
  );
}
