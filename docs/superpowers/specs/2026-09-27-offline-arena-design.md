# Campus Conquest Offline Arena Design

Date: 2026-09-27
Status: Approved design, pending implementation plan

## 1. Purpose

Build a local, offline-first match environment for Campus Conquest bots that uses the provided official engine and protocol as the source of truth. The environment must serve three users through the same core behavior:

- Humans use a local browser dashboard to register bots, configure matches, inspect results, and replay games.
- Codex and Claude use a stable CLI, JSON configuration, JSON/JSONL output, and machine-readable documentation.
- Training and evaluation systems use programmatic Python interfaces for high-volume experiments while keeping official subprocess evaluation available as the fairness reference.

The arena must make timing behavior configurable without corrupting official results. It must support strict competition timing, timing observation without competitive forfeits, and research runs where competition timing is disabled but a separate safety timeout still prevents hung processes.

## 2. Success Criteria

The implementation is successful when all of the following are true:

1. A provided Python or C++ bot can play a single match from the CLI.
2. The same match can be configured and launched from the browser dashboard.
3. Strict mode produces the same game result and deterministic replay as the provided official runner for the same bots, seed, and official configuration.
4. Observe mode records first-turn and normal-turn latency violations without forfeiting solely because the competition budget was exceeded.
5. Off mode ignores competition budgets but still terminates a hung bot using a separately configured safety timeout.
6. Multi-seed series can swap sides, run in parallel, aggregate results, and be reproduced from a saved run configuration.
7. Every result is labeled as official-comparable or experimental.
8. Codex or Claude can discover commands through `--help`, submit JSON configuration, receive JSON output, and locate replays and telemetry without parsing human prose.
9. A human can inspect win rates, side bias, score margins, forfeits, latency, and individual replays in a local browser.
10. Automated tests cover rules integration, timing boundaries, failure modes, storage, CLI, API, and a browser smoke path.

## 3. Non-Goals for the Initial Version

- Reimplementing the official game engine.
- Building the reinforcement-learning trainer itself.
- Providing a public or remotely exposed web service.
- Running untrusted third-party bots with strong OS-level sandboxing.
- Reproducing the competition server's memory, process-count, and CPU isolation guarantees.
- Editing or repackaging the original PDF and ZIP archives.
- Live visualization of every turn while a match is still running. The initial UI reports job progress and opens the completed replay. Turn-streaming may be added later without changing the core interfaces.

## 4. Authoritative Inputs

The source precedence is:

1. `깃발대항전_게임규칙서.pdf`
2. `yk-development-tools.zip` documentation and official engine behavior
3. Official starter kit and examples
4. Arena documentation and implementation

The original archives remain unchanged. `yk-development-tools.zip` is extracted into `vendor/official/` during project setup. Arena code imports and delegates to that copy but does not edit files below `vendor/official/`.

If the PDF, documentation, tests, and engine disagree, development stops at that discrepancy. A minimal reproduction and evidence are recorded instead of silently choosing a behavior.

## 5. Architectural Decision

Use an adapter architecture around the official engine and match orchestrator.

```text
vendor/official (immutable reference)
        |
        v
arena.core
  - bot registry
  - run configuration
  - timing policy adapters
  - official match adapter
  - series/tournament scheduler
  - aggregation and storage
        |
        +-------------------+
        |                   |
        v                   v
arena.cli              arena.web
JSON/JSONL             localhost dashboard
agents/automation      humans
```

All entry points call `arena.core`; the web application does not duplicate match logic. Timing telemetry is stored outside official replay JSON so wall-clock values do not destroy deterministic replay equality.

## 6. Proposed Repository Layout

```text
CTF/
├── arena/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── bot_registry.py
│   ├── timing.py
│   ├── official_adapter.py
│   ├── match_service.py
│   ├── series_service.py
│   ├── tournament_service.py
│   ├── scheduler.py
│   ├── storage.py
│   ├── stats.py
│   ├── web.py
│   └── static/
├── config/
│   ├── arena.default.json
│   └── bots.example.json
├── docs/
│   ├── AGENT_GUIDE.md
│   ├── USER_GUIDE.md
│   ├── CONFIG_REFERENCE.md
│   ├── ARCHITECTURE.md
│   └── superpowers/
├── scripts/
│   └── setup_official.py
├── tests/
│   ├── fixtures/bots/
│   ├── test_official_parity.py
│   ├── test_timing_modes.py
│   ├── test_match_service.py
│   ├── test_series_service.py
│   ├── test_storage.py
│   ├── test_cli.py
│   ├── test_web_api.py
│   └── test_browser_smoke.py
├── vendor/
│   └── official/
├── workspace/
│   ├── arena.sqlite3
│   ├── replays/
│   ├── telemetry/
│   ├── logs/
│   └── exports/
├── README.md
└── pyproject.toml
```

