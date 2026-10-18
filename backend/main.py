from __future__ import annotations

import base64
import io
import math
from typing import Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

app = FastAPI(title="QubitLab Quantum Simulator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQRT2 = math.sqrt(2)
GATES = {"X", "Y", "Z", "H", "S", "T", "RX", "RY", "RZ"}
TARGETS = {
    "0": np.array([1, 0], dtype=complex),
    "1": np.array([0, 1], dtype=complex),
    "+": np.array([1, 1], dtype=complex) / SQRT2,
    "-": np.array([1, -1], dtype=complex) / SQRT2,
    "+i": np.array([1, 1j], dtype=complex) / SQRT2,
    "-i": np.array([1, -1j], dtype=complex) / SQRT2,
}

class GateInput(BaseModel):
    name: str
    angle: float = 90

    @model_validator(mode="after")
    def validate_gate(self):
        self.name = self.name.upper()
        if self.name not in GATES:
            raise ValueError(f"Unsupported gate: {self.name}")
        if self.name in {"RX", "RY", "RZ"} and not -3600 <= self.angle <= 3600:
            raise ValueError("Rotation angle must be between -3600 and 3600 degrees.")
        return self

class SimulationInput(BaseModel):
    initial_state: Literal["0", "1"] = "0"
    gates: list[GateInput] = Field(default_factory=list, max_length=100)
    shots: int = Field(default=1000, ge=1, le=100000)
    target_state: Literal["0", "1", "+", "-", "+i", "-i"] = "+"

def gate_matrix(g: GateInput) -> np.ndarray:
    name = g.name
    if name == "X": return np.array([[0, 1], [1, 0]], dtype=complex)
    if name == "Y": return np.array([[0, -1j], [1j, 0]], dtype=complex)
    if name == "Z": return np.array([[1, 0], [0, -1]], dtype=complex)
    if name == "H": return np.array([[1, 1], [1, -1]], dtype=complex) / SQRT2
    if name == "S": return np.array([[1, 0], [0, 1j]], dtype=complex)
    if name == "T": return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
    theta = math.radians(g.angle)
    if name == "RX":
        return np.array([[np.cos(theta/2), -1j*np.sin(theta/2)],
                         [-1j*np.sin(theta/2), np.cos(theta/2)]], dtype=complex)
    if name == "RY":
        return np.array([[np.cos(theta/2), -np.sin(theta/2)],
                         [np.sin(theta/2), np.cos(theta/2)]], dtype=complex)
    if name == "RZ":
        return np.array([[np.exp(-1j*theta/2), 0],
                         [0, np.exp(1j*theta/2)]], dtype=complex)
    raise ValueError(f"Unsupported gate: {name}")

def qiskit_apply(qc: QuantumCircuit, gate: GateInput):
    n = gate.name
    if n == "X": qc.x(0)
    elif n == "Y": qc.y(0)
    elif n == "Z": qc.z(0)
    elif n == "H": qc.h(0)
    elif n == "S": qc.s(0)
    elif n == "T": qc.t(0)
    elif n == "RX": qc.rx(math.radians(gate.angle), 0)
    elif n == "RY": qc.ry(math.radians(gate.angle), 0)
    elif n == "RZ": qc.rz(math.radians(gate.angle), 0)

def complex_obj(z: complex) -> dict:
    return {"real": round(float(z.real), 8), "imag": round(float(z.imag), 8),
            "magnitude": round(float(abs(z)), 8), "phase_degrees": round(float(np.degrees(np.angle(z))), 4)}

def image_to_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=135, bbox_inches="tight", facecolor="#0b1220")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")

def bloch_image(state: np.ndarray) -> str:
    a, b = state
    x = float(2 * np.real(np.conj(a) * b))
    y = float(2 * np.imag(np.conj(a) * b))
    z = float(abs(a)**2 - abs(b)**2)
    fig = plt.figure(figsize=(5.2, 4.6))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0b1220")
    u = np.linspace(0, 2*np.pi, 70)
    v = np.linspace(0, np.pi, 45)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(xs, ys, zs, color="#1e3a5f", alpha=0.12, linewidth=0)
    for vals in [([ -1, 1], [0, 0], [0, 0]), ([0, 0], [-1, 1], [0, 0]), ([0, 0], [0, 0], [-1, 1])]:
        ax.plot(*vals, color="#52647d", linewidth=0.8, alpha=0.8)
    ax.text(0, 0, 1.13, "|0⟩", color="#f8fafc", ha="center", fontsize=11)
    ax.text(0, 0, -1.18, "|1⟩", color="#f8fafc", ha="center", fontsize=11)
    ax.text(1.12, 0, 0, "+X", color="#f8fafc", ha="center")
    ax.text(0, 1.12, 0, "+Y", color="#f8fafc", ha="center")
    ax.text(-1.12, 0, 0, "-X", color="#f8fafc", ha="center")
    ax.text(0, -1.12, 0, "-Y", color="#f8fafc", ha="center")
    ax.quiver(0, 0, 0, x, y, z, color="#22d3ee", linewidth=3, arrow_length_ratio=0.15)
    ax.scatter([x], [y], [z], color="#fbbf24", s=45)
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.set_zlim(-1.15, 1.15)
    ax.set_box_aspect((1, 1, 1))
    ax.set_title("Qubit state on the Bloch sphere", color="#f8fafc", pad=10)
    ax.tick_params(colors="#94a3b8", labelsize=7)
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
    ax.grid(False)
    return image_to_base64(fig)

