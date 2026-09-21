import type { HealthStatus } from "@/lib/types";

export function healthAlert(
  error: string | null,
  health: HealthStatus | null,
): string | null {
  if (!error && health?.status === "ok") {
    return null;
  }
  if (error && /database unavailable/i.test(error)) {
    return "Database unreachable. Start Postgres, then refresh.";
  }
  return "API unreachable. Start the API on port 8000, then refresh.";
}
