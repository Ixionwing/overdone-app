import { Scratchpad } from "@/components/Scratchpad";
import { getBaseline, getHealth } from "@/lib/api";
import type { BaselineStatus, HealthStatus } from "@/lib/types";
import { pageLead, pageMain, pageTitle } from "@/theme/layout";

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
    <BoxPage
      health={health}
      error={error}
      baseline={baseline}
      baselineError={baselineError}
    />
  );
}

function BoxPage({
  health,
  error,
  baseline,
  baselineError,
}: {
  health: HealthStatus | null;
  error: string | null;
  baseline: BaselineStatus | null;
  baselineError: string | null;
}) {
  return (
    <main id="main" className={pageMain}>
      <h1 className={pageTitle}>Overdone</h1>
      <p className={pageLead}>
        Diagnostic scratchpad for a proposed training increment.
      </p>
      <Scratchpad
        health={health}
        healthError={error}
        baseline={baseline}
        baselineError={baselineError}
      />
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
