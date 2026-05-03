/**
 * src/ui/static/js/sudoku.js
 * 
 * Sudoku UI mantığı — frontend ile backend arasında köprü.
 */

// ============================================================
// State Management
// ============================================================

const state = {
    grid: createEmptyGrid(),
    fixed: createBooleanGrid(),  // Hangi hücreler sabit (kullanıcı değiştiremez)
    selectedCell: null,
    isSolving: false,
};

function createEmptyGrid() {
    return Array.from({ length: 9 }, () => Array(9).fill(0));
}

function createBooleanGrid() {
    return Array.from({ length: 9 }, () => Array(9).fill(false));
}


// ============================================================
// Board Rendering
// ============================================================

const boardElement = document.getElementById('sudoku-board');

function renderBoard() {
    boardElement.innerHTML = '';
    
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            const cell = document.createElement('div');
            cell.className = 'sudoku-cell';
            cell.dataset.row = r;
            cell.dataset.col = c;
            
            const value = state.grid[r][c];
            cell.textContent = value === 0 ? '' : value;
            
            if (state.fixed[r][c]) {
                cell.classList.add('fixed');
            }
            
            if (state.selectedCell && state.selectedCell.row === r && state.selectedCell.col === c) {
                cell.classList.add('selected');
            }
            
            cell.addEventListener('click', () => selectCell(r, c));
            boardElement.appendChild(cell);
        }
    }
}

function selectCell(row, col) {
    if (state.fixed[row][col]) return;
    state.selectedCell = { row, col };
    renderBoard();
}


// ============================================================
// Klavye Girişi
// ============================================================

document.addEventListener('keydown', async (e) => {
    if (!state.selectedCell || state.isSolving) return;
    
    const { row, col } = state.selectedCell;
    
    if (e.key >= '1' && e.key <= '9') {
        state.grid[row][col] = parseInt(e.key);
        renderBoard();
        await checkValidation();  // 🆕 Otomatik kontrol
    } else if (e.key === '0' || e.key === 'Delete' || e.key === 'Backspace') {
        state.grid[row][col] = 0;
        renderBoard();
        await checkValidation();  // 🆕 Otomatik kontrol
    } else if (e.key === 'ArrowUp' && row > 0) {
        selectCell(row - 1, col);
    } else if (e.key === 'ArrowDown' && row < 8) {
        selectCell(row + 1, col);
    } else if (e.key === 'ArrowLeft' && col > 0) {
        selectCell(row, col - 1);
    } else if (e.key === 'ArrowRight' && col < 8) {
        selectCell(row, col + 1);
    }
});

// 🆕 Yeni fonksiyon: tahtayı backend'e gönderip çakışma kontrolü yap
async function checkValidation() {
    try {
        const result = await apiCall('/api/validate', { grid: state.grid });
        if (result.success) {
            if (result.solved) {
                setStatus('✅ Puzzle is solved!', 'success');
            } else if (result.valid) {
                setStatus(`Valid (${result.conflicts} conflicts)`, '');
            } else {
                setStatus(`⚠️ ${result.conflicts} conflicts detected`, 'error');
                highlightConflicts();  // 🆕 Çakışmalı hücreleri kırmızı yap
            }
        }
    } catch (e) {
        // Sessiz hata — kullanıcıyı rahatsız etme
    }
}

// 🆕 Yeni fonksiyon: Çakışmalı hücreleri görsel olarak işaretle
function highlightConflicts() {
    document.querySelectorAll('.sudoku-cell').forEach(cell => {
        const r = parseInt(cell.dataset.row);
        const c = parseInt(cell.dataset.col);
        const value = state.grid[r][c];
        
        if (value === 0) return;
        
        // Aynı satır, sütun veya blokta aynı değer var mı?
        let hasConflict = false;
        
        // Satır kontrolü
        for (let cc = 0; cc < 9; cc++) {
            if (cc !== c && state.grid[r][cc] === value) {
                hasConflict = true;
                break;
            }
        }
        // Sütun kontrolü
        if (!hasConflict) {
            for (let rr = 0; rr < 9; rr++) {
                if (rr !== r && state.grid[rr][c] === value) {
                    hasConflict = true;
                    break;
                }
            }
        }
        // Blok kontrolü
        if (!hasConflict) {
            const boxR = Math.floor(r / 3) * 3;
            const boxC = Math.floor(c / 3) * 3;
            for (let rr = boxR; rr < boxR + 3; rr++) {
                for (let cc = boxC; cc < boxC + 3; cc++) {
                    if (rr === r && cc === c) continue;
                    if (state.grid[rr][cc] === value) {
                        hasConflict = true;
                        break;
                    }
                }
                if (hasConflict) break;
            }
        }
        
        if (hasConflict) {
            cell.classList.add('conflict');
        }
    });
}


