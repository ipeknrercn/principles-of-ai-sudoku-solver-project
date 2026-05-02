"""
src/logic/ac3.py

AC-3 (Arc Consistency 3) algoritması.
Constraint Satisfaction Problem (CSP)'lerde kısıtları yayılma yoluyla daraltır.

Sudoku'da: Bir hücreye değer atandığında, peers'ın candidates'ı güncellenir.
Bu işlem zincirleme şekilde yayılır — bir hücredeki değişiklik başka hücrelerde
yeni inference'lara yol açabilir.
"""

from __future__ import annotations
from collections import deque
from typing import Set, Tuple
from src.core.board import Board


def propagate_constraints(board: Board) -> bool:
    """
    AC-3 algoritması: tüm constraint'leri yayılım yoluyla uygula.
    
    Returns:
        True: tutarlı (çelişki yok)
        False: çelişki bulundu (bir hücrenin candidates'ı boşaldı)
    """
    # İlk olarak tüm dolu hücreler için peers'tan değerleri çıkar
    queue = deque()
    
    # Tüm hücre çiftlerini queue'ya ekle
    for r in range(9):
        for c in range(9):
            if not board.is_empty(r, c):
                # Bu hücrenin değeri peers'ta olmamalı
                value = board.get(r, c)
                for (pr, pc) in board.get_peers(r, c):
                    if board.is_empty(pr, pc):
                        if board.eliminate_candidate(pr, pc, value):
                            queue.append((pr, pc))
    
    # Queue boşalana kadar yayılım
    while queue:
        (r, c) = queue.popleft()
        candidates = board.get_candidates(r, c)
        
        if len(candidates) == 0:
            # Çelişki: bir hücrenin hiç olası değeri kalmadı
            return False
        
        if len(candidates) == 1:
            # Sadece bir olasılık varsa, bu değeri ata
            value = next(iter(candidates))
            try:
                board.set(r, c, value)
            except RuntimeError:
                # Sabit hücre, atlanır
                continue
            
            # Şimdi peers'tan bu değeri çıkar
            for (pr, pc) in board.get_peers(r, c):
                if board.is_empty(pr, pc):
                    if board.eliminate_candidate(pr, pc, value):
                        queue.append((pr, pc))
    
    return True