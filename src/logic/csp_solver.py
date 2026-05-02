"""
src/logic/csp_solver.py

Ana logic solver. Inference + AC-3 + backtracking kombinasyonu.

Akış:
1. Constraint propagation (AC-3) ile candidates'ı daralt
2. Naked Singles + Hidden Singles uygula
3. Eğer hala boş hücre varsa, MRV ile en kısıtlanmış hücreyi seç ve tahmin et (backtracking)
"""

from __future__ import annotations
import time
from typing import List, Optional, Tuple
from src.core.board import Board
from src.core.solver_base import BaseSolver, SolverResult
from src.logic.inference_rules import apply_naked_single, apply_hidden_single, InferenceStep
from src.logic.ac3 import propagate_constraints


class LogicSolver(BaseSolver):
    """CSP tabanlı logic solver. Easy/Medium bulmacaları %100, Hard'ları çoğunlukla çözer."""
    
    @property
    def name(self) -> str:
        return "Logic Solver (CSP + Backtracking)"
    
    def solve(self, board: Board) -> SolverResult:
        start = time.perf_counter()
        working_board = board.copy()
        
        steps: List[InferenceStep] = []
        iterations = 0
        backtrack_count = 0
        
        # Önce AC-3 ile temel propagation
        if not propagate_constraints(working_board):
            return self._build_result(working_board, False, iterations, start, steps,
                                       {"backtracks": backtrack_count, "error": "Initial inconsistency"})
        
        # Inference + backtracking döngüsü
        solved_board, success, backtrack_count = self._solve_recursive(
            working_board, steps, iterations
        )
        
        return self._build_result(
            solved_board, success, iterations, start, steps,
            {"backtracks": backtrack_count, "inference_steps": len(steps)}
        )
    
    def _solve_recursive(
        self, board: Board, steps: List[InferenceStep], iterations: int
    ) -> Tuple[Board, bool, int]:
        """Inference + backtracking ile recursive çözüm."""
        backtracks = 0
        
        # Inference uygula (sabit nokta — değişiklik olmayana kadar)
        while True:
            step = apply_naked_single(board)
            if step is None:
                step = apply_hidden_single(board)
            
            if step is None:
                break  # Daha fazla inference yapılamıyor
            
            try:
                board.set(step.row, step.col, step.value)
                steps.append(step)
                # Yeni atama sonrası constraint propagation
                if not propagate_constraints(board):
                    return board, False, backtracks
            except RuntimeError:
                pass  # Sabit hücre, atlanır
        
        # Çözüldü mü?
        if board.is_solved():
            return board, True, backtracks
        
        # Hala boş hücre var — backtracking gerekli
        # MRV: en az candidates'ı olan boş hücreyi seç
        best_cell = self._select_mrv_cell(board)
        if best_cell is None:
            # Boş hücre yok ama çözülmemiş — geçersiz durum
            return board, False, backtracks
        
        r, c = best_cell
        candidates = board.get_candidates(r, c)
        
        if len(candidates) == 0:
            return board, False, backtracks  # Çözümsüz
        
        # Her olası değeri dene
        for value in sorted(candidates):
            backtracks += 1
            trial = board.copy()
            try:
                trial.set(r, c, value)
                steps.append(InferenceStep(
                    rule_name="Backtracking",
                    row=r, col=c, value=value,
                    reason=f"Trying value {value} at ({r},{c}) [MRV-selected]"
                ))
                if propagate_constraints(trial):
                    result, success, sub_backtracks = self._solve_recursive(trial, steps, iterations)
                    backtracks += sub_backtracks
                    if success:
                        return result, True, backtracks
            except RuntimeError:
                continue
        
        return board, False, backtracks
    
    def _select_mrv_cell(self, board: Board) -> Optional[Tuple[int, int]]:
        """MRV: Minimum Remaining Values heuristic — en kısıtlanmış hücreyi seç."""
        best_cell = None
        best_size = 10
        
        for r, c in board.empty_cells():
            size = len(board.get_candidates(r, c))
            if 0 < size < best_size:
                best_size = size
                best_cell = (r, c)
                if size == 1:
                    return best_cell  # Erken çıkış
        
        return best_cell
    
    @staticmethod
    def _build_result(board, solved, iterations, start, steps, metadata):
        elapsed_ms = (time.perf_counter() - start) * 1000
        return SolverResult(
            board=board,
            solved=solved,
            iterations=iterations,
            elapsed_ms=elapsed_ms,
            steps=[str(s) for s in steps],
            metadata=metadata
        )