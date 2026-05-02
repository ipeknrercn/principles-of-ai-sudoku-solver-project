"""
tests/test_board.py

Tests for the Board class.
At least 1 test for each public method, plus extra edge-case tests.
"""

import pytest
import numpy as np
from src.core.board import Board, BOARD_SIZE, EMPTY_CELL, DIGITS


# Test fixtures (repeated test data)

EASY_PUZZLE_STRING = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

EASY_SOLUTION_STRING = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)


class TestBoardCreation:
    """Board creation tests."""

    def test_empty_board(self):
        """Empty board should be created correctly."""
        board = Board()
        assert board.to_numpy().shape == (9, 9)
        assert np.all(board.to_numpy() == 0)

    def test_board_from_numpy(self):
        """Create board from NumPy array."""
        grid = np.array([[5, 3, 0, 0, 7, 0, 0, 0, 0]] + [[0] * 9] * 8, dtype=np.int8)
        board = Board(grid)
        assert board.get(0, 0) == 5
        assert board.get(0, 1) == 3
        assert board.get(0, 2) == 0

    def test_board_from_string(self):
        """Create board from string."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert board.get(0, 0) == 5
        assert board.get(0, 1) == 3
        assert board.is_empty(0, 2)

    def test_invalid_shape_raises(self):
        """Invalid shape should raise an error."""
        with pytest.raises(ValueError):
            Board(np.zeros((8, 8), dtype=np.int8))

    def test_invalid_value_raises(self):
        """Values outside 0-9 should raise an error."""
        grid = np.zeros((9, 9), dtype=np.int8)
        grid[0, 0] = 10
        with pytest.raises(ValueError):
            Board(grid)


class TestCellOperations:
    """Cell read/write tests."""

    def test_get_set(self):
        """Assign and read a cell value."""
        board = Board()
        board.set(4, 4, 7)
        assert board.get(4, 4) == 7

    def test_fixed_cell_cannot_change(self):
        """Fixed cell should not be modifiable."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        with pytest.raises(RuntimeError):
            board.set(0, 0, 9)  # (0,0) is fixed (5)

    def test_clear_cell(self):
        """Clear a cell by setting it to 0."""
        board = Board()
        board.set(4, 4, 7)
        board.set(4, 4, 0)
        assert board.is_empty(4, 4)

    def test_invalid_value_raises(self):
        """Assigning values outside 0-9 should raise an error."""
        board = Board()
        with pytest.raises(ValueError):
            board.set(0, 0, 10)


class TestCandidates:
    """Candidate-value tests."""

    def test_empty_cell_has_all_digits_initially(self):
        """On an empty board, each cell's candidates should be {1..9}."""
        board = Board()
        assert board.get_candidates(0, 0) == set(DIGITS)

    def test_fixed_cell_has_no_candidates(self):
        """A fixed cell should have no candidates."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert board.get_candidates(0, 0) == set()

    def test_candidates_eliminated_by_peers(self):
        """Peer values should be removed from candidates."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        # (0,0)=5 and (0,1)=3 are given. (0,2) candidates should exclude 5 and 3.
        candidates = board.get_candidates(0, 2)
        assert 5 not in candidates
        assert 3 not in candidates

    def test_setting_value_updates_peers(self):
        """Assigning a value should update peers' candidates."""
        board = Board()
        board.set(0, 0, 5)
        # (0,1), (1,0), (1,1) are all peers; 5 should be removed from candidates
        assert 5 not in board.get_candidates(0, 1)
        assert 5 not in board.get_candidates(1, 0)
        assert 5 not in board.get_candidates(1, 1)


