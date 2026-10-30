"""Terminal UI for Battleship. Run from the project root: python play.py"""

from src.battleship.board import (
    Direction,
    InvalidPlacement,
    InvalidShot,
    LowShipNumber,
    ShipAlreadyPresent,
    ShotTakenAlready,
    TooManyShip,
)
from src.battleship.game import Game, GameStatus
from src.battleship.player import Player
from src.battleship.ship import Ship, ShipType

Placement = tuple[tuple[int, int], Direction]

PLACEMENT_ERRORS = (InvalidPlacement, ShipAlreadyPresent, TooManyShip, LowShipNumber)


def new_game(n: int, name1: str, name2: str) -> Game:
    return Game(n, name1, name2)


def render(player: Player, n: int, reveal_ships: bool) -> str:
    board = player.board
    lines = ["   " + " ".join(f"{c:>2}" for c in range(n))]
    for r in range(n):
        row = []
        for c in range(n):
            cell = (r, c)
            has_ship = cell in board.cell_to_ship
            if cell in board.shots:
                row.append(" X" if has_ship else " o")
            elif reveal_ships and has_ship:
                row.append(" #")
            else:
                row.append(" .")
        lines.append(f"{r:>2} " + " ".join(row))
    return "\n".join(lines)


def show_both(me: Player, opp: Player, n: int) -> None:
    print(f"\n=== {opp.name}'s waters (what you can see) ===")
    print(render(opp, n, reveal_ships=False))
    print(f"\n=== Your waters ({me.name}) ===")
    print(render(me, n, reveal_ships=True))
    print("\n# ship   X hit   o miss   . unknown/water\n")


def ask_ints(prompt: str, count: int) -> tuple[int, ...] | None:
    parts = input(prompt).split()
    if len(parts) != count:
        return None
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def render_draft(n: int, placements: list[Placement]) -> str:
    taken: set[tuple[int, int]] = set()
    for (row, col), direction in placements:
        step_r, step_c = direction.step
        taken.update((row + k * step_r, col + k * step_c) for k in range(Ship.size))
    lines = ["   " + " ".join(f"{c:>2}" for c in range(n))]
    for r in range(n):
        cells = " ".join(" #" if (r, c) in taken else " ." for c in range(n))
        lines.append(f"{r:>2} {cells}")
    return "\n".join(lines)


def collect_fleet(player: Player, n: int) -> dict[Ship, Placement]:
    types = list(ShipType)
    count = player.board.max_ships
    fleet: dict[Ship, Placement] = {}
    while len(fleet) < count:
        i = len(fleet)
        print(
            f"\n{player.name}'s draft board (not placed until all ships are entered):"
        )
        print(render_draft(n, list(fleet.values())))
        print(f"Ship {i + 1} of {count} (length {Ship.size}).")
        raw = input("row col direction(h/v): ").split()
        if len(raw) != 3 or raw[2].lower() not in ("h", "v"):
            print("Enter like: 0 2 h")
            continue
        try:
            loc = (int(raw[0]), int(raw[1]))
        except ValueError:
            print("Row and col must be numbers.")
            continue
        direction = (
            Direction.HORIZONTAL if raw[2].lower() == "h" else Direction.VERTICAL
        )
        ship = Ship()
        ship.id = f"{player.name}-{i}"
        ship.type = types[i % len(types)]
        fleet[ship] = (loc, direction)
    return fleet


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def main() -> None:
    while True:
        try:
            n = int(input("Board size n (>= 3): "))
            break
        except ValueError:
            print("Enter a number.")

    name1 = input("Player 1 name: ") or "P1"
    name2 = input("Player 2 name: ") or "P2"
    game = new_game(n, name1, name2)

    while game.status == GameStatus.SHIP_PLACEMENT:
        p = game.currentPlayer
        input(f"\n{p.name}: press Enter to place ships (others look away)...")
        clear_screen()
        try:
            game.place_ships(collect_fleet(p, n))
        except PLACEMENT_ERRORS as e:
            print(f"Rejected: {e}. Enter the whole fleet again.")
            continue
        input("Done. Press Enter to hide your board...")
        clear_screen()

    previous: Player | None = None
    while game.status != GameStatus.COMPLETED:
        me, opp = game.currentPlayer, game.opp
        if me is not previous:
            input(f"{me.name}'s turn. Press Enter when ready...")
        previous = me
        clear_screen()
        while True:
            show_both(me, opp, n)
            loc = ask_ints("Shoot at (row col): ", 2)
            if loc is None:
                print("Enter two numbers, like: 3 4")
                continue
            try:
                result = game.turn((loc[0], loc[1]))
            except (ShotTakenAlready, InvalidShot) as e:
                print(f"Rejected: {e}")
                continue
            break
        print(f"\nShot result: {result}")
        show_both(me, opp, n)
        if game.currentPlayer is not me:
            input("Press Enter to end turn...")
            clear_screen()

    print(f"Game over. Winner: {game.winner.name if game.winner else None}")


if __name__ == "__main__":
    main()
