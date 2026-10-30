from enum import StrEnum

from src.battleship.board import Direction, ShotResult
from src.battleship.player import Player
from src.battleship.ship import Ship


class GameStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    SHIP_PLACEMENT = "SHIP_PLACEMENT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class GameEnded(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("game has ended already.")


class InvalidGameState(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("can't take action in current game state")


class ShipsPlacedAlready(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("ships have already been placed for this player")


class Game:
    board_size: int = 5
    winner: Player | None = None
    status: GameStatus = GameStatus.NOT_STARTED
    player1: Player
    player2: Player
    currentPlayer: Player
    opp: Player

    def __init__(self, n: int, name1: str, name2: str) -> None:
        self.board_size = n
        self.player1 = Player(name1, n)
        self.player2 = Player(name2, n)
        self.currentPlayer = self.player1
        self.opp = self.player2
        self.status = GameStatus.SHIP_PLACEMENT

    def _switchPlayer(self):
        if self.currentPlayer == self.player1:
            self.currentPlayer = self.player2
            self.opp = self.player1
        else:
            self.currentPlayer = self.player1
            self.opp = self.player2

    def place_ships(self, ships: dict[Ship, tuple[tuple[int, int], Direction]]):
        if self.status != GameStatus.SHIP_PLACEMENT:
            raise InvalidGameState

        self.currentPlayer.place_fleet(ships)

        self._switchPlayer()

        if self.player1.all_ships_placed() and self.player2.all_ships_placed():
            self.status = GameStatus.IN_PROGRESS

    def turn(self, location: tuple[int, int]) -> ShotResult:
        if self.status == GameStatus.COMPLETED:
            raise GameEnded

        if self.status != GameStatus.IN_PROGRESS:
            raise InvalidGameState

        hit = self.opp.board.take_shot(location)
        if self.opp.board.all_ships_shot():
            self.status = GameStatus.COMPLETED
            self.winner = self.currentPlayer
        elif hit == ShotResult.MISS:
            self._switchPlayer()
        return hit
