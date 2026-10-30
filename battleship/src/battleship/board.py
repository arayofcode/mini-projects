from collections import defaultdict
from enum import Enum, StrEnum

from src.battleship.ship import Ship


class InvalidBoardSize(Exception):
    def __init__(self) -> None:
        super().__init__("board size can't be less than 3x3")


class InvalidPlacement(Exception):
    def __init__(self) -> None:
        super().__init__("invalid coordinates to place a ship")


class ShipAlreadyPresent(Exception):
    def __init__(self) -> None:
        super().__init__("the placing coordinates collide with another ship's location")


class InvalidShot(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("you cannot shoot here")


class ShotTakenAlready(Exception):
    def __init__(self) -> None:
        super().__init__("you've already tried shooting at this location before")


class Direction(Enum):
    HORIZONTAL = (0, 1)
    VERTICAL = (1, 0)

    @property
    def step(self) -> tuple[int, int]:
        return self.value


class ShotResult(StrEnum):
    MISS = "MISS"
    HIT = "HIT"
    SUNK = "SUNK"


class TooManyShip(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("placing more ship than the board allows")


class LowShipNumber(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("need to add more ships")


class Board:
    size: int = 3
    cell_to_ship: dict[tuple[int, int], Ship]
    shots: set[tuple[int, int]]
    live_ships: dict[Ship, set[tuple[int, int]]]

    def __init__(self, n: int) -> None:
        if n < 3:
            raise InvalidBoardSize

        self.size = n
        self.cell_to_ship = {}
        self.shots = set()
        self.live_ships = defaultdict(set)

    @property
    def max_ships(self) -> int:
        return 3 if self.size <= 7 else 5

    def add_many_ships(self, ships: dict[Ship, tuple[tuple[int, int], Direction]]):
        if len(self.live_ships) + len(ships) < self.max_ships:
            raise LowShipNumber

        if len(self.live_ships) + len(ships) > self.max_ships:
            raise TooManyShip

        claimed_cells: set[tuple[int, int]] = set()
        placement: list[tuple[Ship, tuple[int, int]]] = []
        for ship, (location, dir) in ships.items():
            x, y = location
            cells: list[tuple[int, int]] = []
            for _ in range(ship.size):
                if not (0 <= x < self.size and 0 <= y < self.size):
                    raise InvalidPlacement

                if (x, y) in self.cell_to_ship or (x, y) in claimed_cells:
                    raise ShipAlreadyPresent

                cells.append((x, y))
                claimed_cells.add((x, y))
                x, y = x + dir.step[0], y + dir.step[1]

            for cell in cells:
                placement.append((ship, cell))

        for ship, cell in placement:
            self.cell_to_ship[cell] = ship
            self.live_ships[ship].add(cell)

    def take_shot(self, location: tuple[int, int]) -> ShotResult:
        if not (0 <= location[0] < self.size and 0 <= location[1] < self.size):
            raise InvalidShot

        if location in self.shots:
            raise ShotTakenAlready

        hit = location in self.cell_to_ship
        result = ShotResult.HIT if hit else ShotResult.MISS
        if hit:
            ship = self.cell_to_ship[location]
            self.live_ships[ship].remove(location)
            if len(self.live_ships[ship]) == 0:
                del self.live_ships[ship]
                result = ShotResult.SUNK

        self.shots.add(location)
        return result

    def all_ships_shot(self) -> bool:
        return self.live_ships == {}

    def all_ships_placed(self) -> bool:
        return len(self.live_ships) == self.max_ships
