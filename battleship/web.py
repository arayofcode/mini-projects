"""Browser UI for Battleship. Run from the project root: python web.py"""

import json
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from src.battleship.board import (
    Board,
    Direction,
    InvalidBoardSize,
    InvalidPlacement,
    InvalidShot,
    LowShipNumber,
    ShipAlreadyPresent,
    ShotTakenAlready,
    TooManyShip,
)
from src.battleship.game import Game, GameEnded, GameStatus, InvalidGameState
from src.battleship.player import Player
from src.battleship.ship import Ship, ShipType

PORT = 8000
DECLARED_ERRORS = (
    InvalidBoardSize,
    InvalidPlacement,
    InvalidShot,
    ShipAlreadyPresent,
    ShotTakenAlready,
    TooManyShip,
    LowShipNumber,
    GameEnded,
    InvalidGameState,
)


class Session:
    n: int = 0
    game: Game | None = None
    last_result: Any = None


session = Session()


def grid(board: Board, n: int, reveal_ships: bool) -> list[list[str]]:
    def cell_state(cell: tuple[int, int]) -> str:
        has_ship = cell in board.cell_to_ship
        if cell in board.shots:
            return "hit" if has_ship else "miss"
        return "ship" if reveal_ships and has_ship else ""

    return [[cell_state((r, c)) for c in range(n)] for r in range(n)]


def new_game(n: int, name1: str, name2: str) -> Game:
    return Game(n, name1, name2)


def view(me: Player, opp: Player) -> dict[str, Any]:
    game = session.game
    assert game is not None
    phases = {
        GameStatus.SHIP_PLACEMENT: "placing",
        GameStatus.IN_PROGRESS: "playing",
        GameStatus.COMPLETED: "over",
    }
    return {
        "phase": phases[game.status],
        "n": session.n,
        "viewer": me.name,
        "opponent": opp.name,
        "to_place": me.board.max_ships,
        "ship_len": Ship.size,
        "winner": game.winner.name if game.winner else None,
        "last_result": str(session.last_result),
        "own": grid(me.board, session.n, reveal_ships=True),
        "enemy": grid(opp.board, session.n, reveal_ships=False),
    }


def current_view() -> dict[str, Any]:
    game = session.game
    if game is None:
        return {"phase": "setup"}
    return view(game.currentPlayer, game.opp)


def start(body: dict[str, Any]) -> dict[str, Any]:
    n = int(body["n"])
    session.n = n
    session.last_result = None
    session.game = new_game(n, body.get("p1") or "P1", body.get("p2") or "P2")
    return current_view()


def place(body: dict[str, Any]) -> dict[str, Any]:
    game = session.game
    assert game is not None
    player = game.currentPlayer
    types = list(ShipType)
    fleet: dict[Ship, tuple[tuple[int, int], Direction]] = {}
    for i, entry in enumerate(body["ships"]):
        ship = Ship()
        ship.id = f"{player.name}-{i}"
        ship.type = types[i % len(types)]
        direction = Direction.HORIZONTAL if entry["dir"] == "h" else Direction.VERTICAL
        fleet[ship] = ((int(entry["row"]), int(entry["col"])), direction)
    game.place_ships(fleet)
    return current_view()


def shoot(body: dict[str, Any]) -> dict[str, Any]:
    game = session.game
    assert game is not None
    shooter, target = game.currentPlayer, game.opp
    session.last_result = game.turn((int(body["row"]), int(body["col"])))
    return {**view(shooter, target), "turn_ended": game.currentPlayer is not shooter}


