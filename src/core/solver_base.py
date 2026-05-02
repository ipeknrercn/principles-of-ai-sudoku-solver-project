"""
src/core/solver_base.py

Tüm solver'ların uyması gereken arayüz (kontrat).
Logic Engineer, SA Specialist, GA Specialist bu sınıflardan miras alarak çalışacak.

Bu dosya değişmez bir "anlaşma"dır — herkes bu kontratlara göre kod yazar.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from src.core.board import Board


@dataclass
class SolverResult:
    """Tüm solver'ların döndürdüğü ortak sonuç tipi."""
    board: Board                          # Çözüm tahtası (veya en iyi tahmin)
    solved: bool                          # Tam çözüldü mü?
    iterations: int = 0                   # Kaç iterasyon harcandı
    elapsed_ms: float = 0.0               # Geçen süre (milisaniye)
    steps: List[str] = field(default_factory=list)  # Adım adım açıklama (UI gösterir)
    metadata: dict = field(default_factory=dict)    # Ekstra bilgi (her solver kendi ekler)


class BaseSolver(ABC):
    """Tüm solver'ların uyması gereken temel arayüz."""

    @abstractmethod
    def solve(self, board: Board) -> SolverResult:
        """
        Bulmacayı çözmeye çalış.
        
        Args:
            board: Çözülecek tahta (Board nesnesi). Modify edilmez (kopya alınır).
        
        Returns:
            SolverResult: Çözüm tahtası + metrikler + adımlar.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Solver'ın görünen adı (UI'da gösterilir, raporda geçer)."""
        ...


class LogicSolver(BaseSolver):
    """
    Logic Engineer'ın implement edeceği solver.
    Sadece mantıksal çıkarım kullanır (Naked/Hidden Singles, AC-3, backtracking).
    """
    @property
    def name(self) -> str:
        return "Logic Solver (CSP)"


class OptimizationSolver(BaseSolver):
    """
    SA ve GA Specialists'in implement edeceği solver.
    Heuristic optimization kullanır.
    """
    pass