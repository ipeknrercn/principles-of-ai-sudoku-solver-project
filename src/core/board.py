"""
src/core/board.py

Shared data structure for the Sudoku board.
All modules (Logic, Math, Optimization, UI) use this class.

This class is the project's "single source of truth."
No module should create its own board representation.
"""

from __future__ import annotations
from typing import List, Set, Tuple, Optional, Iterator
from copy import deepcopy
import numpy as np


# Constants — all modules can import these
BOARD_SIZE = 9          # 9x9 board
BOX_SIZE = 3            # 3x3 box
EMPTY_CELL = 0          # Empty cell value
DIGITS = frozenset(range(1, 10))  # Valid values {1, 2, ..., 9}


class Board:
    """
    Class that represents a Sudoku board.
    
    Internal representation:
        - self._grid: 9x9 NumPy array (int8). 0 = empty, 1-9 = assigned value.
        - self._candidates: 9x9 list-of-sets. Candidate values for each cell.
                            Empty set for fixed (given) cells.
        - self._fixed: 9x9 boolean NumPy array. True = initially given cell.
    
    Design decision:
        We store cell values in a NumPy array and candidates in sets.
        This allows:
            - The Math module to run matrix operations on the grid
            - The Logic module to perform inference on candidates
            - SA/GA to swap grid values quickly
            - The UI to convert the grid to JSON easily
    """

    def __init__(self, grid: Optional[np.ndarray] = None):
        """
        Create a new board.
        
        Args:
            grid: 9x9 NumPy array or None. If None, an empty board is created.
                  Values must be in range 0-9 (0 = empty).
        """
        if grid is None:
            self._grid = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
        else:
            self._validate_grid(grid)
            self._grid = grid.astype(np.int8).copy()
        
        # Fixed cells: initially filled cells (user cannot modify them)
        self._fixed = (self._grid != EMPTY_CELL).copy()
        
        # Candidates: possible values for each cell
        # Empty cells start with {1..9}, filled cells have empty sets
        self._candidates: List[List[Set[int]]] = [
            [set(DIGITS) if self._grid[r, c] == EMPTY_CELL else set()
             for c in range(BOARD_SIZE)]
            for r in range(BOARD_SIZE)
        ]
        
        # Initial constraint propagation: clean candidates affected by filled cells
        self._initialize_candidates()

    # ============================================================
    # Validation
    # ============================================================

    @staticmethod
    def _validate_grid(grid: np.ndarray) -> None:
        """Validate whether the given grid is a valid Sudoku board."""
        if not isinstance(grid, np.ndarray):
            raise TypeError(f"grid must be a NumPy array, got: {type(grid)}")
        
        if grid.shape != (BOARD_SIZE, BOARD_SIZE):
            raise ValueError(f"grid must be {BOARD_SIZE}x{BOARD_SIZE}, got: {grid.shape}")
        
        if not np.all((grid >= 0) & (grid <= 9)):
            raise ValueError("grid values must be in range 0-9")

    def _initialize_candidates(self) -> None:
        """
        Clean candidates affected by initially filled cells.
        Example: if cell (0,0) is 5, then other cells in the same
        row/column/box cannot have 5 as a candidate.
        """
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self._grid[r, c] != EMPTY_CELL:
                    self._eliminate_from_peers(r, c, self._grid[r, c])

    # ============================================================
    # Basic Access Methods
    # ============================================================

    def get(self, row: int, col: int) -> int:
        """Return the value of a specific cell. 0 = empty."""
        return int(self._grid[row, col])

    def set(self, row: int, col: int, value: int) -> None:
        """
        Assign a value to a cell.
        
        Args:
            row, col: in range 0-8
            value: in range 1-9 (0 = clear cell)
        
        Raises:
            ValueError: Invalid cell or value
            RuntimeError: If trying to modify a fixed (initially given) cell
        """
        self._validate_cell(row, col)
        if value != EMPTY_CELL and value not in DIGITS:
            raise ValueError(f"Value must be in range 0-9, got: {value}")
        
        if self._fixed[row, col]:
            raise RuntimeError(f"({row},{col}) is a fixed cell and cannot be changed")
        
        old_value = self._grid[row, col]
        self._grid[row, col] = value
        
        # Update candidates
        if old_value != EMPTY_CELL:
            # Restore previous value to peers
            self._restore_to_peers(row, col, old_value)
        
        if value != EMPTY_CELL:
            self._candidates[row][col] = set()
            self._eliminate_from_peers(row, col, value)
        else:
            # Cell cleared, recompute candidates
            self._candidates[row][col] = self._compute_candidates(row, col)

    def is_empty(self, row: int, col: int) -> bool:
        """Is the cell empty?"""
        return self._grid[row, col] == EMPTY_CELL

    def is_fixed(self, row: int, col: int) -> bool:
        """Is the cell fixed (initially given)?"""
        return bool(self._fixed[row, col])

    def get_candidates(self, row: int, col: int) -> Set[int]:
        """Return a cell's candidate values (copy, immutable from outside)."""
        return self._candidates[row][col].copy()

    def set_candidates(self, row: int, col: int, candidates: Set[int]) -> None:
        """
        Set a cell's candidates externally.
        Used by the Logic module during inference.
        """
        self._validate_cell(row, col)
        if not candidates.issubset(DIGITS):
            raise ValueError(f"Candidates must be within {{1..9}}, got: {candidates}")
        self._candidates[row][col] = candidates.copy()

    def eliminate_candidate(self, row: int, col: int, value: int) -> bool:
        """
        Remove a candidate value from a cell.
        
        Returns:
            True: value was removed (it existed)
            False: value was already absent
        """
        if value in self._candidates[row][col]:
            self._candidates[row][col].discard(value)
            return True
        return False

    # ============================================================
    # NumPy Access (for Math, SA, GA modules)
    # ============================================================

    def to_numpy(self) -> np.ndarray:
        """Return a copy of the 9x9 NumPy array."""
        return self._grid.copy()

    def from_numpy(self, grid: np.ndarray) -> None:
        """
        Reload the board from a NumPy array.
        For SA/GA: update board after optimization.
        Fixed cells are preserved.
        """
        self._validate_grid(grid)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not self._fixed[r, c]:
                    self._grid[r, c] = grid[r, c]
        # Recompute candidates
        self._recompute_all_candidates()

    def to_tensor(self) -> np.ndarray:
        """
        Return a 9x9x9 binary tensor. T[r][c][k-1] = 1 if cell (r,c) contains k.
        Used by the Math Modeler.
        """
        tensor = np.zeros((BOARD_SIZE, BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = self._grid[r, c]
                if v != EMPTY_CELL:
                    tensor[r, c, v - 1] = 1
        return tensor

    # ============================================================
    # Sudoku Rules
    # ============================================================

    def is_valid(self) -> bool:
        """
        Does the board follow Sudoku rules? (It does not need to be full.)
        Checks for conflicts.
        """
        # Rows
        for r in range(BOARD_SIZE):
            row_values = [self._grid[r, c] for c in range(BOARD_SIZE) if self._grid[r, c] != EMPTY_CELL]
            if len(row_values) != len(set(row_values)):
                return False
        # Columns
        for c in range(BOARD_SIZE):
            col_values = [self._grid[r, c] for r in range(BOARD_SIZE) if self._grid[r, c] != EMPTY_CELL]
            if len(col_values) != len(set(col_values)):
                return False
        # Boxes
        for box_r in range(0, BOARD_SIZE, BOX_SIZE):
            for box_c in range(0, BOARD_SIZE, BOX_SIZE):
                box_values = []
                for r in range(box_r, box_r + BOX_SIZE):
                    for c in range(box_c, box_c + BOX_SIZE):
                        if self._grid[r, c] != EMPTY_CELL:
                            box_values.append(self._grid[r, c])
                if len(box_values) != len(set(box_values)):
                    return False
        return True

    def is_solved(self) -> bool:
        """Is the board fully and correctly solved?"""
        return EMPTY_CELL not in self._grid and self.is_valid()

    def count_conflicts(self) -> int:
        """
        Return total number of conflicts. Used for SA energy function.
        A conflict is a repeated value in the same row/column/box.
        """
        conflicts = 0
        # Row conflicts
        for r in range(BOARD_SIZE):
            row = [self._grid[r, c] for c in range(BOARD_SIZE) if self._grid[r, c] != EMPTY_CELL]
            conflicts += len(row) - len(set(row))
        # Column conflicts
        for c in range(BOARD_SIZE):
            col = [self._grid[r, c] for r in range(BOARD_SIZE) if self._grid[r, c] != EMPTY_CELL]
            conflicts += len(col) - len(set(col))
        # Box conflicts
        for box_r in range(0, BOARD_SIZE, BOX_SIZE):
            for box_c in range(0, BOARD_SIZE, BOX_SIZE):
                box = []
                for r in range(box_r, box_r + BOX_SIZE):
                    for c in range(box_c, box_c + BOX_SIZE):
                        if self._grid[r, c] != EMPTY_CELL:
                            box.append(self._grid[r, c])
                conflicts += len(box) - len(set(box))
        return conflicts

    def empty_cells(self) -> Iterator[Tuple[int, int]]:
        """Yield (row, col) coordinates of empty cells."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self._grid[r, c] == EMPTY_CELL:
                    yield (r, c)

    def get_peers(self, row: int, col: int) -> Set[Tuple[int, int]]:
        """
        Return a cell's peers (other cells in same row/column/box).
        This concept is critical in Sudoku CSP.
        """
        peers = set()
        # Same row
        for c in range(BOARD_SIZE):
            if c != col:
                peers.add((row, c))
        # Same column
        for r in range(BOARD_SIZE):
            if r != row:
                peers.add((r, col))
        # Same box
        box_r_start = (row // BOX_SIZE) * BOX_SIZE
        box_c_start = (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_r_start, box_r_start + BOX_SIZE):
            for c in range(box_c_start, box_c_start + BOX_SIZE):
                if (r, c) != (row, col):
                    peers.add((r, c))
        return peers

    # ============================================================
    # Helper (private) methods
    # ============================================================

    @staticmethod
    def _validate_cell(row: int, col: int) -> None:
        """Are the cell coordinates valid?"""
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise ValueError(f"Invalid cell: ({row}, {col})")

    def _eliminate_from_peers(self, row: int, col: int, value: int) -> None:
        """Remove a specific value from (row, col)'s peers."""
        for (r, c) in self.get_peers(row, col):
            self._candidates[r][c].discard(value)

    def _restore_to_peers(self, row: int, col: int, value: int) -> None:
        """
        Restore a value to peers (if not blocked by peers).
        Used when a value is removed (set(r,c,0)).
        """
        for (r, c) in self.get_peers(row, col):
            if self._grid[r, c] == EMPTY_CELL:
                self._candidates[r][c] = self._compute_candidates(r, c)

    def _compute_candidates(self, row: int, col: int) -> Set[int]:
        """Compute a cell's candidate values from scratch."""
        if self._grid[row, col] != EMPTY_CELL:
            return set()
        used = {self._grid[r, c] for (r, c) in self.get_peers(row, col)
                if self._grid[r, c] != EMPTY_CELL}
        return DIGITS - used

    def _recompute_all_candidates(self) -> None:
        """Recompute all candidates from scratch."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self._grid[r, c] == EMPTY_CELL:
                    self._candidates[r][c] = self._compute_candidates(r, c)
                else:
                    self._candidates[r][c] = set()

    # ============================================================
    # Serialization (for UI and tests)
    # ============================================================

    def to_list(self) -> List[List[int]]:
        """Return a JSON-compatible nested list for UI."""
        return self._grid.tolist()

    @classmethod
    def from_list(cls, data: List[List[int]]) -> "Board":
        """Create a board from nested list data (from UI)."""
        return cls(np.array(data, dtype=np.int8))

    @classmethod
    def from_string(cls, s: str) -> "Board":
        """
        Create a board from a single-line string.
        '.' or '0' = empty, '1'-'9' = value.
        Example: "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
        """
        s = s.replace(".", "0").replace(" ", "").replace("\n", "")
        if len(s) != 81:
            raise ValueError(f"String must be 81 characters, got: {len(s)}")
        grid = np.array([int(ch) for ch in s], dtype=np.int8).reshape(9, 9)
        return cls(grid)

    def to_string(self) -> str:
        """Convert to 81-character string. Uses '.' instead of 0."""
        return "".join("." if v == 0 else str(v) for row in self._grid for v in row)

    # ============================================================
    # Copying
    # ============================================================

    def copy(self) -> "Board":
        """Create an independent copy. Critical for backtracking and algorithms."""
        new_board = Board.__new__(Board)
        new_board._grid = self._grid.copy()
        new_board._fixed = self._fixed.copy()
        new_board._candidates = [[s.copy() for s in row] for row in self._candidates]
        return new_board

    def __deepcopy__(self, memo) -> "Board":
        return self.copy()

    # ============================================================
    # Visualization
    # ============================================================

    def __str__(self) -> str:
        """Pretty-print for console output."""
        lines = []
        for r in range(BOARD_SIZE):
            if r % 3 == 0 and r != 0:
                lines.append("------+-------+------")
            row_str = ""
            for c in range(BOARD_SIZE):
                if c % 3 == 0 and c != 0:
                    row_str += "| "
                v = self._grid[r, c]
                row_str += f"{v if v != 0 else '.'} "
            lines.append(row_str.rstrip())
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Board(filled={np.sum(self._grid != 0)}/81, valid={self.is_valid()})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return np.array_equal(self._grid, other._grid)

    def __hash__(self) -> int:
        return hash(self.to_string())