class TestSudokuRules:
    """Sudoku rule tests."""

    def test_valid_empty_board(self):
        """Empty board should be considered valid."""
        assert Board().is_valid()

    def test_valid_puzzle(self):
        """A valid puzzle should be considered valid."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert board.is_valid()

    def test_solved_board(self):
        """Solved board should return True for is_solved()."""
        board = Board.from_string(EASY_SOLUTION_STRING)
        assert board.is_solved()

    def test_unsolved_puzzle_not_solved(self):
        """Incomplete puzzle should return False for is_solved()."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert not board.is_solved()

    def test_count_conflicts_zero_in_valid(self):
        """Conflict count should be 0 for a valid puzzle."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert board.count_conflicts() == 0

    def test_count_conflicts_detects_duplicate(self):
        """Placing two 5s in the same row should create conflicts."""
        # Create board without fixed cells (manual)
        board = Board()
        board.set(0, 0, 5)
        board.set(0, 1, 5)  # 5 in the same row — conflict
        assert board.count_conflicts() > 0


class TestPeers:
    """Peer (neighbor) tests."""

    def test_peers_count(self):
        """Each cell should have 20 peers."""
        board = Board()
        peers = board.get_peers(4, 4)
        assert len(peers) == 20

    def test_peers_include_row_col_box(self):
        """Peers should include row + column + box cells."""
        board = Board()
        peers = board.get_peers(0, 0)
        # Row
        assert (0, 5) in peers
        # Column
        assert (5, 0) in peers
        # Box (top-left 3x3)
        assert (1, 1) in peers
        # The cell itself is not a peer
        assert (0, 0) not in peers


class TestSerialization:
    """Serialization tests."""

    def test_to_from_list(self):
        """Conversion to and from list should be consistent."""
        original = Board.from_string(EASY_PUZZLE_STRING)
        list_data = original.to_list()
        restored = Board.from_list(list_data)
        assert original == restored

    def test_to_from_string(self):
        """Conversion to and from string should be consistent."""
        original = Board.from_string(EASY_PUZZLE_STRING)
        s = original.to_string()
        restored = Board.from_string(s)
        assert original == restored

    def test_to_tensor_shape(self):
        """Tensor should be 9x9x9."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        tensor = board.to_tensor()
        assert tensor.shape == (9, 9, 9)

    def test_tensor_correctness(self):
        """Tensor[r,c,k-1] = 1 iff grid[r,c] = k."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        tensor = board.to_tensor()
        # (0,0) = 5 -> tensor[0, 0, 4] = 1
        assert tensor[0, 0, 4] == 1
        assert tensor[0, 0, 0] == 0  # not 1


class TestCopy:
    """Copy tests."""

    def test_copy_independence(self):
        """Copy should be independent."""
        original = Board.from_string(EASY_PUZZLE_STRING)
        copy = original.copy()
        copy.set(0, 2, 1)  # Assign value to empty cell
        assert original.get(0, 2) == 0  # Original should not change
        assert copy.get(0, 2) == 1

    def test_copy_preserves_state(self):
        """Copy should preserve full state correctly."""
        original = Board.from_string(EASY_PUZZLE_STRING)
        copy = original.copy()
        assert original == copy
        assert original.get_candidates(0, 2) == copy.get_candidates(0, 2)



class TestEdgeCases:
    """Edge-case and error-path tests to increase coverage."""

    def test_invalid_grid_type(self):
        """Non-NumPy input type should raise an error."""
        with pytest.raises(TypeError):
            Board(grid=[[0] * 9] * 9)  # list, not NumPy

    def test_set_invalid_cell_coords(self):
        """Invalid cell coordinates should raise an error."""
        board = Board()
        with pytest.raises(ValueError):
            board.set(9, 0, 5)  # row=9 is invalid
        with pytest.raises(ValueError):
            board.set(0, -1, 5)  # col=-1 is invalid

    def test_set_candidates_invalid(self):
        """Invalid candidates should raise an error."""
        board = Board()
        with pytest.raises(ValueError):
            board.set_candidates(0, 0, {10, 11})  # outside 1-9

    def test_set_candidates_valid(self):
        """Valid candidates should be assignable."""
        board = Board()
        board.set_candidates(0, 0, {1, 2, 3})
        assert board.get_candidates(0, 0) == {1, 2, 3}

    def test_eliminate_candidate_existing(self):
        """Remove an existing candidate value."""
        board = Board()
        result = board.eliminate_candidate(0, 0, 5)
        assert result is True
        assert 5 not in board.get_candidates(0, 0)

    def test_eliminate_candidate_nonexistent(self):
        """Removing a missing value should return False."""
        board = Board()
        board.eliminate_candidate(0, 0, 5)  # remove 5
        result = board.eliminate_candidate(0, 0, 5)  # try removing again
        assert result is False

    def test_is_fixed(self):
        """is_fixed method should work correctly."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        assert board.is_fixed(0, 0) is True   # 5 is given
        assert board.is_fixed(0, 2) is False  # empty

    def test_from_numpy_preserves_fixed(self):
        """from_numpy should preserve fixed cells."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        # Load a fully filled grid into empty cells
        new_grid = np.full((9, 9), 1, dtype=np.int8)  # all ones
        board.from_numpy(new_grid)
        # Fixed cell should not change
        assert board.get(0, 0) == 5  # still 5
        # Empty cell should be updated
        assert board.get(0, 2) == 1

    def test_empty_cells_iterator(self):
        """empty_cells iterator should return all empty cells."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        empty = list(board.empty_cells())
        # In easy puzzle, there should be many empty cells
        assert len(empty) > 0
        # Are all returned cells truly empty?
        for r, c in empty:
            assert board.is_empty(r, c)

    def test_string_invalid_length(self):
        """String length other than 81 should raise an error."""
        with pytest.raises(ValueError):
            Board.from_string("12345")  # too short

    def test_string_with_dots(self):
        """'.' character should be interpreted as 0."""
        s = "5.." + "." * 78  # 81 chars, only 5 is fixed
        board = Board.from_string(s)
        assert board.get(0, 0) == 5
        assert board.is_empty(0, 1)

    def test_string_with_whitespace(self):
        """Spaces and newlines in string should be cleaned."""
        s = "5 . . " + "." * 77 + "."
        # 78 + 3 = 81 characters (excluding spaces)
        s_clean = s.replace(" ", "")
        assert len(s_clean) == 81
        board = Board.from_string(s)
        assert board.get(0, 0) == 5

    def test_repr(self):
        """__repr__ check."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        r = repr(board)
        assert "Board" in r
        assert "valid" in r

    def test_str_format(self):
        """__str__ check — pretty print should work."""
        board = Board.from_string(EASY_PUZZLE_STRING)
        s = str(board)
        # Box separator lines should exist
        assert "------" in s
        # Empty cells should be '.'
        assert "." in s
        # 5 should appear (given)
        assert "5" in s

    def test_equality(self):
        """Two same boards should be equal, different ones should not."""
        b1 = Board.from_string(EASY_PUZZLE_STRING)
        b2 = Board.from_string(EASY_PUZZLE_STRING)
        b3 = Board()
        assert b1 == b2
        assert b1 != b3
        assert b1 != "string not a Board"  # different type

    def test_hash(self):
        """Hashes of equal boards should match."""
        b1 = Board.from_string(EASY_PUZZLE_STRING)
        b2 = Board.from_string(EASY_PUZZLE_STRING)
        assert hash(b1) == hash(b2)
        # Should be insertable into a set (verify hashability)
        board_set = {b1, b2}
        assert len(board_set) == 1  # one element because they are equal

    def test_deepcopy(self):
        """deepcopy should work."""
        from copy import deepcopy
        b1 = Board.from_string(EASY_PUZZLE_STRING)
        b2 = deepcopy(b1)
        assert b1 == b2
        # Independence check
        b2.set(0, 2, 1)
        assert b1.get(0, 2) == 0