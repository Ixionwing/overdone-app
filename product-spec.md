# Overdone — Final Product Specification

## 1. Product Overview & Vision
**Overdone** is an AI-powered, stateless diagnostic webapp designed to prevent overtraining, joint strain, and injury. Operating as a pure diagnostic scratchpad, **Overdone** takes a user's natural language prompt describing a proposed change to their future workout(s) and evaluates it against their physical baseline history to render a traffic-light judgment (**Green / Yellow / Red**) on whether an increment is "overdoing it."

---

## 2. Core UX & System Behaviors

### 2.1 Baseline Ingestion & Onboarding
* **Plain-Text / File Import**: On initial launch, users establish their physical baseline history by pasting workout logs as plain text or uploading a log file/JSON into a configuration box.
* **Mandatory Baseline Requirement**: All evaluations require an active baseline history or a set of 1 Rep Max (1RM) benchmark weights.
* **Missing Exercise Guard (Cold Start)**: If a prompt introduces an exercise not present in the user's history, Overdone halts evaluation and prompts the user to enter a 1RM or baseline working weight before rendering a verdict.

### 2.2 Input Flexibility
* **Single-Session Targets**: Evaluates immediate next-workout increments (e.g., *"I want to add 20 lbs to my bench press tomorrow"*).
* **Multi-Week Macro Goals**: Evaluates time-bound progression goals (e.g., *"I want to bench 225 by next month"*) as an aggregate macro feasibility summary comparing the required progression rate against historical adaptation velocity.
* **Multi-Exercise Prompts**: Evaluates prompts modifying multiple exercises in a single session (e.g., *"Add 10 lbs to Bench, 5 lbs to Incline DB Press, and 3 extra sets of Pushdowns"*).

### 2.3 Diagnostic Verdict & Hybrid Rationale Output
* **Traffic-Light Risk Indicator**: Renders a top-level **Green** (Safe), **Yellow** (Caution), or **Red** (Overdone) status.
* **Itemized Session Granularity**: For multi-exercise prompts, Overdone outputs an **overall session traffic light** (cumulative session strain/peak risk) alongside **individual itemized traffic lights for each modified exercise**.
* **Hybrid Rationale UI**: Combines a **2–3 sentence conversational narrative** explaining the physiological rationale with **visual metric stat gauges / progress bars** for raw quantitative deltas:
  * Percentage volume jump (tonnage vs. safety threshold)
  * Cumulative axial spinal compression score
  * Central Nervous System (CNS) fatigue index
  * Joint strain vectors (e.g., shoulder shear, knee stress)
* **Passive Scratchpad Model**: Operates strictly as a diagnostic tool—displays risk factors and traffic lights without auto-generating alternative workout schedules or committing sessions to a calendar.
* **In-App Viewing**: Verdicts and stat gauges render strictly within the active webapp session.

### 2.4 Contextual & Qualitative Handling
* **Qualitative Log Notes**: Past subjective notes in workout logs (e.g., *"Right shoulder felt tight on set 3"*) are surfaced as informational warning banners alongside the factor breakdown, without altering the quantitative score calculation.
* **In-Prompt Fatigue Declarations**: Explicit user fatigue or low-sleep statements (e.g., *"Slept 4 hours and feel beat up"*) surface an explicit **In-Prompt Fatigue Warning Flag**, keeping the quantitative score strictly grounded in physical log data.
* **Lapsed Training / Time Gaps**: Uses a **Static Last Baseline**, evaluating prompts strictly against the last recorded working weights/1RMs regardless of elapsed time.
* **Strict Unit Enforcement**: Requires explicit units (`lbs` vs `kg`) in prompts if the baseline contains mixed units, or asks for unit clarification before rendering a verdict.

### 2.5 System Scope & Edge Cases
* **Strict Diagnostic Boundary**: Enforces a strict diagnostic mandate. Even if a user explicitly asks *"What should I do instead?"*, Overdone renders the diagnostic traffic light and rationale while stating that exercise substitution generation is out of scope.
* **Standard Evaluation for Extreme Prompts**: Unrealistic or extreme prompts (e.g., *"Add 500 lbs to my Bench Press tomorrow"*) are processed through standard math channels, returning a **Red** verdict alongside the extreme quantitative delta metrics (+300% Volume Jump) and narrative rationale.
* **Stateless Prompt Refinement**: Evaluates every prompt independently against the static baseline history without storing conversational prompt history across turns.

---

