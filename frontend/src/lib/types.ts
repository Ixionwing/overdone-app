export type HealthStatus = {
  status: string;
};

export type BaselineSet = {
  exercise: string;
  weight: number;
  reps: number;
  sets: number;
  unit?: string | null;
  exercise_id?: string | null;
};

export type BaselineSession = {
  date: string;
  notes?: string | null;
  sets: BaselineSet[];
};

export type BaselineBenchmark = {
  exercise: string;
  one_rm: number;
  unit?: string | null;
  exercise_id?: string | null;
};

/** Keep fields aligned with backend/src/overdone/schemas/api.py. */
export type BaselineImport = {
  preferred_unit: string;
  benchmarks: BaselineBenchmark[];
  sessions: BaselineSession[];
};

export type BaselineStatus = {
  preferred_unit: string;
  benchmark_count: number;
  session_count: number;
  set_count: number;
  baseline: BaselineImport;
};

export type TrafficLight = "green" | "yellow" | "red";

export type FactorScores = {
  volume_jump_pct: number;
  axial_compression: number;
  cns_index: number;
  joint_vectors: Record<string, number>;
};

export type ItemVerdict = {
  exercise_id: string;
  exercise_name: string;
  light: TrafficLight;
  factors: FactorScores;
  narrative: string;
  catalog_source_id: string | null;
};

export type WarningFlag = {
  kind: string;
  message: string;
  source_id: string | null;
};

export type Halt = {
  reason: string;
  message: string;
  exercise_name: string | null;
};

export type EvaluationResult = {
  halted: Halt | null;
  overall_light: TrafficLight | null;
  items: ItemVerdict[];
  session_factors: FactorScores | null;
  narrative: string | null;
  warnings: WarningFlag[];
};
