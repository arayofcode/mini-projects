# Battleship

> [!NOTE]
> Note that the UI (both terminal and web) has been written using Claude Code.

A two-player Battleship game. Each player places a fleet of ships on their own n × n board. Players then take turns to fire at the other player's board. The first player to sink every enemy ship wins.

## Run

Run these from this directory. Python 3.13 or later is needed.

```
uv run python play.py   # terminal UI
uv run python web.py    # browser UI at http://127.0.0.1:8000
```

## Requirements

- One game at a time, played by two players (one of them could be a bot, part of extension: not done yet). Both get the same type of ships and count.
- Each player places their ships on their own n × n board before the game begins. A player places the whole fleet in one call.
- n must be at least 3. For 3 <= n <= 7, each player has 3 ships. For bigger n, each player has 5. Each ship is 3 cells long. Ships can be placed horizontally or vertically.
- A player cannot see the other player's ships. On hitting a cell with a ship, only the cell that was hit is visible to them.
- In each turn, a player fires at one cell of the other player's board. The result is one of:
  - `MISS`: the cell is empty water. The turn passes to the other player.
  - `HIT`: the cell holds part of a ship. The same player fires again.
  - `SUNK`: the shot hit the last live cell of a ship. The same player fires again.
- The game ends when one player has sunk all ships of the other player.
- Not allowed: out of bound placements, overlapping ships, a wrong number of ships, repeat shots, shooting outside the grid, shooting before both fleets are placed, and shooting after the game has ended. When a request is rejected, the player can retry. A rejected fleet leaves the board unchanged.

### Out of Scope

- An interface that allows users to play against another user. This is to be built by an agent as I'll focus on building the game core.

## Entities

- `Game`: creates the two players, keeps the game status (`SHIP_PLACEMENT`, `IN_PROGRESS`, `COMPLETED`), and coordinates fleet placement, turns and shots.
- `Player`: has a name and one board.
- `Board`: keeps the grid state for a player. It maps each cell to its ship, tracks the live cells of each ship, and records the cells already shot at. It owns the fleet rules (the ship count and valid placement).
- `Ship`: has an id, a type and a size.

### Relationships

- `Game` has two `Player`s. Association.
- Each `Player` owns a `Board`. Composition.
- `Board` refers to the `Ship`s placed on it. Association.
