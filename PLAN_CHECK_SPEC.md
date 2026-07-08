# Plan Check — future feature spec (balanced)

Status: **not built yet** — planning doc. Rewritten from an earlier draft to fit
Dotline's actual stage. Core principle kept; scope narrowed to what ships value
now, with the speculative parts deferred.

## Guiding principles (the core — keep)
- **Deterministic core, LLM only for language.** Rules never depend on AI; AI
  never computes dates/durations.
- **Progressive enhancement:** fully useful with AI turned off.
- **One shared currency:** every stage emits the same typed `Finding`.

```
Finding = { code, severity: 'info' | 'warning' | 'error', message, eventIds?: string[] }
```

## Phase 0 — Data model (prerequisite, do first)
Overlap / short-duration checks assume events have durations. Dotline events
don't — a Timing point has only a timestamp. So before any checker:

- Decide: add an **optional** `durationMin` per timing event?
  - **No** → overlap/duration checks are explicitly out of scope for v1.
  - **Yes** → optional field, backward-compatible.
- Freeze the normalized shape all stages consume:

```
Plan = { type: 'timing' | 'free',
         events: [{ id, time?: ms, durationMin?: number, label: string }] }
```

## Phase 1 — Rule Engine (ship this alone)
- **Pure functions, shared module, run CLIENT-side** — instant, offline, nothing
  leaves the device. Same code can run server-side later unchanged.
- Scope to what the model supports today:
  - missing/invalid time on a timed event
  - chronological consistency (declared intervals vs. resulting times)
  - non-finite / NaN intervals
  - *(only if `durationMin` exists)* zero/negative duration, overlap, too-short
- **"Business rules" = a small declarative list of named pure predicates**
  (e.g. `minPrepTime`), not an open-ended rules engine. Each testable alone.
- Deterministic, unit-tested, zero network, zero AI.

## Phase 2 — AI Review (optional, opt-in)
- Runs only when enabled AND the user consents (their plan leaves the device →
  privacy notice + toggle).
- Input: the plan **+ Phase-1 findings as grounding**.
- **Strict role:** explain, group, prioritize the deterministic findings in plain
  language, and offer human suggestions. Must reference an existing finding or
  the plan data — no invented time facts, no arithmetic. This is the guardrail
  against hallucinated risks.
- Bake in from day one: **latency** (show Phase-1 instantly, stream AI after),
  **cost** (cache identical plans; small cheap model), **privacy** (opt-in).
- Model options: a hosted frontier model (best quality) OR a small local model
  (Gemma 3 4B / similar) on our own server — the role is constrained enough that
  a 4B model suffices, and local keeps data on-box. Our VPS (4 vCPU, ~12 GB RAM
  free, no GPU) can run a 4B Q4 on CPU at ~20–40 s per short answer, so it must
  be async/streamed, not a blocking button.

## Phase 3 — External validators (only when the 2nd real one exists)
- **Do not build the plugin framework up front.** Implement Phase 1 + one real
  validator (e.g. `TravelTime`), then extract the interface from those two
  concrete cases — that's how you get the right abstraction, not a guessed one.

```
interface PlanValidator { name: string; validate(plan: Plan): Promise<Finding[]> }
```

- Validators are independent, optional, network-allowed; each returns `Finding[]`
  merged with the rest. Registered in a list → new validator = new module, no
  edits to engine or AI (open/closed). Later: TravelTime, Weather, Calendar…

## UI
Single **"Check Plan"** action:
1. Run Phase 1 locally → render grouped findings immediately.
2. If AI enabled + consented → run Phase 2, merge/annotate.
3. *(later)* run registered validators, merge.

Group by severity; each finding highlights the events it touches on the
timeline. Empty state: `✔ No issues found.`

## Guardrails (non-negotiable)
- Rule engine never imports AI or network.
- AI never does arithmetic/date logic; every AI claim grounded in a finding or plan data.
- No speculative plugin framework before a real second validator.
- `Finding` is the single shared type across all stages.

## Phasing
- **P0** data-model decision (durations?) — smallest unblock.
- **P1** local deterministic engine + UI + tests → ships value on its own.
- **P2** opt-in AI explanation layer (hosted or local Gemma).
- **P3** extract validator interface when the first external validator is built.
