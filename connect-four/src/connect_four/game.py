from enum import Enum

from src.connect_four.board import Board
from src.connect_four.player import Player


class GameState(Enum):
    IN_PROGRESS = 0
    WON = 1
    DRAW = 2


class GameOver(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("cannot place disc when game has ended already")


class SameColor(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("both players cannot have the same disc color")


class Game:
    player1: Player
    player2: Player
    board: Board
    state: GameState
    winner: Player | None
    current_player: Player

    def __init__(self, p1: Player, p2: Player) -> None:
        if p1.get_color() == p2.get_color():
            raise SameColor

        self.player1 = p1
        self.player2 = p2
        self.board = Board()
        self.current_player = self.player1
        self.state = GameState.IN_PROGRESS
        self.winner = None

    def make_move(self, col: int):
        """
        Insert disc to a column of choice, check if this led to a win
        and update game state
        """
        if self.get_game_state() != GameState.IN_PROGRESS:
            raise GameOver

        row = self.board.insert_disc(self.current_player.disc, col)
        if self.board.has_four_in_a_row(row, col, self.current_player.disc):
            self.state = GameState.WON
            self.winner = self.current_player
        elif self.board.is_full():
            self.state = GameState.DRAW
        else:
            self.switch_player()

    def get_current_player(self) -> Player:
        return self.current_player

    def get_winner(self) -> Player | None:
        return self.winner

    def switch_player(self) -> None:
        if self.current_player == self.player1:
            self.current_player = self.player2
        else:
            self.current_player = self.player1

    def get_game_state(self) -> GameState:
        return self.state