Runtime data under `workspace/` is ignored by Git except for a placeholder and optional example data.

## 7. Official Match Adapter

`arena.official_adapter` loads the official balance configuration, constructs official bot drivers, and calls the provided `runner.run_match()` function. It must not reproduce map generation, command parsing, turn ordering, combat, capture, building effects, information reveal, or victory calculation.

For official strict mode, the adapter uses the provided `SubprocessBot` behavior without semantic changes. It may wrap the object to collect metadata, but the match input, output, deadlines, error statuses, and replay must remain unchanged.

For observe and off modes, Arena supplies a compatible bot driver implementing the interface expected by `run_match()`:

- `send_init(text)`
- `send_turn(text, timeout_s)`
- `collect_turn()`
- `close()`
- `name` and `dead`

This keeps the official orchestrator and engine while changing only how process deadlines are interpreted.

## 8. Timing Modes

### 8.1 Strict

- Competition first-turn and normal-turn budgets are enforced.
- Timeout, crash, invalid output, and missing `END` follow official forfeit behavior.
- Default budgets are first turn 3000ms and normal turn 300ms.
- The first-turn budget includes process startup, INIT transfer, initialization, and first response, matching the official driver.

### 8.2 Observe

- The same competition budgets are recorded as thresholds.
- Exceeding a threshold records a violation but does not by itself cause a forfeit.
- Crash, process exit, invalid UTF-8, missing `END`, and exceeding the safety timeout remain failures.
- Actual elapsed time is recorded for every turn.

### 8.3 Off

- Competition budgets do not affect results and are not reported as violations.
- Actual elapsed time is still measured for profiling.
- The safety timeout remains active.

### 8.4 Safety Timeout

Every mode has a positive safety timeout independent of competition budgets. Its purpose is process recovery, not competitive scoring. In strict mode it must be greater than or equal to the active competition deadline; in observe and off modes it may be much larger.

### 8.5 Telemetry

Telemetry is written to a separate record containing:

- run ID and match ID
- team and bot ID
- turn number
- whether this was the first turn
- competition budget, when applicable
- elapsed milliseconds
- competition violation flag
- terminal status
- process exit information when available

Telemetry is not added to official replay JSON.

## 9. Configuration Model

Arena accepts a versioned JSON run configuration. CLI flags override the JSON for one invocation, and the fully resolved configuration is saved with the run.

Core fields include:

```json
{
  "schema_version": 1,
  "kind": "series",
  "ruleset": {
    "mode": "official",
    "balance_overrides": {}
  },
  "timing": {
    "mode": "observe",
    "first_turn_ms": 3000,
    "turn_ms": 300,
    "safety_timeout_ms": 60000
  },
  "execution": {
    "mode": "subprocess",
    "jobs": 4,
    "on_bot_error": "forfeit"
  },
  "games": {
    "seeds": [0, 1, 2],
    "swap_sides": true,
    "repetitions": 1,
    "max_turns": 160
  },
  "bots": {
    "a": "bot-id-a",
    "b": "bot-id-b"
  },
  "artifacts": {
    "replay_policy": "all",
    "capture_stderr": true
  }
}
```

`ruleset.mode` is either `official` or `custom`. Official mode rejects balance overrides. Custom mode deep-merges validated overrides into an in-memory copy of the official balance configuration and permanently labels the run `experimental` and `official_comparable=false`.

Subprocess execution is the only official-comparable execution mode. In-process adapters may be added for training throughput, but their results are labeled experimental.

## 10. Bot Registry

Each bot has a stable ID and a versioned registration record:

- display name
- command and arguments
- working directory
- optional safe environment overrides
- language tag
- source/version label
- notes
- creation and update timestamps

Commands are local and trusted. The dashboard displays a warning that Arena is not a security sandbox. Secrets are not accepted in bot records. Environment inheritance is minimized, and arbitrary environment values are never printed in reports.

