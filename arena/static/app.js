const state = { bots: [], runs: [], replay: null, turn: 0, latestRun: null };

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || `요청 실패 (${response.status})`);
  return payload;
}

function showView(name) {
  document.querySelectorAll(".view").forEach((node) => node.classList.toggle("is-visible", node.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach((node) => node.classList.toggle("is-active", node.dataset.view === name));
}

function parseSeeds(text) {
  const values = text.split(",").map((value) => Number(value.trim())).filter(Number.isInteger);
  if (!values.length) throw new Error("시드를 하나 이상 입력하세요.");
  return values;
}

async function loadHealth() {
  try {
    await api("/api/health");
    document.querySelector("#health-dot").classList.add("is-ok");
    document.querySelector("#health-text").textContent = "공식 엔진 준비됨";
  } catch (error) {
    document.querySelector("#health-text").textContent = "엔진 확인 실패";
  }
}

async function loadBots() {
  const payload = await api("/api/bots");
  state.bots = payload.bots;
  const options = state.bots.length
    ? state.bots.map((bot) => `<option value="${escapeHtml(bot.id)}">${escapeHtml(bot.name)} · ${escapeHtml(bot.id)}</option>`).join("")
    : `<option value="">등록된 봇 없음</option>`;
  document.querySelector("#bot-a").innerHTML = options;
  document.querySelector("#bot-b").innerHTML = options;
  if (state.bots.length > 1) document.querySelector("#bot-b").selectedIndex = 1;
  document.querySelector("#bot-list").innerHTML = state.bots.length
    ? state.bots.map((bot) => `<div class="bot-row"><strong>${escapeHtml(bot.name)}</strong><code>${escapeHtml(bot.command)}</code><span>${escapeHtml(bot.language)}</span></div>`).join("")
    : `<div class="bot-row"><span>등록된 봇이 없습니다.</span></div>`;
  document.querySelector("#run-message").textContent = state.bots.length > 1 ? "실행 준비가 됐습니다." : "먼저 두 개 이상의 봇을 등록하세요.";
}

async function loadRuns() {
  const payload = await api("/api/runs");
  state.runs = payload.runs;
  const body = document.querySelector("#runs-table");
  body.innerHTML = state.runs.length ? state.runs.map((run) => `
    <tr><td><code>${run.id.slice(0, 10)}</code></td><td>${escapeHtml(run.bot_a)} ↔ ${escapeHtml(run.bot_b)}</td><td>${statusLabel(run.status)}</td><td>${run.official_comparable ? "예" : "아니오"}</td><td><button class="table-action" data-run="${run.id}">열기</button></td></tr>
  `).join("") : `<tr><td colspan="5">실행 기록이 없습니다.</td></tr>`;
  if (state.runs.length) {
    state.latestRun = state.runs[0].id;
    document.querySelector("#latest-run").textContent = state.runs[0].id.slice(0, 12);
    document.querySelector("#latest-status").textContent = statusLabel(state.runs[0].status);
  }
}

async function openRun(runId) {
  const payload = await api(`/api/runs/${runId}`);
  const matches = payload.matches;
  document.querySelector("#latest-games").textContent = String(matches.length);
  document.querySelector("#run-detail").innerHTML = `
    <div class="section-heading"><h2>${escapeHtml(payload.run.bot_a)} 대 ${escapeHtml(payload.run.bot_b)}</h2><p>${matches.length}경기 · ${statusLabel(payload.run.status)}</p></div>
    ${matches.map((match) => `<div class="match-row"><code>#${match.job_index} · S${match.seed}</code><strong>${escapeHtml(match.bot_y)} ${match.result.score.Y} : ${match.result.score.K} ${escapeHtml(match.bot_k)}</strong><span>${match.result.winner === "DRAW" ? "무승부" : `${match.result.winner} 승`}</span><button data-replay-run="${runId}" data-replay-index="${match.job_index}">리플레이</button></div>`).join("")}
  `;
  showView("results");
}

async function openReplay(runId, index) {
  state.replay = await api(`/api/runs/${runId}/replays/${index}`);
  state.turn = 0;
  renderReplay();
  document.querySelector("#replay-empty").hidden = true;
  document.querySelector("#replay-data").hidden = false;
  showView("replay");
}

function renderMap() {
  const map = document.querySelector("#game-map");
  const replay = state.replay;
  const snapshot = replay && state.turn > 0 ? replay.turns[state.turn - 1].state : null;
  const buildings = new Map((replay?.map.buildings || []).map((building) => [`${building.x},${building.y}`, building]));
  const ownership = new Map((snapshot?.buildings || []).map((building) => [building.id, building.owner]));
  const units = new Map();
  (snapshot?.units || []).forEach(([team, kind, x, y, count]) => {
    const key = `${x},${y}`;
    if (!units.has(key)) units.set(key, []);
    units.get(key).push({ team, kind, count });
  });
  const terrain = replay?.map.terrain || Array.from({ length: 15 }, () => ".".repeat(15));
  const bases = replay?.map.bases || {};
  const cells = [];
  for (let y = 0; y < 15; y += 1) {
    for (let x = 0; x < 15; x += 1) {
      const key = `${x},${y}`;
      const building = buildings.get(key);
      const classes = ["map-cell"];
      if (terrain[y]?.[x] === "#") classes.push("obstacle");
      if (building) classes.push("building", `owner-${(ownership.get(building.id) || "n").toLowerCase()}`);
      if (bases.Y?.[0] === x && bases.Y?.[1] === y) classes.push("base-y");
      if (bases.K?.[0] === x && bases.K?.[1] === y) classes.push("base-k");
      const pieces = (units.get(key) || []).map((unit) => `<span class="unit ${unit.team.toLowerCase()}">${unit.kind}${unit.count}</span>`).join("");
      cells.push(`<span class="${classes.join(" ")}" aria-label="${x},${y}">${pieces}</span>`);
    }
  }
  map.innerHTML = cells.join("");
}

function renderReplay() {
  renderMap();
  const replay = state.replay;
  document.querySelector("#turn-output").value = `T ${state.turn}`;
  if (!replay) return;
  const entry = state.turn > 0 ? replay.turns[state.turn - 1] : null;
  document.querySelector("#map-caption").textContent = `Seed ${replay.seed} · ${replay.teams.Y.name} 대 ${replay.teams.K.name}`;
  document.querySelector("#replay-summary").innerHTML = `<strong>${escapeHtml(replay.teams.Y.name)} vs ${escapeHtml(replay.teams.K.name)}</strong><span>Seed ${replay.seed}</span><span>${replay.result.winner === "DRAW" ? "무승부" : `${replay.result.winner} 승`}</span>`;
  document.querySelector("#event-log").textContent = entry ? JSON.stringify({ commands: entry.commands, events: entry.events, state: entry.state }, null, 2) : "초기 배치";
}

function statusLabel(status) {
  return ({ running: "진행 중", completed: "완료", failed: "실패", cancelled: "취소" })[status] || status;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
document.querySelector("#refresh-all").addEventListener("click", async () => { await Promise.all([loadHealth(), loadBots(), loadRuns()]); });
document.querySelector("#run-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#run-message");
  try {
    message.textContent = "실행을 등록하는 중입니다.";
    const payload = {
      bot_a: document.querySelector("#bot-a").value,
      bot_b: document.querySelector("#bot-b").value,
      seeds: parseSeeds(document.querySelector("#seeds").value),
      repetitions: Number(document.querySelector("#repetitions").value),
      jobs: Number(document.querySelector("#jobs").value),
      max_turns: Number(document.querySelector("#max-turns").value),
      swap_sides: document.querySelector("#swap-sides").checked,
      timing: {
        mode: document.querySelector('input[name="timing"]:checked').value,
        first_turn_ms: Number(document.querySelector("#first-turn-ms").value),
        turn_ms: Number(document.querySelector("#turn-ms").value),
        safety_timeout_ms: Number(document.querySelector("#safety-ms").value),
      },
    };
    const result = await api("/api/runs", { method: "POST", body: JSON.stringify(payload) });
    state.latestRun = result.run_id;
    message.textContent = `실행 ${result.run_id.slice(0, 10)}이 시작됐습니다.`;
    await loadRuns();
  } catch (error) { message.textContent = error.message; }
});
document.querySelector("#bot-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#bot-message");
  try {
    await api("/api/bots", { method: "POST", body: JSON.stringify({
      id: document.querySelector("#bot-id").value,
      name: document.querySelector("#bot-name").value,
      command: document.querySelector("#bot-command").value,
      working_dir: document.querySelector("#bot-cwd").value,
      language: document.querySelector("#bot-language").value,
    }) });
    message.textContent = "봇을 저장했습니다.";
    await loadBots();
  } catch (error) { message.textContent = error.message; }
});
document.addEventListener("click", (event) => {
  const runButton = event.target.closest("[data-run]");
  const replayButton = event.target.closest("[data-replay-run]");
  if (runButton) openRun(runButton.dataset.run).catch(console.error);
  if (replayButton) openReplay(replayButton.dataset.replayRun, replayButton.dataset.replayIndex).catch(console.error);
});
document.querySelector("#open-latest").addEventListener("click", () => state.latestRun && openRun(state.latestRun));
document.querySelector("#prev-turn").addEventListener("click", () => { if (state.replay) { state.turn = Math.max(0, state.turn - 1); renderReplay(); } });
document.querySelector("#next-turn").addEventListener("click", () => { if (state.replay) { state.turn = Math.min(state.replay.turns.length, state.turn + 1); renderReplay(); } });

renderMap();
Promise.all([loadHealth(), loadBots(), loadRuns()]).catch(console.error);

