"""Circuit builder API."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .engine import QuantumEngine
from .gates import GateOp, canonical_gate_name, validate_gate_arity
from .types import QubitRef, qubit_index


@dataclass
class Circuit:
    """A lightweight circuit that can be simulated or exported to QASM."""
    n_qubits: int
    operations: list[GateOp] = field(default_factory=list)

    def add(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> "Circuit":
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        self.operations.append(GateOp(name, qidx, params))
        return self

    def run(self, *, backend: str = "sparse", shots: int | None = None, seed: int | None = None,
            optimize: bool = False, **backend_options):
        if backend == "hybrid":
            from .hybrid import HybridEngine
            return HybridEngine.run_circuit(self.n_qubits, self.operations, shots=shots, seed=seed,
                                            optimize=optimize, **backend_options)
        ops = self.operations
        if optimize:
            from .optimizer import optimize_operations
            ops, _ = optimize_operations(ops)
        if backend in {"auto", "automatic"}:
            from .planner import analyze_operations, enforce_backend_selection
            plan = analyze_operations(self.n_qubits, ops, distributed_workers=len(backend_options.get("addresses") or []))
            enforce_backend_selection(plan)
            selected = {"statevector": "sparse", "sparse_sharded": "sharded", "extended_stabilizer": "stabilizer"}.get(plan.backend, plan.backend)
            backend_options.setdefault("_auto_plan", plan.to_dict())
            backend = selected
        engine = QuantumEngine.create(self.n_qubits, backend=backend, seed=seed, **backend_options)
        for op in ops:
            engine.apply(op.name, *op.qubits, params=op.params)
        if shots is not None:
            return engine.measure_all(shots)
        return engine

    def optimize(self, *, aggressive: bool = True):
        from .optimizer import optimize_operations
        optimized, report = optimize_operations(self.operations, aggressive=aggressive)
        return Circuit(self.n_qubits, optimized), report

    def qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.operations, self.n_qubits, include_measure=include_measure)

    def qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.operations, self.n_qubits, include_measure=include_measure)

    # Common fluent gate aliases
    def H(self, q): return self.add("H", q)
    def X(self, q): return self.add("X", q)
    def Y(self, q): return self.add("Y", q)
    def Z(self, q): return self.add("Z", q)
    def S(self, q): return self.add("S", q)
    def Sdg(self, q): return self.add("Sdg", q)
    def T(self, q): return self.add("T", q)
    def Tdg(self, q): return self.add("Tdg", q)
    def SX(self, q): return self.add("SX", q)
    def SXdg(self, q): return self.add("SXdg", q)
    def Rx(self, q, theta): return self.add("Rx", q, params=(theta,))
    def Ry(self, q, theta): return self.add("Ry", q, params=(theta,))
    def Rz(self, q, theta): return self.add("Rz", q, params=(theta,))
    def Phase(self, q, theta): return self.add("Phase", q, params=(theta,))
    def U3(self, q, theta, phi, lam): return self.add("U3", q, params=(theta, phi, lam))
    def CNOT(self, c, t): return self.add("CNOT", c, t)
    def CX(self, c, t): return self.add("CNOT", c, t)
    def CZ(self, c, t): return self.add("CZ", c, t)
    def SWAP(self, a, b): return self.add("SWAP", a, b)
    def RZZ(self, a, b, theta): return self.add("RZZ", a, b, params=(theta,))
    def Toffoli(self, a, b, c): return self.add("Toffoli", a, b, c)
    def RXX(self, a, b, theta): return self.add("RXX", a, b, params=(theta,))
    def RYY(self, a, b, theta): return self.add("RYY", a, b, params=(theta,))
    def RZX(self, a, b, theta): return self.add("RZX", a, b, params=(theta,))
    def MS(self, a, b): return self.add("MS", a, b)
    def Fredkin(self, c, a, b): return self.add("Fredkin", c, a, b)
    def CCZ(self, a, b, c): return self.add("CCZ", a, b, c)
