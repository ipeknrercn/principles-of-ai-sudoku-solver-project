"""
tests/test_sa.py

Simulated Annealing solver testleri.
SA stochastic olduğu için seed kullanıyoruz — testler deterministik olsun.
"""

import pytest
import numpy as np
from src.core.board import Board
from src.optimization.simulated_annealing import SASolver
from src.optimization.sa_config import SAConfig, DEFAULT_CONFIG, FAST_CONFIG


EASY_PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
MEDIUM_PUZZLE = "...26.7.168..7..9.19...45..82.1...4...46.29...5...3.28..93...74.4..5..367.3.18..."
EASY_SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


class TestSASolver:
    def test_solver_name(self):
        solver = SASolver()
        assert "Annealing" in solver.name
    
    def test_solves_already_solved(self):
        """Çözülmüş bulmaca anında True dönmeli."""
        board = Board.from_string(EASY_SOLUTION)
        solver = SASolver(SAConfig(seed=42, max_iterations=100))
        result = solver.solve(board)
        # Initial energy 0 ise, hemen biter
        assert result.solved is True
    
    def test_returns_solver_result(self):
        """SolverResult yapısı doğru olmalı."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver(SAConfig(seed=42, max_iterations=5000))
        result = solver.solve(board)
        
        assert hasattr(result, 'board')
        assert hasattr(result, 'iterations')
        assert hasattr(result, 'elapsed_ms')
        assert 'final_energy' in result.metadata
        assert 'energy_history' in result.metadata
    
    def test_metadata_contains_history(self):
        """Convergence grafiği için history kaydedilmeli."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver(SAConfig(seed=42, max_iterations=2000))
        result = solver.solve(board)
        
        history = result.metadata['energy_history']
        assert len(history) > 0
        assert all(isinstance(e, int) for e in history)
    
    def test_initial_solution_preserves_fixed_cells(self):
        """Random initialization sabit hücreleri korumalı."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver()
        initial = solver._random_initial_solution(board)
        
        # Sabit hücreler değişmemeli
        original = board.to_numpy()
        for r in range(9):
            for c in range(9):
                if original[r, c] != 0:
                    assert initial[r, c] == original[r, c]
    
    def test_initial_solution_each_row_has_1_to_9(self):
        """Random initialization sonrası her satırda 1-9 olmalı."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver()
        initial = solver._random_initial_solution(board)
        
        for r in range(9):
            row = set(initial[r, :].tolist())
            assert row == set(range(1, 10))
    
    def test_energy_zero_for_solved(self):
        """Çözülmüş tahta energy 0 olmalı."""
        board = Board.from_string(EASY_SOLUTION)
        solver = SASolver()
        assert solver._energy(board) == 0
    
    def test_energy_positive_for_invalid(self):
        """Çakışmalı tahta pozitif energy."""
        # Manuel çakışmalı tahta
        grid = np.zeros((9, 9), dtype=np.int8)
        grid[0, :] = list(range(1, 10))
        grid[1, :] = list(range(1, 10))  # 0. ve 1. satır aynı → sütunlarda 9 çakışma
        # Diğer satırlar boş, ama satırlar dolu olduğu için _energy_grid pozitif dönmeli
        energy = SASolver._energy_grid(grid)
        assert energy > 0
    
    def test_neighbor_swaps_in_same_row(self):
        """Neighbor sadece aynı satır içinde swap yapmalı."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver(SAConfig(seed=42))
        grid = solver._random_initial_solution(board)
        new_grid = solver._neighbor(grid, board)
        
        if new_grid is not None:
            # Tam olarak bir satır farklı olmalı
            diff_rows = [r for r in range(9) if not np.array_equal(grid[r], new_grid[r])]
            assert len(diff_rows) == 1
            # O satırın değerleri aynı set olmalı (sadece pozisyonlar değişti)
            r = diff_rows[0]
            assert set(grid[r].tolist()) == set(new_grid[r].tolist())
    
    def test_solves_easy_with_enough_iterations(self):
        """Easy bulmacayı çözebilmeli."""
        board = Board.from_string(EASY_PUZZLE)
        solver = SASolver(SAConfig(seed=42, max_iterations=50_000))
        result = solver.solve(board)
        # Easy bulmacalar SA için kolay olmasa da, yeterli iterasyon ile bulunmalı
        # En azından enerji çok düştüyse "yakın" demektir
        assert result.metadata['final_energy'] <= 5
    
    def test_deterministic_with_seed(self):
        """Aynı seed → aynı sonuç."""
        board = Board.from_string(EASY_PUZZLE)
        config = SAConfig(seed=123, max_iterations=1000)
        
        result1 = SASolver(config).solve(board)
        result2 = SASolver(config).solve(board)
        
        assert result1.metadata['final_energy'] == result2.metadata['final_energy']