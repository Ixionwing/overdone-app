import { BaselinePanel } from "@/components/BaselinePanel";
import { PromptPanel } from "@/components/PromptPanel";
import { StatusBar } from "@/components/StatusBar";
import { getBaseline, getHealth } from "@/lib/api";
import type { BaselineStatus, HealthStatus } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [healthResult, baselineResult] = await Promise.allSettled([
    getHealth(),
    getBaseline(),
  ]);

  const health =
    healthResult.status === "fulfilled" ? healthResult.value : null;
  const error = rejectionMessage(healthResult, "API unreachable");
  const baseline =
    baselineResult.status === "fulfilled" ? baselineResult.value : null;
  const baselineError = rejectionMessage(
    baselineResult,
    "Failed to load baseline",
  );

  return (
    <main>
      <h1>Overdone</h1>
      <p>Diagnostic scratchpad — evaluate a proposed increment</p>
      <StatusBar health={health} error={error} />
      <BaselinePanel initialStatus={baseline} initialError={baselineError} />
      <PromptPanel />
    </main>
  );
}

function rejectionMessage(
  result: PromiseSettledResult<HealthStatus | BaselineStatus>,
  fallback: string,
): string | null {
  if (result.status === "fulfilled") {
    return null;
  }
  return result.reason instanceof Error ? result.reason.message : fallback;
}