ROUTES = {"/start": start, "/place": place, "/shoot": shoot}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def do_GET(self) -> None:
        if self.path == "/state":
            self._run(current_view)
        else:
            self._send(200, PAGE.encode(), "text/html")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        self._run(lambda: ROUTES[self.path](body))

    def _run(self, action: Any) -> None:
        try:
            self._send_json(200, action())
        except DECLARED_ERRORS as e:
            self._send_json(400, {"error": str(e)})
        except Exception:  # noqa: BLE001 - show any crash in the page
            trace = traceback.format_exc()
            print(trace)
            self._send_json(500, {"error": trace})

    def log_message(self, format: str, *args: Any) -> None:
        pass


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Battleship</title>
<style>
  :root {
    --paper: #e6edef;
    --ink: #12263a;
    --muted: #46606f;
    --water: #c3d9df;
    --water-hover: #d9eaee;
    --line: #9db9c1;
    --ship: #4a5a68;
    --hit: #e4572e;
    --hit-ink: #a5300d;
    --focus: #1f5fbf;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: clamp(1rem, 4vw, 2.5rem);
    background: var(--paper); color: var(--ink);
    font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  :focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
  header { border-bottom: 1px solid var(--line); padding-bottom: .6rem; margin-bottom: 1.6rem; }
  header strong {
    font: italic 700 1.25rem/1 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    letter-spacing: .01em;
  }
  h2 {
    margin: 0 0 .25rem;
    font: 600 clamp(1.6rem, 3.4vw, 2.3rem)/1.15 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  }
  h3 { margin: 0 0 .5rem; font-size: 1rem; font-weight: 600; }
  .sub, .legend { margin: 0 0 1rem; color: var(--muted); }
  #msg { min-height: 1.5rem; margin: .4rem 0; color: var(--hit-ink); font-weight: 600; }
  .result { margin: .4rem 0 1rem; font-size: 1.15rem; font-weight: 600; }
  .result.hit, .result.sunk { color: var(--hit-ink); }

  button { font: inherit; cursor: pointer; }
  .primary {
    background: var(--ink); color: var(--paper); border: 0; border-radius: 6px;
    padding: .5rem 1.1rem; font-weight: 600;
  }
  .result .primary { margin-left: .9rem; }
  #again { margin-bottom: 1.4rem; }
  .link { background: none; border: 0; padding: .4rem .2rem; color: var(--ink); text-decoration: underline; }
  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-bottom: 1.2rem; }
  .seg { display: inline-flex; border: 1px solid var(--ink); border-radius: 6px; overflow: hidden; }
  .seg button { background: transparent; color: var(--ink); border: 0; padding: .4rem 1rem; }
  .seg button + button { border-left: 1px solid var(--ink); }
  .seg button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }

  .setup { display: grid; gap: .9rem; max-width: 22rem; }
  .setup label { display: grid; gap: .25rem; font-weight: 600; }
  .setup input {
    font: inherit; padding: .5rem .6rem; border: 1px solid var(--ink); border-radius: 6px;
    background: #f6fafb; color: var(--ink);
  }
  .setup .primary { justify-self: start; margin-top: .4rem; }

  .stage { display: flex; flex-wrap: wrap; gap: 2.5rem; align-items: flex-start; }
  .main { flex: 1 1 min(22rem, 100%); min-width: 0; max-width: clamp(18rem, calc(100vh - 21rem), 34rem); }
  .side { flex: 0 1 15rem; min-width: 0; }

  .board {
    display: grid; gap: 3px; width: 100%;
    grid-template-columns: 1.3rem repeat(var(--n), minmax(0, 1fr));
    align-items: center;
  }
  .axis { text-align: center; font-size: .75rem; color: var(--muted); font-variant-numeric: tabular-nums; }
  .cell {
    position: relative; display: block; width: 100%; aspect-ratio: 1;
    background: var(--water); border: 0; border-radius: 3px; padding: 0;
  }
  button.cell:not(:disabled):hover { background: var(--water-hover); box-shadow: inset 0 0 0 2px var(--ink); }
  button.cell:disabled { cursor: default; }
  .cell.ship { background: var(--ship); }
  .cell.hit { background: var(--hit); }
  .cell.hit::before, .cell.hit::after {
    content: ""; position: absolute; left: 20%; right: 20%; top: calc(50% - 1.5px);
    height: 3px; background: #fff; border-radius: 2px;
  }
  .cell.hit::before { transform: rotate(45deg); }
  .cell.hit::after { transform: rotate(-45deg); }
  .cell.miss::before {
    content: ""; position: absolute; inset: 34%; border-radius: 50%;
    background: #fff; box-shadow: 0 0 0 2px #5e8793;
  }
  .cell.preview { background: #7f95a4; box-shadow: inset 0 0 0 2px var(--ink); }
  .cell.bad { background: #e8b8a8; box-shadow: inset 0 0 0 2px var(--hit-ink); }
  .cell.last { outline: 2px solid var(--ink); outline-offset: 1px; }
  @media (prefers-reduced-motion: no-preference) {
    .cell.last { animation: ping .9s ease-out 1; }
    @keyframes ping {
      from { box-shadow: 0 0 0 0 rgba(228, 87, 46, .75); }
      to { box-shadow: 0 0 0 12px rgba(228, 87, 46, 0); }
    }
  }

  .legend { display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; margin-top: 1.4rem; font-size: .9rem; }
  .legend span { display: inline-flex; align-items: center; gap: .45rem; }
  .legend i { width: .9rem; height: .9rem; border-radius: 3px; display: inline-block; }

  #err {
    display: none; white-space: pre-wrap; margin-top: 1.5rem; padding: .8rem;
    background: #3a0d0d; color: #ffd0c4; font: .85rem/1.4 ui-monospace, Menlo, monospace;
  }
  dialog#cover {
    border: 0; padding: 0; width: 100vw; height: 100vh; max-width: none; max-height: none;
    background: var(--ink); color: var(--paper);
  }
  dialog#cover[open] { display: grid; place-content: center; justify-items: center; gap: 1.4rem; text-align: center; }
  dialog#cover p { margin: 0; font: 600 clamp(1.6rem, 5vw, 2.6rem)/1.2 "Iowan Old Style", Palatino, Georgia, serif; }
  dialog#cover .primary { background: var(--paper); color: var(--ink); margin: 0; }
