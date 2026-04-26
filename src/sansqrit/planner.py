"""Adaptive backend planner and execution estimator for Sansqrit.

The planner is the middle-layer brain of Sansqrit. It does not claim that a
large dense state-vector can be simulated magically; instead, it inspects the
circuit structure and chooses a safe execution strategy among sparse/sharded,
hierarchical tensor shards, MPS, stabilizer/extended-stabilizer, density matrix,
GPU, and distributed backends.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import inf
from typing import Sequence, Any, Iterable

CLIFFORD = {"I", "X", "Y", "Z", "H", "S", "Sdg", "CNOT", "CX", "CZ", "SWAP", "CY", "CH", "CCX", "Toffoli", "CCZ"}
NON_CLIFFORD_MARKERS = {"T", "Tdg", "SX", "SXdg", "Rx", "Ry", "Rz", "Phase", "U1", "U2", "U3", "RXX", "RYY", "RZZ", "RZX", "CP", "CU", "CRx", "CRy", "CRz"}
TWO = {"CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "RXX", "RYY", "RZZ", "RZX", "ECR", "MS", "CP", "CU", "CRx", "CRy", "CRz"}
DENSE_CPU_SAFE_QUBITS = 26
DENSE_GPU_SAFE_QUBITS = 32
DENSITY_SAFE_QUBITS = 14

@dataclass
class CircuitFeatures:
    n_qubits: int
    gates: int
    single_qubit_gates: int
    two_qubit_gates: int
    multi_qubit_gates: int
    h_gates: int
    parameterized_gates: int
    non_clifford_gates: int
    clifford_only: bool
    touched_qubits: int
    component_sizes: list[int]
    max_component_size: int
    cross_block_edges: int
    estimated_depth: int
    estimated_dense_bytes: int | str
    estimated_density_bytes: int | str
    estimated_sparse_amplitudes: int | str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class BackendPlan:
    backend: str
    n_qubits: int
    gates: int
    clifford_only: bool
    non_clifford_gates: int
    estimated_amplitudes: int | str
    estimated_dense_bytes: int | str
    reason: str
    warnings: list[str]
    confidence: float = 0.75
    alternatives: list[str] | None = None
    features: dict[str, Any] | None = None
    enforce: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def explain(self) -> str:
        lines = [
            f"selected_backend: {self.backend}",
            f"n_qubits: {self.n_qubits}",
            f"gates: {self.gates}",
            f"clifford_only: {self.clifford_only}",
            f"non_clifford_gates: {self.non_clifford_gates}",
            f"estimated_amplitudes: {self.estimated_amplitudes}",
            f"estimated_dense_bytes: {self.estimated_dense_bytes}",
            f"confidence: {self.confidence:.2f}",
            f"reason: {self.reason}",
        ]
        if self.alternatives:
            lines.append("alternatives: " + ", ".join(self.alternatives))
        for w in self.warnings:
            lines.append("warning: " + w)
        return "\n".join(lines)


def _op_name(op: Any) -> str:
    if hasattr(op, "name"):
        return str(op.name)
    if isinstance(op, tuple) and op:
        return str(op[0])
    if isinstance(op, dict):
        return str(op.get("name") or op.get("gate") or "")
    return str(op)


def _op_qubits(op: Any) -> tuple[int, ...]:
    if hasattr(op, "qubits"):
        return tuple(int(q) for q in op.qubits)
    if isinstance(op, tuple) and len(op) > 1:
        try:
            return tuple(int(q) for q in op[1])
        except Exception:
            return tuple()
    if isinstance(op, dict):
        try:
            return tuple(int(q) for q in op.get("qubits", ()))
        except Exception:
            return tuple()
    return tuple()


def _op_params(op: Any) -> tuple[float, ...]:
    if hasattr(op, "params"):
        return tuple(float(x) for x in op.params)
    if isinstance(op, tuple) and len(op) > 2:
        try:
            return tuple(float(x) for x in op[2])
        except Exception:
            return tuple()
    if isinstance(op, dict):
        try:
            return tuple(float(x) for x in op.get("params", ()))
        except Exception:
            return tuple()
    return tuple()


def _component_sizes(n_qubits: int, operations: Sequence[Any]) -> tuple[list[int], int]:
    parent = list(range(n_qubits))
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    touched = set()
    cross_block_edges = 0
    for op in operations:
        qs = [q for q in _op_qubits(op) if 0 <= q < n_qubits]
        touched.update(qs)
        if len(qs) >= 2:
            if qs[0] // 10 != qs[1] // 10:
                cross_block_edges += 1
            first = qs[0]
            for q in qs[1:]:
                union(first, q)
    sizes: dict[int, int] = {}
    for q in touched:
        r = find(q)
        sizes[r] = sizes.get(r, 0) + 1
    return sorted(sizes.values(), reverse=True), cross_block_edges


def estimate_depth(n_qubits: int, operations: Sequence[Any]) -> int:
    last = [0] * max(1, n_qubits)
    depth = 0
    for op in operations:
        qs = [q for q in _op_qubits(op) if 0 <= q < n_qubits]
        if not qs:
            depth += 1
            continue
        layer = max(last[q] for q in qs) + 1
        for q in qs:
            last[q] = layer
        depth = max(depth, layer)
    return depth


def dense_memory_bytes(n_qubits: int, bytes_per_amplitude: int = 16) -> int | str:
    if n_qubits > 62:
        return f"2^{n_qubits} * {bytes_per_amplitude} bytes"
    return (1 << n_qubits) * bytes_per_amplitude


def density_memory_bytes(n_qubits: int, bytes_per_entry: int = 16) -> int | str:
    if n_qubits > 31:
        return f"4^{n_qubits} * {bytes_per_entry} bytes"
    return (1 << (2 * n_qubits)) * bytes_per_entry


def analyze_features(n_qubits: int, operations: Sequence[Any]) -> CircuitFeatures:
    names = [_op_name(op) for op in operations]
    qs_by_op = [_op_qubits(op) for op in operations]
    gates = len(names)
    single = sum(1 for qs in qs_by_op if len(qs) == 1)
    two = sum(1 for qs in qs_by_op if len(qs) == 2)
    multi = sum(1 for qs in qs_by_op if len(qs) >= 3)
    h_count = sum(1 for n in names if n == "H")
    param = sum(1 for op in operations if _op_params(op))
    non_clifford = sum(1 for n in names if n not in CLIFFORD)
    touched = len({q for qs in qs_by_op for q in qs if 0 <= q < n_qubits})
    comp, cross = _component_sizes(n_qubits, operations)
    max_comp = max(comp, default=0)
    notes: list[str] = []
    if n_qubits >= 80:
        notes.append("large logical register; dense state-vector should be avoided unless a specialized backend proves structure")
    if max_comp <= 10 and comp:
        notes.append("all connected components fit packaged <=10q lookup blocks")
    if non_clifford == 0 and gates:
        notes.append("Clifford-only circuit can use stabilizer/tableau representation")
    # This is a conservative upper-bound hint, not a promise.
    if h_count == 0:
        sparse_amp: int | str = min(2 ** max(0, two + multi), 1 << 30)
    elif h_count <= 20 and two <= n_qubits:
        sparse_amp = min(2 ** min(h_count + max(0, two // 2), 30), 1 << 30)
    else:
        sparse_amp = "structure-dependent"
    return CircuitFeatures(
        n_qubits=n_qubits,
        gates=gates,
        single_qubit_gates=single,
        two_qubit_gates=two,
        multi_qubit_gates=multi,
        h_gates=h_count,
        parameterized_gates=param,
        non_clifford_gates=non_clifford,
        clifford_only=(non_clifford == 0),
        touched_qubits=touched,
        component_sizes=comp,
        max_component_size=max_comp,
        cross_block_edges=cross,
        estimated_depth=estimate_depth(n_qubits, operations),
        estimated_dense_bytes=dense_memory_bytes(n_qubits),
        estimated_density_bytes=density_memory_bytes(n_qubits),
        estimated_sparse_amplitudes=sparse_amp,
        notes=notes,
    )


def analyze_operations(n_qubits: int, operations: Sequence[Any], *, noise: bool = False, shots: int | None = None,
                       prefer: str | None = None, available_gpu: bool | None = None,
                       distributed_workers: int = 0, force_dense: bool = False) -> BackendPlan:
    features = analyze_features(n_qubits, operations)
    warnings: list[str] = []
    alternatives: list[str] = []

    if noise:
        if n_qubits <= DENSITY_SAFE_QUBITS:
            return BackendPlan("density", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                               "density-matrix", features.estimated_dense_bytes, "Noise model requested and qubit count is density-matrix safe.", warnings, 0.95, ["sparse trajectory", "qiskit-aer"], features.to_dict())
        warnings.append("Density matrix grows as 4^n; using trajectory/sparse noise recommendation instead of dense density matrix.")

    if prefer and prefer not in {"auto", "automatic"}:
        # Enforce user preference only if not obviously dangerous.
        if prefer in {"statevector", "dense"} and n_qubits > DENSE_GPU_SAFE_QUBITS and not force_dense:
            warnings.append("Requested dense statevector is too large; planner refuses unless force_dense=True.")
        else:
            return BackendPlan(prefer, n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                               features.estimated_sparse_amplitudes, features.estimated_dense_bytes,
                               f"User preference requested backend {prefer!r}.", warnings, 0.8, [], features.to_dict())

    if features.clifford_only and n_qubits >= 40:
        return BackendPlan("stabilizer", n_qubits, features.gates, True, 0, "implicit tableau", "not materialized",
                           "Clifford-only large circuit; stabilizer tableau avoids exponential state-vector storage.", warnings, 0.98,
                           ["stim" if n_qubits >= 100 else "sparse"], features.to_dict())

    if 0 < features.non_clifford_gates <= 12 and n_qubits >= 40:
        return BackendPlan("extended_stabilizer", n_qubits, features.gates, False, features.non_clifford_gates,
                           "stabilizer-rank dependent", "not materialized",
                           "Mostly Clifford circuit with few non-Clifford gates; use extended-stabilizer/magic decomposition when available.", warnings, 0.78,
                           ["mps", "sparse_sharded"], features.to_dict())

    if n_qubits >= 40 and features.max_component_size and features.max_component_size <= 10:
        return BackendPlan("hierarchical", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                           "product of <=10q components", features.estimated_dense_bytes,
                           "Entanglement graph splits into <=10-qubit components; use packaged lookup tensor shards.", warnings, 0.96,
                           ["sparse_sharded", "distributed"], features.to_dict())

    if n_qubits >= 80 and features.cross_block_edges <= max(2, n_qubits // 20):
        return BackendPlan("mps", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                           "bond-dimension dependent", features.estimated_dense_bytes,
                           "Large circuit with limited cross-block bridges; MPS/hierarchical bridge mode is the safest low-entanglement strategy.", warnings, 0.72,
                           ["hierarchical", "sparse_sharded"], features.to_dict())

    if n_qubits >= 40:
        backend = "distributed" if distributed_workers > 1 else "sparse_sharded"
        warnings.append("Dense state-vector simulation is infeasible at this size; performance depends on actual nonzero amplitudes and entanglement.")
        return BackendPlan(backend, n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                           features.estimated_sparse_amplitudes, features.estimated_dense_bytes,
                           "Large non-Clifford circuit; use sparse/sharded or distributed execution and abort if active amplitudes explode.", warnings, 0.65,
                           ["mps", "hybrid", "hardware export"], features.to_dict())

    if n_qubits <= DENSE_CPU_SAFE_QUBITS and features.gates > 0 and features.h_gates > n_qubits // 3:
        return BackendPlan("statevector", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                           1 << n_qubits, features.estimated_dense_bytes,
                           "Small enough for dense state-vector; dense kernels may be faster than sparse maps.", warnings, 0.9,
                           ["gpu" if available_gpu else "sparse"], features.to_dict())

    if available_gpu and n_qubits <= DENSE_GPU_SAFE_QUBITS and features.h_gates > n_qubits // 3:
        return BackendPlan("gpu", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                           1 << n_qubits, features.estimated_dense_bytes,
                           "Dense moderate circuit and GPU is available.", warnings, 0.85,
                           ["statevector", "qiskit-aer-gpu"], features.to_dict())

    return BackendPlan("sparse", n_qubits, features.gates, features.clifford_only, features.non_clifford_gates,
                       features.estimated_sparse_amplitudes, features.estimated_dense_bytes,
                       "Default sparse backend with lookup acceleration; switch if profiler shows dense expansion.", warnings, 0.8,
                       ["sharded", "hierarchical", "mps"], features.to_dict())


def explain_backend_plan(n_qubits: int, operations: Sequence[Any], **kwargs: Any) -> str:
    return analyze_operations(n_qubits, operations, **kwargs).explain()


def enforce_backend_selection(plan: BackendPlan, *, max_dense_qubits: int = DENSE_GPU_SAFE_QUBITS) -> None:
    if plan.backend in {"statevector", "gpu", "dense"} and plan.n_qubits > max_dense_qubits:
        raise RuntimeError(plan.explain() + "\nRefusing dense execution above safe qubit threshold.")


def estimate_dense_memory(n_qubits: int, bytes_per_amplitude: int = 16) -> int:
    return (1 << n_qubits) * bytes_per_amplitude


def plan_from_gate_tuples(n_qubits: int, gates: Iterable[tuple[str, Iterable[int], Iterable[float] | None]]) -> BackendPlan:
    return analyze_operations(n_qubits, [(name, tuple(qs), tuple(params or ())) for name, qs, params in gates])
