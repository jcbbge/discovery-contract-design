# Made Well Discovery — fixed marker inventory (draft for review)

**Source of truth, not this draft:** `~/projects/infinity/arc/.madewell/skills/discovery.md` (Arc checkout `e522fb0e`), `~/projects/infinity/arc/.madewell/ground/PROTOCOL.md`, `ground/ROOTS.md`, `ground/PICTURE.md`, and `.madewell/AGENTS.md`. The older `~/projects/infinity/discovery/pipeline/v3.md` declares itself superseded; do not execute it. This is a **proposed measurable projection** of the current protocol, not a rewrite or a claim that the original defines numeric weights. No Made Well files were modified.

## Fixed-shape completion semantics

- **All marker IDs below exist in every run.** No run discovers or adds stages, markers, or denominators. A branch fills a fixed marker with either the performed result or a documented, contract-authorized bypass (e.g., `not PRD-shaped`, `no paired artifact`, `blind: Ground prohibited`). Deep-comb creates variable *records* within fixed markers, not new progress markers.
- Marker values: `pending`, `in_progress`, `blocked`, `satisfied`, `satisfied_by_rule`, `failed`. `satisfied_by_rule` needs a reason and the exact rule; never conflate it with `satisfied`. `failed` is a recorded attempt and remains open to correction. Only `satisfied` and `satisfied_by_rule` count towards progress, subject to required evidence.
- Progress = **count of settled fixed markers / count of all fixed markers** for this exact contract version. A gate blocks advancement even when the percentage is high. No partially filled marker counts. This simple equal-weight definition is a design choice to validate with the operator, *not* a percentage claimed by Made Well.
- A marker is about a **specific observable obligation**, not whether an arbitrary number of findings has been created. Inside a marker, each finding/topic/slice/ruling is a separate variable-size record with its own evidence and validation. A universal condition such as “every finding is routed” satisfies the fixed marker only when all current findings pass and the candidate set is declared closed.
- `blind`, `live`, `solo`, `human meeting`, `AI chat`, `paired`, `PRD-shaped`, `single-pass`, `deep-comb`, and `live conversation` fill *fixed* conditional markers. “No findings from this lens” is a documented lens result, not a skipped lens. A rule-ineligible operation must never be silently checked off.
- Render sequence follows the authored skill. Ground is expanded as a nested fixed protocol, not reduced to one checkbox. Mode `blind` forbids reading the answer key; this disables relevant Ground/context *activities*, never hides their markers.

## Marker register

Each bullet is exactly one fixed marker. `→` describes the minimum result/evidence for satisfying it. References `D` = discovery skill and `G` = Ground protocol, with section names that remain searchable even if line numbers move.

### A — Declare the run (`D §Step 0`)
- `A01` Run mode → `live` or `blind`, recorded **before reading source**.
- `A02` Ground disposition → `on` for live or explicitly `skipped (blind)`.
- `A03` Rack disposition → `loaded` or `not loaded`, with reason (blind must not load rack).

### B — Look before adding (`D §Step 0.5`; blind exclusions from `D §Step 0`)
- `B01` Current-depth rack → path `P/stock/`, inventory or `blind: prohibited`.
- `B02` Decisions → `DECISIONS.md` read or `blind: prohibited`.
- `B03` Product vision → `PRODUCT.md` read or `blind: prohibited`.
- `B04` Paired source → paired primary artifact read, explicitly `none`, or `blind: prohibited` if it is a prior analysis/answer key. Do not conflate “no pair” with “pair not checked”; do not assume every primary paired artifact is prohibited in blind mode.

### C — Ground (nested protocol, live only; `G §Steps 0–3`)
- `C01` Ground applicability/mode → start Ground in live, or `blind: prohibited` with no reads.
- `C02` Read project's `ground/ROOTS.md` → identify kernel/project roots and external owners (live) or blind skip.
- `C03` Preflight paths → confirm existence/misses explicitly; `NO EXISTING IMPLEMENTATION — net new` for a genuine miss (live) or blind skip.
- `C04` Extract task nouns/surfaces/values → search terms and owner for each external value (live) or blind skip.
- `C05` Corpus sweep → relevant existing decisions, product, rack/bench/finished, guides/docs/trade, with `path | what it is | relevance | one line` table, locked decisions each file:line, open questions/contradictions each file:line or UNKNOWN, and short corpus synthesis (live) or blind skip.
- `C06` Material sweep → locate/read actual material or external system of record; per relevant surface record `path | lines | BUILT/PARTIAL/NET-NEW | one line`, gap and contradiction; record `OWNER: <system> — NOT READ` if inaccessible (live) or blind skip.
- `C07` Separate owner from mirror → for externally owned claims, show owner evidence or mark unverified (live) or blind skip.
- `C08` Present corpus half in the `ground/PICTURE.md` shape (spoken is sufficient; write only if requested) (live) or blind skip.
- `C09` Present material half in the `ground/PICTURE.md` shape (spoken is sufficient; write only if requested) (live) or blind skip.
- `C10` Choose own-context by default or document size-triggered other-hands exception (live) or blind skip.
- `C11` Synthesize both halves into the picture's final gap: required vs actual; binding locked decisions; open decisions classified lead-owned vs external; recommended next move with file:line anchors. Every behavioral claim cited (live) or blind skip.
- `C12` Stop and present decision-ready picture **before acting**; Ground remains read-only (live) or blind skip. Ground does not itself mint stock.

