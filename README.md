# QubitLab — Interactive Quantum Gate Simulator

A learning-focused React + FastAPI app for exploring single-qubit quantum gates.

## Features
- Pauli-X, Y, Z; Hadamard H; S and T gates; RX, RY, RZ rotation gates
- Build and clear a gate sequence
- Complex state-vector amplitudes and measurement probabilities
- Bloch sphere and circuit diagrams rendered by Matplotlib
- Simulated measurement shots vs theoretical probabilities
- Fidelity against target states |0>, |1>, |+>, |->, |+i>, |-i>
- Qiskit statevector cross-check of the NumPy result

## Requirements
- Python 3.10+ recommended
- Node.js 18+ and npm

## Project structure
```text
quantum-gate-simulator/
├── backend/
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── styles.css
```

## 1. Start the backend
Open a terminal in the project folder:

```bash
cd backend
python -m venv .venv
```

Activate the environment:
- Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
- Windows Command Prompt: `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies and start the API:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend API: http://127.0.0.1:8000  
Interactive API docs: http://127.0.0.1:8000/docs

## 2. Start the frontend
Open a **second terminal** in the project folder:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173).

## How to use
1. Pick the initial state |0> or |1>.
2. Select a gate. For RX, RY, or RZ, set the angle in degrees.
3. Press **Apply gate** to append it to the sequence.
4. Inspect the state vector, Bloch sphere, circuit, and probabilities.
5. Change shots and press **Run measurements**.
6. Choose a target state to calculate fidelity.

## Notes
- Gate rotation angles are entered in degrees in the UI and converted to radians in the API.
- Measurement is simulated with NumPy's random sampler; finite-shot counts vary between runs.
- Fidelity is `|<target|state>|²` for pure states.
- Global phase does not change the physical qubit state. The displayed relative phase is the phase of alpha relative to beta when both amplitudes are nonzero.
- This is a local educational simulator, not a connection to quantum hardware.
