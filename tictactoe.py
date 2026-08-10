"""Tic-Tac-Toe -- Player 1 vs Computer (or 2 Player), 5x5, 4-in-a-row. See DOCUMENTATION.md for full details."""

import random
import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import List, Optional, Tuple

EMPTY = " "
PLAYER_1 = "X"
PLAYER_2 = "O"

SIZE = 5
WIN_LENGTH = 4  # consecutive marks needed to win


def _generate_win_lines(n: int, k: int) -> Tuple[Tuple[int, ...], ...]:
    # Sliding window over all 4 directions -> every possible run of k cells on the board.
    lines = []
    directions = [
        (0, 1),   # horizontal
        (1, 0),   # vertical
        (1, 1),   # diagonal down-right
        (1, -1),  # diagonal down-left
    ]

    for r in range(n):
        for c in range(n):
            for dr, dc in directions:
                end_r = r + dr * (k - 1)
                end_c = c + dc * (k - 1)
                if 0 <= end_r < n and 0 <= end_c < n:  # only keep runs that fit on the board
                    line = tuple((r + dr * i) * n + (c + dc * i) for i in range(k))
                    lines.append(line)

    return tuple(lines)


WIN_LINES: Tuple[Tuple[int, ...], ...] = _generate_win_lines(SIZE, WIN_LENGTH)  # computed once at import


class Board:
    """Flat-list board: index i -> row i // SIZE, col i % SIZE."""

    def __init__(self) -> None:
        self.n = SIZE
        self.cells: List[str] = [EMPTY] * (SIZE * SIZE)
        self.win_lines = WIN_LINES

    def available_moves(self) -> List[int]:
        return [i for i, v in enumerate(self.cells) if v == EMPTY]

    def make_move(self, index: int, player: str) -> None:
        self.cells[index] = player

    def undo_move(self, index: int) -> None:
        self.cells[index] = EMPTY  # used for backtracking during move search

    def is_full(self) -> bool:
        return EMPTY not in self.cells

    def winning_line(self) -> Optional[Tuple[int, ...]]:
        # Check each candidate line: does every cell in it match the first cell?
        for line in self.win_lines:
            first = self.cells[line[0]]
            if first != EMPTY and all(self.cells[i] == first for i in line):
                return line
        return None

    def winner(self) -> Optional[str]:
        line = self.winning_line()
        return self.cells[line[0]] if line else None

    def game_over(self) -> bool:
        return self.winner() is not None or self.is_full()

    def lines_through(self, index: int) -> List[Tuple[int, ...]]:
        return [line for line in self.win_lines if index in line]  # used by the heuristic scorer


# ---------------------------------------------------------------------------
# Computer move logic
# ---------------------------------------------------------------------------

def find_winning_move(board: Board, player: str) -> Optional[int]:
    # Try each move, check for a win, undo -- backtracking search for a 1-move win.
    for move in board.available_moves():
        board.make_move(move, player)
        won = board.winner() == player
        board.undo_move(move)
        if won:
            return move
    return None


def heuristic_move(board: Board) -> int:
    # No full minimax at this board size -- score candidate moves by how many
    # winning lines they build for us / block for the opponent, plus a small
    # center-preference bonus, then pick the best (tie broken randomly).
    best_score = -1.0
    best_moves: List[int] = []

    for move in board.available_moves():
        score = 0.0
        for line in board.lines_through(move):
            marks = [board.cells[i] for i in line]
            opp_count = marks.count(PLAYER_1)
            own_count = marks.count(PLAYER_2)
            if opp_count == 0:
                score += 10 ** own_count       # building our own line
            if own_count == 0 and opp_count > 0:
                score += 5 ** opp_count        # dampening opponent's line

        n = board.n
        r, c = divmod(move, n)
        center = (n - 1) / 2
        score += 1.0 / (1 + abs(r - center) + abs(c - center))  # slight center preference

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    return random.choice(best_moves)


