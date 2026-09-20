"use client";

import { useState } from "react";

import { putBaseline, putBaselineText } from "@/lib/api";
import { parseBaselineImport } from "@/lib/baseline";
import type { BaselineStatus } from "@/lib/types";

type BaselinePanelProps = {
  initialStatus: BaselineStatus | null;
  initialError: string | null;
};

export function BaselinePanel({
  initialStatus,
  initialError,
}: BaselinePanelProps) {
  const [status, setStatus] = useState(initialStatus);
  const [error, setError] = useState(initialError);
  const [draft, setDraft] = useState(() =>
    initialStatus ? JSON.stringify(initialStatus.baseline, null, 2) : "",
  );
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const trimmed = draft.trim();
      const saved = trimmed.startsWith("{")
        ? await putBaseline(parseJsonBaseline(trimmed))
        : await putBaselineText(trimmed);
      setStatus(saved);
      setDraft(JSON.stringify(saved.baseline, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function onFile(file: File | undefined) {
    if (!file) {
      return;
    }
    setDraft(await file.text());
  }

  return (
    <section aria-label="Baseline">
      <h2>Baseline</h2>
      <p>
        Sessions: {status?.session_count ?? 0} · Benchmarks:{" "}
        {status?.benchmark_count ?? 0} · Sets: {status?.set_count ?? 0}
      </p>
      <label htmlFor="baseline-draft">Paste JSON or a text log</label>
      <textarea
        id="baseline-draft"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        rows={14}
        spellCheck={false}
      />
      <div className="actions">
        <input
          type="file"
          accept=".json,.txt,application/json,text/plain"
          onChange={(event) => void onFile(event.target.files?.[0])}
        />
        <button type="button" onClick={() => void save()} disabled={busy}>
          {busy ? "Saving…" : "Save baseline"}
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
    </section>
  );
}

function parseJsonBaseline(text: string) {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text) as unknown;
  } catch {
    throw new Error("Invalid JSON");
  }
  return parseBaselineImport(parsed);
}