The registry supports add, update, list, show, validate, and remove operations. Removing a bot registration does not delete historical match records.

## 11. Match, Series, and Tournament Services

### 11.1 Match

Runs one seed with fixed sides. It produces an official replay, result record, telemetry, and logs according to artifact policy.

### 11.2 Series

Expands seeds, repetitions, and optional side swapping into deterministic match jobs. Job identity is derived from the resolved run configuration plus the job index. A resumed series skips completed jobs and reruns failed or explicitly selected jobs.

Aggregates include:

- win/draw/loss counts and rates
- score and score-margin distributions
- occupation-turn and surviving-unit tiebreak values when available
- side-specific performance
- forfeit causes
- latency percentiles and budget-violation counts
- per-seed paired results when sides are swapped

### 11.3 Tournament

The initial tournament format is round robin. It reuses series scheduling for every bot pair. Brackets and rating systems are deferred until round-robin behavior is reliable.

## 12. Scheduler and Concurrency

The scheduler uses local worker processes for match isolation. Each worker runs complete matches; two workers never share a live bot process. The configured `jobs` value is capped by validation and can be set to one for deterministic troubleshooting.

The parent process owns run state and persistent writes. Workers return structured match results and artifact paths. SQLite writes are serialized through the parent to avoid lock contention.

Cancellation stops scheduling new matches, terminates active bot processes, and marks unfinished jobs as cancelled. Completed results remain available and a cancelled run can be resumed.

## 13. Persistence

SQLite stores normalized metadata:

- schema version
- bots and bot versions
- runs and resolved configurations
- match jobs and status
- results and aggregate statistics
- timing telemetry summaries
- artifact paths

Large or append-heavy content remains in files:

- official replay JSON
- optional per-turn telemetry JSONL
- captured stderr
- exported result bundles

Writes use temporary files followed by atomic rename. Database migrations are explicit and tested. Arena refuses to open a database with a newer unsupported schema version.

## 14. CLI Contract

The executable interface is `python -m arena`, with an optional installed `arena` command.

Initial commands:

```text
arena doctor
arena bots add|list|show|validate|remove
arena match
arena series
arena tournament
arena runs list|show|cancel|resume|export
arena replay inspect
arena serve
```

Agent-facing conventions:

- `--config PATH` accepts JSON configuration.
- `--json` emits one JSON result to stdout.
- `--jsonl` emits progress and results as JSON Lines.
- Human diagnostics and progress go to stderr.
- Exit code 0 means the requested Arena operation completed, even if a bot lost normally.
- Nonzero codes distinguish invalid configuration, missing bot, Arena internal failure, interrupted run, and failed requested validation.
- Schema version and stable machine-readable error codes are present in JSON errors.
- Relative artifact paths are resolved against the saved run directory and returned as absolute paths in CLI output.

CLI help contains copyable examples. Commands have noninteractive forms and never require prompts when JSON mode is active.

## 15. Local Web Dashboard

The dashboard binds to loopback by default and must not expose itself to the network unless a future explicit option is designed and reviewed.

Initial views:

1. Bots: register, validate, edit, and inspect bot commands.
2. New Run: choose bots, match type, seeds, side swapping, timing policy, concurrency, ruleset, and artifact policy.
3. Runs: see queued, running, completed, failed, cancelled, and resumable runs.
4. Results: compare aggregate statistics and filter individual matches.
5. Replay: render the map and step through commands, events, units, buildings, resources, revealed scores, and result.
6. Settings: inspect workspace paths and official-tool validation status.

The frontend is static HTML, CSS, and JavaScript served by the local Python application. The initial implementation avoids a JavaScript build toolchain. The backend uses Python standard-library HTTP and JSON capabilities unless implementation planning identifies a clear reliability gap that justifies a local-only dependency.

The web API is a thin adapter over Arena Core. It never calls the official engine directly.

## 16. Replay Viewer

The viewer consumes the official replay schema without mutating it. It shows:

- terrain, bases, buildings, and scores from the spectator map
- units by team and kind
- resources and occupation-turn values
- raw commands and parsed commands
- combat, capture, and building events
- turn navigation, play/pause, and speed selection
- final winner, reason, tiebreak information, and forfeits

Unknown event types are displayed as structured JSON rather than discarded, preserving forward compatibility.

## 17. Failure Handling

Arena distinguishes:

