"""Browser UI for Connect Four. Run from the project root: python web.py"""

import json
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from src.connect_four.board import Board, ColumnFull, DiscColor, InvalidColumn
from src.connect_four.game import Game, GameOver, GameState, SameColor
from src.connect_four.player import Player

PORT = 8001
DECLARED_ERRORS = (InvalidColumn, ColumnFull, GameOver, SameColor)


class Session:
    game: Game | None = None


session = Session()


def grid(board: Board) -> list[list[str]]:
    def cell_state(row: int, col: int) -> str:
        disc = board.get_cell(row, col)
        return disc.value if disc else ""

    return [[cell_state(r, c) for c in range(board.cols)] for r in range(board.rows)]


def current_view() -> dict[str, Any]:
    game = session.game
    if game is None:
        return {"phase": "setup"}
    over = game.get_game_state() != GameState.IN_PROGRESS
    current = game.get_current_player()
    winner = game.get_winner()
    return {
        "phase": "over" if over else "playing",
        "grid": grid(game.board),
        "current": current.get_name(),
        "color": current.get_color().value,
        "state": game.get_game_state().name,
        "winner": winner.get_name() if winner else None,
        "draw": game.get_game_state() == GameState.DRAW,
    }


def start(body: dict[str, Any]) -> dict[str, Any]:
    p1 = Player(body.get("p1") or "P1", DiscColor.RED)
    p2 = Player(body.get("p2") or "P2", DiscColor.YELLOW)
    session.game = Game(p1, p2)
    return current_view()


def move(body: dict[str, Any]) -> dict[str, Any]:
    game = session.game
    assert game is not None
    game.make_move(int(body["col"]))
    return current_view()


