"""
src/optimization/sa_config.py

Simulated Annealing hyperparameter konfigürasyonu.
Tek yerde tutmak: tuning ve raporlama kolaylaşır.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SAConfig:
    """Simulated Annealing parametreleri."""
    
    # Sıcaklık parametreleri
    initial_temperature: float = 1.0    # T₀ — başlangıç sıcaklığı
    cooling_rate: float = 0.99           # α — geometrik soğuma oranı
    min_temperature: float = 0.001       # Algoritmanın durduğu minimum T
    
    # İterasyon limitleri
    max_iterations: int = 100_000        # Toplam iterasyon limiti
    iterations_per_temperature: int = 50 # Her T'de yapılacak swap denemesi
    
    # Reheat (yeniden ısıtma) — yerel optimumda sıkışırsak
    enable_reheat: bool = True
    stuck_threshold: int = 2000          # Bu kadar iterasyon iyileşme yoksa reheat
    reheat_factor: float = 2.0           # Sıcaklığı bu kadar artır
    
    # Random seed (deterministik testler için)
    seed: int | None = None


# Hazır profil — farklı hyperparameter setleri raporda karşılaştırılacak
DEFAULT_CONFIG = SAConfig()

FAST_CONFIG = SAConfig(
    initial_temperature=2.0,
    cooling_rate=0.995,
    max_iterations=50_000,
)

THOROUGH_CONFIG = SAConfig(
    initial_temperature=5.0,
    cooling_rate=0.999,
    max_iterations=200_000,
    stuck_threshold=5000,
)