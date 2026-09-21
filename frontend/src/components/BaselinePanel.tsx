"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { putBaseline, putBaselineText } from "@/lib/api";
import { hasStoredBaseline, parseBaselineImport } from "@/lib/baseline";
import {
  alert,
  button,
  buttonQuiet,
  col,
  displayHeading,
  field,
  label,
  mute,
  row,
  textarea,
  warning,
} from "@/theme/layout";
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
  const [savedDraft, setSavedDraft] = useState(() =>
    initialStatus ? JSON.stringify(initialStatus.baseline, null, 2) : "",
  );
  const [draft, setDraft] = useState(savedDraft);
  const [busy, setBusy] = useState(false);
  const [pendingSave, setPendingSave] = useState(false);
  const [pendingFileText, setPendingFileText] = useState<string | null>(null);
  const dirty = draft !== savedDraft;
  const fileRef = useRef<HTMLInputElement>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (!dirty) {
      return;
    }
    function onLeave(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", onLeave);
    return () => window.removeEventListener("beforeunload", onLeave);
  }, [dirty]);

  useEffect(() => {
    if (error) {
      errorRef.current?.focus();
    }
  }, [error]);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const trimmed = draft.trim();
      const saved = trimmed.startsWith("{")
        ? await putBaseline(parseJsonBaseline(trimmed))
        : await putBaselineText(trimmed);
      setStatus(saved);
      const next = JSON.stringify(saved.baseline, null, 2);
      setSavedDraft(next);
      setDraft(next);
      setPendingSave(false);
    } catch (err) {
      setPendingSave(false);
      setError(
        err instanceof Error
          ? nextStep(err.message)
          : "Save failed. Check that the API is reachable, then save again.",
      );
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pendingFileText !== null) {
      return;
    }
    if (hasStoredBaseline(status) && !pendingSave) {
      setPendingSave(true);
      return;
    }
    void save();
  }

  async function onFile(file: File | undefined) {
    if (!file) {
      return;
    }
    const text = await file.text();
    if (dirty) {
      setPendingFileText(text);
      setPendingSave(false);
      return;
    }
    setDraft(text);
  }

  return (
    <form className={col} aria-label="Baseline" onSubmit={onSubmit}>
      <h2 className={displayHeading}>Baseline</h2>
      <p className={`${mute} tabular`}>
        {status?.session_count ?? 0} sessions, {status?.benchmark_count ?? 0}{" "}
        benchmarks, {status?.set_count ?? 0} sets
      </p>
      <div className={field}>
        <label className={label} htmlFor="baseline-draft">
          Paste JSON or a Text Log
        </label>
        <textarea
          className={textarea}
          id="baseline-draft"
          name="baseline-draft"
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
            setPendingSave(false);
          }}
          rows={10}
          spellCheck={false}
          autoComplete="off"
          placeholder={"2024-09-21\nBench Press 3x5 @ 185 lb…"}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "baseline-error" : undefined}
        />
      </div>
      {pendingFileText !== null ? (
        <>
          <p className={warning} role="status">
            Replace the unsaved draft? The loaded file replaces the text in the
            box.
          </p>
          <div className={row}>
            <button
              className={button}
              type="button"
              onClick={() => {
                setDraft(pendingFileText);
                setPendingFileText(null);
              }}
            >
              Replace Draft
            </button>
            <button
              className={`${button} ${buttonQuiet}`}
              type="button"
              onClick={() => setPendingFileText(null)}
            >
              Keep Draft
            </button>
          </div>
        </>
      ) : pendingSave ? (
        <>
          <p className={warning} role="status">
            Replace the saved baseline? This cannot be undone.
          </p>
          <div className={row}>
            <button className={button} type="submit" disabled={busy}>
              {busy ? "Saving…" : "Replace Baseline"}
            </button>
            <button
              className={`${button} ${buttonQuiet}`}
              type="button"
              onClick={() => setPendingSave(false)}
            >
              Keep Current
            </button>
          </div>
        </>
      ) : (
        <div className={row}>
          <button
            className={`${button} ${buttonQuiet}`}
            type="button"
            onClick={() => fileRef.current?.click()}
          >
            Load Log File
          </button>
          <input
            ref={fileRef}
            className="visually-hidden"
            tabIndex={-1}
            aria-hidden="true"
            type="file"
            name="baseline-file"
            accept=".json,.txt,application/json,text/plain"
            onChange={(event) => {
              void onFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
          <button className={button} type="submit" disabled={busy}>
            {busy ? "Saving…" : "Save Baseline"}
          </button>
        </div>
      )}
      {error ? (
        <p
          ref={errorRef}
          className={alert}
          id="baseline-error"
          role="alert"
          tabIndex={-1}
        >
          {error}
        </p>
      ) : null}
    </form>
  );
}

function nextStep(message: string): string {
  if (message === "Invalid JSON") {
    return "Invalid JSON. Paste valid JSON or a text log, then save again.";
  }
  return `${message} Check that the API is reachable, then save again.`;
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
