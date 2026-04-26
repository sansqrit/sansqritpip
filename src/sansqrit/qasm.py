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

# ---------------------------------------------------------------------------
# OpenQASM 3 advanced program builder
# ---------------------------------------------------------------------------
class Qasm3Builder:
    """Small OpenQASM 3 builder for classical control, delays, barriers and pragmas.

    It is intentionally text-first so generated payloads can be sent to providers
    that accept OpenQASM 3 strings while still being readable by AI/ML tools.
    """
    def __init__(self, n_qubits: int, n_bits: int | None = None, *, include_std: bool = True):
        self.n_qubits = int(n_qubits)
        self.n_bits = int(n_bits if n_bits is not None else n_qubits)
        self.lines = ["OPENQASM 3.0;"]
        if include_std:
            self.lines.append('include "stdgates.inc";')
        self.lines.append(f"qubit[{self.n_qubits}] q;")
        self.lines.append(f"bit[{self.n_bits}] c;")

    def gate(self, name: str, qubits: Iterable[int], params: Iterable[float] = ()) -> "Qasm3Builder":
        qs = ", ".join(f"q[{int(q)}]" for q in qubits)
        params = tuple(params)
        if params:
            ps = ", ".join(f"{float(p):.17g}" for p in params)
            self.lines.append(f"{name}({ps}) {qs};")
        else:
            self.lines.append(f"{name} {qs};")
        return self

    def measure(self, qubit: int, bit: int) -> "Qasm3Builder":
        self.lines.append(f"c[{int(bit)}] = measure q[{int(qubit)}];")
        return self

    def reset(self, qubit: int) -> "Qasm3Builder":
        self.lines.append(f"reset q[{int(qubit)}];")
        return self

    def if_bit(self, bit: int, value: int, body: str) -> "Qasm3Builder":
        body_lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
        self.lines.append(f"if (c[{int(bit)}] == {int(value)}) {{")
        for ln in body_lines:
            self.lines.append("  " + ln)
        self.lines.append("}")
        return self

    def delay(self, duration: str, qubits: Iterable[int] | None = None) -> "Qasm3Builder":
        if qubits is None:
            target = "q"
        else:
            target = ", ".join(f"q[{int(q)}]" for q in qubits)
        self.lines.append(f"delay[{duration}] {target};")
        return self

    def barrier(self, qubits: Iterable[int] | None = None) -> "Qasm3Builder":
        target = "q" if qubits is None else ", ".join(f"q[{int(q)}]" for q in qubits)
        self.lines.append(f"barrier {target};")
        return self

    def pragma(self, text: str) -> "Qasm3Builder":
        self.lines.append(f"#pragma {text}")
        return self

    def extern(self, signature: str) -> "Qasm3Builder":
        self.lines.append(f"extern {signature};")
        return self

    def cal_block(self, body: str) -> "Qasm3Builder":
        self.lines.append("cal {")
        for ln in body.splitlines():
            self.lines.append("  " + ln.rstrip())
        self.lines.append("}")
        return self

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"


def export_qasm3_advanced(ops: Iterable[GateOp], n_qubits: int, *, include_measure: bool = False,
                          delays: list[tuple[str, tuple[int, ...]]] | None = None,
                          pragmas: list[str] | None = None,
                          classical_controls: list[tuple[int, int, str]] | None = None) -> str:
    b = Qasm3Builder(n_qubits, n_qubits)
    for p in pragmas or []:
        b.pragma(p)
    for op in ops:
        name = canonical_gate_name(op.name)
        gate_name = {"CNOT": "cx", "Rx": "rx", "Ry": "ry", "Rz": "rz", "Phase": "p", "Toffoli": "ccx"}.get(name, name.lower())
        b.gate(gate_name, op.qubits, op.params)
    for duration, qs in delays or []:
        b.delay(duration, qs)
    for bit, value, body in classical_controls or []:
        b.if_bit(bit, value, body)
    if include_measure:
        for i in range(n_qubits):
            b.measure(i, i)
    return b.text()


def qasm3_mid_circuit_template(n_qubits: int = 2) -> str:
    b = Qasm3Builder(n_qubits, n_qubits)
    b.gate("h", [0]).measure(0, 0).if_bit(0, 1, "x q[1];").barrier().delay("100ns", [1]).measure(1, 1)
    return b.text()
