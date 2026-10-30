from src.battleship.board import Board, Direction
from src.battleship.ship import Ship


class Player:
    name: str
    board: Board

    def __init__(self, name: str, board_size: int) -> None:
        self.name = name
        self.board = Board(board_size)

    def place_fleet(self, fleet: dict[Ship, tuple[tuple[int, int], Direction]]):
        self.board.add_many_ships(fleet)

    def all_ships_placed(self) -> bool:
        return self.board.all_ships_placed()
