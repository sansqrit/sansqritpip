"""Optional CuPy GPU state-vector backend.

Install with a CUDA-specific CuPy wheel, for example:
    pip install sansqrit[gpu]

This backend is dense, so it is for GPU-accelerated moderate-qubit simulation,
not arbitrary 150+ qubit dense states.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Sequence

from .errors import QuantumError
from .gates import GateOp, SINGLE_GATES, TWO_GATES, canonical_gate_name, matrix_2x2, matrix_4x4, validate_gate_arity
from .sparse import conventional_bitstring
from .types import QuantumRegister, QubitRef, qubit_index

try:
    import cupy as cp
except Exception:  # pragma: no cover
    cp = None  # type: ignore


def _need_cupy():
    if cp is None:
        raise QuantumError("GPU backend requires CuPy. Install a CUDA-compatible extra, e.g. pip install sansqrit[gpu]")


@dataclass
class CuPyStateVectorEngine:
    """Dense CuPy state-vector backend."""
    n_qubits: int
    seed: int | None = None
    history: list[GateOp] = field(default_factory=list)

    def __post_init__(self) -> None:
        _need_cupy()
        if self.n_qubits <= 0:
            raise QuantumError("CuPyStateVectorEngine requires at least one qubit")
        if self.n_qubits > 32:
            raise QuantumError("dense GPU backend refuses >32 qubits by default; use sparse/MPS/stabilizer for large logical circuits")
        self.rng = Random(self.seed)
        self.state = cp.zeros(1 << self.n_qubits, dtype=cp.complex128)
        self.state[0] = 1.0

    @property
    def nnz(self) -> int:
        return int(cp.count_nonzero(cp.abs(self.state) > 1e-14).get())

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def ensure_qubits(self, qs: Sequence[int]) -> None:
        for q in qs:
            if q < 0 or q >= self.n_qubits:
                raise QuantumError(f"qubit index {q} out of range for {self.n_qubits} qubits")
        if len(set(qs)) != len(tuple(qs)):
            raise QuantumError(f"gate qubits must be distinct, got {qs}")

    def _apply_dense_matrix(self, qubits: tuple[int, ...], matrix) -> None:
        # Uses tensor reshape with little-endian qubit axes. Axis n-1-q maps qubit q.
        axes = [self.n_qubits - 1 - q for q in qubits]
        psi = self.state.reshape((2,) * self.n_qubits)
        k = len(qubits)
        perm = axes + [a for a in range(self.n_qubits) if a not in axes]
        inv = [0] * self.n_qubits
        for i, a in enumerate(perm):
            inv[a] = i
        psi_p = cp.transpose(psi, perm).reshape(2**k, -1)
        out = cp.asarray(matrix, dtype=cp.complex128).reshape(2**k, 2**k) @ psi_p
        self.state = cp.transpose(out.reshape((2,) * self.n_qubits), inv).reshape(-1)

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        self.ensure_qubits(qidx)
        if name in SINGLE_GATES:
            mat = [[matrix_2x2(name, params)[0], matrix_2x2(name, params)[1]], [matrix_2x2(name, params)[2], matrix_2x2(name, params)[3]]]
            self._apply_dense_matrix(qidx, mat)
        elif name in TWO_GATES:
            self._apply_dense_matrix(qidx, matrix_4x4(name, params))
        else:
            raise QuantumError(f"GPU backend currently supports one- and two-qubit gates, got {name}")
        self.history.append(GateOp(name, qidx, params))

    def probabilities(self) -> dict[str, float]:
        probs_gpu = cp.abs(self.state) ** 2
        idxs = cp.where(probs_gpu > 1e-14)[0].get().tolist()
        probs = probs_gpu.get()
        return {conventional_bitstring(int(i), self.n_qubits): float(probs[int(i)]) for i in idxs}

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        probs = self.probabilities()
        keys = list(probs)
        weights = [probs[k] for k in keys]
        total = sum(weights) or 1.0
        cum = []
        acc = 0.0
        for w in weights:
            acc += w / total; cum.append(acc)
        counts: dict[str, int] = {}
        for _ in range(shots):
            r = self.rng.random(); idx = 0
            while idx < len(cum)-1 and cum[idx] < r:
                idx += 1
            counts[keys[idx]] = counts.get(keys[idx], 0) + 1
        return dict(sorted(counts.items()))

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)

# ---------------------------------------------------------------------------
# Deeper GPU / cuQuantum capability layer
# ---------------------------------------------------------------------------
def gpu_capabilities() -> dict:
    """Return optional GPU/cuQuantum capabilities without importing heavy SDKs eagerly."""
    import importlib.util
    cupy_ok = importlib.util.find_spec("cupy") is not None
    cuquantum_ok = importlib.util.find_spec("cuquantum") is not None
    return {
        "cupy": cupy_ok,
        "cuquantum": cuquantum_ok,
        "dense_statevector": cupy_ok,
        "cuStateVec_target": cuquantum_ok,
        "cuTensorNet_target": cuquantum_ok,
        "cuDensityMat_target": cuquantum_ok,
        "notes": "CuPy backend is executable when CuPy/CUDA is installed. cuQuantum fields expose adapter targets for production GPU deployments.",
    }


def estimate_gpu_statevector_memory(n_qubits: int, bytes_per_amplitude: int = 16, overhead: float = 1.25) -> dict:
    if n_qubits < 0:
        raise QuantumError("n_qubits must be non-negative")
    if n_qubits > 62:
        dense = f"2^{n_qubits} * {bytes_per_amplitude} bytes"
        total = "exponential"
    else:
        dense_bytes = (1 << n_qubits) * bytes_per_amplitude
        dense = dense_bytes
        total = int(dense_bytes * overhead)
    return {"n_qubits": n_qubits, "statevector_bytes": dense, "estimated_total_bytes": total, "overhead_factor": overhead}


class CuQuantumAdapter:
    """Lazy adapter for production cuQuantum integrations.

    The package remains lightweight by not depending on cuQuantum. When installed,
    this object tells users which accelerated targets can be used by an external
    production runner: cuStateVec for dense state-vector, cuTensorNet for tensor
    networks, and cuDensityMat for density-matrix simulation.
    """
    def __init__(self):
        self.capabilities = gpu_capabilities()

    @property
    def available(self) -> bool:
        return bool(self.capabilities.get("cuquantum"))

    def require(self) -> None:
        if not self.available:
            raise QuantumError("cuQuantum is not installed. Install an appropriate NVIDIA cuQuantum Python package in a CUDA environment.")

    def recommendation(self, n_qubits: int, circuit_type: str = "auto") -> dict:
        caps = self.capabilities
        if not caps.get("cuquantum"):
            return {"available": False, "recommended": "install cuQuantum/CUDA or use sparse/MPS/stabilizer"}
        if circuit_type in {"mps", "tensor", "low_entanglement"}:
            target = "cuTensorNet"
        elif circuit_type in {"density", "noise"}:
            target = "cuDensityMat"
        else:
            target = "cuStateVec" if n_qubits <= 32 else "cuTensorNet"
        return {"available": True, "recommended": target, "memory": estimate_gpu_statevector_memory(min(n_qubits, 62))}
