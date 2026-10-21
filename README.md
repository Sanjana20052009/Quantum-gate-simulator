# QubitLab — Interactive Quantum Gate Simulator (Upgraded)

React + Vite frontend, FastAPI backend, NumPy state engine, Qiskit cross-check, and report exports.

Deployments:https://quantum-gate-simulator-khaki.vercel.app/

## Included features
- All nine gates: X, Y, Z, H, S, T, RX, RY, RZ
- Animated, draggable SVG Bloch sphere
- Step-by-step gate history, play/pause, previous/next, undo/redo
- Theoretical probabilities and simulated measurement shots
- Fidelity and relative-phase analysis
- X/Y/Z-basis quantum state tomography with reconstructed density matrix
- Interactive quizzes and gate challenges
- CSV and PDF experiment report export
- Qiskit state-vector verification

## Requirements
Python 3.10+ and Node.js 18+ with npm.

## Backend setup
```bash
cd backend
python -m venv .venv
```
Activate on Windows PowerShell: `\.venv\Scripts\Activate.ps1`  
Windows CMD: `.venv\Scripts\activate.bat`  
macOS/Linux: `source .venv/bin/activate`

Then run:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```
API: http://127.0.0.1:8000 · API docs: http://127.0.0.1:8000/docs

## Frontend setup
Open a second terminal from the project root:
```bash
cd frontend
npm install
npm run dev
```
Open the URL Vite prints, usually http://localhost:5173. Keep both terminals running.

## Test checklist
1. Apply X to |0⟩: P(0)=0 and P(1)=1.
2. Reset and apply H: P(0)=P(1)=0.5.
3. Apply H twice: returns to |0⟩.
4. Try RX/RY/RZ with different angles.
5. Use playback, undo, and redo.
6. Run measurement shots and compare theoretical/observed frequencies.
7. Run tomography in X/Y/Z bases; finite-shot estimates vary.
8. Compare fidelity with target states.
9. Complete quiz and load challenges.
10. Enter a custom initial state using the real and imaginary parts of α and β.
11. Adjust rotation angles in 1° steps for sensitivity comparisons.
12. Export CSV and PDF.

## Scientific notes
- Rotation angles are input in degrees and converted to radians.
- Pure-state fidelity is |<target|state>|^2.
- Tomography simulates finite-shot measurements along X/Y/Z and uses linear inversion to estimate the density matrix. Finite-shot linear inversion can produce a nonphysical estimate; this is explained in the UI.
- This is a learning simulator, not a connection to quantum hardware.

## Custom initial states and rotation sensitivity

- Enter Re(α), Im(α), Re(β), and Im(β) for the initial state α|0⟩ + β|1⟩.
- The backend rejects non-finite or all-zero amplitudes and normalizes valid amplitudes before simulation.
- The RX, RY, and RZ angle slider uses 1° steps. For a sensitivity experiment, compare the same initial state and gate using an ideal angle and nearby perturbed angles.
- These experiments are simulations of state-vector calculations; they do not model hardware noise.
