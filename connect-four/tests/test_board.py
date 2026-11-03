import copy

import pytest

from src.connect_four.board import (
    Board,
    ColumnFull,
    DiscColor,
    InvalidCell,
    InvalidColumn,
)

RED = DiscColor.RED
YELLOW = DiscColor.YELLOW

LINES = {
    "horizontal": (5, 0, 0, 1),
    "vertical": (2, 3, 1, 0),
    "diagonal_down_right": (1, 1, 1, 1),
    "diagonal_up_right": (4, 2, -1, 1),
}


def place_line(board: Board, start: tuple[int, int], step: tuple[int, int], length: int) -> list[tuple[int, int]]:
    cells = [(start[0] + i * step[0], start[1] + i * step[1]) for i in range(length)]
    for r, c in cells:
        board.grid[r][c] = RED
    return cells


def test_board_dimensions() -> None:
    board = Board()
    assert board.rows == 6
    assert board.cols == 7
    assert len(board.grid) == 6
    assert all(len(row) == 7 for row in board.grid)


@pytest.mark.parametrize("col", [0, 3, 6])
def test_insert_disc_into_empty_column_lands_on_bottom_row(col: int) -> None:
    board = Board()
    assert board.insert_disc(RED, col) == 5
    assert board.get_cell(5, col) == RED


def test_insert_disc_fills_column_from_bottom() -> None:
    board = Board()
    rows = [board.insert_disc(RED, 2) for _ in range(6)]
    assert rows == [5, 4, 3, 2, 1, 0]


@pytest.mark.parametrize("col", [-1, 7])
def test_insert_disc_invalid_column(col: int) -> None:
    with pytest.raises(InvalidColumn):
        Board().insert_disc(RED, col)


def test_insert_disc_column_full_on_seventh_disc() -> None:
    board = Board()
    for _ in range(6):
        board.insert_disc(RED, 4)
    with pytest.raises(ColumnFull):
        board.insert_disc(RED, 4)


@pytest.mark.parametrize("col", [-1, 7])
def test_invalid_column_leaves_board_unchanged(col: int) -> None:
    board = Board()
    board.insert_disc(RED, 0)
    grid_before = copy.deepcopy(board.grid)
    empty_before = board.empty_cells
    with pytest.raises(InvalidColumn):
        board.insert_disc(YELLOW, col)
    assert board.grid == grid_before
    assert board.empty_cells == empty_before


def test_column_full_leaves_board_unchanged() -> None:
    board = Board()
    for _ in range(6):
        board.insert_disc(RED, 4)
    grid_before = copy.deepcopy(board.grid)
    empty_before = board.empty_cells
    with pytest.raises(ColumnFull):
        board.insert_disc(YELLOW, 4)
    assert board.grid == grid_before
    assert board.empty_cells == empty_before


def test_is_full_false_at_start() -> None:
    assert not Board().is_full()


def test_is_full_false_after_41_discs() -> None:
    board = Board()
    for i in range(41):
        board.insert_disc(RED, i % 7)
    assert not board.is_full()


def test_is_full_true_after_42_discs() -> None:
    board = Board()
    for i in range(42):
        board.insert_disc(RED, i % 7)
    assert board.is_full()


def test_get_cell_empty_is_none() -> None:
    board = Board()
    assert all(board.get_cell(r, c) is None for r in range(6) for c in range(7))


@pytest.mark.parametrize("color", [RED, YELLOW])
def test_get_cell_returns_disc_color(color: DiscColor) -> None:
    board = Board()
    row = board.insert_disc(color, 3)
    assert board.get_cell(row, 3) == color


@pytest.mark.parametrize("row, col", [(-1, 0), (6, 0), (0, -1), (0, 7)])
def test_get_cell_out_of_range(row: int, col: int) -> None:
    with pytest.raises(InvalidCell):
        Board().get_cell(row, col)


@pytest.mark.parametrize("row, col", [(-1, 0), (6, 0), (0, -1), (0, 7)])
def test_has_four_in_a_row_out_of_range(row: int, col: int) -> None:
    with pytest.raises(InvalidCell):
        Board().has_four_in_a_row(row, col, RED)


@pytest.mark.parametrize(
    "line, index",
    [(line, i) for line in LINES for i in range(4)],
)
def test_four_in_a_row_detected_from_every_cell(line: str, index: int) -> None:
    board = Board()
    r, c, dr, dc = LINES[line]
    cells = place_line(board, (r, c), (dr, dc), 4)
    row, col = cells[index]
    assert board.has_four_in_a_row(row, col, RED)


@pytest.mark.parametrize(
    "line, index",
    [(line, i) for line in LINES for i in range(3)],
)
def test_three_in_a_row_is_not_four(line: str, index: int) -> None:
    board = Board()
    r, c, dr, dc = LINES[line]
    cells = place_line(board, (r, c), (dr, dc), 3)
    row, col = cells[index]
    assert not board.has_four_in_a_row(row, col, RED)


def test_four_in_a_row_requires_matching_color() -> None:
    board = Board()
    cells = place_line(board, (5, 0), (0, 1), 4)
    row, col = cells[0]
    assert not board.has_four_in_a_row(row, col, YELLOW)


@pytest.mark.parametrize("col", [0, 1, 2, 3, 4])
def test_one_disc_joining_two_runs_makes_five(col: int) -> None:
    board = Board()
    for c in (0, 1, 3, 4):
        board.grid[5][c] = RED
    board.grid[5][2] = RED
    assert board.has_four_in_a_row(5, col, RED)


def test_gap_between_runs_is_not_four() -> None:
    board = Board()
    for c in (0, 1, 3, 4):
        board.grid[5][c] = RED
    assert not board.has_four_in_a_row(5, 1, RED)
    assert not board.has_four_in_a_row(5, 3, RED)
