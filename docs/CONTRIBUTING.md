# Team onboarding guide



Steps to follow to start working on this project.



## 1. Environment setup (one-time)



```powershell

# Clone the repo

git clone https://github.com/ipeknrercn/principles-of-ai-sudoku-solver-project

cd sudoku-solver



# Create a virtual environment

python -m venv venv

.\venv\Scripts\Activate.ps1   # Windows

# source venv/bin/activate    # macOS/Linux



# Install packages

pip install -r requirements.txt



# Verify tests run

pytest

```



All tests should pass (44 tests — all green).



## 2. Workflow (for each new task)



```powershell

# Get the latest main

git checkout main

git pull



# Create a new feature branch

git checkout -b feature/logic-csp-solver  # branch name pattern: feature/<short-task-name>



# Write code, commit often

git add .

git commit -m "feat(logic): implement naked single rule"



# Push when finished

git push -u origin feature/logic-csp-solver

```



Then open a **Pull Request** on GitHub — the Lead Developer will review.



## 3. Who works on what?



| Role | Folder you work in | What you implement |

|-----|--------------------|---------------------|

| **Logic Engineer** | `src/logic/` | `LogicSolver(BaseSolver)` class — `csp_solver.py` |

| **Mathematical Modeler** | `src/math_module/` | `probability.py`, `entropy.py`, `norms.py` |

| **SA Specialist** | `src/optimization/` | `SASolver(BaseSolver)` — `simulated_annealing.py` |

| **GA Specialist** | `src/optimization/` | `GASolver(BaseSolver)` — `genetic_algorithm.py` |

| **UI/UX Developer** | `src/ui/` | `app.py` (Flask), `templates/`, `static/` |

| **Evaluation Specialist** | `src/evaluation/`, `tests/`, `benchmarks/` | Metrics, benchmarks, additional tests |



## 4. Shared conventions



### Board usage



**Never implement your own board representation.** Always use `Board`:



```python

from src.core.board import Board



board = Board.from_string("53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79")

print(board)                    # Pretty print

board.get(0, 0)                 # 5

board.get_candidates(0, 2)      # {1, 2, 4, 8}

board.count_conflicts()         # 0

solution_grid = board.to_numpy()  # 9x9 NumPy array

```



### Solver implementation



All solvers must implement the `BaseSolver` interface:



```python

from src.core.solver_base import BaseSolver, SolverResult

from src.core.board import Board



class LogicSolver(BaseSolver):

    @property

    def name(self) -> str:

        return "Logic Solver"



    def solve(self, board: Board) -> SolverResult:

        # Your implementation

        return SolverResult(board=solved_board, solved=True, iterations=42)

```



### Testing requirements



Write **at least 5–10 tests** per new module. Coverage should not drop below 80%.



```powershell

pytest tests/test_<module>.py -v

pytest --cov=src --cov-report=term-missing

```



### Commit messages



- `feat(logic): add naked single inference rule`

- `fix(sa): correct cooling schedule formula`

- `test(math): add entropy calculation tests`

- `docs: update contributing guide`