def computer_move(board: Board) -> int:
    # Priority: win now > block opponent's win > best heuristic move.
    win = find_winning_move(board, PLAYER_2)
    if win is not None:
        return win

    block = find_winning_move(board, PLAYER_1)
    if block is not None:
        return block

    return heuristic_move(board)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class TicTacToeGUI:
    """Tkinter front-end; delegates all game rules to Board / computer_move."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.root.resizable(False, False)

        # Ask for the human player's name before building the rest of the UI.
        entered_name = simpledialog.askstring(
            "Your Name", "Enter your name:", parent=self.root
        )
        self.player1_name = entered_name.strip() if entered_name and entered_name.strip() else "Player 1"
        self.root.title(f"Tic-Tac-Toe — {self.player1_name}")

        self.board = Board()
        self.buttons: List[tk.Button] = []
        self.game_active = True
        self.current_player = PLAYER_1  # human always moves first

        # --- Top controls: opponent selector ---
        controls = tk.Frame(root, pady=8)
        controls.grid(row=0, column=0)

        self.opponent_var = tk.StringVar(value="computer")
        tk.Label(controls, text="Player 2:", font=("Helvetica", 11)).pack(side="left")
        tk.Radiobutton(
            controls, text="Computer", variable=self.opponent_var,
            value="computer", font=("Helvetica", 11)
        ).pack(side="left")
        tk.Radiobutton(
            controls, text="Human", variable=self.opponent_var,
            value="human", font=("Helvetica", 11)
        ).pack(side="left")

        tk.Button(controls, text="New Game", command=self.reset).pack(side="left", padx=(16, 0))

        # --- Status label ---
        self.status_var = tk.StringVar(value=f"{self.player1_name}'s turn (X)")
        tk.Label(
            root, textvariable=self.status_var, font=("Helvetica", 16), pady=6
        ).grid(row=1, column=0)

        # --- Board grid ---
        self.grid_frame = tk.Frame(root)
        self.grid_frame.grid(row=2, column=0)

        self.build_grid()

    def build_grid(self) -> None:
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.buttons = []

        for i in range(SIZE * SIZE):
            btn = tk.Button(
                self.grid_frame,
                text=EMPTY,
                font=("Helvetica", 32, "bold"),
                width=3,
                height=1,
                command=lambda idx=i: self.on_click(idx),  # idx=i binds each button's own index
            )
            btn.grid(row=i // SIZE, column=i % SIZE, padx=2, pady=2)
            self.buttons.append(btn)

    def vs_computer(self) -> bool:
        return self.opponent_var.get() == "computer"

    def on_click(self, index: int) -> None:
        if not self.game_active or self.board.cells[index] != EMPTY:
            return
        if self.vs_computer() and self.current_player != PLAYER_1:
            return  # ignore stray clicks while it's the computer's turn

        self.place(index, self.current_player)
        if self.check_end():
            return

        self.advance_turn()

    def place(self, index: int, player: str) -> None:
        self.board.make_move(index, player)
        color = "#1E88E5" if player == PLAYER_1 else "#E53935"  # blue X, red O
        self.buttons[index].config(text=player, fg=color, state="disabled")

    def advance_turn(self) -> None:
        self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1

        if self.vs_computer() and self.current_player == PLAYER_2:
            self.status_var.set("Computer's turn...")
            self.root.update_idletasks()
            self.root.after(200, self.do_computer_move)  # slight delay so the label renders first
        else:
            label = f"{self.player1_name}'s turn (X)" if self.current_player == PLAYER_1 else "Player 2's turn (O)"
            self.status_var.set(label)

    def do_computer_move(self) -> None:
        if not self.game_active:
            return  # game may have ended while this callback was pending
        move = computer_move(self.board)
        self.place(move, PLAYER_2)
        if self.check_end():
            return
        self.advance_turn()

    def check_end(self) -> bool:
        winner = self.board.winner()
        if winner is not None:
            self.highlight_win()
            if self.vs_computer() and winner == PLAYER_2:
                name = "Computer"
            elif winner == PLAYER_1:
                name = self.player1_name
            else:
                name = "Player 2"
            self.end_game(f"{name} ({winner}) wins!")
            return True
        if self.board.is_full():
            self.end_game("It's a draw!")
            return True
        return False

    def highlight_win(self) -> None:
        line = self.board.winning_line()
        if line:
            for idx in line:
                self.buttons[idx].config(bg="#A5D6A7")  # green highlight on the winning line

    def end_game(self, message: str) -> None:
        self.game_active = False
        self.status_var.set(message)
        for btn in self.buttons:
            btn.config(state="disabled")
        messagebox.showinfo("Game Over", message)

    def reset(self) -> None:
        self.board = Board()
        self.game_active = True
        self.current_player = PLAYER_1
        self.status_var.set(f"{self.player1_name}'s turn (X)")
        self.build_grid()


def main() -> None:
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()