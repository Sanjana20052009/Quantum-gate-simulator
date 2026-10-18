import { useCallback, useEffect, useState } from "react";
import {
  Activity, Atom, BookOpen, Check, ChevronDown, CircleHelp, FlaskConical,
  RotateCcw, Play, Plus, Waves, Zap
} from "lucide-react";

const API = "http://127.0.0.1:8000";
const GATE_OPTIONS = [
  { name: "X", label: "Pauli-X", description: "Bit flip: swaps |0⟩ and |1⟩." },
  { name: "Y", label: "Pauli-Y", description: "Bit and phase flip." },
  { name: "Z", label: "Pauli-Z", description: "Changes the phase of |1⟩." },
  { name: "H", label: "Hadamard", description: "Creates or removes equal superpositions." },
  { name: "S", label: "S gate", description: "Adds a π/2 phase to |1⟩." },
  { name: "T", label: "T gate", description: "Adds a π/4 phase to |1⟩." },
  { name: "RX", label: "Rotation X", description: "Rotates the state around the X axis." },
  { name: "RY", label: "Rotation Y", description: "Rotates the state around the Y axis." },
  { name: "RZ", label: "Rotation Z", description: "Rotates the state around the Z axis." },
];
const TARGETS = [
  { value: "0", label: "|0⟩ — North pole" },
  { value: "1", label: "|1⟩ — South pole" },
  { value: "+", label: "|+⟩ — +X axis" },
  { value: "-", label: "|−⟩ — −X axis" },
  { value: "+i", label: "|+i⟩ — +Y axis" },
  { value: "-i", label: "|−i⟩ — −Y axis" },
];
const emptyResult = {
  state: { alpha: { real: 1, imag: 0, magnitude: 1, phase_degrees: 0 }, beta: { real: 0, imag: 0, magnitude: 0, phase_degrees: 0 } },
  probabilities: { "0": 1, "1": 0 },
  measurement: { shots: 1000, counts: { "0": 1000, "1": 0 }, frequencies: { "0": 1, "1": 0 } },
  fidelity: { target: "+", value: 0.5 }, bloch: { x: 0, y: 0, z: 1 },
  relative_phase_degrees: null, history: [], images: {}, qiskit_cross_check_error: 0,
};

function percent(v) { return `${(v * 100).toFixed(1)}%`; }
function complexText(c) {
  const re = Math.abs(c.real) < 1e-7 ? 0 : c.real;
  const im = Math.abs(c.imag) < 1e-7 ? 0 : c.imag;
  if (im === 0) return re.toFixed(3);
  if (re === 0) return `${im.toFixed(3)}i`;
  return `${re.toFixed(3)} ${im < 0 ? "−" : "+"} ${Math.abs(im).toFixed(3)}i`;
}

