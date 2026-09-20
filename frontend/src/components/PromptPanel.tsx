"use client";

import { useState } from "react";

import { VerdictPanel } from "@/components/VerdictPanel";
import { evaluatePrompt } from "@/lib/api";
import type { EvaluationResult } from "@/lib/types";

export function PromptPanel() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function evaluate() {
    setBusy(true);
    setError(null);
    try {
      setResult(await evaluatePrompt(prompt));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Evaluate failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Prompt">
      <h2>Proposed change</h2>
      <label htmlFor="prompt-draft">One-shot prompt</label>
      <textarea
        id="prompt-draft"
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        rows={4}
        placeholder="I want to add 20 lbs to my bench press tomorrow"
      />
      <div className="actions">
        <button type="button" onClick={() => void evaluate()} disabled={busy}>
          {busy ? "Evaluating…" : "Evaluate"}
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      {result ? <VerdictPanel result={result} /> : null}
    </section>
  );
}
