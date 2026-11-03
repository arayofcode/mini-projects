# Connect Four

This is a game in which players choose a color then take turns dropping colored discs into a six row, seven column vertically suspended grid. Pieces fall straight down, occupying the lowest available space. The objective of the game is to be the first one to form a horizontal, vertical, or diagonal line of four of one's discs. 

Source: https://en.wikipedia.org/wiki/Connect_Four

> [!NOTE]
> UI and tests have been written using Claude Code.

## Requirements

> "Build the object-oriented design for a two-player Connect Four game. Players take turns dropping discs into a 7-column, 6-row board. The first to align four of their own discs vertically, horizontally, or diagonally wins."

- Two players take turns dropping discs in a valid column
- When dropped, the disc occupies the lowest unoccupied space
- Players interact with the game by choosing a column number, and the disc drops.
- Game ends following ways:
    - In a winner if there are four discs of the same color in a row: horizontal, vertical, or diagonal.
    - In a draw if entire board gets filled up with no winner
- Raise error for invalid game states or moves (inserting in non-existent column or a full column, trying to insert disc when it isn't the player's turn, or after the game ends)
- Board size is fixed - 7 x 6
- Out of scope: UI
- Assumption: Single process, one client. Both players take turns on the same Game object so no lock is needed.

## Entities

- Game: Orchestrates the game, and owns a Board. Responsible for coordinating player turns, manages game state, move validation, and enforcing game rules.
- Board: Manages grid state. Game interacts with the board and manages disc placement.
- Player: Represents a person in the game. 

### Relationships

- A Game has two Players: Association
- A Game owns the Board: Composition

## Class Design

### Game

This is the orchestration layer. External entities (Players) interact with Game to make moves, play a game, or check winner. Requirements for Game:

| Requirement | What to track |
|-|-|
| Two players take turns dropping discs in a valid column, Player1 starts first | List of players, who's the current player, Board itself |
| Players interact with the game by choosing a column number, and the disc drops. | Board |
| Maintain who wins, or if game ends in a draw | Game state, winner |
| Two players shouldn't have the same color | Validation in constructor |

```
ENUM GameState:
    IN_PROGRESS
    WON
    DRAW

CLASS Game:
    - player1: Player
    - player2: Player
    - board: Board
    - state: GameState
    - winner: Player | None
    - currentPlayer: Player

    + make_move(column)
    + get_current_player() -> Player
    + get_winner() -> Player | None
    + get_game_state() -> GameState
```

### Board

Only responsible for maintaining a grid. Allows Game to insert a disc, raise errors, and check for row being present at a given location.

| Requirement | What to track |
|-|-|
| Insert at lowest available space | Which disc acquires a given location |
| Draw - board is full | check empty cells |
| Four discs in a row | Check row from any arbitrary point in grid |

```
ENUM DiscColor:
    RED
    YELLOW

CLASS Board:
    - rows: int
    - cols: int
    - grid: DiscColor[rows][cols]

    + insert_disc(DiscColor, col) -> int
    + is_full() -> bool
    + has_four_in_a_row(row, col, DiscColor) -> bool
    + get_cell(row, col) -> DiscColor | None
```

### Player

Just for identifying a player. No operations here.

```
CLASS Player:
    - name: str
    - color: DiscColor

    + get_name() -> str
    + get_color() -> DiscColor
```

## Errors to Handle

| Error | Owner | Description |
|-|-|-|
| InvalidColumn | Board | When player tries insertion in an out-of-bound column |
| ColumnFull | Board | Player tried insertion in a column that has no space left |
<!--| WrongPlayer | Game | When it's Player 1's turn, but Player 2 tries making a move |-->
| GameOver | Game | When a player tries making move after game has ended |
| SameColor | Game | When both players take the same color |