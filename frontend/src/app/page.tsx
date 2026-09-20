import { BaselinePanel } from "@/components/BaselinePanel";
import { PromptPanel } from "@/components/PromptPanel";
import { StatusBar } from "@/components/StatusBar";
import { getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  let health = null;
  let error: string | null = null;

  try {
    health = await getHealth();
  } catch (err) {
    error = err instanceof Error ? err.message : "API unreachable";
  }

  return (
    <main>
      <h1>Overdone</h1>
      <p>Diagnostic scratchpad — evaluate a proposed increment</p>
      <StatusBar health={health} error={error} />
      <BaselinePanel />
      <PromptPanel />
    </main>
  );
}