- bot timeout or safety timeout
- bot crash
- invalid or incomplete output
- official runner or transport error
- invalid Arena configuration
- corrupt replay or persistence failure
- user cancellation

Bot failures affect match results according to the selected policy. Arena infrastructure failures never masquerade as a bot forfeit. Partial files are cleaned or marked incomplete. A failed match stores enough context to reproduce it without exposing the host environment.

If both bots fail in the same strict turn, the official simultaneous-error result is preserved.

## 18. Correctness and Test Strategy

### 18.1 Official Baseline

- Run all provided official self-tests and submission tests before Arena integration.
- Preserve a record of the official package checksum.

### 18.2 Strict Parity

For fixed seeds and deterministic fixture bots, compare official CLI output with Arena strict mode:

- winner and reason
- score and turns
- forfeit structure
- full replay JSON
- deterministic replay hash

### 18.3 Differential Coverage

Run parity across many seeds, both sides, and fixture strategies. The test suite includes no-op, valid greedy, invalid-command, crash, missing-END, slow-first-turn, slow-normal-turn, and dual-failure bots.

### 18.4 Timing Tests

Use controlled fixture bots with generous margins around deadlines rather than tests that depend on one-millisecond scheduler precision. Verify strict, observe, off, and safety-timeout semantics separately.

### 18.5 Configuration Tests

- Official mode rejects balance overrides.
- Custom mode labels results experimental.
- Resolved configurations are stable and serializable.
- Invalid or unsafe values fail before any bot starts.

### 18.6 End-to-End Tests

- CLI single match and series
- JSON/JSONL schemas
- cancellation and resume
- database reopen and migration
- web API lifecycle
- browser smoke test for creating a run and opening a replay

### 18.7 Cross-Platform Verification

Run fixed-seed strict parity tests on macOS and the remote PC. Game results and replay hashes must match. Timing values are expected to differ.

## 19. Documentation Deliverables

Documentation is part of the product and is required before completion.

### `README.md`

Short project overview, prerequisites, setup, first match, first series, and dashboard launch.

### `docs/USER_GUIDE.md`

Human-oriented instructions for bot registration, timing modes, official versus custom runs, series, tournaments, results, and replay inspection.

### `docs/AGENT_GUIDE.md`

Codex/Claude handoff containing:

- project architecture and source-of-truth rules
- setup and health-check commands
- complete CLI command patterns
- JSON and JSONL contracts
- where configurations, results, telemetry, logs, and replays live
- how to add and validate a bot
- how to run and compare models reproducibly
- prohibited shortcuts, especially modifying official engine behavior
- troubleshooting decision tree
- safe task prompts that an agent can execute without interactive input

### `docs/CONFIG_REFERENCE.md`

Every configuration field, default, validation rule, interaction, and official-comparability effect.

### `docs/ARCHITECTURE.md`

Component boundaries, data flow, persistence schema, timing behavior, and extension points.

`REMOTE_CODEX_HANDOFF.md` is updated after implementation to point to `docs/AGENT_GUIDE.md` and give the remote machine the exact setup and verification sequence.

## 20. Security and Trust Boundary

Arena is an offline development tool, not a hostile-code sandbox. Only trusted bot commands are run. The web server binds to `127.0.0.1` by default. The API rejects arbitrary filesystem browsing and uses IDs for stored resources.

The project does not implement or encourage access to private competition APIs, opponent commands before resolution, or any unauthorized service. Testing remains within the provided local engine and protocol.

## 21. Portability

The core targets Python 3.12 to match the competition environment while remaining usable on the available macOS and remote-PC development environments. The initial core prefers the Python standard library. Optional development dependencies are isolated from submission bots and documented separately.

Bot commands may target Python or compiled C++ executables. Platform-specific command details live in bot registrations rather than match configuration.

## 22. Implementation Boundaries

Implementation proceeds in independently verifiable increments:

1. Repository and immutable official-tool setup.
2. Strict single-match adapter with official parity tests.
3. Timing policy drivers and telemetry.
4. Bot registry and versioned configuration.
5. SQLite persistence and artifact layout.
6. Series scheduler, side swapping, concurrency, cancellation, and resume.
7. Statistics and exports.
8. CLI completion.
9. Local web API and dashboard.
10. Replay viewer.
11. Round-robin tournaments.
12. Cross-platform verification and documentation.

No later layer may compensate for a parity failure in an earlier layer. Strict official parity is the gate for series, UI, and training integration.