ROUTES = {"/start": start, "/move": move}


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
<title>Connect Four</title>
<style>
  :root {
    --paper: #e6edef;
    --ink: #12263a;
    --muted: #46606f;
    --frame: #2f4a66;
    --hole: #c3d9df;
    --hole-hover: #d9eaee;
    --line: #9db9c1;
    --red: #d64525;
    --red-ink: #a5300d;
    --yellow: #f2c230;
    --yellow-ink: #6b5200;
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
  #msg { min-height: 1.5rem; margin: .4rem 0; color: var(--red-ink); font-weight: 600; }
  .turn { display: flex; align-items: center; gap: .6rem; margin: 0 0 .8rem; font-size: 1.15rem; font-weight: 600; }

  button { font: inherit; cursor: pointer; }
  .primary {
    background: var(--ink); color: var(--paper); border: 0; border-radius: 6px;
    padding: .5rem 1.1rem; font-weight: 600;
  }
  #again { margin-bottom: 1.2rem; }

  .setup { display: grid; gap: .9rem; max-width: 22rem; }
  .setup label { display: grid; gap: .25rem; font-weight: 600; }
  .setup input {
    font: inherit; padding: .5rem .6rem; border: 1px solid var(--ink); border-radius: 6px;
    background: #f6fafb; color: var(--ink);
  }
  .setup .primary { justify-self: start; margin-top: .4rem; }

  .board {
    display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px;
    width: 100%; max-width: 30rem; padding: 8px; background: var(--frame); border-radius: 10px;
  }
  .col {
    display: grid; grid-template-rows: repeat(6, auto); gap: 6px;
    padding: 0; border: 0; border-radius: 6px; background: transparent;
  }
  .col:disabled { cursor: default; }
  .col:not(:disabled):hover { background: rgba(255, 255, 255, .18); }
  .hole {
    display: grid; place-items: center; width: 100%; aspect-ratio: 1; border-radius: 50%;
    background: var(--hole); font-weight: 800; font-size: clamp(.8rem, 2.6vw, 1.3rem);
  }
  .disc { box-shadow: inset 0 0 0 3px rgba(255, 255, 255, .0); }
  .disc.RED { background: var(--red); color: #fff; box-shadow: inset 0 0 0 4px #fff, inset 0 0 0 6px var(--red-ink); }
  .disc.YELLOW { background: var(--yellow); color: var(--yellow-ink); border: 3px dashed var(--yellow-ink); }
  .chip { display: inline-grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%; font-size: .8rem; font-weight: 800; }
  .chip.RED { background: var(--red); color: #fff; box-shadow: inset 0 0 0 2px #fff, inset 0 0 0 3px var(--red-ink); }
  .chip.YELLOW { background: var(--yellow); color: var(--yellow-ink); border: 2px dashed var(--yellow-ink); }
  .legend { display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; margin-top: 1.2rem; font-size: .9rem; color: var(--muted); }
  .legend span { display: inline-flex; align-items: center; gap: .45rem; }
  @media (prefers-reduced-motion: no-preference) {
    .hole.last { animation: drop .35s ease-in 1; }
    @keyframes drop { from { transform: translateY(-300%); } to { transform: none; } }
  }

  #err {
    display: none; white-space: pre-wrap; margin-top: 1.5rem; padding: .8rem;
    background: #3a0d0d; color: #ffd0c4; font: .85rem/1.4 ui-monospace, Menlo, monospace;
  }
</style></head>
<body>
<header><strong>Connect Four</strong></header>
<main id="app"></main>
<pre id="err"></pre>
<script>
let state = {phase: "setup"};
let lastCell = null;
let notice = "";

const $ = id => document.getElementById(id);
const LETTER = {RED: "R", YELLOW: "Y"};
const NAME = {RED: "red", YELLOW: "yellow"};

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

function boardHtml(s) {
  const open = s.phase === "playing";
  let h = `<div class="board" role="group" aria-label="Connect Four board">`;
  for (let c = 0; c < 7; c++) {
    const top = s.grid[0][c];
    const off = !open || top !== "" ? " disabled" : "";
    const filled = s.grid.filter(row => row[c] !== "").length;
    h += `<button type="button" class="col" data-c="${c}" aria-label="Drop disc in column ${c + 1}, ${filled} of 6 filled"${off}>`;
    for (let r = 0; r < 6; r++) {
      const d = s.grid[r][c];
      const last = lastCell && lastCell.r === r && lastCell.c === c ? " last" : "";
      h += d === ""
        ? `<span class="hole"></span>`
        : `<span class="hole disc ${d}${last}" role="img" aria-label="${NAME[d]} disc">${LETTER[d]}</span>`;
    }
    h += `</button>`;
  }
  return h + "</div>";
}

function render() {
  const s = state;
  const app = $("app");
  if (s.phase === "setup") {
    app.innerHTML = `<form id="setup" class="setup">
      <h2>New game</h2>
      <label>Player 1 (red) <input id="p1" value="Alice"></label>
      <label>Player 2 (yellow) <input id="p2" value="Bob"></label>
      <button class="primary">Start game</button>
      <p id="msg" role="alert"></p></form>`;
    $("setup").onsubmit = async e => {
      e.preventDefault();
      const data = await api("/start", {p1: $("p1").value, p2: $("p2").value});
      if (data) { state = data; lastCell = null; render(); }
      else { $("msg").textContent = notice; notice = ""; }
    };
    return;
  }

  let head;
  if (s.phase === "over") {
    head = s.draw ? `<h2>Draw</h2>` : `<h2>${esc(s.winner)} wins</h2>`;
  } else {
    head = `<h2>${esc(s.current)}'s turn</h2>
      <p class="turn" role="status"><span class="chip ${s.color}" aria-hidden="true">${LETTER[s.color]}</span>Playing ${NAME[s.color]}</p>`;
  }
  const again = `<button id="newgame" class="primary" style="margin:.4rem 0 1rem">New game</button>`;
  app.innerHTML = head + again + `<p id="msg" role="alert"></p>` + boardHtml(s) + `
    <p class="legend">
      <span><i class="chip RED" aria-hidden="true">R</i>Red (solid ring)</span>
      <span><i class="chip YELLOW" aria-hidden="true">Y</i>Yellow (dashed edge)</span>
    </p>`;
  $("msg").textContent = notice; notice = "";

  document.querySelectorAll("button.col:not(:disabled)").forEach(b => {
    b.onclick = async () => {
      const c = +b.dataset.c;
      const before = state.grid;
      const data = await api("/move", {col: c});
      if (!data) { render(); return; }
      let r = 5;
      while (r > 0 && before[r][c] !== "") r--;
      lastCell = {r, c};
      state = data;
      render();
      const next = document.querySelector(`button.col[data-c="${c}"]`);
      if (next && !next.disabled) next.focus();
    };
  });
  $("newgame").onclick = () => { state = {phase: "setup"}; lastCell = null; render(); };
}

function esc(text) {
  const el = document.createElement("span");
  el.textContent = text;
  return el.innerHTML;
}

render();
</script></body></html>
"""


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Connect Four running at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
