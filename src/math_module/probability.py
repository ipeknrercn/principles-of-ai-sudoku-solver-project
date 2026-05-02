"""
src/math_module/probability.py

Sudoku için probability tabanlı analiz fonksiyonları.

Math of AI pillar'ının probability bileşeni:
- Olasılık dağılımları (probability distributions)
- Shannon entropy
- Expected value
- KL divergence (bonus)
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple
import numpy as np
from src.core.board import Board, BOARD_SIZE, DIGITS


def candidate_probability(board: Board, row: int, col: int) -> Dict[int, float]:
    """
    Bir hücredeki candidates için uniform probability distribution döndür.
    
    Eğer hücrede 3 candidate varsa, her birinin olasılığı 1/3.
    Bu, "bilgi yoksa eşit dağılım" prensibi (maximum entropy principle).
    
    Returns:
        {value: probability} dict'i. Boş hücre için {1: 1/n, 2: 1/n, ...}
    """
    if not board.is_empty(row, col):
        # Dolu hücre: olasılık 1.0 mevcut değere
        return {board.get(row, col): 1.0}
    
    candidates = board.get_candidates(row, col)
    if not candidates:
        return {}  # Çelişkili durum
    
    n = len(candidates)
    return {value: 1.0 / n for value in candidates}


def shannon_entropy(board: Board, row: int, col: int) -> float:
    """
    Bir hücrenin Shannon entropy'sini hesapla.
    
    H(X) = -Σ p(x) · log₂(p(x))
    
    Yüksek entropy = belirsizlik fazla = solver bu hücreye odaklanmalı
    Düşük entropy = belirsizlik az = bu hücre kolay belirlenir
    
    Returns:
        Bit cinsinden entropy. Maksimum log₂(9) ≈ 3.17 bit (9 candidate varsa).
    """
    probs = candidate_probability(board, row, col)
    if len(probs) <= 1:
        return 0.0  # Tek olasılık → belirsizlik yok
    
    entropy = 0.0
    for p in probs.values():
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def board_entropy_map(board: Board) -> np.ndarray:
    """
    Tüm hücrelerin entropy'sini 9x9 matris olarak döndür.
    UI'da heat map olarak gösterilir.
    
    Returns:
        9x9 NumPy array, float değerler.
    """
    entropy_matrix = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float64)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            entropy_matrix[r, c] = shannon_entropy(board, r, c)
    return entropy_matrix


def total_uncertainty(board: Board) -> float:
    """
    Tahtadaki toplam belirsizlik (tüm hücrelerin entropy toplamı).
    Çözüldükçe 0'a yaklaşır.
    """
    return float(np.sum(board_entropy_map(board)))


def most_uncertain_cell(board: Board) -> Tuple[int, int]:
    """
    En yüksek entropy'li (en belirsiz) boş hücreyi bul.
    Logic solver'ın MRV heuristic'inin tam tersi —
    "tahmin etmek için en zor olan hücreyi seç".
    
    Returns:
        (row, col) tuple'ı. Eğer boş hücre yoksa (-1, -1).
    """
    max_entropy = -1.0
    best_cell = (-1, -1)
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.is_empty(r, c):
                e = shannon_entropy(board, r, c)
                if e > max_entropy:
                    max_entropy = e
                    best_cell = (r, c)
    
    return best_cell


def expected_value_of_assignment(board: Board, row: int, col: int) -> float:
    """
    Bir hücreye atama yapmanın "beklenen faydası".
    
    Tanım: Bu hücre çözülürse kaç peer hücresinin de candidates'ı azalacak?
    
    Returns:
        Beklenen kazanç değeri (yüksek = daha değerli atama).
    """
    if not board.is_empty(row, col):
        return 0.0
    
    candidates = board.get_candidates(row, col)
    if not candidates:
        return 0.0
    
    # Her candidate için, atanırsa kaç peer'da candidate azalır?
    p = 1.0 / len(candidates)  # uniform prior
    expected_reduction = 0.0
    
    for value in candidates:
        # Bu değeri içeren peer sayısı
        affected_peers = sum(
            1 for (pr, pc) in board.get_peers(row, col)
            if board.is_empty(pr, pc) and value in board.get_candidates(pr, pc)
        )
        expected_reduction += p * affected_peers
    
    return expected_reduction


def kl_divergence(p: Dict[int, float], q: Dict[int, float]) -> float:
    """
    KL divergence: D_KL(P || Q)
    
    İki probability distribution arasındaki "uzaklık".
    P'deki bilgi Q'ya göre ne kadar farklı?
    
    Bonus özellik: solver ilerledikçe candidates dağılımının
    uniform'dan ne kadar uzaklaştığını ölçer.
    """
    divergence = 0.0
    for value, p_val in p.items():
        q_val = q.get(value, 1e-12)  # 0 olmasın diye küçük epsilon
        if p_val > 0:
            divergence += p_val * math.log2(p_val / q_val)
    return divergence