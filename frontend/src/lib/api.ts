import type {
  BaselineImport,
  BaselineStatus,
  EvaluationResult,
  HealthStatus,
} from "@/lib/types";

export type { BaselineImport, BaselineStatus, EvaluationResult, HealthStatus };

function apiBaseUrl(): string {
  return (
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${apiBaseUrl()}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return (await response.json()) as HealthStatus;
}

export async function getBaseline(): Promise<BaselineStatus> {
  const response = await fetch("/api/v1/baseline", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load baseline (${response.status})`);
  }
  return (await response.json()) as BaselineStatus;
}

export async function putBaseline(
  payload: BaselineImport,
): Promise<BaselineStatus> {
  const response = await fetch("/api/v1/baseline", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to save baseline"));
  }
  return (await response.json()) as BaselineStatus;
}

export async function putBaselineText(text: string): Promise<BaselineStatus> {
  const response = await fetch("/api/v1/baseline/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to import text"));
  }
  return (await response.json()) as BaselineStatus;
}

export async function evaluatePrompt(
  prompt: string,
): Promise<EvaluationResult> {
  const response = await fetch("/api/v1/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to evaluate prompt"));
  }
  return (await response.json()) as EvaluationResult;
}

async function errorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    /* use fallback */
  }
  return `${fallback} (${response.status})`;
}
