# Akıllı Sudoku Çözücü Ajan

**Principles of AI — Final Project**

Sudoku bulmacalarını mantıksal çıkarım, matematiksel modelleme ve optimizasyon teknikleri kullanarak çözen rasyonel bir AI ajanı.

## Üç Pillar

1. **Logic** — Propositional Logic, CSP, AC-3, Naked/Hidden Singles, Modus Ponens, Resolution
2. **Math of AI** — Matris/Tensör gösterimi, olasılık dağılımları, Shannon entropy, expected value
3. **Optimization** — Simulated Annealing, Genetic Algorithm

## Kurulum

```powershell
# Virtual environment oluştur ve aktive et
python -m venv venv
.\venv\Scripts\Activate.ps1

# Paketleri kur
pip install -r requirements.txt
```

## Çalıştırma

```powershell
# Web arayüzünü başlat
python -m src.ui.app

# Tarayıcıda aç
# http://localhost:5000
```

## Test

```powershell
pytest
pytest --cov=src tests/
```

## Proje Yapısı