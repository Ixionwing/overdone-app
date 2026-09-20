import type {
  BaselineBenchmark,
  BaselineImport,
  BaselineSession,
  BaselineSet,
} from "@/lib/types";

const ROOT_KEYS = new Set(["preferred_unit", "benchmarks", "sessions"]);
const SET_KEYS = new Set([
  "exercise",
  "weight",
  "reps",
  "sets",
  "unit",
  "exercise_id",
]);
const BENCH_KEYS = new Set(["exercise", "one_rm", "unit", "exercise_id"]);
const SESSION_KEYS = new Set(["date", "notes", "sets"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function rejectUnknown(
  value: Record<string, unknown>,
  allowed: Set<string>,
): void {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new Error(`Unexpected field: ${key}`);
    }
  }
}

function optionalUnit(value: unknown): string | null | undefined {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  if (value !== "lb" && value !== "kg") {
    throw new Error("unit must be lb or kg");
  }
  return value;
}

function optionalExerciseId(value: unknown): string | null | undefined {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value !== "string") {
    throw new Error("exercise_id must be a string");
  }
  return value;
}

function parseSet(value: unknown): BaselineSet {
  if (!isRecord(value)) {
    throw new Error("Each set must be an object");
  }
  rejectUnknown(value, SET_KEYS);
  if (typeof value.exercise !== "string" || !value.exercise.trim()) {
    throw new Error("Set exercise must be a non-empty string");
  }
  if (typeof value.weight !== "number" || !Number.isFinite(value.weight)) {
    throw new Error("Set weight must be a number");
  }
  if (typeof value.reps !== "number" || !Number.isInteger(value.reps)) {
    throw new Error("Set reps must be an integer");
  }
  const sets =
    value.sets === undefined
      ? 1
      : typeof value.sets === "number" && Number.isInteger(value.sets)
        ? value.sets
        : null;
  if (sets === null) {
    throw new Error("Set sets must be an integer");
  }
  return {
    exercise: value.exercise,
    weight: value.weight,
    reps: value.reps,
    sets,
    unit: optionalUnit(value.unit),
    exercise_id: optionalExerciseId(value.exercise_id),
  };
}

function parseBenchmark(value: unknown): BaselineBenchmark {
  if (!isRecord(value)) {
    throw new Error("Each benchmark must be an object");
  }
  rejectUnknown(value, BENCH_KEYS);
  if (typeof value.exercise !== "string" || !value.exercise.trim()) {
    throw new Error("Benchmark exercise must be a non-empty string");
  }
  if (typeof value.one_rm !== "number" || !Number.isFinite(value.one_rm)) {
    throw new Error("Benchmark one_rm must be a number");
  }
  return {
    exercise: value.exercise,
    one_rm: value.one_rm,
    unit: optionalUnit(value.unit),
    exercise_id: optionalExerciseId(value.exercise_id),
  };
}

function parseSession(value: unknown): BaselineSession {
  if (!isRecord(value)) {
    throw new Error("Each session must be an object");
  }
  rejectUnknown(value, SESSION_KEYS);
  if (
    typeof value.date !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value.date)
  ) {
    throw new Error("Session date must be YYYY-MM-DD");
  }
  if (
    value.notes !== undefined &&
    value.notes !== null &&
    typeof value.notes !== "string"
  ) {
    throw new Error("Session notes must be a string");
  }
  if (value.sets !== undefined && !Array.isArray(value.sets)) {
    throw new Error("Session sets must be an array");
  }
  return {
    date: value.date,
    notes:
      value.notes === undefined ? undefined : (value.notes as string | null),
    sets: (value.sets ?? []).map(parseSet),
  };
}

export function parseBaselineImport(value: unknown): BaselineImport {
  if (!isRecord(value)) {
    throw new Error("Baseline JSON must be an object");
  }
  rejectUnknown(value, ROOT_KEYS);
  const preferred =
    value.preferred_unit === undefined ? "lb" : value.preferred_unit;
  if (preferred !== "lb" && preferred !== "kg") {
    throw new Error("preferred_unit must be lb or kg");
  }
  if (value.benchmarks !== undefined && !Array.isArray(value.benchmarks)) {
    throw new Error("benchmarks must be an array");
  }
  if (value.sessions !== undefined && !Array.isArray(value.sessions)) {
    throw new Error("sessions must be an array");
  }
  return {
    preferred_unit: preferred,
    benchmarks: (value.benchmarks ?? []).map(parseBenchmark),
    sessions: (value.sessions ?? []).map(parseSession),
  };
}
