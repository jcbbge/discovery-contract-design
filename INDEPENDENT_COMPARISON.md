# Independent Discovery extraction vs 72-marker draft

Five parallel read-only `openai/gpt-6-astra:high` subagents independently inspected bounded source slices on 2026-10-20. Workflow `01M5BZE176D5D9NQW38ENN4S1Q`: `intake`, `lenses`, `routing`, `variants`, `ground`, all sealed `ok`. None was given the 72-marker draft. Source: `~/projects/infinity/arc/.madewell/skills/discovery.md`, `ground/{PROTOCOL,PICTURE,ROOTS}.md`; comparison target: `MARKER_INVENTORY.md`. This is a comparison, **not** approval of a 72-marker canonical schema.

## Convergence

The independent passes support the main anatomy: declare mode before reading, conditionally withhold answer-key context in blind evaluation, classify before analysis, choose single/deep-comb/cross-artifact mode with explicit rules, apply six universal lenses, record exactly one One Thing, route every meaningful finding once, capture operator rulings verbatim, preserve corpus pointers, and never move discovery stock to the bench. Ground is a required nested protocol in live mode, not one generic `grounded` checkbox. Variable numbers of slices/findings/rulings remain payload, not marker counts. Sources: Discovery lines 34–50, 63–120, 122–181, 200–302; Ground PROTOCOL steps 0–3.

## Material differences and corrections to the draft

| Priority | Draft marker(s) | Independent source finding | Correction before freezing |
|---|---|---|---|
| HIGH | `C05`, `C08–C11` | Ground's `PICTURE.md:3–54` mandates a four-section picture **in this sitting**: preflight, corpus with path/relevance table + cited locked decisions + open questions, material with `BUILT/PARTIAL/NET-NEW` + gaps/contradictions, and final gap with lead-owned vs external open decisions and recommended move. Our markers are too broad to verify that whole shape. | Add explicit satisfaction fields/validators **inside existing fixed markers**, or split into more fixed markers with a new *candidate* denominator. Do not mark Ground complete on a generic “picture presented.” Spoken presentation suffices; no disk write without request. |
| HIGH | `H02`, `M02–M07` | One Thing says write to PRODUCT/rack/DECISIONS (`discovery.md:176–181`), while Step 5 says draft first, ask second, finding unseen by operator not eligible for rack (`:277–287`), with an unavailable-operator exception. | Flag ordering as source ambiguity. Do not silently impose a deferred One Thing write or bypass the review gate. Get operator ruling on its destination/timing and how unavailable review works. |
| HIGH | `B01–B04`, `C01` | Blind explicitly withholds **rack, prior analyses of this artifact, and built material** (`:45–47`). It does *not* expressly forbid every decision/product doc or all paired primary sources by filename. Ground PROTOCOL also names three skip reasons for general use, while Discovery says blind specifically skips Ground. | Define which contextual sources are an answer key in blind runs. Distinguish the Discovery-specific blind rule from Ground's general skip conditions; don't treat all omitted reads as authorized without classification. |
| HIGH | `E02–E06`, `F01–F07`, `L01–L04` | Paired input uses cross-artifact synthesis **in place of a lens-only pass** (`:118–120`, `:306–332`). Our draft lists it after all core lenses and routing, which may misorder the operation. | Define the order and fixed marker verdicts when paired synthesis supplants lens-only processing. Do not assert all six lens-result markers must produce separate lens artifacts in that mode without a ruling. |
| MED | `B01`, `J04` | Rack search is **per candidate at write time**, not one initial sweep (`:54–57`); decisions prevent re-raising decided findings. | Require timestamped/per-candidate evidence within `J04`, not just `B01` inventory evidence. |
| MED | `E03` | When no stable slice address exists, fold into **numbered segments, commit the copy beside the original**, cite segments, never scratch (`:114–118`). | Record a verifiable committed source address, not merely a saved copy. Decide how that coexists with corpus read-only policy; this is a source tension. |
| MED | `J02–J05` | Finding schema explicitly requires `ID | Lens | Finding (one sentence) | Disposition | Evidence | Attribution` (`:210–217`); in-flight work gets its verdict **first** (`:231–236`). | Validate all six fields and first-priority ordering, not merely a disposition and in-flight flag. |
| MED | `C02–C06` | PROTOCOL names root-level `SPEC.md` (`:96`); project ROOTS names `.madewell/SPEC.md` (`ROOTS.md:16`). Direct path check on this Arc checkout: root `SPEC.md` does **not** exist and `.madewell/SPEC.md` does; this resolves the usable path *here*, though source prose still disagrees. ROOTS external-owner section is still a placeholder (`ROOTS.md:23–29`), not evidence that external owners are mapped. | Do not treat placeholder as an authoritative owner map. For Arc use `.madewell/SPEC.md` as the verified path; report the stale root-level instruction as a source defect. Require an explicit owner/not-read determination per claim. |
| MED | `F01–F06`, `I01–I05`, `K01–K03`, `M09` | “Explicitly no finding,” `not PRD-shaped`, and `no change needed` are sensible **observer-designed result encodings**, not literal source-mandated field values. Source prescribes applicability, not a specific checkbox schema. | Keep these as `PROPOSED` instrument semantics. Don't present them as a requirement quoted from the skill. |
| LOW | `N01–N03` | Live conversation mode explicitly invites free narration, listens uninterrupted, performs lens/maturity work internally, then Steps 2.5–5 aloud (`:336–346`). | Preserve that interaction order in `N03` evidence. Unrelated mid-session capture is an explicit exception, not ordinary publication permission. |
| LOW | Cross-cut annotations | Cross-artifact optional classification list (`:318–326`) is **not** seven required result fields. | Keep optional classification in telemetry/payload; never inflate fixed progress by seven. |

