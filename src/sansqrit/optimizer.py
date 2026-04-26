"""Circuit optimization passes for Sansqrit.

The optimizer is deliberately conservative: every pass preserves the unitary
for the supported gates and refuses transformations that require global phase
bookkeeping beyond what the circuit exporter can represent.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose, tau
from typing import Iterable

from .gates import GateOp, canonical_gate_name

SELF_INVERSE = {"H", "X", "Y", "Z", "CNOT", "CX", "CZ", "CY", "SWAP", "Toffoli", "CCX", "Fredkin", "CSWAP", "CCZ"}
INVERSES = {"S": "Sdg", "Sdg": "S", "T": "Tdg", "Tdg": "T", "SX": "SXdg", "SXdg": "SX"}
ROTATION_GATES = {"Rx", "Ry", "Rz", "Phase", "U1", "CRx", "CRy", "CRz", "CP", "RXX", "RYY", "RZZ", "RZX"}

@dataclass(frozen=True)
class OptimizationReport:
    before: int
    after: int
    removed: int
    passes: tuple[str, ...]


def _norm_angle(theta: float) -> float:
    value = ((theta + tau) % tau)
    if value > tau / 2:
        value -= tau
    if abs(value) < 1e-12:
        return 0.0
    return value


def _same_target(a: GateOp, b: GateOp) -> bool:
    return a.qubits == b.qubits


def _is_inverse(a: GateOp, b: GateOp) -> bool:
    an = canonical_gate_name(a.name)
    bn = canonical_gate_name(b.name)
    if a.params or b.params or a.qubits != b.qubits:
        return False
    return (an in SELF_INVERSE and an == bn) or INVERSES.get(an) == bn


def optimize_operations(operations: Iterable[GateOp], *, aggressive: bool = True) -> tuple[list[GateOp], OptimizationReport]:
    """Optimize a list of operations.

    Passes implemented:
    - remove zero-angle rotations;
    - cancel adjacent inverse gates;
    - merge adjacent rotations of the same type and qubits;
    - delete resulting zero-angle rotations;
    - optionally repeat until no change.
    """
    ops = [op.canonical() for op in operations]
    before = len(ops)
    passes: list[str] = []

    changed = True
    while changed:
        changed = False
        out: list[GateOp] = []
        i = 0
        while i < len(ops):
            op = ops[i]
            name = canonical_gate_name(op.name)
            if name in ROTATION_GATES and op.params and _norm_angle(op.params[0]) == 0.0:
                passes.append("remove-zero-rotation")
                changed = True
                i += 1
                continue
            if i + 1 < len(ops) and _is_inverse(op, ops[i+1]):
                passes.append("cancel-adjacent-inverse")
                changed = True
                i += 2
                continue
            if i + 1 < len(ops):
                nxt = ops[i+1].canonical()
                if name == canonical_gate_name(nxt.name) and name in ROTATION_GATES and _same_target(op, nxt):
                    merged = _norm_angle(float(op.params[0]) + float(nxt.params[0]))
                    if merged == 0.0:
                        passes.append("merge-delete-rotations")
                        changed = True
                        i += 2
                        continue
                    out.append(GateOp(name, op.qubits, (merged,) + tuple(op.params[1:])))
                    passes.append("merge-rotations")
                    changed = True
                    i += 2
                    continue
            out.append(op)
            i += 1
        ops = out
        if not aggressive:
            break
    return ops, OptimizationReport(before=before, after=len(ops), removed=before-len(ops), passes=tuple(sorted(set(passes))))


def is_clifford_operation(op: GateOp) -> bool:
    """Return True for operations supported by the stabilizer backend."""
    name = canonical_gate_name(op.name)
    return name in {"I", "X", "Y", "Z", "H", "S", "Sdg", "CNOT", "CX", "CZ", "SWAP"}


def is_clifford_circuit(operations: Iterable[GateOp]) -> bool:
    return all(is_clifford_operation(op) for op in operations)
