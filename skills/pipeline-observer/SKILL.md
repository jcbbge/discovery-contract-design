---
name: pipeline-observer
description: Run or resume a pre-defined, fixed-marker pipeline such as Made Well Discovery; record each source-backed marker, branch, operation input/return, evidence and work artifact in the shared local workflow ledger. Use with Pi, Codex or Claude Code when a user supplies a voicemail, transcript, notes or another pipeline input, asks for percent complete, or requests a workflow trace.
compatibility: Requires Python 3 and /home/jrg/.local/bin/pipeline-observer on this VPS.
---

# Shared pipeline contract (Pi · Codex · Claude Code)

Read `/home/jrg/projects/discovery-contract-design/runtime/README.md` for CLI use. The current default Discovery definition is `/home/jrg/projects/discovery-contract-design/runtime/contracts/made-well-discovery-v2.json` (existing runs retain their pinned version), compiled from the Made Well skill. Before running Discovery, read the **canonical** `~/projects/infinity/arc/.madewell/skills/discovery.md` and Ground references where applicable. The ledger never replaces that protocol or its authoritative stock/decisions/product locations.

## WWWWW+H run declaration

- **Who:** operator, agent/harness, actors and human review gate.
- **What:** named pipeline + workflow + pinned version, source pointer, artifact type, goal and output contract.
- **When:** event date, declaration time, classification and review timestamps; declare live/blind **before** opening input.
- **Where:** source corpus pointer, Made Well depth `P`, rack, decision and product destinations; do not store raw transcript bodies in the ledger.
- **Why:** purpose, audience, acceptance and explicit downstream boundary (Discovery is ideate, never plan/implement).
- **Which:** selected mode and conditional route, eligible context, lens/trade, branch rules and governing source revisions.
- **How:** follow the fixed marker order; capture arguments → prescribed operation(arguments) → returned values → evidence → result with `pipeline-observer trace`; settle markers using `mark` and inspect `status` regularly.

For a new run, use `pipeline-observer start <corpus-pointer> --id <stable-id> --mode live|blind`. The run pins the exact fixed contract snapshot. For an artifact-to-candidates request, keep the user's interaction **one artifact in → numbered candidate list out**. Do not ask the user to pick slices, confirm an intermediate map, approve, rank, or choose a candidate merely to deliver J03. Choose a valid non-interrupting route under the governing workflow; do not claim a human-confirmed route if none occurred. If the governing workflow actually demands human confirmation for a proposed route, do not falsely mark it complete or silently bypass it—use an authorized non-interrupting route and record why. This instruction does not alter the Made Well skill or declare later publication/review markers complete. A new shell, tmux, Pi, Codex or Claude Code process must `pipeline-observer status <id> --detail` before resuming, and must not repeat a side effect merely because a marker appears pending. Record external side effects and inspect them first. Use `--revise` for explicit corrected marker claims, never rewrite history.

Use `pipeline-observer configure <id> deep_comb true` and other conditional choices **after classification, before dependent markers settle**. The same fixed 72-marker definition remains visible for every input; conditional activities receive exact authorized rule dispositions, never disappear from the denominator. Variable findings and slices are records **inside** marker operations, not added checkpoints. Record coverage or quality measures separately with `pipeline-observer measure` (explicit numerator, denominator population, method and evidence); do not turn a finding count into a completion percentage. Record an actual evidence pointer for each satisfied marker; `no findings` is a result of applying a lens, not permission to skip it. As work occurs, record a bounded `trace` adjacent to each real operation (input/arguments → operation → observed return → reported result), then `mark` only the fixed marker that the recorded evidence supports. Do not backfill a false trace or mark a merely attempted step complete. At J03, write the source-backed candidate array **in production order** as the candidate-output artifact; do not reorder, rank, group, select, or approve candidates. J03 may exist before the separate review/publication stages settle; report the candidates immediately. If candidate generation yields zero, record an empty J03 candidate array rather than inventing work. Human confirmation is not inferred from silence. When unavailable, present the draft, carry open questions and mark output unconfirmed under the protocol's exception.

The dashboard is read-only: `pipeline-observer serve --port 8787` on the VPS, then SSH-forward localhost if viewing elsewhere. Do not open the port to the public network. The dashboard and percentages reflect **recorded claims**, not independent proof of reasoning quality; verify the published Made Well artifacts themselves.

## Observer versus executor

If the user supplies **another pipeline for analysis**, do **not** force its stages into Discovery's 72 markers. Use `/home/jrg/projects/discovery-contract-design/PIPELINE_OBSERVER_META_PROMPT.md` to extract that pipeline's authority, ontology, fixed anatomy and graph in a separate output directory. Only after operator review publish a new versioned definition. Do not modify the source workflow without a separate explicit request.
