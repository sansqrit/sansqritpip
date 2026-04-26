"""Optional interoperability with Qiskit, Cirq, Braket and PennyLane."""
from __future__ import annotations

from typing import Iterable

from .errors import QuantumError
from .gates import GateOp, canonical_gate_name


def _ops(circuit_or_ops) -> tuple[int | None, list[GateOp]]:
    if hasattr(circuit_or_ops, "operations"):
        return getattr(circuit_or_ops, "n_qubits", None), list(circuit_or_ops.operations)
    return None, list(circuit_or_ops)


def to_qiskit(circuit):
    """Convert a Sansqrit Circuit to qiskit.QuantumCircuit if qiskit is installed."""
    n, ops = _ops(circuit)
    if n is None:
        raise QuantumError("to_qiskit expects a Sansqrit Circuit with n_qubits")
    try:
        from qiskit import QuantumCircuit
    except Exception as exc:
        raise QuantumError("Qiskit is not installed. Install with: pip install sansqrit[qiskit]") from exc
    qc = QuantumCircuit(n)
    for op in ops:
        name = canonical_gate_name(op.name)
        q = op.qubits; p = op.params
        if name == "I": qc.id(q[0])
        elif name == "H": qc.h(q[0])
        elif name == "X": qc.x(q[0])
        elif name == "Y": qc.y(q[0])
        elif name == "Z": qc.z(q[0])
        elif name == "S": qc.s(q[0])
        elif name == "Sdg": qc.sdg(q[0])
        elif name == "T": qc.t(q[0])
        elif name == "Tdg": qc.tdg(q[0])
        elif name == "SX": qc.sx(q[0])
        elif name == "SXdg": qc.sxdg(q[0])
        elif name == "Rx": qc.rx(p[0], q[0])
        elif name == "Ry": qc.ry(p[0], q[0])
        elif name == "Rz": qc.rz(p[0], q[0])
        elif name == "Phase": qc.p(p[0], q[0])
        elif name == "U3": qc.u(p[0], p[1], p[2], q[0])
        elif name == "CNOT": qc.cx(q[0], q[1])
        elif name == "CZ": qc.cz(q[0], q[1])
        elif name == "CY": qc.cy(q[0], q[1])
        elif name == "CH": qc.ch(q[0], q[1])
        elif name == "SWAP": qc.swap(q[0], q[1])
        elif name == "RXX": qc.rxx(p[0], q[0], q[1])
        elif name == "RYY": qc.ryy(p[0], q[0], q[1])
        elif name == "RZZ": qc.rzz(p[0], q[0], q[1])
        elif name == "Toffoli": qc.ccx(q[0], q[1], q[2])
        elif name == "Fredkin": qc.cswap(q[0], q[1], q[2])
        else: raise QuantumError(f"Qiskit exporter does not support {name}")
    return qc


def to_cirq(circuit):
    """Convert a Sansqrit Circuit to cirq.Circuit if Cirq is installed."""
    n, ops = _ops(circuit)
    if n is None:
        raise QuantumError("to_cirq expects a Sansqrit Circuit with n_qubits")
    try:
        import cirq
    except Exception as exc:
        raise QuantumError("Cirq is not installed. Install with: pip install sansqrit[cirq]") from exc
    qs = cirq.LineQubit.range(n)
    out = cirq.Circuit()
    for op in ops:
        name = canonical_gate_name(op.name); q = op.qubits; p = op.params
        if name == "H": out.append(cirq.H(qs[q[0]]))
        elif name == "X": out.append(cirq.X(qs[q[0]]))
        elif name == "Y": out.append(cirq.Y(qs[q[0]]))
        elif name == "Z": out.append(cirq.Z(qs[q[0]]))
        elif name == "S": out.append(cirq.S(qs[q[0]]))
        elif name == "T": out.append(cirq.T(qs[q[0]]))
        elif name == "Rx": out.append(cirq.rx(p[0])(qs[q[0]]))
        elif name == "Ry": out.append(cirq.ry(p[0])(qs[q[0]]))
        elif name == "Rz": out.append(cirq.rz(p[0])(qs[q[0]]))
        elif name == "CNOT": out.append(cirq.CNOT(qs[q[0]], qs[q[1]]))
        elif name == "CZ": out.append(cirq.CZ(qs[q[0]], qs[q[1]]))
        elif name == "SWAP": out.append(cirq.SWAP(qs[q[0]], qs[q[1]]))
        else: raise QuantumError(f"Cirq exporter does not support {name}")
    return out


def to_braket(circuit):
    """Convert a Sansqrit Circuit to braket.circuits.Circuit if the Braket SDK is installed."""
    _, ops = _ops(circuit)
    try:
        from braket.circuits import Circuit
    except Exception as exc:
        raise QuantumError("Amazon Braket SDK is not installed. Install with: pip install sansqrit[braket]") from exc
    out = Circuit()
    for op in ops:
        name = canonical_gate_name(op.name); q = op.qubits; p = op.params
        if name == "H": out.h(q[0])
        elif name == "X": out.x(q[0])
        elif name == "Y": out.y(q[0])
        elif name == "Z": out.z(q[0])
        elif name == "S": out.s(q[0])
        elif name == "T": out.t(q[0])
        elif name == "Rx": out.rx(q[0], p[0])
        elif name == "Ry": out.ry(q[0], p[0])
        elif name == "Rz": out.rz(q[0], p[0])
        elif name == "CNOT": out.cnot(q[0], q[1])
        elif name == "CZ": out.cz(q[0], q[1])
        elif name == "SWAP": out.swap(q[0], q[1])
        else: raise QuantumError(f"Braket exporter does not support {name}")
    return out


def apply_to_pennylane(circuit):
    """Return a callable quantum function that applies a Sansqrit Circuit in PennyLane."""
    n, ops = _ops(circuit)
    try:
        import pennylane as qml
    except Exception as exc:
        raise QuantumError("PennyLane is not installed. Install with: pip install sansqrit[pennylane]") from exc
    def qfunc():
        for op in ops:
            name = canonical_gate_name(op.name); q = op.qubits; p = op.params
            if name == "H": qml.Hadamard(wires=q[0])
            elif name == "X": qml.PauliX(wires=q[0])
            elif name == "Y": qml.PauliY(wires=q[0])
            elif name == "Z": qml.PauliZ(wires=q[0])
            elif name == "S": qml.S(wires=q[0])
            elif name == "T": qml.T(wires=q[0])
            elif name == "Rx": qml.RX(p[0], wires=q[0])
            elif name == "Ry": qml.RY(p[0], wires=q[0])
            elif name == "Rz": qml.RZ(p[0], wires=q[0])
            elif name == "CNOT": qml.CNOT(wires=[q[0], q[1]])
            elif name == "CZ": qml.CZ(wires=[q[0], q[1]])
            elif name == "SWAP": qml.SWAP(wires=[q[0], q[1]])
            else: raise QuantumError(f"PennyLane exporter does not support {name}")
    return qfunc