## Source tensions surfaced independently

1. **Written Ground picture:** `ground/PICTURE.md:3–6` permits a written picture only if requested; `ground/PROTOCOL.md:152–154` says Ground never writes. Spoken presentation is clearly allowed; request-based write precedence needs ruling.
2. **Spec path (factually resolved for Arc, source text still inconsistent):** `ground/PROTOCOL.md:96` says `SPEC.md` (missing on disk); `ground/ROOTS.md:16` says `.madewell/SPEC.md` (present). No operator ruling is needed to choose the existing file.
3. **Operator unavailable:** `discovery.md:277–278` requires seen draft before racking; `:286–287` permits racking with open question if the operator is unavailable. Need precedence and state representation.
4. **One Thing write timing:** `discovery.md:181` says write it down; Step 5 delays rack eligibility until after draft/ask. Clarify permissible early destinations.
5. **Blind context:** exact decision/product/paired primary-source availability is not settled by the rack/previous-analysis/built-material prohibition (`:45–60`).
6. **Source pointer wording:** `discovery.md:219–229` says “title plus path — never both,” while the example shows title + `Source:` path; likely means no duplicated body but the phrase itself is unclear.

## Percent status

The five independent slices **do not validate the number 72**. They extracted obligations, not a mutually agreed atomic marker count. The sample run's `23/72` is a draft demonstration, not an approved measurement. Once the source tensions and granularity are settled, fix the denominator for a pinned version, verify it against several recorded/synthetic cases, then publish the percentage.

## Suggested minimal ruling sequence

1. Decide the one authoritative ordering for paired-artifact runs and One Thing write/review; these affect admissibility.
2. Decide blind allowlist and Ground picture written/spoken precedence; these affect evidence and privacy.
3. Tighten Ground and finding validation in the inventory, then count fixed markers again.
4. Replay a short, blind, paired and deep-comb run; only then freeze the denominator and move to the next pipeline.

No Arc/Discovery source file was changed by this comparison.
