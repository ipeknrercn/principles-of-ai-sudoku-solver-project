"""
src/math_module/norms.py

Sudoku için Linear Algebra fonksiyonları.

Math of AI pillar'ının Linear Algebra bileşeni:
- Frobenius norm (matris uzaklığı)
- Distance from solved state
- Constraint matrix yapısı
"""

from __future__ import annotations
import numpy as np
from src.core.board import Board, BOARD_SIZE


def frobenius_norm(matrix: np.ndarray) -> float:
    """
    Frobenius normu: ||A||_F = sqrt(Σ a_ij^2)
    
    İki matris arasındaki uzaklığı ölçmek için kullanılır.
    """
    return float(np.linalg.norm(matrix, ord='fro'))


def distance_to_target(current: Board, target: Board) -> float:
    """
    İki tahta arasındaki Frobenius normu (uzaklık).
    
    Eğer target tam çözümse, bu metric SA/GA için "mevcut durum
    ne kadar yakın?" ölçütü olur. 0 = aynı.
    """
    diff = current.to_numpy().astype(np.float64) - target.to_numpy().astype(np.float64)
    return frobenius_norm(diff)


def conflict_matrix(board: Board) -> np.ndarray:
    """
    9x9 çakışma matrisi: her hücrenin kaç çakışmaya dahil olduğunu gösterir.
    
    UI'da kırmızı tonlarda gösterilebilir — kullanıcı hatalı hücreleri görür.
    """
    matrix = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int32)
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            value = board.get(r, c)
            if value == 0:
                continue
            # Bu hücre kaç peer ile çakışıyor?
            for (pr, pc) in board.get_peers(r, c):
                if board.get(pr, pc) == value:
                    matrix[r, c] += 1
    
    return matrix


def build_constraint_matrix() -> np.ndarray:
    """
    Sudoku CSP'sinin constraint matrisini oluştur.
    
    Boyut: 324 x 729
    - 324 kısıt: 81 cell + 81 row+digit + 81 col+digit + 81 box+digit
    - 729 değişken: 9x9x9 (her hücre için 9 olası değer)
    
    Bu, exact cover problemi olarak Sudoku'nun matematiksel ifadesidir.
    Raporda gösterilebilecek güzel bir matematiksel yapı.
    """
    n_constraints = 4 * 81  # 324
    n_variables = 9 * 9 * 9  # 729
    matrix = np.zeros((n_constraints, n_variables), dtype=np.int8)
    
    var_idx = lambda r, c, d: r * 81 + c * 9 + d
    
    constraint = 0
    
    # 1. Her hücrede en az bir değer olmalı
    for r in range(9):
        for c in range(9):
            for d in range(9):
                matrix[constraint, var_idx(r, c, d)] = 1
            constraint += 1
    
    # 2. Her satırda her digit bir kez
    for r in range(9):
        for d in range(9):
            for c in range(9):
                matrix[constraint, var_idx(r, c, d)] = 1
            constraint += 1
    
    # 3. Her sütunda her digit bir kez
    for c in range(9):
        for d in range(9):
            for r in range(9):
                matrix[constraint, var_idx(r, c, d)] = 1
            constraint += 1
    
    # 4. Her blokta her digit bir kez
    for box_r in range(0, 9, 3):
        for box_c in range(0, 9, 3):
            for d in range(9):
                for dr in range(3):
                    for dc in range(3):
                        matrix[constraint, var_idx(box_r + dr, box_c + dc, d)] = 1
                constraint += 1
    
    return matrix