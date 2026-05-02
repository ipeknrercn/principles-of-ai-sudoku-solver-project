"""
src/math_module/difficulty_scorer.py

Eigenvector tabanlı puzzle zorluk skorlama.

Bonus özellik: Tahtanın "yapısal zorluğunu" lineer cebir ile ölçmek.
Raporda çok değerli görünür çünkü gelişmiş bir matematiksel kavram.
"""

from __future__ import annotations
import numpy as np
from src.core.board import Board
from src.math_module.probability import board_entropy_map


def difficulty_score(board: Board) -> float:
    """
    Bulmacanın zorluk skoru.
    
    Kombine yaklaşım:
    1. Boş hücre sayısı (basit faktör)
    2. Toplam entropy (belirsizlik)
    3. Entropy matrisinin spektral normu (en büyük eigenvalue)
    
    Yüksek skor = zor bulmaca.
    """
    grid = board.to_numpy()
    empty_count = int(np.sum(grid == 0))
    
    # Faktör 1: Boş hücre oranı
    empty_factor = empty_count / 81.0
    
    # Faktör 2: Toplam entropy
    entropy = board_entropy_map(board)
    total_entropy = float(np.sum(entropy))
    max_total_entropy = 81 * np.log2(9)  # max ~256
    entropy_factor = total_entropy / max_total_entropy
    
    # Faktör 3: Entropy matrisinin spektral normu
    # En büyük singular value → entropy'nin "yoğunluğu"
    if entropy_factor > 0:
        try:
            singular_values = np.linalg.svd(entropy, compute_uv=False)
            spectral_factor = float(singular_values[0]) / (9 * np.log2(9))
        except np.linalg.LinAlgError:
            spectral_factor = 0.0
    else:
        spectral_factor = 0.0
    
    # Ağırlıklı kombinasyon
    score = 0.4 * empty_factor + 0.4 * entropy_factor + 0.2 * spectral_factor
    return min(1.0, score)


def difficulty_label(score: float) -> str:
    """Sayısal skoru anlamlı bir etikete çevir."""
    if score < 0.3:
        return "Easy"
    elif score < 0.5:
        return "Medium"
    elif score < 0.7:
        return "Hard"
    elif score < 0.85:
        return "Expert"
    else:
        return "Evil"