import pytest

from src.connect_four.board import ColumnFull, DiscColor, InvalidColumn
from src.connect_four.game import Game, GameOver, GameState, SameColor
from src.connect_four.player import Player

DRAW_MOVES = [
    4, 3, 6, 0, 1, 4, 5, 5, 1, 1, 5, 0, 1, 6, 0, 1, 5, 5, 1, 0, 4,
    6, 3, 2, 6, 6, 0, 4, 6, 5, 2, 0, 4, 2, 4, 2, 2, 2, 3, 3, 3, 3,
]
LAST_DISC_WIN_MOVES = [
    4, 5, 6, 4, 4, 4, 3, 4, 1, 2, 3, 2, 5, 3, 0, 6, 1, 1, 4, 6, 0,
    2, 2, 3, 0, 5, 6, 0, 3, 1, 1, 0, 0, 5, 3, 6, 1, 2, 6, 2, 5, 5,
]
P1_VERTICAL_WIN = [0, 1, 0, 1, 0, 1, 0]


@pytest.fixture
def p1() -> Player:
    return Player("Alice", DiscColor.RED)


@pytest.fixture
def p2() -> Player:
    return Player("Bob", DiscColor.YELLOW)


@pytest.fixture
def game(p1: Player, p2: Player) -> Game:
    return Game(p1, p2)


def play(game: Game, moves: list[int]) -> None:
    for col in moves:
        game.make_move(col)


def test_player1_moves_first(game: Game, p1: Player) -> None:
    assert game.get_current_player() is p1


def test_new_game_state_and_winner(game: Game) -> None:
    assert game.get_winner() is None
    assert game.get_game_state() == GameState.IN_PROGRESS


def test_turns_alternate_after_non_winning_moves(game: Game, p1: Player, p2: Player) -> None:
    game.make_move(0)
    assert game.get_current_player() is p2
    game.make_move(1)
    assert game.get_current_player() is p1


@pytest.mark.parametrize("color", [DiscColor.RED, DiscColor.YELLOW])
def test_same_color_rejected(color: DiscColor) -> None:
    with pytest.raises(SameColor):
        Game(Player("A", color), Player("B", color))


def test_vertical_win_sets_state_and_winner(game: Game, p1: Player) -> None:
    play(game, P1_VERTICAL_WIN)
    assert game.get_game_state() == GameState.WON
    assert game.get_winner() is p1


def test_win_does_not_switch_current_player(game: Game, p1: Player) -> None:
    play(game, P1_VERTICAL_WIN)
    assert game.get_current_player() is p1


def test_player2_win_is_attributed_to_player2(game: Game, p2: Player) -> None:
    play(game, [0, 1, 0, 1, 0, 1, 2, 1])
    assert game.get_game_state() == GameState.WON
    assert game.get_winner() is p2


def test_make_move_after_win_raises_game_over(game: Game) -> None:
    play(game, P1_VERTICAL_WIN)
    with pytest.raises(GameOver):
        game.make_move(3)


def test_draw_on_full_board_without_winner(game: Game) -> None:
    play(game, DRAW_MOVES[:-1])
    assert game.get_game_state() == GameState.IN_PROGRESS
    game.make_move(DRAW_MOVES[-1])
    assert game.board.is_full()
    assert game.get_game_state() == GameState.DRAW
    assert game.get_winner() is None


def test_make_move_after_draw_raises_game_over(game: Game) -> None:
    play(game, DRAW_MOVES)
    with pytest.raises(GameOver):
        game.make_move(0)


def test_win_with_last_disc_is_won_not_draw(game: Game, p2: Player) -> None:
    play(game, LAST_DISC_WIN_MOVES[:-1])
    assert game.get_game_state() == GameState.IN_PROGRESS
    game.make_move(LAST_DISC_WIN_MOVES[-1])
    assert game.board.is_full()
    assert game.get_game_state() == GameState.WON
    assert game.get_winner() is p2


@pytest.mark.parametrize("col", [-1, 7])
def test_invalid_column_leaves_game_unchanged(game: Game, p2: Player, col: int) -> None:
    game.make_move(0)
    with pytest.raises(InvalidColumn):
        game.make_move(col)
    assert game.get_current_player() is p2
    assert game.get_game_state() == GameState.IN_PROGRESS
    assert game.get_winner() is None


def test_full_column_leaves_game_unchanged(game: Game, p1: Player) -> None:
    play(game, [0] * 6)
    empty_before = game.board.empty_cells
    with pytest.raises(ColumnFull):
        game.make_move(0)
    assert game.get_current_player() is p1
    assert game.get_game_state() == GameState.IN_PROGRESS
    assert game.get_winner() is None
    assert game.board.empty_cells == empty_before
