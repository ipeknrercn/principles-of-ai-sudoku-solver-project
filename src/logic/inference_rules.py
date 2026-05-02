"""
src/logic/inference_rules.py

Sudoku için klasik inference (çıkarım) kuralları.
Bunlar Modus Ponens'in pratik uygulamalarıdır.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from dataclasses import dataclass
from src.core.board import Board, BOARD_SIZE, BOX_SIZE, DIGITS


@dataclass
class InferenceStep:
    """Bir inference adımının kaydı. UI ve rapor için kullanılır."""
    rule_name: str          # Örn: "Naked Single", "Hidden Single"
    row: int
    col: int
    value: int
    reason: str             # İnsan tarafından okunabilir açıklama
    
    def __str__(self) -> str:
        return f"[{self.rule_name}] ({self.row},{self.col}) = {self.value} — {self.reason}"


def apply_naked_single(board: Board) -> Optional[InferenceStep]:
    """
    Naked Single Kuralı (Modus Ponens uygulaması):
    "Eğer bir hücrenin yalnızca bir olası değeri varsa, o değer atanmalıdır."
    
    Premise 1: Bu hücrede {1..9} içinden bir değer olmalı
    Premise 2: 8 değer peers'ta zaten var
    Conclusion: Kalan değer bu hücreye atanmalı
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.is_empty(r, c):
                candidates = board.get_candidates(r, c)
                if len(candidates) == 1:
                    value = next(iter(candidates))
                    return InferenceStep(
                        rule_name="Naked Single",
                        row=r, col=c, value=value,
                        reason=f"Cell ({r},{c}) only has {{{value}}} as candidate"
                    )
    return None


def apply_hidden_single(board: Board) -> Optional[InferenceStep]:
    """
    Hidden Single Kuralı:
    "Eğer bir satır/sütun/blokta belirli bir değer yalnızca tek hücreye konabilirse,
    o değer o hücreye atanmalıdır."
    """
    # Satırlarda kontrol
    for r in range(BOARD_SIZE):
        for digit in DIGITS:
            cells_with_digit = [
                (r, c) for c in range(BOARD_SIZE)
                if board.is_empty(r, c) and digit in board.get_candidates(r, c)
            ]
            if len(cells_with_digit) == 1:
                row, col = cells_with_digit[0]
                return InferenceStep(
                    rule_name="Hidden Single (Row)",
                    row=row, col=col, value=digit,
                    reason=f"In row {r}, value {digit} can only fit in cell ({row},{col})"
                )
    
    # Sütunlarda kontrol
    for c in range(BOARD_SIZE):
        for digit in DIGITS:
            cells_with_digit = [
                (r, c) for r in range(BOARD_SIZE)
                if board.is_empty(r, c) and digit in board.get_candidates(r, c)
            ]
            if len(cells_with_digit) == 1:
                row, col = cells_with_digit[0]
                return InferenceStep(
                    rule_name="Hidden Single (Column)",
                    row=row, col=col, value=digit,
                    reason=f"In column {c}, value {digit} can only fit in cell ({row},{col})"
                )
    
    # Bloklarda kontrol
    for box_r in range(0, BOARD_SIZE, BOX_SIZE):
        for box_c in range(0, BOARD_SIZE, BOX_SIZE):
            for digit in DIGITS:
                cells_with_digit = []
                for r in range(box_r, box_r + BOX_SIZE):
                    for c in range(box_c, box_c + BOX_SIZE):
                        if board.is_empty(r, c) and digit in board.get_candidates(r, c):
                            cells_with_digit.append((r, c))
                if len(cells_with_digit) == 1:
                    row, col = cells_with_digit[0]
                    return InferenceStep(
                        rule_name="Hidden Single (Box)",
                        row=row, col=col, value=digit,
                        reason=f"In box ({box_r//3},{box_c//3}), value {digit} can only fit in ({row},{col})"
                    )
    return None