</style></head>
<body>
<header><strong>Battleship</strong></header>
<main id="app"></main>
<pre id="err"></pre>
<dialog id="cover" aria-labelledby="coverText">
  <p id="coverText"></p>
  <form method="dialog"><button class="primary" autofocus>I'm ready</button></form>
</dialog>
<script>
let state = {phase: "setup"};
let dir = "h";
let lastViewer = null;
let afterShot = false;
let lastShot = null;
let pending = [];
let notice = "";

const $ = id => document.getElementById(id);
const WORDS = {"": "water", ship: "your ship", hit: "hit", miss: "miss"};

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} :
    {method: "POST", body: JSON.stringify(body)});
  const data = await res.json();
  if (res.status === 500) { showErr(data.error); throw new Error("server error"); }
  if (res.status === 400) { notice = data.error; return null; }
  $("err").style.display = "none";
  return data;
}

function showErr(text) {
  $("err").textContent = text;
  $("err").style.display = "block";
}

function cover(name) {
  $("coverText").textContent = "Pass the screen to " + name + ".";
  $("cover").showModal();
}
$("cover").addEventListener("cancel", e => e.preventDefault());

function boardHtml(cells, label, mode, lastCell) {
  const n = cells.length;
  let h = `<div class="board" style="--n:${n}" role="group" aria-label="${label}"><span></span>`;
  for (let c = 0; c < n; c++) h += `<span class="axis" aria-hidden="true">${c}</span>`;
  for (let r = 0; r < n; r++) {
    h += `<span class="axis" aria-hidden="true">${r}</span>`;
    for (let c = 0; c < n; c++) {
      const s = cells[r][c];
      const last = lastCell && lastCell.r === r && lastCell.c === c ? " last" : "";
      const name = `Row ${r}, column ${c}, ${WORDS[s]}`;
      if (mode === "view") {
        h += `<span class="cell ${s}${last}" role="img" aria-label="${name}"></span>`;
      } else {
        const off = mode === "shoot" && s !== "" ? " disabled" : "";
        h += `<button type="button" class="cell ${s}${last}" data-r="${r}" data-c="${c}" aria-label="${name}"${off}></button>`;
      }
    }
  }
  return h + "</div>";
}

function withDraft(own, ships, shipLen) {
  const cells = own.map(row => row.slice());
  for (const p of ships) {
    for (let k = 0; k < shipLen; k++) {
      const r = p.row + (p.dir === "v" ? k : 0);
      const c = p.col + (p.dir === "h" ? k : 0);
      if (r >= 0 && r < cells.length && c >= 0 && c < cells.length) cells[r][c] = "ship";
    }
  }
  return cells;
}

function setPreview(r, c, on) {
  document.querySelectorAll("#own .cell.preview, #own .cell.bad")
    .forEach(el => el.classList.remove("preview", "bad"));
  if (!on) return;
  const n = state.n;
  const cells = [];
  for (let k = 0; k < state.ship_len; k++) {
    cells.push([r + (dir === "v" ? k : 0), c + (dir === "h" ? k : 0)]);
  }
  const fits = cells.every(([a, b]) => a >= 0 && a < n && b >= 0 && b < n);
  for (const [a, b] of cells) {
    const el = document.querySelector(`#own .cell[data-r="${a}"][data-c="${b}"]`);
    if (el) el.classList.add(fits ? "preview" : "bad");
  }
}

