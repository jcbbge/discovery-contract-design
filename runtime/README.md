# Pipeline Observatory MVP — Discovery v2

A local, fixed-shape **workflow ledger** for Pi, Codex and Claude Code. One immutable-by-run contract snapshot, a transactional SQLite event log, a shared CLI, and a read-only, single-run **Discovery observer** at http://127.0.0.1:18787/ through the existing M5 tunnel. One artifact produces a numbered candidate list; the real run page shows that recorded output first, in original order, with expandable source pointers and fixed-step/operation records. The user service is installed and enabled on loopback. It does **not** capture native agent model/tool execution automatically or guarantee that self-reported evidence is truthful: the agent must record each real operation as it works. A previously backfilled trace is not automatically captured telemetry. Source files, stock and decisions remain Made Well's sources of truth. No raw voicemail or transcript is copied to SQLite by default: give the runner a corpus *pointer*, not its body.

## Install / inspect

- User command: `~/.local/bin/pipeline-observer` → this project's `durable.py`.
- User skill: `~/.agents/skills/pipeline-observer/SKILL.md`; Claude gets a symlink under `~/.claude/skills/`.
- State: `~/.local/state/pipeline-observer/runs.sqlite` (`PIPELINE_HOME` overrides it). Read-only dashboard is enabled as the user service `pipeline-observer.service`, listening **only** on `127.0.0.1:8787`. Stop it with `systemctl --user disable --now pipeline-observer.service`.
- Source inventory: `../MARKER_INVENTORY.md`; accepted defaults: `../RESOLUTION_PROPOSAL.md`; frozen artifacts: `contracts/made-well-discovery-v1.json` (legacy) and `contracts/made-well-discovery-v2.json` (default for new runs). Every run pins its exact contract JSON and SHA256. Source-hash changes do not mutate existing runs.
- v2 records a file-byte SHA256 and absolute path for the marker inventory plus all five governing files: Arc `AGENTS.md`, `.madewell/skills/discovery.md`, and `.madewell/ground/{PROTOCOL,PICTURE,ROOTS}.md`. This is a **local snapshot**, not a Git revision: ignored files are not asserted to be in any commit. New v2 runs refuse to start if a source is missing or its hash differs; compare/review the change and publish a new contract version rather than rewriting v2. This checks file bytes at start, not semantic consistency or later source changes. The file paths are local to this installation; relocation requires a new reviewed snapshot.
- v1 is unchanged byte-for-byte and remains readable for previously pinned runs. Its `source_revision: arc:e522fb0e` is **not** proof that the commit contains `.madewell/skills/discovery.md`; its hashes omit `AGENTS.md`. Explicit `--contract contracts/made-well-discovery-v1.json` for a new run emits a legacy provenance warning and does not enforce snapshot freshness; avoid it for new work. Status of existing runs reads their pinned snapshots, not the current files.

## Interactive test laboratory

On your M5, keep the existing `ssh -N -L 18787:127.0.0.1:8787 hive` tunnel open and visit **http://127.0.0.1:18787/lab/**. This is a *clickable*, synthetic sandbox, not a screenshot or the real Discovery run. It uses `~/.local/state/pipeline-observer-lab/runs.sqlite`; its mutation API cannot select a production run. You can create Empty, Preflight, Deep-comb (E04 blocked) and Review Gate scenarios, select any marker, edit its JSON value and evidence pointer, configure deep-comb before its classification settles, append operation traces and measurements, replay each event with the timeline slider, and reset the sandbox. A deliberately seeded deep-comb scenario has E01/E02 done and E04 blocked; marking E04 satisfied with `{ "simulation": "confirmed in lab" }` and `lab/synthetic-fixture.md#simulation` should release its fan-out gate. *This sandbox verdict is not human confirmation in any real run.* The UI only edits synthetic claims; validators can reject invalid transitions. The synthetic fixture pointer is a labeled placeholder, never source evidence.

The real, **read-only** candidate-first observer is at http://127.0.0.1:18787/ and shows `mw-discovery-0902-live-v2` separately. Its recorded eleven candidates are available, but its full post-candidate review/publication protocol is not complete; source pointers and actions are reported, not independently captured or certified. No lab action writes to Arc, the real run, or the transcript corpus. HTTP lab writes require a same-origin localhost Origin, JSON, and a custom lab header; loopback users sharing the server may still operate the synthetic sandbox. Use `systemctl --user stop pipeline-observer.service` to disable both browser surfaces temporarily.

## Command example

