"""
src/core/mock_solver.py

UI Designer'ın gerçek solver hazır olmadan çalışabilmesi için sahte solver.
Ekip Faz 2'de gerçek solver'ları yazana kadar UI bunu kullanır.
"""

from __future__ import annotations
import time
import random
from src.core.board import Board
from src.core.solver_base import BaseSolver, SolverResult


class MockSolver(BaseSolver):
    """Demo amaçlı sahte solver — gerçek solver hazır olunca silinecek."""

    @property
    def name(self) -> str:
        return "Mock Solver (Demo)"

    def solve(self, board: Board) -> SolverResult:
        # Sahte gecikme — gerçek hesap gibi görünsün
        time.sleep(0.5)
        
        # Sahte sonuç: tahtayı olduğu gibi döndür, "yapay" iterasyonlar
        return SolverResult(
            board=board.copy(),
            solved=False,
            iterations=random.randint(100, 5000),
            elapsed_ms=500.0,
            steps=["Mock solver çalıştı", "Bu sahte bir cevap"],
            metadata={"is_mock": True}
        )