**Ground picture semantics:** `ground/PICTURE.md` explicitly says speaking the picture is enough and nothing should be created on disk unless requested. The runner can store the *fact of presentation and its evidence references* without writing a new Made Well picture or altering implementation/product/stock. Do not auto-write or overwrite `ground/PICTURE.md`.

### D — Classify (`D §Step 1`)
- `D01` Source type → brain dump/transcript/meeting/AI chat/planning note/document (or explicit extension), with source path.
- `D02` Artifact date → event date, **not** analysis date; unknown must be explicit.
- `D03` Participants → present actors and their roles, including explicit solo/unknown.
- `D04` Off-stage named actors → list or explicit none.
- `D05` Maturity → `SUBSTRATE | IDEATION | PLANNING | EXECUTION | VERIFICATION | FIELD`, with basis.
- `D06` Mixed-maturity treatment → per-section classifications or documented single-maturity basis; FIELD rubric handled correctly.
- `D07` Signal density → HIGH / MED / LOW, with short rationale.

### E — Choose pass mode (`D §Step 1.5`)
- `E01` Distinct-topic count → count **topics, not lines**; record boundaries/basis.
- `E02` Select processing route → single-pass, deep-comb, or cross-artifact; justify exceptional overrides (e.g., serial walkthrough).
- `E03` Stable slice addresses → for deep-comb with unusable line ranges, fold into numbered segments, commit the copy beside the original (not a scratch file), and cite segments; if addresses already stable, record that basis; otherwise rule-bypass citing `single-pass`/`cross-artifact`.
- `E04` Topic map and confirmation → for deep-comb, 5–8 scoped slices and **human confirmation before fan-out**; otherwise rule-bypass.
- `E05` Isolated reader execution → for deep-comb, scope each reader to its slice; otherwise rule-bypass.
- `E06` Cross-cut synthesis → for deep-comb, reconcile outputs and keep cross-cuts distinct from per-slice findings; otherwise rule-bypass. Number of slices does not change marker count.