// ============================================================
// API Calls
// ============================================================

async function apiCall(endpoint, data = null, method = 'POST') {
    const options = {
        method: method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (data) options.body = JSON.stringify(data);
    
    const response = await fetch(endpoint, options);
    return await response.json();
}


// ============================================================
// Solve Logic
// ============================================================

const btnSolve = document.getElementById('btn-solve');
const btnReset = document.getElementById('btn-reset');
const btnClear = document.getElementById('btn-clear');
const btnAnalyze = document.getElementById('btn-analyze');
const statusText = document.getElementById('status-text');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');

btnSolve.addEventListener('click', async () => {
    if (state.isSolving) return;
    
    const filledCount = state.grid.flat().filter(v => v !== 0).length;
    if (filledCount === 0) {
        const ok = confirm(
            "The board is empty. The solver will generate one of trillions of possible solutions, " +
            "but Logic-only mode may be slow.\n\n" +
            "Tip: Click a preset (Easy/Medium/Hard) for a proper puzzle.\n\n" +
            "Continue anyway?"
        );
        if (!ok) return;
    }
    
    if (filledCount < 17) {
        // Sudoku için minimum 17 ipucu gerekir (matematiksel teorem)
        console.warn(`Only ${filledCount} clues — puzzle may have multiple solutions or no unique solution.`);
    }
    
    const algoMode = document.querySelector('input[name="algo"]:checked').value;
    
    // İlk solve'da fixed durumunu kilitle
    if (!state.fixed.flat().some(v => v)) {
        state.fixed = state.grid.map(row => row.map(v => v !== 0));
    }
    
    state.isSolving = true;
    btnSolve.disabled = true;
    setLoading(true, `Solving with ${getAlgoName(algoMode)}...`);
    setStatus('Solving...', '');
    
    try {
        const result = await apiCall('/api/solve', {
            grid: state.grid,
            mode: algoMode,
        });
        
        if (result.success) {
            state.grid = result.grid;
            renderBoard();
            highlightSolved();
            displayResults(result);
            displaySteps(result.steps, result.total_steps);
            
            if (result.solved) {
                setStatus('✅ Solved!', 'success');
            } else {
                setStatus(`⚠️ Partial solution (${result.metadata.final_energy || 0} conflicts)`, 'error');
            }
        } else {
            // 🆕 Backend hata mesajını net göster
            setStatus(`❌ ${result.error}`, 'error');
            if (result.conflicts) {
                highlightConflicts();
            }
        }
    } catch (error) {
        setStatus(`❌ Network error: ${error.message}`, 'error');
    } finally {
        state.isSolving = false;
        btnSolve.disabled = false;
        setLoading(false);
    }
});

btnReset.addEventListener('click', () => {
    // Sadece çözüm hücrelerini temizle (sabit hücreler korunsun)
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            if (!state.fixed[r][c]) {
                state.grid[r][c] = 0;
            }
        }
    }
    renderBoard();
    setStatus('Reset to original puzzle', '');
});

btnClear.addEventListener('click', () => {
    state.grid = createEmptyGrid();
    state.fixed = createBooleanGrid();
    state.selectedCell = null;
    renderBoard();
    clearResults();
    setStatus('Board cleared', '');
});


// ============================================================
// Preset Loader
// ============================================================

