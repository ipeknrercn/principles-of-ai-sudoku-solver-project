"""
src/core/solver.py

Tüm solver'ları birleştiren ana sınıf.
UI bu sınıfı çağırır, hangi algoritma kullanılacaksa o devreye girer.
"""

from __future__ import annotations
from enum import Enum
from src.core.board import Board
from src.core.solver_base import BaseSolver, SolverResult
from src.core.mock_solver import MockSolver


class SolverMode(Enum):
    """Kullanıcının seçebileceği solver modları."""
    LOGIC_ONLY = "logic"
    SIMULATED_ANNEALING = "sa"
    GENETIC_ALGORITHM = "ga"
    HYBRID = "hybrid"  # Önce logic, kalanını optimization


class SudokuSolver:
    """
    Ana entegrasyon sınıfı. UI bunu çağırır.
    
    Kullanım:
        solver = SudokuSolver()
        result = solver.solve(board, mode=SolverMode.HYBRID)
    """

    def __init__(self):
    # Faz 1'den gelen mock'ları gerçek solver'larla değiştiriyoruz
        from src.logic.csp_solver import LogicSolver
        
        logic_solver = LogicSolver()
        
        self._solvers: dict[SolverMode, BaseSolver] = {
            SolverMode.LOGIC_ONLY: logic_solver,           # ✅ Gerçek logic solver
            SolverMode.SIMULATED_ANNEALING: MockSolver(),  # Hala mock — SA Specialist yapacak
            SolverMode.GENETIC_ALGORITHM: MockSolver(),    # Hala mock — GA Specialist yapacak
            SolverMode.HYBRID: logic_solver,               # ✅ Şimdilik logic, sonra hybrid yapacağız
        }
    def solve(self, board: Board, mode: SolverMode = SolverMode.HYBRID) -> SolverResult:
        """Seçilen mode'a göre uygun solver'ı çağır."""
        if mode not in self._solvers:
            raise ValueError(f"Bilinmeyen mode: {mode}")
        return self._solvers[mode].solve(board)

    def register_solver(self, mode: SolverMode, solver: BaseSolver) -> None:
        """
        Faz 2'de gerçek solver'lar geldikçe burada kayıt edilecek.
        Örnek: solver.register_solver(SolverMode.LOGIC_ONLY, LogicCSPSolver())
        """
        self._solvers[mode] = solver