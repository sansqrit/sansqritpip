"""Hybrid backend selection for Sansqrit circuits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .errors import QuantumError
from .gates import GateOp
from .optimizer import is_clifford_circuit, optimize_operations


@dataclass
class HybridRunReport:
    selected_backend: str
    reason: str
    optimized_before: int
    optimized_after: int


class HybridEngine:
    """Factory-style hybrid backend.

    It does not maintain a mixed representation internally yet. Instead it
    chooses the safest backend for a whole circuit: stabilizer for Clifford,
    MPS for large low-entanglement non-Clifford circuits when NumPy is present,
    and sparse otherwise.
    """

    @staticmethod
    def run_circuit(n_qubits: int, operations: Iterable[GateOp], *, shots: int | None = None,
                    seed: int | None = None, optimize: bool = True, max_bond_dim: int | None = 128):
        ops = list(operations)
        if optimize:
            ops, report = optimize_operations(ops)
        else:
            report = type("Report", (), {"before": len(ops), "after": len(ops)})()
        if is_clifford_circuit(ops):
            from .stabilizer import StabilizerEngine
            engine = StabilizerEngine(n_qubits, seed=seed)
            selected = "stabilizer"
            reason = "all operations are Clifford"
        elif n_qubits >= 24 and all(len(op.qubits) <= 2 for op in ops):
            try:
                from .mps import MPSEngine
                engine = MPSEngine(n_qubits, max_bond_dim=max_bond_dim, seed=seed)
                selected = "mps"
                reason = "large two-local circuit; using tensor-network MPS"
            except Exception:
                from .engine import QuantumEngine
                engine = QuantumEngine.create(n_qubits, backend="sparse", seed=seed)
                selected = "sparse"
                reason = "MPS unavailable; using sparse fallback"
        else:
            from .engine import QuantumEngine
            engine = QuantumEngine.create(n_qubits, backend="sparse", seed=seed)
            selected = "sparse"
            reason = "general non-Clifford circuit"
        for op in ops:
            engine.apply(op.name, *op.qubits, params=op.params)
        engine.hybrid_report = HybridRunReport(selected, reason, report.before, report.after)  # type: ignore[attr-defined]
        if shots is not None:
            return engine.measure_all(shots)
        return engine