document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', async () => {
        const difficulty = btn.dataset.difficulty;
        try {
            const result = await apiCall(`/api/preset/${difficulty}`, null, 'GET');
            state.grid = result.grid;
            state.fixed = state.grid.map(row => row.map(v => v !== 0));
            renderBoard();
            clearResults();
            setStatus(`Loaded ${difficulty.toUpperCase()} puzzle`, '');
        } catch (e) {
            setStatus(`❌ Error loading: ${e.message}`, 'error');
        }
    });
});


// ============================================================
// Math Analysis
// ============================================================

btnAnalyze.addEventListener('click', async () => {
    try {
        const result = await apiCall('/api/analyze', { grid: state.grid });
        if (result.success) {
            document.getElementById('analysis-result').classList.remove('hidden');
            document.getElementById('difficulty-label').textContent = result.difficulty_label;
            document.getElementById('difficulty-score').textContent = result.difficulty_score;
            document.getElementById('empty-cells').textContent = result.empty_cells;
        }
    } catch (e) {
        setStatus(`❌ Analysis failed: ${e.message}`, 'error');
    }
});


// ============================================================
// UI Helpers
// ============================================================

function setStatus(text, type = '') {
    statusText.textContent = text;
    statusText.parentElement.className = 'status-bar' + (type ? ' ' + type : '');
}

function setLoading(isLoading, text = 'Solving...') {
    loadingOverlay.classList.toggle('hidden', !isLoading);
    loadingText.textContent = text;
}

function getAlgoName(mode) {
    const names = {
        'logic': 'Logic Solver',
        'sa': 'Simulated Annealing',
        'ga': 'Genetic Algorithm',
        'hybrid': 'Hybrid Solver',
    };
    return names[mode] || mode;
}

function highlightSolved() {
    document.querySelectorAll('.sudoku-cell').forEach(cell => {
        const r = parseInt(cell.dataset.row);
        const c = parseInt(cell.dataset.col);
        if (!state.fixed[r][c] && state.grid[r][c] !== 0) {
            cell.classList.add('solved');
        }
    });
}

function displayResults(result) {
    const container = document.getElementById('results');
    container.innerHTML = `
        <div class="result-item">
            <span>Status:</span>
            <strong>${result.solved ? '✅ Solved' : '⚠️ Partial'}</strong>
        </div>
        <div class="result-item">
            <span>Iterations:</span>
            <strong>${result.iterations.toLocaleString()}</strong>
        </div>
        <div class="result-item">
            <span>Time:</span>
            <strong>${result.elapsed_ms} ms</strong>
        </div>
        ${result.metadata.final_energy !== undefined ? `
        <div class="result-item">
            <span>Final Energy:</span>
            <strong>${result.metadata.final_energy}</strong>
        </div>` : ''}
        ${result.metadata.backtracks !== undefined ? `
        <div class="result-item">
            <span>Backtracks:</span>
            <strong>${result.metadata.backtracks}</strong>
        </div>` : ''}
        ${result.metadata.inference_steps !== undefined ? `
        <div class="result-item">
            <span>Inferences:</span>
            <strong>${result.metadata.inference_steps}</strong>
        </div>` : ''}
    `;
}

function displaySteps(steps, total) {
    const container = document.getElementById('inference-steps');
    if (!steps || steps.length === 0) {
        container.innerHTML = '<p class="placeholder">No steps recorded.</p>';
        return;
    }
    
    const stepsHTML = steps.map(s => `<li>${escapeHtml(s)}</li>`).join('');
    const showing = `<p style="color:var(--text-muted); font-size:0.85em; margin-bottom:8px;">Showing first ${steps.length} of ${total} steps</p>`;
    container.innerHTML = showing + `<ol>${stepsHTML}</ol>`;
}

function clearResults() {
    document.getElementById('results').innerHTML = '<p class="placeholder">Solve to see results...</p>';
    document.getElementById('inference-steps').innerHTML = '<p class="placeholder">Steps will appear here...</p>';
    document.getElementById('analysis-result').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// ============================================================
// Initialize
// ============================================================

renderBoard();
setStatus('Ready. Load a preset or enter a puzzle.', '');