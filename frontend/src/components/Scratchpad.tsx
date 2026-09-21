"use client";

import { useState } from "react";

import { css } from "@pigment-css/react";

import { BaselinePanel } from "@/components/BaselinePanel";
import { PromptPanel } from "@/components/PromptPanel";
import { StatusBar } from "@/components/StatusBar";
import { VerdictPanel } from "@/components/VerdictPanel";
import { col, rail } from "@/theme/layout";
import { tokens } from "@/theme/tokens";
import type {
  BaselineStatus,
  EvaluationResult,
  HealthStatus,
} from "@/lib/types";

const grid = css({
  display: "grid",
  gap: 24,
  alignItems: "start",
  gridTemplateColumns: "1fr",
  "@media (min-width: 900px)": {
    gridTemplateColumns: "minmax(0, 5fr) minmax(0, 7fr)",
  },
});

const stickyPane = css({
  backgroundColor: tokens.paper,
  padding: 16,
  minWidth: 0,
  "@media (min-width: 900px)": {
    position: "sticky",
    top: 16,
  },
});

type ScratchpadProps = {
  health: HealthStatus | null;
  healthError: string | null;
  baseline: BaselineStatus | null;
  baselineError: string | null;
};

export function Scratchpad({
  health,
  healthError,
  baseline,
  baselineError,
}: ScratchpadProps) {
  const [result, setResult] = useState<EvaluationResult | null>(null);

  return (
    <div className={grid}>
      <div className={col}>
        <StatusBar health={health} error={healthError} />
        <div className={rail}>
          <BaselinePanel
            initialStatus={baseline}
            initialError={baselineError}
          />
        </div>
        <div className={rail}>
          <PromptPanel onResult={setResult} />
        </div>
      </div>
      <div className={stickyPane}>
        <VerdictPanel result={result} />
      </div>
    </div>
  );
}
