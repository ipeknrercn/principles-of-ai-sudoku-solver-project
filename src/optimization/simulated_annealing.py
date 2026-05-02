"""
src/optimization/simulated_annealing.py

Simulated Annealing tabanlı Sudoku çözücü.

Algoritma:
1. Random initial solution (her satırda 1-9)
2. Energy = column conflicts + box conflicts (rows are always valid by construction)
3. Move = swap two non-fixed cells in the same row
4. Accept move if ΔE < 0, else with probability e^(-ΔE/T)
5. Cool down T geometrically
6. Reheat if stuck in local minimum
"""

from __future__ import annotations
import math
import random
import time
from typing import List, Optional, Tuple
import numpy as np

from src.core.board import Board, BOARD_SIZE, BOX_SIZE
from src.core.solver_base import BaseSolver, SolverResult
from src.optimization.sa_config import SAConfig, DEFAULT_CONFIG


class SASolver(BaseSolver):
    """
    Simulated Annealing tabanlı Sudoku çözücü.
    
    Logic solver'ın aksine:
    - Hard ve Expert bulmacaları da çözebilir
    - Stochastic — aynı bulmacayı farklı sürelerde çözebilir
    - Convergence garantisi yok, ama pratikte yüksek başarı
    """
    
    def __init__(self, config: SAConfig = DEFAULT_CONFIG):
        self.config = config
        if config.seed is not None:
            random.seed(config.seed)
            np.random.seed(config.seed)
    
    @property
    def name(self) -> str:
        return "Simulated Annealing"
    
    def solve(self, board: Board) -> SolverResult:
        start = time.perf_counter()
        
        # 1) Başlangıç durumu: her satırı rastgele doldur (1-9 olacak şekilde)
        current = self._random_initial_solution(board)
        current_energy = self._energy_grid(current)
        
        best = current.copy()
        best_energy = current_energy
        
        # İzleme verileri (rapor için convergence grafikleri)
        energy_history: List[int] = [current_energy]
        temperature_history: List[float] = [self.config.initial_temperature]
        
        # SA döngüsü
        T = self.config.initial_temperature
        iterations = 0
        stuck_counter = 0
        reheats = 0
        
        while iterations < self.config.max_iterations and best_energy > 0:
            for _ in range(self.config.iterations_per_temperature):
                iterations += 1
                
                # Komşu üret: aynı satırdan iki non-fixed hücreyi swap'le
                new_grid = self._neighbor(current, board)
                if new_grid is None:
                    continue
                
                new_energy = self._energy_grid(new_grid)
                delta = new_energy - current_energy
                
                # Acceptance kriteri
                if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-12)):
                    current = new_grid
                    current_energy = new_energy
                    
                    if current_energy < best_energy:
                        best = current.copy()
                        best_energy = current_energy
                        stuck_counter = 0
                    else:
                        stuck_counter += 1
                else:
                    stuck_counter += 1
                
                # Erken çıkış: çözüldü
                if best_energy == 0:
                    break
            
            # Sıcaklığı düşür (geometric cooling)
            T = max(T * self.config.cooling_rate, self.config.min_temperature)
            
            # Reheat: sıkışmışsak sıcaklığı tekrar yükselt
            if (self.config.enable_reheat and 
                stuck_counter >= self.config.stuck_threshold and 
                best_energy > 0):
                T = self.config.initial_temperature * self.config.reheat_factor
                stuck_counter = 0
                reheats += 1
            
            # İzleme verisi (her sıcaklık adımında kayıt)
            energy_history.append(best_energy)
            temperature_history.append(T)
            
            if best_energy == 0:
                break
        
        # Sonuç board'unu inşa et
        result_board = self._grid_to_board(best, board)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        return SolverResult(
            board=result_board,
            solved=(best_energy == 0),
            iterations=iterations,
            elapsed_ms=elapsed_ms,
            steps=[
                f"Initial energy: {energy_history[0]}",
                f"Final energy: {best_energy}",
                f"Reheats: {reheats}",
                f"Final temperature: {T:.4f}",
            ],
            metadata={
                "final_energy": best_energy,
                "reheats": reheats,
                "energy_history": energy_history,
                "temperature_history": temperature_history,
                "config": {
                    "initial_temperature": self.config.initial_temperature,
                    "cooling_rate": self.config.cooling_rate,
                    "max_iterations": self.config.max_iterations,
                }
            }
        )
    
    # ============================================================
    # Yardımcı metotlar
    # ============================================================
    
    @staticmethod
    def _random_initial_solution(board: Board) -> np.ndarray:
        """
        Her satırda 1-9 olacak şekilde rastgele başlangıç tahtası üret.
        Sabit hücreler korunur.
        """
        grid = board.to_numpy().copy()
        for r in range(BOARD_SIZE):
            # Sabit (verilen) değerleri tespit et
            fixed_values = {grid[r, c] for c in range(BOARD_SIZE) if grid[r, c] != 0}
            # Eksik değerleri belirle
            missing = list(set(range(1, 10)) - fixed_values)
            random.shuffle(missing)
            
            # Boş hücreleri eksik değerlerle doldur
            idx = 0
            for c in range(BOARD_SIZE):
                if grid[r, c] == 0:
                    grid[r, c] = missing[idx]
                    idx += 1
        return grid
    
    @staticmethod
    def _energy(board: Board) -> int:
        """Board'un enerjisi: count_conflicts (Board sınıfındaki yardımcı)."""
        return board.count_conflicts()
    
    @staticmethod
    def _energy_grid(grid: np.ndarray) -> int:
        """
        Bir grid'in enerjisi.
        Her satır construction tarafından geçerli olduğundan,
        sadece sütun + blok çakışmalarını sayarız.
        """
        conflicts = 0
        # Sütun çakışmaları
        for c in range(BOARD_SIZE):
            col = grid[:, c]
            conflicts += BOARD_SIZE - len(set(col.tolist()))
        # Blok çakışmaları
        for box_r in range(0, BOARD_SIZE, BOX_SIZE):
            for box_c in range(0, BOARD_SIZE, BOX_SIZE):
                box = grid[box_r:box_r + BOX_SIZE, box_c:box_c + BOX_SIZE].flatten()
                conflicts += BOX_SIZE * BOX_SIZE - len(set(box.tolist()))
        return conflicts
    
    @staticmethod
    def _neighbor(grid: np.ndarray, original_board: Board) -> Optional[np.ndarray]:
        """
        Komşu durum üret: rastgele bir satırda iki non-fixed hücreyi swap'le.
        
        Returns:
            Yeni grid (kopya) veya None (swap mümkün değilse).
        """
        # Rastgele satır seç
        r = random.randint(0, BOARD_SIZE - 1)
        
        # Bu satırdaki non-fixed hücreleri bul
        non_fixed_cols = [
            c for c in range(BOARD_SIZE)
            if not original_board.is_fixed(r, c)
        ]
        
        if len(non_fixed_cols) < 2:
            return None  # Swap için en az 2 non-fixed hücre lazım
        
        # İki rastgele non-fixed hücre seç
        c1, c2 = random.sample(non_fixed_cols, 2)
        
        new_grid = grid.copy()
        new_grid[r, c1], new_grid[r, c2] = new_grid[r, c2], new_grid[r, c1]
        return new_grid
    
    @staticmethod
    def _grid_to_board(grid: np.ndarray, original_board: Board) -> Board:
        """Grid'den Board nesnesi oluştur (sabit hücreler korunur)."""
        new_board = Board.from_list(original_board.to_list())  # sabit hücreleri korur
        new_board.from_numpy(grid)
        return new_board