export default function App() {
  const [initialState, setInitialState] = useState("0");
  const [selectedGate, setSelectedGate] = useState("H");
  const [angle, setAngle] = useState(90);
  const [gates, setGates] = useState([]);
  const [shots, setShots] = useState(1000);
  const [target, setTarget] = useState("+");
  const [result, setResult] = useState(emptyResult);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const runSimulation = useCallback(async (nextGates = gates, nextInitial = initialState, nextShots = shots, nextTarget = target) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initial_state: nextInitial,
          gates: nextGates.map(g => ({ name: g.name, angle: g.angle ?? 90 })),
          shots: Number(nextShots),
          target_state: nextTarget,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail?.[0]?.msg || body.detail || "The simulation request failed.");
      }
      setResult(await response.json());
    } catch (e) {
      setError(`Could not reach the Python API. Start the backend at ${API}. (${e.message})`);
    } finally {
      setLoading(false);
    }
  }, [gates, initialState, shots, target]);

  useEffect(() => { runSimulation([], "0", 1000, "+"); }, []); // initial API health check/simulation

  function applyGate() {
    const gate = { name: selectedGate, ...(selectedGate.startsWith("R") ? { angle: Number(angle) } : {}) };
    const next = [...gates, gate];
    setGates(next);
    runSimulation(next, initialState, shots, target);
  }
  function reset() {
    setGates([]);
    runSimulation([], initialState, shots, target);
  }
  function changeInitial(value) {
    setInitialState(value);
    setGates([]);
    runSimulation([], value, shots, target);
  }
  function removeGate(index) {
    const next = gates.filter((_, i) => i !== index);
    setGates(next);
    runSimulation(next, initialState, shots, target);
  }

  const selected = GATE_OPTIONS.find(g => g.name === selectedGate);
  const state = result.state || emptyResult.state;
  const probs = result.probabilities || emptyResult.probabilities;
  const meas = result.measurement || emptyResult.measurement;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon"><Atom size={22} /></div>
          <div><div className="brand-name">Qubit<span>Lab</span></div><div className="brand-caption">QUANTUM GATE SIMULATOR</div></div>
        </div>
        <nav className="top-nav">
          <button className={activeTab === "overview" ? "nav-link active" : "nav-link"} onClick={() => setActiveTab("overview")}><Activity size={16}/> Simulator</button>
          <button className={activeTab === "learn" ? "nav-link active" : "nav-link"} onClick={() => setActiveTab("learn")}><BookOpen size={16}/> Learn</button>
        </nav>
        <div className="live-pill"><span className="live-dot"/> LOCAL SIMULATOR</div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="eyebrow"><span className="eyebrow-line"/> EXPLORE QUANTUM STATES</div>
          <h1>One qubit. <span>Infinite possibilities.</span></h1>
          <p>Apply quantum gates, observe state transformations, and build intuition for quantum computing — one experiment at a time.</p>
          <div className="hero-tags"><span><Waves size={14}/> Bloch sphere</span><span><Zap size={14}/> 9 quantum gates</span><span><FlaskConical size={14}/> Measurement lab</span></div>
        </section>

        {activeTab === "learn" ? (
          <section className="learn-grid">
            <article className="panel lesson-card"><div className="panel-kicker">01 / THE BASICS</div><h2>What is a qubit?</h2><p>A qubit is a quantum system whose pure state can be written as <code>α|0⟩ + β|1⟩</code>, where α and β are complex amplitudes and <code>|α|² + |β|² = 1</code>.</p><p>Unlike a classical bit, a qubit can be in a superposition. A measurement in the computational basis returns 0 or 1 probabilistically.</p></article>
            <article className="panel lesson-card"><div className="panel-kicker">02 / GATES</div><h2>What do gates do?</h2><p>Quantum gates are reversible transformations represented by unitary matrices. They rotate or reflect the qubit state while preserving total probability.</p><p>Try applying H to |0⟩, then apply H again. The two Hadamard gates return the qubit to |0⟩.</p></article>
            <article className="panel lesson-card"><div className="panel-kicker">03 / MEASUREMENT</div><h2>Probability vs. outcome</h2><p>The state determines theoretical probabilities. A finite number of measurement shots produces counts that fluctuate around those probabilities.</p><p>Increase the number of shots to see the observed frequencies usually move closer to the theoretical values.</p></article>
            <article className="panel lesson-card"><div className="panel-kicker">04 / FIDELITY</div><h2>How close are two states?</h2><p>For pure states, fidelity is <code>|⟨target|state⟩|²</code>. A value of 1 means the states are physically equivalent; 0 means they are orthogonal.</p><p>Global phase does not change a physical state, so fidelity correctly treats globally phased states as equivalent.</p></article>
            <button className="primary-button" onClick={() => setActiveTab("overview")}>Open simulator <ChevronDown size={16}/></button>
          </section>
        ) : (
          <>
            {error && <div className="error-banner"><CircleHelp size={18}/><span>{error}</span></div>}
            <section className="workspace">
              <aside className="panel control-panel">
                <div className="panel-heading"><div><div className="panel-kicker">EXPERIMENT SETUP</div><h2>Gate controls</h2></div><div className="heading-icon"><FlaskConical size={18}/></div></div>
                <label className="field-label">INITIAL QUBIT STATE</label>
                <div className="segmented">
                  <button className={initialState === "0" ? "selected" : ""} onClick={() => changeInitial("0")}>|0⟩ <small>Ground</small></button>
                  <button className={initialState === "1" ? "selected" : ""} onClick={() => changeInitial("1")}>|1⟩ <small>Excited</small></button>
                </div>
                <div className="field-row"><label className="field-label" htmlFor="gate-select">SELECT GATE</label><span className="field-note">Single-qubit</span></div>
                <select id="gate-select" value={selectedGate} onChange={e => setSelectedGate(e.target.value)}>
                  {GATE_OPTIONS.map(g => <option value={g.name} key={g.name}>{g.label} ({g.name})</option>)}
                </select>
                <div className="gate-description"><span className="gate-symbol">{selectedGate}</span><p>{selected?.description}</p></div>
                {selectedGate.startsWith("R") && <div className="angle-control"><div className="field-row"><label className="field-label">ROTATION ANGLE</label><strong>{angle}°</strong></div><input type="range" min="-360" max="360" step="15" value={angle} onChange={e => setAngle(Number(e.target.value))}/><div className="range-labels"><span>−360°</span><span>0°</span><span>360°</span></div></div>}
                <button className="primary-button full-width" onClick={applyGate} disabled={loading}><Plus size={17}/> Apply gate <span className="button-shortcut">↵</span></button>
                <button className="secondary-button full-width" onClick={reset} disabled={loading}><RotateCcw size={15}/> Reset sequence</button>
                <div className="sequence-block"><div className="field-row"><label className="field-label">GATE SEQUENCE</label><span className="count-badge">{gates.length} gates</span></div>
                  {gates.length === 0 ? <div className="empty-sequence">Your sequence is empty.<br/><span>Add a gate to begin experimenting.</span></div> :
                    <div className="gate-sequence">{gates.map((g, i) => <div className="sequence-item" key={`${g.name}-${i}`}><span className="sequence-index">{String(i + 1).padStart(2, "0")}</span><span className="sequence-gate">{g.name}{g.angle !== undefined ? <small> {g.angle}°</small> : ""}</span><button aria-label={`Remove gate ${i + 1}`} onClick={() => removeGate(i)}>×</button></div>)}</div>}
                </div>
              </aside>

              <div className="visual-column">
                <section className="panel bloch-panel">
                  <div className="panel-heading"><div><div className="panel-kicker">STATE VISUALIZATION</div><h2>Bloch sphere <span className="subtle-title">/ 3D</span></h2></div><span className="live-label"><span className="live-dot"/> LIVE STATE</span></div>
                  <div className="bloch-visual">{result.images?.bloch_sphere ? <img src={`data:image/png;base64,${result.images.bloch_sphere}`} alt="3D Bloch sphere showing the current qubit state"/> : <div className="image-placeholder">Waiting for simulation…</div>}</div>
                  <div className="bloch-coordinates"><div><span>X</span><strong>{result.bloch?.x?.toFixed(3) ?? "0.000"}</strong></div><div><span>Y</span><strong>{result.bloch?.y?.toFixed(3) ?? "0.000"}</strong></div><div><span>Z</span><strong>{result.bloch?.z?.toFixed(3) ?? "1.000"}</strong></div></div>
                </section>
                <section className="panel circuit-panel">
                  <div className="panel-heading"><div><div className="panel-kicker">QUANTUM CIRCUIT</div><h2>Your experiment</h2></div><span className="count-badge">{gates.length} operations</span></div>
                  <div className="circuit-image">{result.images?.circuit ? <img src={`data:image/png;base64,${result.images.circuit}`} alt="Diagram of the initial state and quantum gate sequence"/> : <div className="image-placeholder">Circuit appears here</div>}</div>
                </section>
              </div>
            </section>

            <section className="metrics-grid">
              <article className="panel state-panel"><div className="panel-heading"><div><div className="panel-kicker">STATE VECTOR</div><h2>Amplitude inspector</h2></div><div className="heading-icon"><Activity size={17}/></div></div>
                <div className="amplitude-row"><div className="ket">|0⟩</div><div className="amplitude-info"><span className="muted">Amplitude α</span><strong>{complexText(state.alpha)}</strong><div className="amplitude-track"><span style={{width: `${Math.min(100, state.alpha.magnitude * 100)}%`}}/></div></div><div className="amplitude-prob"><strong>{percent(probs["0"])}</strong><span>probability</span></div></div>
                <div className="amplitude-row"><div className="ket ket-one">|1⟩</div><div className="amplitude-info"><span className="muted">Amplitude β</span><strong>{complexText(state.beta)}</strong><div className="amplitude-track pink"><span style={{width: `${Math.min(100, state.beta.magnitude * 100)}%`}}/></div></div><div className="amplitude-prob"><strong>{percent(probs["1"])}</strong><span>probability</span></div></div>
                <div className="phase-row"><span>Relative phase</span><strong>{result.relative_phase_degrees == null ? "Undefined" : `${result.relative_phase_degrees.toFixed(1)}°`}</strong></div>
              </article>
              <article className="panel probability-panel"><div className="panel-heading"><div><div className="panel-kicker">BORN RULE</div><h2>Measurement probabilities</h2></div><div className="heading-icon"><Activity size={17}/></div></div>
                <div className="probability-bars"><div className="prob-item"><div className="prob-label"><span><i className="legend-dot cyan"/> |0⟩</span><strong>{percent(probs["0"])}</strong></div><div className="bar-track"><div className="bar-fill cyan-fill" style={{width: percent(probs["0"])}}/></div></div><div className="prob-item"><div className="prob-label"><span><i className="legend-dot pink-dot"/> |1⟩</span><strong>{percent(probs["1"])}</strong></div><div className="bar-track"><div className="bar-fill pink-fill" style={{width: percent(probs["1"])}}/></div></div></div>
                <div className="formula-note"><code>P(0) = |α|²</code><code>P(1) = |β|²</code></div>
              </article>
              <article className="panel fidelity-panel"><div className="panel-heading"><div><div className="panel-kicker">STATE COMPARISON</div><h2>Fidelity</h2></div><div className="heading-icon"><Check size={17}/></div></div>
                <label className="field-label" htmlFor="target-state">TARGET STATE</label><select id="target-state" value={target} onChange={e => {setTarget(e.target.value); runSimulation(gates, initialState, shots, e.target.value);}}>{TARGETS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}</select>
                <div className="fidelity-score"><strong>{percent(result.fidelity?.value ?? 0)}</strong><span>state fidelity</span></div><div className="bar-track fidelity-track"><div className="bar-fill cyan-fill" style={{width: percent(result.fidelity?.value ?? 0)}}/></div><p className="micro-copy">1.0 = same physical state · 0.0 = orthogonal</p>
              </article>
            </section>

            <section className="bottom-grid">
              <article className="panel measurement-panel"><div className="panel-heading"><div><div className="panel-kicker">REPEATED MEASUREMENT</div><h2>Shot simulator</h2></div><span className="count-badge">Z basis</span></div>
                <div className="shots-control"><label className="field-label" htmlFor="shots">NUMBER OF SHOTS</label><select id="shots" value={shots} onChange={e => setShots(Number(e.target.value))}><option value={100}>100 shots</option><option value={1000}>1,000 shots</option><option value={10000}>10,000 shots</option><option value={100000}>100,000 shots</option></select><button className="primary-button" onClick={() => runSimulation(gates, initialState, shots, target)} disabled={loading}><Play size={15}/>{loading ? "Simulating…" : "Run measurements"}</button></div>
                <div className="counts-grid"><div className="count-card"><span>Outcome 0</span><strong>{meas.counts["0"].toLocaleString()}</strong><small>{percent(meas.frequencies["0"])} observed</small></div><div className="count-card"><span>Outcome 1</span><strong>{meas.counts["1"].toLocaleString()}</strong><small>{percent(meas.frequencies["1"])} observed</small></div></div>
                <div className="comparison-list"><div><span>Theoretical P(0)</span><strong>{percent(probs["0"])}</strong><span>Observed</span><strong>{percent(meas.frequencies["0"])}</strong></div><div><span>Theoretical P(1)</span><strong>{percent(probs["1"])}</strong><span>Observed</span><strong>{percent(meas.frequencies["1"])}</strong></div></div>
                <p className="micro-copy">Counts are randomly sampled on each run. Finite-shot results may differ from the theoretical probabilities.</p>
              </article>
              <article className="panel history-panel"><div className="panel-heading"><div><div className="panel-kicker">TRANSFORMATION LOG</div><h2>Step-by-step state</h2></div><span className="count-badge">{(result.history || []).length} steps</span></div>
                <div className="history-list">{(result.history || []).map((step, i) => <div className="history-step" key={`${step.label}-${i}`}><div className="history-marker">{String(i).padStart(2, "0")}</div><div className="history-step-info"><strong>{step.label}</strong><span>α = {complexText(step.alpha)} · β = {complexText(step.beta)}</span></div>{i === (result.history || []).length - 1 && <span className="current-tag">CURRENT</span>}</div>)}</div>
                <div className="validation-note"><Check size={15}/><span>Qiskit cross-check error: <strong>{Number(result.qiskit_cross_check_error ?? 0).toExponential(2)}</strong></span></div>
              </article>
            </section>
          </>
        )}
        <footer><div className="footer-brand"><Atom size={16}/> QubitLab</div><span>Built for learning quantum computing · Simulated locally, not quantum hardware</span><span className="footer-status"><span className="live-dot"/> API-connected when running</span></footer>
      </main>
    </div>
  );
}