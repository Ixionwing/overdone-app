"use client";

import { useEffect, useState } from "react";

import { getBaseline, putBaseline, putBaselineText } from "@/lib/api";
import type { BaselineStatus } from "@/lib/types";

export function BaselinePanel() {
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<BaselineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void getBaseline()
      .then((loaded) => {
        if (cancelled) {
          return;
        }
        setStatus(loaded);
        setDraft(JSON.stringify(loaded.baseline, null, 2));
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load baseline",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const trimmed = draft.trim();
      const saved = trimmed.startsWith("{")
        ? await putBaseline(JSON.parse(trimmed) as never)
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
