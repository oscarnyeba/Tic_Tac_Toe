# Tic-Tac-Toe — Documentation

A 5x5 tic-tac-toe game with a Tkinter GUI, playable as Player 1 (human) vs.
either the computer or a second human. Winning requires 4 marks in a row,
placed next to each other, anywhere on the board.

Run it with:

```
python tictactoe_gui.py
```

## Gameplay

- On launch, you're asked for your name. It replaces "Player 1" throughout
  the game (title bar, status text, win message). Leaving it blank falls
  back to "Player 1".
- Choose whether Player 2 is the **Computer** or a **Human**, via the radio
  buttons at the top. This can be changed any time before starting a new
  game with "New Game".
- The board is a fixed 5x5 grid (25 cells).
- **Win condition:** 4 of your marks in a row — horizontally, vertically,
  or diagonally — where all 4 are adjacent to each other. You do **not**
  need to fill an entire row/column/diagonal; any 4 consecutive cells in a
  line count. This is the classic "K-in-a-row" rule used in games like
  Gomoku, and is formally an
  [m,n,k-game](https://en.wikipedia.org/wiki/M,n,k-game) with m = n = 5,
  k = 4.
- If the board fills up with no winner, the game ends in a draw.

## Data structures

- **Board**: the 5x5 grid is stored as a flat Python list of length 25
  (`self.cells`), rather than a nested 2D list. Index `i` maps to
  `row = i // 5, col = i % 5`. A flat list keeps win-checking simple: a
  winning line is just a tuple of indices, and checking it means reading a
  few list positions rather than juggling row/column offsets everywhere.
- **`WIN_LINES`**: a tuple of every possible run of `WIN_LENGTH` (4)
  consecutive cells in a straight line — horizontal, vertical, or either
  diagonal direction. It's generated once at import time by
  `_generate_win_lines()` and shared by every `Board` instance, so it's
  never recomputed during play. On a 5x5 board with a win length of 4,
  this produces 28 lines.

## Algorithms

### Win checking

For each line in `WIN_LINES`, check whether its first cell is non-empty
and every other cell in the line matches it. If so, that line — and thus
the game — has a winner. This runs in `O(number of lines)` per check
(28 lines here), independent of how many moves have been played.

### Sliding-window line generation

`_generate_win_lines(n, k)` builds every valid run of `k` consecutive
cells on an `n x n` board by scanning every starting cell and, for each of
the 4 directions (horizontal, vertical, and both diagonals), checking
whether a run of `k` cells starting there stays on the board. This is what
allows "4 in a row" to be satisfied *anywhere* on the board — including
diagonal runs that don't touch the board's corners — rather than only by
filling a whole row, column, or diagonal.

### Computer's move

A full unbeatable minimax search (as used in the classic 3x3 version of
this game) is not practical at this board size — the game tree is far
larger once the board is 5x5 with a 4-in-a-row win condition satisfiable
anywhere. Instead, `computer_move()` uses a layered strategy:

1. **Win immediately** — if any available move completes a 4-in-a-row for
   the computer, play it (`find_winning_move`).
2. **Block immediately** — otherwise, if the opponent has a move that
   would complete their own 4-in-a-row next turn, play there instead to
   block it.
3. **Heuristic scoring** — otherwise, score every available move by
   looking at all the winning lines that pass through it
   (`Board.lines_through`):
   - A line containing only the computer's marks (no opponent marks) adds
     `10 ** own_marks_in_line` to the score — so a line that's already 3/4
     full is worth far more than one that's 1/4 full.
   - A line containing only the opponent's marks adds `5 ** opponent_marks`
     to the score, as a softer pressure to lean away from the opponent's
     developing lines.
   - A small bonus is added for moves closer to the board's center, since
     central cells participate in more winning lines than edge or corner
     cells.
   - The move with the highest total score is played; ties are broken
     randomly so the computer doesn't play identically every game.

`find_winning_move(board, player)` itself is a brute-force backtracking
search: try each available move, check if it produces a win for `player`,
then undo the move (`Board.undo_move`) before trying the next candidate.
This avoids the overhead of copying the whole board for every trial move.

## File overview

| Piece | Responsibility |
|---|---|
| `Board` | Game state and rules: cells, legal moves, win detection. Has no knowledge of the GUI. |
| `find_winning_move`, `heuristic_move`, `computer_move` | Computer opponent's decision-making, operating purely on a `Board`. |
| `TicTacToeGUI` | Tkinter front-end: drawing the grid, handling clicks, showing status text. Delegates all game-rule questions to `Board` / `computer_move`. |

This split means the game logic (`Board` and the move-choosing functions)
could be reused with a different front-end (e.g. a command-line version)
without any changes.
