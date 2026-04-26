"""OpenQASM exporters."""
from __future__ import annotations

from typing import Iterable

from .gates import GateOp, gate_to_qasm2, canonical_gate_name


def export_qasm2(ops: Iterable[GateOp], n_qubits: int, *, include_measure: bool = False) -> str:
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n_qubits}];",
    ]
    if include_measure:
        lines.append(f"creg c[{n_qubits}];")
    for op in ops:
        lines.append(gate_to_qasm2(op.name, op.qubits, op.params))
    if include_measure:
        for i in range(n_qubits):
            lines.append(f"measure q[{i}] -> c[{i}];")
    return "\n".join(lines) + "\n"


def export_qasm3(ops: Iterable[GateOp], n_qubits: int, *, include_measure: bool = False) -> str:
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{n_qubits}] q;",
    ]
    if include_measure:
        lines.append(f"bit[{n_qubits}] c;")
    for op in ops:
        name = canonical_gate_name(op.name)
        gate_name = {
            "I": "id", "X": "x", "Y": "y", "Z": "z", "H": "h", "S": "s", "Sdg": "sdg",
            "T": "t", "Tdg": "tdg", "SX": "sx", "SXdg": "sxdg", "CNOT": "cx", "CZ": "cz",
            "CY": "cy", "CH": "ch", "SWAP": "swap", "Toffoli": "ccx", "CCZ": "ccz",
            "Rx": "rx", "Ry": "ry", "Rz": "rz", "Phase": "p", "U1": "p", "U2": "u2",
            "U3": "u3", "CRx": "crx", "CRy": "cry", "CRz": "crz", "CP": "cp",
            "RXX": "rxx", "RYY": "ryy", "RZZ": "rzz",
        }.get(name)
        qs = ", ".join(f"q[{q}]" for q in op.qubits)
        if gate_name is None:
            lines.append(f"// unsupported export: {name} {qs};")
        elif op.params:
            ps = ", ".join(f"{p:.17g}" for p in op.params)
            lines.append(f"{gate_name}({ps}) {qs};")
        else:
            lines.append(f"{gate_name} {qs};")
    if include_measure:
        for i in range(n_qubits):
            lines.append(f"c[{i}] = measure q[{i}];")
    return "\n".join(lines) + "\n"
