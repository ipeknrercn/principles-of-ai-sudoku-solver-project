# Intelligent Sudoku Solver Agent

> A rational AI agent that solves Sudoku puzzles by integrating **Logic**, **Mathematics**, and **Optimization** — built for the *Principles of AI* course final project.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](#)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [The Three AI Pillars](#the-three-ai-pillars)
3. [System Architecture](#system-architecture)
4. [Project Structure](#project-structure)
5. [Testing](#testing)


---

## Project Overview

This project implements a **rational AI agent** that perceives Sudoku puzzles, reasons about them, and produces solutions by combining three foundational AI principles. The agent supports multiple solving strategies and exposes them through an interactive web interface where users can:

- Input or load preset Sudoku puzzles (Easy / Medium / Hard / Expert)
- Choose a solving algorithm (Logic-only / Simulated Annealing / Genetic Algorithm / Hybrid)
- Watch the solving process step-by-step with live visualizations
- Compare algorithm performance across difficulty levels

**Project Type:** Group project (9 members)
**Course:** Principles of AI
**Deadline:** May 8, 2025, 16:00

---

## The Three AI Pillars

Our agent is built on three foundational AI principles, each implemented as an independent module that contributes to the final solution.

### 1. Logic — Rational Inference Engine

The agent uses **Propositional Logic** to model Sudoku as a Constraint Satisfaction Problem (CSP).

- **Variables:** `X(i,j,k)` = "Cell (i,j) contains value k"
- **Constraints:** Row, column, and 3×3 box uniqueness; cell exclusivity
- **Inference Rules:** Modus Ponens, Resolution
- **Techniques:** Naked Singles, Hidden Singles, AC-3 (arc consistency), backtracking with MRV heuristic

### 2. Mathematics of AI — Theoretical Foundation

The agent's reasoning is grounded in linear algebra and probability theory.

- **Linear Algebra:** 9×9 matrix and 9×9×9 binary tensor representations; Frobenius norm for solution distance; eigenvector-based puzzle difficulty scoring
- **Probability:** Probability distributions over candidate values; Shannon entropy to identify the most uncertain cells; expected value calculations for assignments

### 3. Optimization — Heuristic Search

When pure logical inference is insufficient (e.g., Hard or Expert puzzles), the agent invokes optimization algorithms.

- **Simulated Annealing:** Energy function based on conflict count, geometric cooling schedule, probabilistic acceptance criterion
- **Genetic Algorithm:** Tournament selection, row-based crossover, swap mutation, elitism
- **Comparative Analysis:** Both algorithms are benchmarked across difficulty levels

---

## System Architecture
---
┌─────────────────────────────────────────────────┐
│      Web UI (Flask + HTML/CSS/JS)               │
│  • Interactive 9×9 grid                         │
│  • Algorithm selection                          │
│  • Step-by-step visualization                   │
│  • Live performance metrics                     │
└──────────────────┬──────────────────────────────┘
│
┌──────────────────▼──────────────────────────────┐
│      Integration Layer (core/solver.py)         │
│      Dispatches requests to the correct solver  │
└──────────────────┬──────────────────────────────┘
│
┌──────────┼──────────┬──────────┐
▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Logic  │ │  Math  │ │   SA   │ │   GA   │
│ Module │ │ Module │ │ Module │ │ Module │
└────────┘ └────────┘ └────────┘ └────────┘
│
▼
┌────────────────────────┐
│  Shared Data Structure │
│  (core/board.py)       │
│  • NumPy 9×9 grid      │
│  • Candidates sets     │
│  • Fixed-cell tracking │
└────────────────────────┘

---
The `Board` class is the **single source of truth**. All modules read and write through this class, ensuring consistency across the system.


## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account (with collaborator access to this repo)

### Setup

```powershell
# Clone the repository
git clone https://github.com/ipeknrercn/principles-of-ai-sudoku-solver-project.git
cd principles-of-ai-sudoku-solver-project

# Create a virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# On Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify the setup by running tests
pytest
```

If you see all tests passing (44+ tests, ~98% coverage), you're ready to go.

### Running the Web Interface

```powershell
python -m src.ui.app
```

Then open `http://localhost:5000` in your browser.

---

## Project Structure
---

principles-of-ai-sudoku-solver-project/
├── .github/
│   └── workflows/
│       └── ci.yml                # CI/CD: runs tests on every PR
├── benchmarks/
│   ├── puzzles.json              # 50 benchmark puzzles
│   └── results.csv               # Performance results
├── docs/
│   ├── CONTRIBUTING.md           # How to contribute
│   ├── report_draft.md           # Final report draft
│   └── architecture.md           # Detailed architecture notes
├── src/
│   ├── core/                     # Shared infrastructure (LEAD DEV)
│   │   ├── board.py              # The Board class — used by everyone
│   │   ├── solver_base.py        # Abstract base classes (interfaces)
│   │   ├── mock_solver.py        # Mock for parallel UI development
│   │   └── solver.py             # Integration / dispatcher layer
│   ├── logic/                    # LOGIC ENGINEER
│   │   ├── csp_solver.py         # Main LogicSolver class
│   │   ├── inference_rules.py    # Naked / Hidden Singles
│   │   └── ac3.py                # Arc consistency
│   ├── math_module/              # MATHEMATICAL MODELER
│   │   ├── probability.py        # Distributions, entropy
│   │   ├── norms.py              # Distance metrics
│   │   └── difficulty_scorer.py  # Eigenvector-based scoring
│   ├── optimization/             # SA + GA SPECIALISTS
│   │   ├── simulated_annealing.py
│   │   ├── sa_config.py
│   │   ├── genetic_algorithm.py
│   │   └── ga_config.py
│   ├── evaluation/               # EVALUATION SPECIALIST
│   │   ├── metrics.py
│   │   └── benchmarker.py
│   └── ui/                       # UI/UX DEVELOPER
│       ├── app.py                # Flask application
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── css/style.css
│           └── js/sudoku.js
├── tests/                        # All unit and integration tests
│   └── test_board.py
├── .gitignore
├── README.md
└── requirements.txt

---


## Testing

We follow a **test-first** approach. Every module ships with comprehensive unit tests.

### Running Tests

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_board.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run with coverage and HTML report
pytest --cov=src --cov-report=html
# Then open htmlcov/index.html in your browser
```

### Test Requirements

- Every new module must include unit tests
- Coverage target: **≥80% per module**, **≥85% overall**
- All tests must pass before opening a pull request
- CI runs tests on Python 3.10, 3.11, and 3.12

---
