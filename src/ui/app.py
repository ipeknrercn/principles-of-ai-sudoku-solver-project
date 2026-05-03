"""
src/ui/app.py

Flask web uygulaması.
Frontend (HTML/JS) ile backend (solver) arasındaki köprü.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from src.core.board import Board
from src.core.solver import SudokuSolver, SolverMode
from src.math_module.probability import board_entropy_map
from src.math_module.difficulty_scorer import difficulty_score, difficulty_label


app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)

# Tek solver instance (thread-safe değil ama demo için yeterli)
solver = SudokuSolver()


# ============================================================
# Hazır puzzle veritabanı (Evaluation Specialist çoğaltacak)
# ============================================================

PRESET_PUZZLES = {
    "easy": [
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
        "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3..",
    ],
    "medium": [
        "...26.7.168..7..9.19...45..82.1...4...46.29...5...3.28..93...74.4..5..367.3.18...",
        ".2.6.8...58...97......4....37....5..6.......4..8....13....2......98...36...3.6.9.",
    ],
    "hard": [
        "..53.....8......2..7..1.5..4....53...1..7...6..32...8..6.5....9..4....3......97..",
        "12..4......5.69.1...0.1.....1...7.92.......5....6...3.7..4...62.....3..0.5...3...".replace("0", "."),
    ],
    "expert": [
        "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
    ],
}


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    """Ana sayfa."""
    return render_template("index.html")

@app.route("/api/solve", methods=["POST"])
def solve():
    """
    Bulmacayı çöz.
    """
    try:
        data = request.get_json()
        grid = data.get("grid")
        mode_str = data.get("mode", "logic")
        
        # Mode parse
        mode_map = {
            "logic": SolverMode.LOGIC_ONLY,
            "sa": SolverMode.SIMULATED_ANNEALING,
            "ga": SolverMode.GENETIC_ALGORITHM,
            "hybrid": SolverMode.HYBRID,
        }
        mode = mode_map.get(mode_str, SolverMode.LOGIC_ONLY)
        
        # Board oluştur
        board = Board.from_list(grid)
        
        # 🆕 ÖNCE: Tahta zaten geçerli mi? (çakışma kontrolü)
        conflicts = board.count_conflicts()
        if conflicts > 0:
            return jsonify({
                "success": False,
                "error": f"Puzzle has {conflicts} conflicts. Please fix duplicates in rows, columns, or 3x3 boxes.",
                "conflicts": conflicts,
            }), 400
        
        # 🆕 SONRA: Tahta zaten çözülmüş mü?
        if board.is_solved():
            return jsonify({
                "success": True,
                "solved": True,
                "grid": board.to_list(),
                "iterations": 0,
                "elapsed_ms": 0,
                "steps": ["Puzzle was already solved."],
                "total_steps": 1,
                "metadata": {"already_solved": True},
                "energy_history": [],
            })
        
        # 🆕 KONTROL: En az bir boş hücre var mı?
        empty_count = sum(1 for row in grid for cell in row if cell == 0)
        if empty_count == 0:
            # Boş hücre yok ama çözülmemiş = çakışma var demektir
            return jsonify({
                "success": False,
                "error": "Board is full but invalid. Please clear conflicting cells.",
            }), 400
        
        # Çöz
        result = solver.solve(board, mode=mode)
        
        # Metadata'dan büyük history'leri çıkar
        clean_metadata = {k: v for k, v in result.metadata.items()
                          if k not in ("energy_history", "temperature_history")}
        
        history = result.metadata.get("energy_history", [])
        if len(history) > 100:
            step = len(history) // 100
            history = history[::step]
        
        return jsonify({
            "success": True,
            "solved": result.solved,
            "grid": result.board.to_list(),
            "iterations": result.iterations,
            "elapsed_ms": round(result.elapsed_ms, 2),
            "steps": result.steps[:20],
            "total_steps": len(result.steps),
            "metadata": clean_metadata,
            "energy_history": history,
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/preset/<difficulty>", methods=["GET"])
def get_preset(difficulty: str):
    """Hazır bulmaca getir."""
    import random
    puzzles = PRESET_PUZZLES.get(difficulty.lower(), PRESET_PUZZLES["easy"])
    puzzle_string = random.choice(puzzles)
    board = Board.from_string(puzzle_string)
    return jsonify({
        "grid": board.to_list(),
        "difficulty": difficulty,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Bulmacayı analiz et (entropy heat map + difficulty score).
    Math pillar'ı UI'da gösterir.
    """
    try:
        data = request.get_json()
        grid = data.get("grid")
        board = Board.from_list(grid)
        
        entropy_map = board_entropy_map(board).tolist()
        score = difficulty_score(board)
        label = difficulty_label(score)
        
        return jsonify({
            "success": True,
            "entropy_map": entropy_map,
            "difficulty_score": round(score, 3),
            "difficulty_label": label,
            "empty_cells": sum(1 for row in grid for cell in row if cell == 0),
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/validate", methods=["POST"])
def validate():
    """Bulmaca geçerli mi (çakışma var mı)?"""
    try:
        data = request.get_json()
        grid = data.get("grid")
        board = Board.from_list(grid)
        return jsonify({
            "success": True,
            "valid": board.is_valid(),
            "solved": board.is_solved(),
            "conflicts": board.count_conflicts(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)