function render() {
  const s = state;
  const app = $("app");
  if (s.phase === "setup") {
    app.innerHTML = `<form id="setup" class="setup">
      <h2>New game</h2>
      <label>Board size <input id="n" type="number" min="3" max="15" value="5"></label>
      <label>Player 1 <input id="p1" value="Alice"></label>
      <label>Player 2 <input id="p2" value="Bob"></label>
      <button class="primary">Start game</button>
      <p id="msg" role="alert"></p></form>`;
    $("setup").onsubmit = async e => {
      e.preventDefault();
      const data = await api("/start", {n: $("n").value, p1: $("p1").value, p2: $("p2").value});
      if (data) { state = data; lastViewer = data.viewer; pending = []; render(); }
      else { $("msg").textContent = notice; notice = ""; }
    };
    return;
  }

  const placing = s.phase === "placing";
  const over = s.phase === "over";
  const turnPassed = afterShot && s.turn_ended && !over;
  const canShoot = s.phase === "playing" && !turnPassed;

  let head = "";
  if (placing) {
    head = `<h2>${s.viewer}, place your fleet</h2>
      <p class="sub">${pending.length} of ${s.to_place} ships entered. Each ship covers ${s.ship_len} cells.</p>
      <div class="tools">
        <div class="seg" role="group" aria-label="Ship direction">
          <button type="button" id="dh" aria-pressed="${dir === "h"}">Horizontal</button>
          <button type="button" id="dv" aria-pressed="${dir === "v"}">Vertical</button>
        </div>
        <button type="button" id="reset" class="link">Reset fleet</button>
      </div>`;
  } else if (over) {
    head = `<h2>${s.winner} wins</h2>`;
  } else {
    head = `<h2>${s.viewer}, fire at ${s.opponent}'s waters</h2>`;
  }

  let result = "";
  if (afterShot) {
    const base = {HIT: "Hit.", SUNK: "Ship sunk.", MISS: "Miss."}[s.last_result];
    const again = over || turnPassed ? "" : " Shoot again.";
    const action = turnPassed ? `<button id="end" class="primary">End turn</button>` : "";
    result = `<p class="result ${s.last_result.toLowerCase()}" role="status">${base}${again}${action}</p>`;
  }
  if (over) result += `<button id="again" class="primary">New game</button>`;

  let stage;
  if (placing) {
    stage = `<section id="own" class="main"><h3>Your waters</h3>
      ${boardHtml(withDraft(s.own, pending, s.ship_len), "Your waters", "place")}</section>`;
  } else {
    stage = `<section id="enemy" class="main"><h3>${s.opponent}'s waters</h3>
      ${boardHtml(s.enemy, s.opponent + "'s waters", canShoot ? "shoot" : "view", afterShot ? lastShot : null)}</section>
      <section id="own" class="side"><h3>Your fleet</h3>
      ${boardHtml(s.own, "Your waters", "view")}</section>`;
  }

  app.innerHTML = head + `<p id="msg" role="alert"></p>` + result + `<div class="stage">${stage}</div>
    <p class="legend">
      <span><i style="background:var(--ship)"></i>Your ship</span>
      <span><i style="background:var(--hit)"></i>Hit</span>
      <span><i style="background:#fff;box-shadow:0 0 0 2px #5e8793"></i>Miss</span>
    </p>`;
  $("msg").textContent = notice; notice = "";

  if (placing) {
    $("dh").onclick = () => { dir = "h"; render(); };
    $("dv").onclick = () => { dir = "v"; render(); };
    $("reset").onclick = () => { pending = []; render(); };
    document.querySelectorAll("#own button.cell").forEach(b => {
      const row = +b.dataset.r, col = +b.dataset.c;
      b.addEventListener("pointerenter", () => setPreview(row, col, true));
      b.addEventListener("focus", () => setPreview(row, col, true));
      b.addEventListener("pointerleave", () => setPreview(row, col, false));
      b.addEventListener("blur", () => setPreview(row, col, false));
      b.onclick = async () => {
        pending.push({row, col, dir});
        if (pending.length < s.to_place) { render(); return; }
        const data = await api("/place", {ships: pending});
        pending = [];
        if (!data) { render(); return; }
        state = data;
        const switched = data.viewer !== lastViewer;
        lastViewer = data.viewer;
        render();
        if (switched) cover(data.viewer);
      };
    });
  }
  if (canShoot) {
    document.querySelectorAll("#enemy button.cell:not(:disabled)").forEach(b => {
      b.onclick = async () => {
        const row = +b.dataset.r, col = +b.dataset.c;
        const data = await api("/shoot", {row, col});
        if (!data) { render(); return; }
        state = data; afterShot = true; lastShot = {r: row, c: col}; render();
      };
    });
  }
  if ($("end")) {
    $("end").onclick = async () => {
      afterShot = false; lastShot = null;
      state = await api("/state");
      render();
      cover(state.viewer);
    };
  }
  if ($("again")) {
    $("again").onclick = () => {
      state = {phase: "setup"}; pending = []; afterShot = false; lastShot = null;
      render();
    };
  }
}

render();
</script></body></html>
"""


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Battleship running at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
