# Offline Arena Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline-first Campus Conquest match arena with official-engine parity, configurable timing, CLI/JSON automation, a local browser dashboard, replay inspection, and agent-facing usage documentation.

**Architecture:** Keep the extracted official development tools immutable under `vendor/official`, and implement a separate `arena` package that adapts the official runner. All CLI and browser operations call the same services and store reproducible runs in SQLite plus replay/telemetry files.

**Tech Stack:** Python 3.12 standard library, official Python engine/runner, SQLite, vanilla HTML/CSS/JavaScript, unittest.

**Spec:** User requirements in the active conversation; no standalone design specification by explicit user request.

## Global Constraints

- Never reimplement game rules that the official engine already supplies.
- Strict mode must preserve official subprocess timing and replay semantics.
- Timing modes are `strict`, `observe`, and `off`; every mode retains a safety timeout.
- Official and custom rulesets must never be mixed in reporting.
- The web server binds to loopback by default.
- Core usage must work without third-party runtime dependencies.
- Original PDF and ZIP files remain unchanged.
- Final documentation must include a Codex/Claude-oriented Markdown guide.

## Review Focus

- A bot that never prints `END` must stop at the configured strict or safety deadline without hanging the arena.
- Observe mode must record a budget violation while allowing an otherwise valid late response.
- Side-swapped series must pair the same seed and aggregate from bot identity rather than team letter.
- Invalid paths or malformed JSON must fail before starting any bot process.
- Browser API requests must not permit arbitrary filesystem reads outside registered artifacts.

---

### Task 1: Official Tool Setup and Configuration Core

**Files:**
- Create: `.gitignore`, `pyproject.toml`, `scripts/setup_official.py`
- Create: `arena/__init__.py`, `arena/config.py`, `arena/models.py`
- Test: `tests/test_setup_and_config.py`

**Interfaces:**
- Produces: `ArenaConfig`, `TimingConfig`, `GamePlan`, `load_run_config(path)`, `resolve_official_root()`.

- [ ] Write failing tests for safe ZIP extraction, official-root validation, defaults, official override rejection, and custom labeling.
- [ ] Run the tests and confirm failures are caused by missing production modules.
- [ ] Implement the smallest setup and configuration core that passes the tests.
- [ ] Run the task tests and full suite.
- [ ] Commit the task.

### Task 2: Timing Drivers and Official Match Adapter

**Files:**
- Create: `arena/timing.py`, `arena/official_adapter.py`
- Test: `tests/fixtures/bots/*.py`, `tests/test_timing_and_match.py`

**Interfaces:**
- Consumes: configuration models from Task 1.
- Produces: `run_official_match(config, bot_y, bot_k, seed) -> MatchOutcome` and per-turn telemetry.

- [ ] Write failing tests for strict parity, observe late-response continuation, off mode, safety timeout, crash, missing END, and simultaneous failures.
- [ ] Run the tests and confirm expected failures.
- [ ] Implement compatible bot timing drivers and official adapter without editing vendor code.
- [ ] Run official tests, task tests, and full suite.
- [ ] Commit the task.

### Task 3: Registry, Persistence, Series, and CLI

**Files:**
- Create: `arena/bot_registry.py`, `arena/storage.py`, `arena/series.py`, `arena/stats.py`, `arena/cli.py`, `arena/__main__.py`
- Test: `tests/test_registry_storage_series.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `run_official_match` and Task 1 models.
- Produces: SQLite-backed bot/run APIs, deterministic side-swapped series expansion, aggregate statistics, and JSON/JSONL CLI commands.

- [ ] Write failing tests for registry validation, persistence, side swapping, aggregation by bot identity, resume behavior, JSON stdout, and preflight errors.
- [ ] Run the tests and confirm expected failures.
- [ ] Implement registry, database schema, sequential/parallel series service, statistics, and CLI.
- [ ] Run task tests and full suite.
- [ ] Commit the task.

### Task 4: Local Web Dashboard and Replay Viewer

**Files:**
- Create: `arena/web.py`, `arena/static/index.html`, `arena/static/styles.css`, `arena/static/app.js`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: registry, storage, series service, and replay artifacts.
- Produces: loopback HTTP server, JSON API, run form, results dashboard, and official-replay viewer.

- [ ] Write failing API tests for health, bots, runs, run creation, safe artifact retrieval, and replay response.
- [ ] Run the tests and confirm expected failures.
- [ ] Implement the HTTP API and functional UI using no frontend build step.
- [ ] Load Impeccable new-work and craft-floor guidance immediately before UI edits.
- [ ] Run task tests and full suite; inspect desktop and narrow screenshots once, fix defects in one batch, and confirm once.
- [ ] Commit the task.

### Task 5: Documentation and Handoff

**Files:**
- Create: `README.md`, `docs/USER_GUIDE.md`, `docs/AGENT_GUIDE.md`, `docs/CONFIG_REFERENCE.md`, `docs/ARCHITECTURE.md`
- Modify: `REMOTE_CODEX_HANDOFF.md`
- Test: `tests/test_documented_commands.py`

**Interfaces:**
- Consumes: final CLI and UI behavior.
- Produces: executable setup/usage instructions for humans, Codex, and Claude.

- [ ] Write failing smoke tests for every documented command that can run locally.
- [ ] Run the tests and confirm the missing documentation/commands fail as expected.
- [ ] Write the documentation with copyable noninteractive commands and artifact locations.
- [ ] Run documentation smoke tests and full suite.
- [ ] Commit the task.

### Task 6: End-to-End Verification and Packaging

**Files:**
- Create: `config/arena.default.json`, `config/bots.example.json`
- Modify as required by verified defects only.

**Interfaces:**
- Consumes: the complete system.
- Produces: a verified offline arena ready to copy to the remote PC.

- [ ] Run official self-tests and record exact results.
- [ ] Run the complete Arena test suite.
- [ ] Run a strict example match and compare it with the official runner.
- [ ] Run an observe-mode series with side swapping and inspect stored telemetry.
- [ ] Start the dashboard, exercise its health/API flow, and inspect the rendered UI.
- [ ] Run documented setup and agent commands from a clean temporary workspace.
- [ ] Commit only fixes supported by failing regression tests.

