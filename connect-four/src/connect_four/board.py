from enum import StrEnum


class InvalidColumn(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("tried inserting into a column that doesn't exist")


class ColumnFull(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("tried inserting into a column that's full already")


class InvalidCell(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("tried fetching cell that doesn't exist")


class DiscColor(StrEnum):
    RED = "RED"
    YELLOW = "YELLOW"


class Board:
    rows: int = 6
    cols: int = 7
    empty_cells: int
    grid: list[list[DiscColor | None]]

    def __init__(self) -> None:
        self.grid = [[None] * self.cols for _ in range(self.rows)]
        self.empty_cells = self.rows * self.cols

    def insert_disc(self, disc: DiscColor, col: int) -> int:
        """
        Insert disc of a given color in the provided column.
        Return row where the disc was inserted.
        """
        if not (0 <= col < self.cols):
            raise InvalidColumn

        for row in range(self.rows - 1, -1, -1):
            if self.grid[row][col] is None:
                self.grid[row][col] = disc
                self.empty_cells -= 1
                return row

        raise ColumnFull

    def is_full(self) -> bool:
        return self.empty_cells == 0

    def get_cell(self, row: int, col: int) -> DiscColor | None:
        if not ((0 <= row < self.rows) and (0 <= col < self.cols)):
            raise InvalidCell

        return self.grid[row][col]

    def has_four_in_a_row(self, row: int, col: int, disc: DiscColor) -> bool:
        """
        Validate if a given cell location (row, col) is a part of a 4-in-a-row
        """
        if not ((0 <= row < self.rows) and (0 <= col < self.cols)):
            raise InvalidCell

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            total = 1
            for sign in (1, -1):
                i, j = row + sign * dr, col + sign * dc
                while (
                    (0 <= i < self.rows)
                    and (0 <= j < self.cols)
                    and self.grid[i][j] == disc
                ):
                    total += 1
                    i, j = i + sign * dr, j + sign * dc
                if total >= 4:
                    return True
        return False
