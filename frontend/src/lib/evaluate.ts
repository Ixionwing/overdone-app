import type {
  EvaluationResult,
  FactorScores,
  Halt,
  ItemVerdict,
  TrafficLight,
  WarningFlag,
} from "@/lib/types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function optionalString(value: unknown): string | null {
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    throw new Error("Expected a string or null");
  }
  return value;
}

function parseLight(value: unknown): TrafficLight | null {
  if (value === undefined || value === null) {
    return null;
  }
  if (value !== "green" && value !== "yellow" && value !== "red") {
    throw new Error("overall_light must be green, yellow, or red");
  }
  return value;
}

function parseFactors(value: unknown): FactorScores {
  if (!isRecord(value)) {
    throw new Error("Factor scores must be an object");
  }
  if (
    typeof value.volume_jump_pct !== "number" ||
    typeof value.axial_compression !== "number" ||
    typeof value.cns_index !== "number"
  ) {
    throw new Error("Factor scores must be numbers");
  }
  if (!isRecord(value.joint_vectors)) {
    throw new Error("joint_vectors must be an object");
  }
  const joint_vectors: Record<string, number> = {};
  for (const [name, amount] of Object.entries(value.joint_vectors)) {
    if (typeof amount !== "number" || !Number.isFinite(amount)) {
      throw new Error("Joint vectors must be numbers");
    }
    joint_vectors[name] = amount;
  }
  return {
    volume_jump_pct: value.volume_jump_pct,
    axial_compression: value.axial_compression,
    cns_index: value.cns_index,
    joint_vectors,
  };
}

function parseHalt(value: unknown): Halt | null {
  if (value === undefined || value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw new Error("halted must be an object");
  }
  if (typeof value.reason !== "string" || typeof value.message !== "string") {
    throw new Error("halted needs reason and message");
  }
  return {
    reason: value.reason,
    message: value.message,
    exercise_name: optionalString(value.exercise_name),
  };
}

function parseItem(value: unknown): ItemVerdict {
  if (!isRecord(value)) {
    throw new Error("Each item must be an object");
  }
  const light = parseLight(value.light);
  if (!light) {
    throw new Error("Item light is required");
  }
  if (
    typeof value.exercise_id !== "string" ||
    typeof value.exercise_name !== "string" ||
    typeof value.narrative !== "string"
  ) {
    throw new Error("Item identity fields must be strings");
  }
  return {
    exercise_id: value.exercise_id,
    exercise_name: value.exercise_name,
    light,
    factors: parseFactors(value.factors),
    narrative: value.narrative,
    catalog_source_id: optionalString(value.catalog_source_id),
  };
}

function parseWarning(value: unknown): WarningFlag {
  if (!isRecord(value)) {
    throw new Error("Each warning must be an object");
  }
  if (typeof value.kind !== "string" || typeof value.message !== "string") {
    throw new Error("Warning needs kind and message");
  }
  return {
    kind: value.kind,
    message: value.message,
    source_id: optionalString(value.source_id),
  };
}

export function parseEvaluationResult(value: unknown): EvaluationResult {
  if (!isRecord(value)) {
    throw new Error("Evaluation JSON must be an object");
  }
  if (value.items !== undefined && !Array.isArray(value.items)) {
    throw new Error("items must be an array");
  }
  if (value.warnings !== undefined && !Array.isArray(value.warnings)) {
    throw new Error("warnings must be an array");
  }
  const session =
    value.session_factors === undefined || value.session_factors === null
      ? null
      : parseFactors(value.session_factors);
  return {
    halted: parseHalt(value.halted),
    overall_light: parseLight(value.overall_light),
    items: (value.items ?? []).map(parseItem),
    session_factors: session,
    narrative: optionalString(value.narrative),
    warnings: (value.warnings ?? []).map(parseWarning),
  };
}
