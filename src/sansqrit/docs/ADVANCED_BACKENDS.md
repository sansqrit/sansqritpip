# Sansqrit Advanced Backends

Sansqrit 0.2 adds advanced backends for large and specialized simulations. These backends are not magic: a fully dense, highly entangled 150-qubit state is still infeasible on local hardware. The goal is to avoid expanding the state whenever the circuit structure allows it.

## Backend selection summary

| Backend | DSL syntax | Best for | Scaling idea | Important limit |
|---|---|---|---|---|
| Sparse | `simulate(n, engine="sparse")` | few nonzero amplitudes, oracle circuits, large-index demos | stores only nonzero basis amplitudes | dense superpositions still explode |
| Sharded | `simulate(n, engine="sharded", n_shards=8)` | larger sparse states on one machine | partitions sparse dictionary | not multi-node |
| Threaded | `simulate(n, engine="threaded", workers=8)` | large sparse single-qubit transforms | thread pool over sparse chunks | Python GIL limits CPU speedups for some operations |
| Stabilizer | `simulate(n, engine="stabilizer")` | Clifford circuits with hundreds/thousands of qubits | binary tableau | rejects non-Clifford gates such as T/Rx/RZZ |
| MPS / tensor network | `simulate(n, engine="mps", max_bond_dim=128)` | low-entanglement 1D-ish circuits | matrix product state with SVD truncation | high entanglement increases bond dimension |
| Hybrid | Python API: `Circuit(...).run(backend="hybrid")` | automatic whole-circuit routing | chooses stabilizer/MPS/sparse | dynamic DSL routing is intentionally conservative |
| Density / noisy | `simulate(n, engine="density")` | small noisy circuits | sparse density matrix and Kraus channels | density matrices scale as 4^n in the worst case |
| GPU / CuPy | `simulate(n, engine="gpu")` | moderate dense state vectors on CUDA GPUs | dense vector on GPU | not for 150 dense qubits |
| Distributed cluster | Python API: `DistributedSparseEngine.from_addresses(...)` | correctness-first multi-node sparse shards | TCP workers store shards | gathers state per gate; not MPI-performance yet |

## Stabilizer backend

Use it for Clifford circuits:

```sansqrit
simulate(1000, engine="stabilizer", seed=7) {
    H(0)
    for i in range(0, 999) {
        CNOT(i, i + 1)
    }
    print(measure_all(shots=8))
}
```

Supported stabilizer gates: `I`, `X`, `Y`, `Z`, `H`, `S`, `Sdg`, `CNOT`/`CX`, `CZ`, `SWAP`.

The backend raises an error for non-Clifford gates. This is intentional: silently switching to dense simulation would defeat the purpose.

## MPS / tensor-network backend

Use it when the circuit has limited entanglement:

```sansqrit
simulate(64, engine="mps", max_bond_dim=64, cutoff=1e-10) {
    for i in range(0, 64) { Ry(i, 0.05) }
    for i in range(0, 63) { CNOT(i, i + 1) }
    print(measure_all(shots=32))
}
```

Install dependencies:

```bash
pip install sansqrit[tensor]
```

## Noise and density matrices

```sansqrit
simulate(2, engine="density", seed=1) {
    H(0)
    CNOT(0, 1)
    noise_depolarize(0, 0.01)
    noise_amplitude_damping(1, 0.05)
    print(probabilities())
}
```

Noise functions:

- `noise_depolarize(q, p)`
- `noise_bit_flip(q, p)`
- `noise_phase_flip(q, p)`
- `noise_amplitude_damping(q, gamma)`

## GPU backend

```bash
pip install sansqrit[gpu]
```

```sansqrit
simulate(20, engine="gpu") {
    H(0)
    CNOT(0, 1)
    print(measure_all(shots=100))
}
```

The GPU backend is dense. It accelerates moderate state vectors but cannot store arbitrary 150-qubit dense states.

## Distributed cluster backend

Start workers on machines reachable by TCP:

```bash
sansqrit worker --host 0.0.0.0 --port 8765
sansqrit worker --host 0.0.0.0 --port 8766
```

Use from Python:

```python
from sansqrit.cluster import DistributedSparseEngine

engine = DistributedSparseEngine.from_addresses(150, ["worker-a:8765", "worker-b:8766"])
engine.apply("H", 0)
engine.apply("CNOT", 0, 149)
print(engine.measure_all(100))
```

This mode is a real multi-node protocol, but it prioritizes correctness. It gathers/repartitions state around each operation, so it is not yet a high-performance MPI simulator.

## Interop

Install extras as needed:

```bash
pip install sansqrit[qiskit]
pip install sansqrit[cirq]
pip install sansqrit[braket]
pip install sansqrit[pennylane]
```

Python API:

```python
from sansqrit import Circuit
from sansqrit.interop import to_qiskit, to_cirq, to_braket, apply_to_pennylane

circuit = Circuit(2).H(0).CNOT(0, 1)
qc = to_qiskit(circuit)
cc = to_cirq(circuit)
braket_circuit = to_braket(circuit)
qml_function = apply_to_pennylane(circuit)
```

## Formal verification helpers

```python
from sansqrit import Circuit
from sansqrit.verification import verify_all_available

circuit = Circuit(2).H(0).CNOT(0, 1)
for result in verify_all_available(circuit):
    print(result)
```

The helpers compare Sansqrit probabilities against installed SDK simulators. They are regression checks, not mathematical proof certificates.