## 3. Tech Stack Architecture

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Runtime** | Python 3.12 (Containerized) | Service execution & API layer |
| **Protocol Layer** | FastMCP / Model Context Protocol | Standardized MCP tool interfaces for AI agent interaction |
| **Ingestion Engine** | Pydantic AI | Schema-constrained extraction of shorthand text & goal prompts |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` | Relational log storage + vector search for biomechanics metadata |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local 384-dimensional embeddings (100% free & offline) |
| **Reference Bank** | `free-exercise-db` (GitHub Open Source) | ~800 exercises enriched with local axial load & joint factors |

---

## 4. System Behavior Matrix

| User Prompt / Scenario | System Classification | Primary Logic / Tool | Processing Strategy | Output / Verdict Structure |
| :--- | :--- | :--- | :--- | :--- |
| *"Add 20 lbs to DB Bench Press tomorrow."* | **Single Session (Single Movement)** | Ingestion + Deterministic Math | Evaluates immediate tonnage jump and joint load against recent DB Bench history using fixed global thresholds. | **Traffic Light** + **Narrative Rationale** + **Visual Stat Gauges** (% volume jump, shoulder strain). |
| *"Tomorrow: +10 lbs Bench, +5 lbs Incline DB Press, +3 sets Pushdowns."* | **Single Session (Multi-Movement)** | Ingestion + Multi-Exercise Analyzer | Evaluates total cumulative session volume/CNS strain AND individual movement jumps. | **Overall Session Traffic Light** + **Itemized Per-Exercise Traffic Lights** + Narrative & stat bars. |
| *"Reach a 225 lb Squat by next month."* | **Macro Goal** | Macro Feasibility Analyzer | Compares requested multi-week progression rate against historical adaptation velocity. | **Traffic Light (Macro Feasibility)** + Aggregate volume/axial load narrative + metric progress graphics. |
| *"4 sets of 185 lb Overhead Press tomorrow."* *(No OHP in log)* | **Missing Exercise (Cold Start)** | Baseline Validator | Identifies absence of OHP in user logs/1RMs. Halts evaluation. | **Incomplete Baseline Prompt**: Halts evaluation and requests baseline OHP weight. |
| *"Add 10 lbs to Incline DB Flys tomorrow."* *(Log: "Right shoulder felt tight")* | **Session with Qualitative Log Notes** | Ingestion + Deterministic Math + Context Search | Computes quantitative score from physical load; surfaces recent qualitative pain/tightness notes. | **Traffic Light Score** + Narrative & Metric Gauges + **Contextual Warning Flag**: *"Note from 2 days ago: 'Right shoulder felt tight'"*. |
| *"Slept 4 hours, but want to add 10 lbs to Bench tomorrow."* | **Prompt with Fatigue Declaration** | Ingestion + Deterministic Math + Context Search | Computes quantitative score from physical load; surfaces an explicit fatigue warning banner. | **Traffic Light Score** + Narrative & Metric Gauges + **In-Prompt Fatigue Warning Flag**: *"User declared: 'Slept 4 hours / beat up'"*. |
| *"Add 30 lbs to Bench tomorrow, or tell me what to do instead."* | **Prompt Requesting Substitution** | Ingestion + Deterministic Math | Evaluates proposed jump against baseline; enforces strict diagnostic scope boundary. | **Traffic Light Score (Red)** + Narrative & Gauges + **Scope Disclaimer**: *"Diagnostic evaluation complete; exercise substitution is outside scope."* |
| *"Add 500 lbs to my Bench Press tomorrow."* | **Extreme / Outlier Prompt** | Ingestion + Deterministic Math | Evaluates massive tonnage delta through standard quantitative pipeline. | **Traffic Light Score (Red)** + Extreme Metric Gauges (+300% Volume Jump) + Narrative explaining extreme physiological risk. |
| *"Add 200 to Bench tomorrow."* *(Baseline has mixed lbs/kg)* | **Ambiguous Unit Prompt** | Unit Normalizer / Validator | Detects missing units amidst mixed baseline units. Halts evaluation. | **Unit Clarification Request**: Asks whether "200" refers to `lbs` or `kg` before rendering verdict. |

---

## 5. Definition of Done (DoD) for Agentic Coding Harness

- [ ] **Container Readiness**: PostgreSQL 16 + `pgvector` container starts via `docker compose` and passes health checks.
- [ ] **Seeding Pipeline**: Open-source `free-exercise-db` is seeded and enriched with local axial load and joint stress metadata.
- [ ] **Baseline Ingestion**: Plain-text and JSON log importer populates baseline user exercise history.
- [ ] **Traffic Light Diagnostics**: FastMCP tool endpoints evaluate single-session (single and multi-movement) and macro goal prompts against database baselines using fixed global rules.
- [ ] **Multi-Exercise Itemization**: Returns both overall session risk and per-exercise itemized verdicts for multi-movement prompts.
- [ ] **Hybrid Rationale UI**: Outputs short 2–3 sentence narrative explanations paired with structured quantitative factor graphics/gauges.
- [ ] **Baseline & Unit Guards**: Evaluation halts with clean prompts when an unknown exercise is introduced or when units are ambiguous.
- [ ] **Subjective Note & Fatigue Surfacing**: Qualitative pain/tightness flags from logs and in-prompt fatigue declarations are surfaced alongside factor breakdowns.
- [ ] **Strict Scope Boundary**: Enforces passive diagnostic boundary without executing exercise substitution generation even when requested.
- [ ] **Standard Outlier Processing**: Evaluates extreme prompts through standard math channels, outputting a Red verdict with extreme delta metrics.
- [ ] **Stateless Execution**: Operates purely in-memory/scratchpad mode without mutating historical logs or storing session prompt memory.