def circuit_image(initial: str, gates: list[GateInput]) -> str:
    labels = [f"Initial |{initial}⟩"] + [
        f"{g.name}({g.angle:g}°)" if g.name in {"RX", "RY", "RZ"} else g.name for g in gates
    ]
    n = len(labels)
    fig, ax = plt.subplots(figsize=(max(6, min(14, n*1.15)), 2.2))
    fig.patch.set_facecolor("#0b1220"); ax.set_facecolor("#0b1220")
    ax.plot([0.05, 0.95], [0.5, 0.5], color="#94a3b8", linewidth=2, transform=ax.transAxes)
    positions = np.linspace(0.08, 0.92, n)
    for x, label in zip(positions, labels):
        ax.text(x, 0.5, label, transform=ax.transAxes, ha="center", va="center",
                color="#f8fafc", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.45", facecolor="#123047", edgecolor="#22d3ee", linewidth=1))
    ax.text(0.02, 0.79, "q0", transform=ax.transAxes, color="#f8fafc", fontsize=9)
    ax.set_axis_off()
    ax.set_title("Circuit sequence", color="#f8fafc", pad=8)
    return image_to_base64(fig)

@app.get("/")
def root():
    return {"message": "QubitLab API is running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/simulate")
def simulate(payload: SimulationInput):
    state = np.array([1, 0] if payload.initial_state == "0" else [0, 1], dtype=complex)
    qc = QuantumCircuit(1)
    if payload.initial_state == "1":
        qc.x(0)
    history = []
    history.append({"label": f"Initial |{payload.initial_state}⟩",
                    "alpha": complex_obj(state[0]), "beta": complex_obj(state[1])})
    for gate in payload.gates:
        state = gate_matrix(gate) @ state
        qiskit_apply(qc, gate)
        history.append({"label": f"{gate.name}" + (f" ({gate.angle:g}°)" if gate.name in {"RX", "RY", "RZ"} else ""),
                        "alpha": complex_obj(state[0]), "beta": complex_obj(state[1])})

    # Cross-check the matrix result against Qiskit's Statevector.
    qiskit_state = np.asarray(Statevector.from_instruction(qc).data, dtype=complex)
    qiskit_error = float(np.linalg.norm(state - qiskit_state))
    p0 = float(abs(state[0])**2)
    p1 = float(abs(state[1])**2)
    rng = np.random.default_rng()
    counts = rng.multinomial(payload.shots, [p0, p1])
    target = TARGETS[payload.target_state]
    fidelity = float(abs(np.vdot(target, state))**2)
    rel_phase = None
    if abs(state[0]) > 1e-10 and abs(state[1]) > 1e-10:
        rel_phase = float(np.degrees(np.angle(state[1] / state[0])))
    bloch = [
        float(2 * np.real(np.conj(state[0]) * state[1])),
        float(2 * np.imag(np.conj(state[0]) * state[1])),
        float(abs(state[0])**2 - abs(state[1])**2),
    ]
    return {
        "state": {"alpha": complex_obj(state[0]), "beta": complex_obj(state[1])},
        "probabilities": {"0": p0, "1": p1},
        "measurement": {"shots": payload.shots, "counts": {"0": int(counts[0]), "1": int(counts[1])},
                        "frequencies": {"0": float(counts[0]/payload.shots), "1": float(counts[1]/payload.shots)}},
        "fidelity": {"target": payload.target_state, "value": fidelity},
        "bloch": {"x": bloch[0], "y": bloch[1], "z": bloch[2]},
        "relative_phase_degrees": rel_phase,
        "history": history,
        "circuit_gate_count": len(payload.gates),
        "qiskit_cross_check_error": qiskit_error,
        "images": {"bloch_sphere": bloch_image(state), "circuit": circuit_image(payload.initial_state, payload.gates)},
    }
