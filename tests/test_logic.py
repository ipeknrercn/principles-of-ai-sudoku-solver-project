"""
tests/test_logic.py

Logic solver ve inference kurallarının testleri.
"""

import pytest
from src.core.board import Board
from src.logic.csp_solver import LogicSolver
from src.logic.inference_rules import apply_naked_single, apply_hidden_single
from src.logic.ac3 import propagate_constraints


# Test fixtures
EASY_PUZZLE = (
    "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
)
EASY_SOLUTION = (
    "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
)

MEDIUM_PUZZLE = (
    "...26.7.168..7..9.19...45..82.1...4...46.29...5...3.28..93...74.4..5..367.3.18..."
)


class TestInferenceRules:
    def test_naked_single_finds_solution(self):
        """Tek olası değeri olan hücreyi tespit etmeli."""
        board = Board.from_string(EASY_PUZZLE)
        propagate_constraints(board)
        step = apply_naked_single(board)
        # Easy puzzle'da naked single bulunmalı
        assert step is not None
        assert step.rule_name == "Naked Single"
    
    def test_hidden_single_finds_solution(self):
        """Hidden single tespiti çalışmalı."""
        board = Board.from_string(EASY_PUZZLE)
        propagate_constraints(board)
        step = apply_hidden_single(board)
        # Hidden single bulunabilir
        assert step is None or step.rule_name.startswith("Hidden Single")


class TestAC3:
    def test_ac3_consistent_puzzle(self):
        """Geçerli puzzle'da AC-3 True dönmeli."""
        board = Board.from_string(EASY_PUZZLE)
        assert propagate_constraints(board) is True
    
    def test_ac3_reduces_candidates(self):
        """AC-3 candidates'ı azaltmalı."""
        board = Board.from_string(EASY_PUZZLE)
        # (0,2) hücresi başta {1,2,3,4,5,6,7,8,9} - peers
        before = len(board.get_candidates(0, 2))
        propagate_constraints(board)
        after = len(board.get_candidates(0, 2))
        assert after <= before


class TestLogicSolver:
    def test_solves_easy(self):
        """Easy puzzle'ı çözmeli."""
        board = Board.from_string(EASY_PUZZLE)
        solver = LogicSolver()
        result = solver.solve(board)
        assert result.solved is True
        assert result.board.is_solved()
        assert result.board.to_string() == EASY_SOLUTION
    
    def test_solves_medium(self):
        """Medium puzzle'ı çözmeli."""
        board = Board.from_string(MEDIUM_PUZZLE)
        solver = LogicSolver()
        result = solver.solve(board)
        assert result.solved is True
        assert result.board.is_solved()
    
    def test_records_inference_steps(self):
        """Inference adımları kaydedilmeli."""
        board = Board.from_string(EASY_PUZZLE)
        solver = LogicSolver()
        result = solver.solve(board)
        assert len(result.steps) > 0
        # Adımlar string olmalı (UI için hazır)
        assert all(isinstance(s, str) for s in result.steps)
    
    def test_records_metadata(self):
        """Metadata doğru bilgi içermeli."""
        board = Board.from_string(EASY_PUZZLE)
        solver = LogicSolver()
        result = solver.solve(board)
        assert "backtracks" in result.metadata
        assert "inference_steps" in result.metadata
    
    def test_already_solved_board(self):
        """Çözülmüş board verilirse hızlıca True dönmeli."""
        board = Board.from_string(EASY_SOLUTION)
        solver = LogicSolver()
        result = solver.solve(board)
        assert result.solved is True
    
    def test_solver_name(self):
        """Solver'ın adı düzgün dönmeli."""
        solver = LogicSolver()
        assert "Logic" in solver.name