```sh
pipeline-observer start /absolute/path/to/source-transcript.md --id discovery-001 --mode live
pipeline-observer mark discovery-001 A02 --status satisfied --value '{"ground":"on"}' --evidence 'discovery-001:declaration'
pipeline-observer mark discovery-001 A03 --status satisfied --value '{"rack":"loaded"}' --evidence '.madewell/stock/'
pipeline-observer status discovery-001 --detail

# Once classification indicates a high-density multi-topic input (before E markers settle):
pipeline-observer configure discovery-001 deep_comb true

# A recorded operation/result, separate from a marker verdict:
pipeline-observer trace discovery-001 D05 classify_maturity \
  --inputs '{"source":"/absolute/path/to/source-transcript.md"}' \
  --outputs '{"maturity":"IDEATION"}' --result 'classified' --evidence 'source:segment-2'
pipeline-observer mark discovery-001 D05 --status satisfied \
  --value '{"maturity":"IDEATION"}' --evidence 'source:segment-2'

# Explicit conditional branch (only if contract permits it for this run):
pipeline-observer mark discovery-001 I02 --status satisfied_by_rule \
  --value '{"rule":"not a PRD/compression document"}' --evidence 'I01:classification'

pipeline-observer measure discovery-001 source_spans_read 8 10 \
  --denominator-label 'indexed source spans' --method 'source span inventory' --evidence 'corpus/index.md#spans'
pipeline-observer status discovery-001 --events
pipeline-observer serve --port 8787
# On the VPS: ssh -L 8787:127.0.0.1:8787 vps ; open http://127.0.0.1:8787/
```

Use `pipeline-observer status --json discovery-001` for programmatic inspection. Supported marker statuses: `pending`, `in_progress`, `blocked`, `failed`, `satisfied`, `satisfied_by_rule`. A settled marker cannot be overwritten silently; `--revise` makes an append-only correction event. `mark` requires evidence for settlement. Events expose actor-reported inputs/outputs and must **not** include secrets or raw transcripts. The dashboard is read-only and escapes untrusted text. Local users on the VPS can access the unauthenticated loopback dashboard: do not forward its port publicly. Source pointers and reported evidence may still be sensitive.

## Gates and limits

- All 72 markers exist in every run; variable numbers of findings, topics and slice readers are recorded inside their markers and event traces. `done/72` is fixed by the pinned definition; bypass only counts with exact contract rule and evidence.
- Publication (`M07`) is refused until every upstream marker (`A` through `M06`, including conditionals) settles; `M03` requires draft/reflection and a `confirmed` or `unavailable` outcome. If unavailable, the stock output must carry an `open_question`, never synthetic confirmation. Ground in blind mode and prohibited context reads cannot be marked performed.
- `measure` records a named, evidence-backed numerator and a defensible denominator with a stated collection method; unknown/zero denominator yields no metric percentage. Metrics never affect fixed-marker progress. Later measurements append corrections instead of rewriting earlier values.
- The CLI checks shape, dependency states, restricted bypasses, required evidence, and a few high-risk review gates. **It does not independently inspect every source citation, prove all six finding fields, authenticate a human ruling, or physically write stock**; those assertions must be checked by review or additional validators. Passing 100% means all marker claims were *recorded*, not that a human certified the discovery's quality. Work remains unverified until its outputs are reviewed.
- Start mode is selected before the input is read. Branch options (`paired`, `deep_comb`, `prd`, `trade`, `in_flight`, `live_conversation`) may be configured **after** classification, before affected markers settle. A blind paired source must be explicitly certified as primary at creation. No option change can rewrite a branch already claimed complete.
- The built-in defaults are those documented in `../RESOLUTION_PROPOSAL.md`, accepted for this prototype by the request to proceed. `build_contract.py` verifies both frozen file digests and re-renders v2 in memory to detect changed sources or marker inventory; it never rewrites either file. If Made Well's source instructions change, review and create a **new contract version**, not a silent rewrite of a frozen file or existing runs.

## Offline verification

```sh
cd ~/projects/discovery-contract-design/runtime
python3 build_contract.py
python3 -m unittest -v test_durable
```

Tests use isolated temporary SQLite homes; they cover v2 snapshot hashes and missing/mismatched source refusal, builder freeze guards for both versions, v1 pinning, fixed denominator across variants, prohibited blind reads, branch changes, operator gating, full 72-marker fixture, read-only HTTP projection and revision trace. The full fixture uses **synthetic reported evidence**; it tests machinery, not a real Made Well analysis.
