"""Gate definitions and matrix helpers.

Sansqrit uses pure Python complex numbers and little-endian qubit indexing.
The functions in this module deliberately mirror the Rust Sansqrit gate names
where possible while adding common library names from OpenQASM/Qiskit/Cirq.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, sin, sqrt, pi
from cmath import exp
from typing import Iterable, Sequence

FRAC_1_SQRT2 = 1 / sqrt(2)

STATIC_SINGLE_GATES = {
    "I", "X", "Y", "Z", "H", "S", "Sdg", "T", "Tdg", "SX", "SXdg"
}
SINGLE_GATES = STATIC_SINGLE_GATES | {"Rx", "Ry", "Rz", "Phase", "U1", "U2", "U3"}
TWO_GATES = {
    "CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "iSWAP", "ISWAP",
    "SqrtSWAP", "fSWAP", "FSWAP", "DCX", "CRx", "CRy", "CRz", "CP", "CU",
    "RXX", "RYY", "RZZ", "RZX", "ECR", "MS"
}
THREE_GATES = {"Toffoli", "CCX", "Fredkin", "CSWAP", "CCZ"}
MULTI_GATES = {"MCX", "MCZ", "C3X", "C4X"}
ALL_GATES = SINGLE_GATES | TWO_GATES | THREE_GATES | MULTI_GATES

ALIASES = {
    "CX": "CNOT",
    "ISWAP": "iSWAP",
    "FSWAP": "fSWAP",
    "CCX": "Toffoli",
    "CSWAP": "Fredkin",
    "U": "U3",
    "P": "Phase",
}

@dataclass(frozen=True)
class GateOp:
    """An operation in a circuit or engine history."""
    name: str
    qubits: tuple[int, ...]
    params: tuple[float, ...] = field(default_factory=tuple)

    def canonical(self) -> "GateOp":
        return GateOp(canonical_gate_name(self.name), self.qubits, self.params)

    def __repr__(self) -> str:
        args = ", ".join(str(q) for q in self.qubits)
        if self.params:
            args = args + "; " + ", ".join(f"{p:g}" for p in self.params)
        return f"{self.name}({args})"


def canonical_gate_name(name: str) -> str:
    return ALIASES.get(name, name)


def cis(theta: float) -> complex:
    return exp(1j * theta)


def matrix_2x2(name: str, params: Sequence[float] = ()) -> tuple[complex, complex, complex, complex]:
    """Return a single-qubit unitary as (m00, m01, m10, m11)."""
    name = canonical_gate_name(name)
    if name == "I":
        return 1+0j, 0j, 0j, 1+0j
    if name == "X":
        return 0j, 1+0j, 1+0j, 0j
    if name == "Y":
        return 0j, -1j, 1j, 0j
    if name == "Z":
        return 1+0j, 0j, 0j, -1+0j
    if name == "H":
        h = FRAC_1_SQRT2
        return h+0j, h+0j, h+0j, -h+0j
    if name == "S":
        return 1+0j, 0j, 0j, 1j
    if name == "Sdg":
        return 1+0j, 0j, 0j, -1j
    if name == "T":
        return 1+0j, 0j, 0j, cis(pi/4)
    if name == "Tdg":
        return 1+0j, 0j, 0j, cis(-pi/4)
    if name == "SX":
        return 0.5+0.5j, 0.5-0.5j, 0.5-0.5j, 0.5+0.5j
    if name == "SXdg":
        return 0.5-0.5j, 0.5+0.5j, 0.5+0.5j, 0.5-0.5j
    if name == "Rx":
        theta = params[0]
        return cos(theta/2)+0j, -1j*sin(theta/2), -1j*sin(theta/2), cos(theta/2)+0j
    if name == "Ry":
        theta = params[0]
        return cos(theta/2)+0j, -sin(theta/2)+0j, sin(theta/2)+0j, cos(theta/2)+0j
    if name == "Rz":
        theta = params[0]
        return cis(-theta/2), 0j, 0j, cis(theta/2)
    if name in {"Phase", "U1"}:
        theta = params[0]
        return 1+0j, 0j, 0j, cis(theta)
    if name == "U2":
        phi, lam = params[0], params[1]
        h = FRAC_1_SQRT2
        return h+0j, -cis(lam)*h, cis(phi)*h, cis(phi+lam)*h
    if name == "U3":
        theta, phi, lam = params[0], params[1], params[2]
        return cos(theta/2)+0j, -cis(lam)*sin(theta/2), cis(phi)*sin(theta/2), cis(phi+lam)*cos(theta/2)
    raise ValueError(f"not a single-qubit gate: {name}")


def controlled_matrix(single: tuple[complex, complex, complex, complex]) -> list[list[complex]]:
    """Controlled-U matrix with qubit order |control,target>."""
    m00, m01, m10, m11 = single
    return [
        [1+0j, 0j, 0j, 0j],
        [0j, 1+0j, 0j, 0j],
        [0j, 0j, m00, m01],
        [0j, 0j, m10, m11],
    ]


def matrix_4x4(name: str, params: Sequence[float] = ()) -> list[list[complex]]:
    """Return a two-qubit unitary in basis |q0 q1> = 00,01,10,11."""
    name = canonical_gate_name(name)
    z = 0j
    one = 1+0j
    if name == "CNOT":
        return [[one,z,z,z],[z,one,z,z],[z,z,z,one],[z,z,one,z]]
    if name == "CZ":
        return [[one,z,z,z],[z,one,z,z],[z,z,one,z],[z,z,z,-one]]
    if name == "CY":
        return [[one,z,z,z],[z,one,z,z],[z,z,z,-1j],[z,z,1j,z]]
    if name == "CH":
        return controlled_matrix(matrix_2x2("H"))
    if name == "CSX":
        return controlled_matrix(matrix_2x2("SX"))
    if name == "SWAP":
        return [[one,z,z,z],[z,z,one,z],[z,one,z,z],[z,z,z,one]]
    if name == "iSWAP":
        return [[one,z,z,z],[z,z,1j,z],[z,1j,z,z],[z,z,z,one]]
    if name == "SqrtSWAP":
        a = 0.5 + 0.5j
        b = 0.5 - 0.5j
        return [[one,z,z,z],[z,a,b,z],[z,b,a,z],[z,z,z,one]]
    if name == "fSWAP":
        return [[one,z,z,z],[z,z,one,z],[z,one,z,z],[z,z,z,-one]]
    if name == "DCX":
        # CNOT(q0,q1) followed by CNOT(q1,q0)
        return [[one,z,z,z],[z,z,z,one],[z,z,one,z],[z,one,z,z]]
    if name == "CRx":
        return controlled_matrix(matrix_2x2("Rx", params))
    if name == "CRy":
        return controlled_matrix(matrix_2x2("Ry", params))
    if name == "CRz":
        return controlled_matrix(matrix_2x2("Rz", params))
    if name == "CP":
        return controlled_matrix(matrix_2x2("Phase", params))
    if name == "CU":
        return controlled_matrix(matrix_2x2("U3", params))
    if name == "RXX":
        theta = params[0]
        c = cos(theta/2)+0j
        s = -1j*sin(theta/2)
        return [[c,z,z,s],[z,c,s,z],[z,s,c,z],[s,z,z,c]]
    if name == "RYY":
        theta = params[0]
        c = cos(theta/2)+0j
        # YY maps |00> -> -|11>, |01> -> |10>, |10> -> |01>, |11> -> -|00>
        a = 1j*sin(theta/2)
        b = -1j*sin(theta/2)
        return [[c,z,z,a],[z,c,b,z],[z,b,c,z],[a,z,z,c]]
    if name == "RZZ":
        theta = params[0]
        return [[cis(-theta/2),z,z,z],[z,cis(theta/2),z,z],[z,z,cis(theta/2),z],[z,z,z,cis(-theta/2)]]
    if name == "RZX":
        theta = params[0]
        c = cos(theta/2)+0j
        s = -1j*sin(theta/2)
        # exp(-i theta/2 Z⊗X)
        return [[c,s,z,z],[s,c,z,z],[z,z,c,-s],[z,z,-s,c]]
    if name == "ECR":
        h = FRAC_1_SQRT2
        return [[z,h*1j,z,h],[h*1j,z,h,z],[z,h,z,h*1j],[h,z,h*1j,z]]
    if name == "MS":
        return matrix_4x4("RXX", (pi/2,))
    raise ValueError(f"not a two-qubit gate: {name}")


def validate_gate_arity(name: str, qubits: Sequence[int], params: Sequence[float]) -> None:
    name = canonical_gate_name(name)
    if name in SINGLE_GATES and len(qubits) != 1:
        raise ValueError(f"{name} expects 1 qubit")
    if name in TWO_GATES and len(qubits) != 2:
        raise ValueError(f"{name} expects 2 qubits")
    if name in THREE_GATES and len(qubits) != 3:
        raise ValueError(f"{name} expects 3 qubits")
    if name == "MCX" and len(qubits) < 2:
        raise ValueError("MCX expects one or more controls plus a target")
    if name == "MCZ" and len(qubits) < 2:
        raise ValueError("MCZ expects two or more qubits")
    if name == "C3X" and len(qubits) != 4:
        raise ValueError("C3X expects 4 qubits")
    if name == "C4X" and len(qubits) != 5:
        raise ValueError("C4X expects 5 qubits")
    param_counts = {
        "Rx": 1, "Ry": 1, "Rz": 1, "Phase": 1, "U1": 1, "U2": 2, "U3": 3,
        "CRx": 1, "CRy": 1, "CRz": 1, "CP": 1, "CU": 3,
        "RXX": 1, "RYY": 1, "RZZ": 1, "RZX": 1,
    }
    need = param_counts.get(name, 0)
    if len(params) != need:
        raise ValueError(f"{name} expects {need} parameter(s), got {len(params)}")


def gate_to_qasm2(name: str, qubits: Sequence[int], params: Sequence[float] = ()) -> str:
    """Export one operation to OpenQASM 2-ish qelib1 syntax."""
    name = canonical_gate_name(name)
    qs = [f"q[{q}]" for q in qubits]
    lower = {
        "I": "id", "X": "x", "Y": "y", "Z": "z", "H": "h", "S": "s", "Sdg": "sdg",
        "T": "t", "Tdg": "tdg", "SX": "sx", "SXdg": "sxdg", "CNOT": "cx", "CZ": "cz",
        "CY": "cy", "CH": "ch", "SWAP": "swap", "Toffoli": "ccx", "CCZ": "ccz",
    }.get(name)
    if lower:
        return f"{lower} " + ", ".join(qs) + ";"
    param_map = {
        "Rx": "rx", "Ry": "ry", "Rz": "rz", "Phase": "p", "U1": "u1", "U2": "u2", "U3": "u3",
        "CRx": "crx", "CRy": "cry", "CRz": "crz", "CP": "cp", "RXX": "rxx", "RYY": "ryy", "RZZ": "rzz",
    }
    if name in param_map:
        ps = ",".join(f"{p:.17g}" for p in params)
        return f"{param_map[name]}({ps}) " + ", ".join(qs) + ";"
    return "// unsupported export: " + f"{name}({', '.join(qs)})"


def flatten_qubits(args: Iterable[object]) -> tuple[int, ...]:
    from .types import qubit_index
    return tuple(qubit_index(a) for a in args)
