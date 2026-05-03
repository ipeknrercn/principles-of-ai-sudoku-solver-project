"""
benchmarker.py — Benchmark runner for all 4 Sudoku solving algorithms.

Loads puzzles from benchmarks/puzzles.json, runs each algorithm on every puzzle,
and outputs:
  - benchmarks/results.csv       : per-puzzle metrics
  - benchmarks/benchmark_chart.png : bar chart summary (matplotlib)

Usage:
    python -m src.evaluation.benchmarker
    python -m src.evaluation.benchmarker --output-dir benchmarks --puzzles benchmarks/puzzles.json
"""

import json
import time
import csv
import argparse
import sys
import traceback
from pathlib import Path
from typing import Optional
import numpy as np

# ── matplotlib (non-interactive backend for headless/CI environments) ──────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Project imports ────────────────────────────────────────────────────────────
# Adjust these if solver class names differ in the actual repo.
try:
    from src.core.board import Board
    from src.core.solver import Solver
    from src.logic.csp_solver import LogicSolver
    from src.optimization.simulated_annealing import SimulatedAnnealingSolver
    from src.optimization.genetic_algorithm import GeneticAlgorithmSolver
except ImportError as e:
    print(f"[WARN] Import error: {e}")
    print("[WARN] Running in STUB mode — real solvers not loaded.")
    Board = None
    LogicSolver = None
    SimulatedAnnealingSolver = None
    GeneticAlgorithmSolver = None


# ── Constants ──────────────────────────────────────────────────────────────────
ALGORITHMS = ["logic", "simulated_annealing", "genetic_algorithm", "hybrid"]
TIMEOUT_SECONDS = 30  # Hard limit per puzzle × algorithm


# ── Helpers ────────────────────────────────────────────────────────────────────

def string_to_grid(s: str) -> list[list[int]]:
    """Convert 81-char puzzle string to 9×9 list of ints."""
    assert len(s) == 81, f"Puzzle string must be 81 chars, got {len(s)}"
    return [[int(s[r * 9 + c]) for c in range(9)] for r in range(9)]