### F — Apply the lenses (`D §Step 2`)
- `F01` Substance → signals; HIGH-density friction inventory (#, friction, affected person, root cause); explicitly no findings if none.
- `F02` People → each person's optimization and actual vocabulary; note `context.language` implications.
- `F03` Process → actual/shadow workflow, decision/communication practice.
- `F04` Gap → unanswered questions, unvalidated assumptions, unexplained references.
- `F05` Subtext → select and apply the *correct* rubric for meeting/human conversation, AI chat, or solo source; maturity-aware interpretation.
- `F06` Meta → process/skill/rack improvements or explicit no findings; do not quietly turn meta into product stock.
- `F07` Trade lens slot → applicable loaded trade's additional lenses applied **after** core, or explicitly `no trade loaded`. Variable observations do not create new process markers.

### H — Extract the One Thing (`D §Step 2.5`)
- `H01` Identify the single most important *not already written down* finding, without hedging, citing its basis.
- `H02` Record it at its proper durable address: `PRODUCT.md`, the rack, or `DECISIONS.md` (the address may be proposed until the Step 5 human gate permits the write). Do not count a statement living only in chat as recorded.

### I — PRD compression check (`D §Step 2.6`)
- `I01` Determine whether source is PRD/compression-shaped; if not, record rule-bypass for `I02–I05`.
- `I02` What survived from earlier discussion → results or authorized non-PRD bypass.
- `I03` What was dropped and what was added → both compared or authorized bypass.
- `I04` Every metric checked for instrument and baseline → inventory/verdicts or authorized bypass.
- `I05` “Complete blueprint” claim tested for structural gaps → verdict, claim absent, or authorized bypass.

### J — Route every finding (`D §Step 3`)
- `J01` Candidate set declared ready for routing; retain source pointers and lens for each; no fixed number of findings.
- `J02` Each meaningful finding has exactly one `rack | decision | release` disposition; releases **named**, never silently discarded.
- `J03` Validate all six source-required fields for each finding: `ID | Lens | Finding (one sentence) | Disposition | Evidence | Attribution`; mark attribution stated/inferred and qualify consequential inference.
- `J04` Duplicate/repeated decision check **per candidate at write time**, with timestamped rack search and decisions reference; do not substitute Step 0.5's initial stock inventory or re-rack a duplicate.
- `J05` For in-flight work, preserve `in-flight` on rack, verdict it **first** before racking more, and never bypass the gate; otherwise rule-bypass.
- `J06` For transcript-derived stock, propose **title + corpus path** pointer, not a body copy; preserve corpus boundary.

### K — Name things and track open questions (`D §Step 4`)
- `K01` Name surfaced patterns, gaps and shadow workflows, or explicitly record none.
- `K02` Add new cross-artifact questions to `DECISIONS.md` or `PRODUCT.md` (propose before human gate if required); explicit none if absent.
- `K03` Close questions this artifact answers, with cited source; explicit none if absent.

### L — Cross-artifact synthesis (`D §Cross-Artifact Synthesis`, selected by Step 1.5)
- `L01` Determine paired-source applicability; when applicable, verify prerequisite Step 0.5 current design/direction loaded.
- `L02` ALIGNMENTS → record settled agreements with `do not reopen`, or authorized no-pair bypass.
- `L03` DISCREPANCY MAP → assumption vs existing state vs consequence vs decision, ranked by leverage, or bypass.
- `L04` THROUGH-LINE → single root connecting discrepancies, or bypass; only cross-cuts enter stock at synthesis.

### M — Reflect, operator gate, publish (`D §Step 5`)
- `M01` Reflect in plain language: “here's what I heard.”
- `M02` Present **draft before asking**, with ready-to-rack / needs-decision / named-release proposals and scope.
- `M03` Ask operator “Does that match what you meant?” and record review request/status; never infer agreement from silence.
- `M04` Capture every ruling **verbatim with timestamp**, including confirmations; treat reply as a second source artifact.
- `M05` Cite rulings inline; where ruling contradicts a finding, retain struck-through prior reading and show corrected one.
- `M06` If operator unavailable, carry explicit open question; otherwise record their rulings. **The skill permits racking while unavailable**, not silent approval.
- `M07` Publish eligible stock to current-depth `P/stock/<slug>.md`, or record justified absence; stock points to corpus rather than copying transcript body.
- `M08` Record decided/unmade decisions in `DECISIONS.md` / `PRODUCT.md`, or explicit none; open threads have an actual reader.
- `M09` Update `PRODUCT.md` and refresh `context.summary`, `context.openThread`, `context.language` **when new information exists**; record explicit no-change reason otherwise.
- `M10` Check the boundary: discovery stays at ideate/rack; **no bench move, plan, implementation, STAGING.md or STG-* minting** from discovery.

### N — Live conversation specialization (`D §Live Conversation Mode`)
- `N01` Determine whether input is live conversation or a supplied artifact.
- `N02` If live, invite unorganized narration and listen without interruption; else authorized bypass.
- `N03` If live, do classification/lenses internally and Steps 2.5–5 aloud; unrelated work is captured on rack immediately with acknowledgement, then return; else bypass. Such capture is a specific exception, not permission to skip the Step 5 draft/review of the current discovery.

## Contract-wide validation rules (not extra percentage markers)

- **Temporal:** `A01` precedes reading; classification before analysis; deep-comb topic map approved before fan-out; draft before operator ruling; operator rulings before treating confirmation as evidence; grounded picture before source-of-truth claims are promoted in live mode.
- **Privacy/corpus:** never copy full transcript into dist, preserve original in read-only corpus and cite stable spans; protect sensitive voicemail/transcript content in telemetry and dashboards.
- **Position:** `P/stock/` at current depth is authoritative, not a shadow status table; an external runner records observations but must not create a competing Made Well board.
- **Honesty:** Ground is read-only; blind sees no answer key; FIELD differs from SUBSTRATE; nothing rejected at discovery rack; optional no-result is recorded rather than fabricated; avoid self-graded acceptance where operator judgement is required.
- **Hard gates:** publish requires mode declared, required lenses completed, candidate routing, and draft-before-review. Human silence is **not approval**, although `D §Step 5` explicitly allows racking with an open question if unavailable. That exception must be visible in the dashboard.

## Decisions needed before freezing this draft

1. How the runner records a **spoken Ground picture** and its evidence references without creating an unauthorized on-disk Made Well picture; do not overwrite active work.
2. Where `context.summary`, `context.openThread`, `context.language` live in this installation and how to verify updates without inventing a second context ledger.
3. Whether equal-weight marker percentage is desired or predefined stage weights; whichever is chosen must be fixed within a version.
4. Whether `M03` is allowed to stay visibly `blocked/waiting` while `M07` publishes under the source's explicit unavailable-operator exception, and what “run complete” means in that case.
5. Confirm boundary between Ground's read-only *lookup* and source-driven Step 0.5 preflight; do not count the same file read twice as evidence of two distinct obligations.
6. Clarify the paired-artifact route: Step 1.5 says cross-artifact synthesis runs *in place of a lens-only pass*, while Step 2 says apply all six lenses. The contract keeps both marker groups fixed, but must define what evidence satisfies each on paired runs and place the cross-artifact operation in its actual execution order before implementation.
