"""Adaptive backend planner and execution estimator for Sansqrit."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import log2
from typing import Sequence, Any

CLIFFORD = {"I", "X", "Y", "Z", "H", "S", "Sdg", "CNOT", "CX", "CZ", "SWAP"}
TWO = {"CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "RXX", "RYY", "RZZ", "RZX", "ECR", "MS"}

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _op_name(op: Any) -> str:
    if hasattr(op, "name"):
        return str(op.name)
    if isinstance(op, tuple) and op:
        return str(op[0])
    return str(op)


def _op_qubits(op: Any) -> tuple[int, ...]:
    if hasattr(op, "qubits"):
        return tuple(int(q) for q in op.qubits)
    if isinstance(op, tuple) and len(op) > 1:
        try:
            return tuple(int(q) for q in op[1])
        except Exception:
            return tuple()
    return tuple()


def _component_sizes(n_qubits: int, operations: Sequence[Any]) -> list[int]:
    parent = list(range(n_qubits))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    touched = set()
    for op in operations:
        qs = [q for q in _op_qubits(op) if 0 <= q < n_qubits]
        touched.update(qs)
        if len(qs) >= 2:
            first = qs[0]
            for q in qs[1:]:
                union(first, q)
    sizes: dict[int, int] = {}
    for q in touched:
        r = find(q)
        sizes[r] = sizes.get(r, 0) + 1
    return sorted(sizes.values(), reverse=True)


def analyze_operations(n_qubits: int, operations: Sequence[Any]) -> BackendPlan:
    names = [_op_name(op) for op in operations]
    gates = len(names)
    non_clifford = sum(1 for n in names if n not in CLIFFORD)
    two_qubit = sum(1 for n in names if n in TWO)
    h_count = sum(1 for n in names if n == "H")
    warnings: list[str] = []
    clifford_only = non_clifford == 0
    if clifford_only and n_qubits >= 40:
        return BackendPlan("stabilizer", n_qubits, gates, True, 0, "implicit", "not materialized", "Clifford-only large circuit; tableau avoids dense expansion.", warnings)
    if n_qubits <= 24:
        dense_bytes = (2 ** n_qubits) * 16
    else:
        dense_bytes = "exponential"
    component_sizes = _component_sizes(n_qubits, operations)
    if n_qubits >= 40 and component_sizes and max(component_sizes) <= 10:
        return BackendPlan("hierarchical", n_qubits, gates, clifford_only, non_clifford, "product-of-<=10q-blocks", dense_bytes, "Independent components fit packaged 10-qubit tensor shards; dense global state avoided.", warnings)
    if h_count == 0 and two_qubit <= max(1, n_qubits // 4):
        est_amp: int | str = min(2 ** min(h_count + 1, 20), 1 << 20)
        return BackendPlan("sparse_sharded" if n_qubits >= 40 else "sparse", n_qubits, gates, clifford_only, non_clifford, est_amp, dense_bytes, "Sparse-looking circuit with limited superposition/entanglement.", warnings)
    if n_qubits >= 60:
        warnings.append("Dense state-vector simulation would be infeasible; auto planner will avoid dense backend.")
        if clifford_only:
            backend = "stabilizer"
            reason = "Large Clifford circuit."
        else:
            backend = "mps"
            reason = "Large non-Clifford circuit; try MPS if entanglement is low."
        return BackendPlan(backend, n_qubits, gates, clifford_only, non_clifford, "structure-dependent", dense_bytes, reason, warnings)
    return BackendPlan("sparse", n_qubits, gates, clifford_only, non_clifford, "runtime", dense_bytes, "Default sparse backend; use GPU for dense small circuits if available.", warnings)


def estimate_dense_memory(n_qubits: int, bytes_per_amplitude: int = 16) -> int:
    return (1 << n_qubits) * bytes_per_amplitude