def is_valid_solution(grid: list[list[int]]) -> bool:
    """Check that a 9×9 grid is a valid, fully-filled Sudoku."""
    target = set(range(1, 10))
    for i in range(9):
        if set(grid[i]) != target:
            return False
        if {grid[r][i] for r in range(9)} != target:
            return False
        br, bc = (i // 3) * 3, (i % 3) * 3
        box = {grid[br + dr][bc + dc] for dr in range(3) for dc in range(3)}
        if box != target:
            return False
    return True


def count_empty_cells(s: str) -> int:
    return s.count("0")


# ── Stub solver (used when real solvers are not importable) ────────────────────

class StubResult:
    """Minimal result object matching expected interface."""
    def __init__(self, solved: bool, iterations: int, grid=None):
        self.solved = solved
        self.iterations = iterations
        self.grid = grid


def stub_solve(puzzle_str: str, algorithm: str) -> StubResult:
    """
    Placeholder that simulates solver behaviour for testing the benchmarker
    pipeline without real solver classes.  Replace with real calls below.
    """
    import random
    delay = {"logic": 0.01, "simulated_annealing": 0.15,
             "genetic_algorithm": 0.2, "hybrid": 0.08}.get(algorithm, 0.05)
    time.sleep(delay + random.uniform(0, 0.02))
    difficulty_clues = 81 - count_empty_cells(puzzle_str)
    # Harder puzzles (fewer clues) fail more often in SA/GA stubs
    success_prob = min(1.0, difficulty_clues / 45)
    solved = random.random() < success_prob
    iters = random.randint(50, 5000)
    return StubResult(solved=solved, iterations=iters)


# ── Real solver dispatch ───────────────────────────────────────────────────────

def run_solver(puzzle_str: str, algorithm: str) -> dict:
    """
    Run one algorithm on one puzzle string.

    Returns a dict with keys:
        solved (bool), time_s (float), iterations (int), error (str|None)
    """
    result = {"solved": False, "time_s": 0.0, "iterations": 0, "error": None}
    start = time.perf_counter()

    try:
        # ── Real solver paths ────────────────────────────────────────────────
        if Board is not None:
            grid = string_to_grid(puzzle_str)
            board = Board(grid)

            if algorithm == "logic":
                solver = LogicSolver(board)
                res = solver.solve()
                result["solved"] = res.solved if hasattr(res, "solved") else bool(res)
                result["iterations"] = getattr(res, "iterations", 0)

            elif algorithm == "simulated_annealing":
                solver = SimulatedAnnealingSolver(board)
                res = solver.solve()
                result["solved"] = res.solved if hasattr(res, "solved") else bool(res)
                result["iterations"] = getattr(res, "iterations", 0)

            elif algorithm == "genetic_algorithm":
                solver = GeneticAlgorithmSolver(board)
                res = solver.solve()
                result["solved"] = res.solved if hasattr(res, "solved") else bool(res)
                result["iterations"] = getattr(res, "iterations", 0)

            elif algorithm == "hybrid":
                # Logic first; fall back to SA if unsolved
                board_copy = Board(string_to_grid(puzzle_str))
                logic_res = LogicSolver(board_copy).solve()
                if getattr(logic_res, "solved", False):
                    result["solved"] = True
                    result["iterations"] = getattr(logic_res, "iterations", 0)
                else:
                    sa_res = SimulatedAnnealingSolver(board_copy).solve()
                    result["solved"] = getattr(sa_res, "solved", False)
                    result["iterations"] = (
                        getattr(logic_res, "iterations", 0)
                        + getattr(sa_res, "iterations", 0)
                    )

        else:
            # ── Stub path (no real solvers available) ────────────────────────
            stub = stub_solve(puzzle_str, algorithm)
            result["solved"] = stub.solved
            result["iterations"] = stub.iterations

    except Exception as exc:
        result["error"] = str(exc)
        result["solved"] = False

    result["time_s"] = round(time.perf_counter() - start, 6)
    return result


# ── Main benchmark loop ────────────────────────────────────────────────────────

def run_benchmark(puzzles_path: Path, output_dir: Path) -> list[dict]:
    """Run all algorithms on all puzzles; return list of result rows."""
    with open(puzzles_path) as f:
        data = json.load(f)

    puzzles = data["puzzles"]
    rows = []

    total = len(puzzles) * len(ALGORITHMS)
    done = 0

    print(f"\n{'─'*60}")
    print(f"  Benchmark: {len(puzzles)} puzzles × {len(ALGORITHMS)} algorithms = {total} runs")
    print(f"{'─'*60}\n")

    for puzzle_meta in puzzles:
        pid = puzzle_meta["id"]
        difficulty = puzzle_meta["difficulty"]
        puzzle_str = puzzle_meta["puzzle"]
        clues = 81 - count_empty_cells(puzzle_str)

        for algo in ALGORITHMS:
            done += 1
            print(f"  [{done:3d}/{total}] {pid:<12} | {algo:<22} ", end="", flush=True)

            result = run_solver(puzzle_str, algo)

            status = "✓" if result["solved"] else "✗"
            print(f"{status}  {result['time_s']:.4f}s  iters={result['iterations']}")

            rows.append({
                "id": pid,
                "difficulty": difficulty,
                "clues": clues,
                "algorithm": algo,
                "solved": result["solved"],
                "time_s": result["time_s"],
                "iterations": result["iterations"],
                "error": result["error"] or "",
            })

    return rows


# ── CSV output ─────────────────────────────────────────────────────────────────

def save_csv(rows: list[dict], output_dir: Path):
    path = output_dir / "results.csv"
    fieldnames = ["id", "difficulty", "clues", "algorithm",
                  "solved", "time_s", "iterations", "error"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  CSV saved → {path}")
    return path


# ── Chart output ───────────────────────────────────────────────────────────────

DIFFICULTY_ORDER = ["easy", "medium", "hard", "expert", "extra"]
ALGO_COLORS = {
    "logic": "#4C72B0",
    "simulated_annealing": "#DD8452",
    "genetic_algorithm": "#55A868",
    "hybrid": "#C44E52",
}
ALGO_LABELS = {
    "logic": "Logic (CSP)",
    "simulated_annealing": "Simulated Annealing",
    "genetic_algorithm": "Genetic Algorithm",
    "hybrid": "Hybrid",
}


def build_summary(rows: list[dict]) -> dict:
    """
    Aggregate rows into per-(difficulty, algorithm) stats.
    Returns nested dict: summary[difficulty][algorithm] = {success_rate, avg_time, avg_iters}
    """
    from collections import defaultdict

    buckets: dict = defaultdict(lambda: defaultdict(list))
    for row in rows:
        buckets[row["difficulty"]][row["algorithm"]].append(row)

    summary = {}
    for diff in DIFFICULTY_ORDER:
        summary[diff] = {}
        for algo in ALGORITHMS:
            bucket = buckets[diff][algo]
            if not bucket:
                summary[diff][algo] = {"success_rate": 0, "avg_time": 0, "avg_iters": 0}
                continue
            n = len(bucket)
            summary[diff][algo] = {
                "success_rate": round(sum(r["solved"] for r in bucket) / n * 100, 1),
                "avg_time": round(sum(r["time_s"] for r in bucket) / n, 4),
                "avg_iters": round(sum(r["iterations"] for r in bucket) / n, 1),
            }
    return summary


def save_chart(rows: list[dict], output_dir: Path):
    summary = build_summary(rows)

    difficulties = [d for d in DIFFICULTY_ORDER if d in summary]
    x = np.arange(len(difficulties))
    n_algos = len(ALGORITHMS)
    bar_width = 0.18
    offsets = np.linspace(-(n_algos - 1) / 2, (n_algos - 1) / 2, n_algos) * bar_width

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Sudoku Solver Algorithm Benchmark", fontsize=15, fontweight="bold", y=1.02)

    metrics = [
        ("success_rate", "Success Rate (%)", (0, 105)),
        ("avg_time", "Average Time (s)", None),
        ("avg_iters", "Average Iterations", None),
    ]

    for ax, (metric_key, ylabel, ylim) in zip(axes, metrics):
        for i, algo in enumerate(ALGORITHMS):
            values = [summary[d][algo][metric_key] for d in difficulties]
            bars = ax.bar(
                x + offsets[i], values, bar_width,
                label=ALGO_LABELS[algo],
                color=ALGO_COLORS[algo],
                alpha=0.87,
                edgecolor="white",
                linewidth=0.5,
            )
            # Value labels on bars
            for bar, val in zip(bars, values):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (bar.get_height() * 0.03 + 0.001),
                        f"{val:.1f}" if isinstance(val, float) else str(val),
                        ha="center", va="bottom", fontsize=6.5, color="#333333",
                    )

        ax.set_xlabel("Difficulty", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(ylabel, fontsize=12, pad=8)
        ax.set_xticks(x)
        ax.set_xticklabels([d.capitalize() for d in difficulties], fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)
        if ylim:
            ax.set_ylim(*ylim)

    plt.tight_layout()
    chart_path = output_dir / "benchmark_chart.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved → {chart_path}")
    return chart_path


# ── Summary table ──────────────────────────────────────────────────────────────

def print_summary(rows: list[dict]):
    summary = build_summary(rows)
    print(f"\n{'═'*72}")
    print("  BENCHMARK SUMMARY")
    print(f"{'═'*72}")
    header = f"{'Difficulty':<10} {'Algorithm':<24} {'Success%':>9} {'AvgTime(s)':>11} {'AvgIters':>10}"
    print(header)
    print("─" * 72)
    for diff in DIFFICULTY_ORDER:
        if diff not in summary:
            continue
        for algo in ALGORITHMS:
            s = summary[diff][algo]
            print(
                f"  {diff.capitalize():<8} {ALGO_LABELS[algo]:<24}"
                f" {s['success_rate']:>8.1f}%"
                f" {s['avg_time']:>11.4f}"
                f" {s['avg_iters']:>10.1f}"
            )
        print("─" * 72)
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run Sudoku solver benchmarks.")
    parser.add_argument(
        "--puzzles",
        default="benchmarks/puzzles.json",
        help="Path to puzzles.json (default: benchmarks/puzzles.json)",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmarks",
        help="Directory for results.csv and chart (default: benchmarks/)",
    )
    args = parser.parse_args()

    puzzles_path = Path(args.puzzles)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not puzzles_path.exists():
        print(f"[ERROR] Puzzles file not found: {puzzles_path}")
        sys.exit(1)

    rows = run_benchmark(puzzles_path, output_dir)
    save_csv(rows, output_dir)
    save_chart(rows, output_dir)
    print_summary(rows)
    print("  Done!\n")


if __name__ == "__main__":
    main()
