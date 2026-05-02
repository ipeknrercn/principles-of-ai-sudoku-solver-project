"""
tests/test_math.py

Math modülünün testleri.
"""

import pytest
import numpy as np
import math
from src.core.board import Board
from src.math_module.probability import (
    candidate_probability, shannon_entropy, board_entropy_map,
    total_uncertainty, most_uncertain_cell, expected_value_of_assignment,
    kl_divergence
)
from src.math_module.norms import (
    frobenius_norm, distance_to_target, conflict_matrix, build_constraint_matrix
)
from src.math_module.difficulty_scorer import difficulty_score, difficulty_label


EASY_PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
EASY_SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


class TestProbability:
    def test_filled_cell_probability_is_one(self):
        board = Board.from_string(EASY_PUZZLE)
        probs = candidate_probability(board, 0, 0)  # Sabit hücre = 5
        assert probs == {5: 1.0}
    
    def test_empty_cell_probability_uniform(self):
        board = Board()
        probs = candidate_probability(board, 0, 0)
        # Boş tahtada 9 candidate, hepsi 1/9
        assert len(probs) == 9
        assert all(abs(p - 1/9) < 1e-10 for p in probs.values())
    
    def test_entropy_filled_cell_is_zero(self):
        board = Board.from_string(EASY_PUZZLE)
        assert shannon_entropy(board, 0, 0) == 0.0
    
    def test_entropy_uniform_is_max(self):
        board = Board()  # boş tahta
        e = shannon_entropy(board, 0, 0)
        assert abs(e - math.log2(9)) < 1e-10
    
    def test_entropy_decreases_with_constraints(self):
        empty = Board()
        puzzle = Board.from_string(EASY_PUZZLE)
        # Doluluk arttıkça toplam entropy azalır
        assert total_uncertainty(puzzle) < total_uncertainty(empty)
    
    def test_solved_board_zero_uncertainty(self):
        solved = Board.from_string(EASY_SOLUTION)
        assert total_uncertainty(solved) == 0.0
    
    def test_most_uncertain_cell_finds_empty(self):
        board = Board.from_string(EASY_PUZZLE)
        r, c = most_uncertain_cell(board)
        assert board.is_empty(r, c)
    
    def test_expected_value_zero_for_filled(self):
        board = Board.from_string(EASY_PUZZLE)
        assert expected_value_of_assignment(board, 0, 0) == 0.0
    
    def test_expected_value_positive_for_empty(self):
        board = Board.from_string(EASY_PUZZLE)
        # En az bir boş hücre pozitif beklenen değere sahip olmalı
        any_positive = any(
            expected_value_of_assignment(board, r, c) > 0
            for r in range(9) for c in range(9)
        )
        assert any_positive
    
    def test_kl_divergence_self_is_zero(self):
        p = {1: 0.5, 2: 0.5}
        assert kl_divergence(p, p) < 1e-10


class TestNorms:
    def test_frobenius_zero(self):
        assert frobenius_norm(np.zeros((9, 9))) == 0.0
    
    def test_frobenius_identity(self):
        eye = np.eye(9)
        # Identity'nin Frobenius normu = sqrt(9) = 3
        assert abs(frobenius_norm(eye) - 3.0) < 1e-10
    
    def test_distance_zero_for_same_board(self):
        b = Board.from_string(EASY_PUZZLE)
        assert distance_to_target(b, b) == 0.0
    
    def test_distance_positive_for_different(self):
        b1 = Board.from_string(EASY_PUZZLE)
        b2 = Board.from_string(EASY_SOLUTION)
        assert distance_to_target(b1, b2) > 0.0
    
    def test_conflict_matrix_zero_for_valid(self):
        board = Board.from_string(EASY_PUZZLE)
        assert np.sum(conflict_matrix(board)) == 0
    
    def test_constraint_matrix_dimensions(self):
        m = build_constraint_matrix()
        assert m.shape == (324, 729)
        assert m.dtype == np.int8


class TestDifficulty:
    def test_solved_is_easy(self):
        board = Board.from_string(EASY_SOLUTION)
        score = difficulty_score(board)
        assert score < 0.3
    
    def test_empty_board_is_evil(self):
        board = Board()
        score = difficulty_score(board)
        assert score > 0.85
    
    def test_label_consistency(self):
        assert difficulty_label(0.1) == "Easy"
        assert difficulty_label(0.4) == "Medium"
        assert difficulty_label(0.6) == "Hard"
        assert difficulty_label(0.8) == "Expert"
        assert difficulty_label(0.95) == "Evil"
    
    def test_easy_puzzle_has_score(self):
        board = Board.from_string(EASY_PUZZLE)
        score = difficulty_score(board)
        # Bir easy puzzle 0-1 arası bir skor almalı
        assert 0.0 <= score <= 1.0