"""Stabilizer tableau backend for large Clifford circuits.

This backend implements an Aaronson-Gottesman style binary tableau with Python
integer bitsets. It can track thousands of qubits for Clifford-only circuits
because memory scales roughly O(n^2 / word_size) for the tableau instead of
O(2^n) for a dense state vector.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Sequence

from .errors import QuantumError
from .gates import GateOp, canonical_gate_name, validate_gate_arity
from .types import QuantumRegister, QubitRef, qubit_index

CLIFFORD_GATES = {"I", "X", "Y", "Z", "H", "S", "Sdg", "CNOT", "CX", "CZ", "SWAP"}


def _phase_delta(x1: int, z1: int, x2: int, z2: int) -> int:
    # P(x,z)=i^(x·z) X^x Z^z. Returns delta exponent mod 4 for P1*P2.
    return ((x1 & z1).bit_count() + (x2 & z2).bit_count() +
            2 * (z1 & x2).bit_count() - ((x1 ^ x2) & (z1 ^ z2)).bit_count()) % 4


@dataclass
class StabilizerEngine:
    """Clifford-only simulator backed by a stabilizer tableau.

    Supported gates: I, X, Y, Z, H, S, Sdg, CNOT/CX, CZ and SWAP. Non-Clifford
    gates intentionally raise QuantumError instead of silently expanding the
    state. Use the hybrid backend to route non-Clifford circuits elsewhere.
    """
    n_qubits: int
    seed: int | None = None
    x: list[int] = field(init=False)
    z: list[int] = field(init=False)
    phase: list[int] = field(init=False)  # 0,1,2,3 means i^phase
    history: list[GateOp] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.n_qubits <= 0:
            raise QuantumError("StabilizerEngine requires at least one qubit")
        self.rng = Random(self.seed)
        self.x = [0] * (2 * self.n_qubits)
        self.z = [0] * (2 * self.n_qubits)
        self.phase = [0] * (2 * self.n_qubits)
        for q in range(self.n_qubits):
            self.x[q] = 1 << q          # destabilizer X_q
            self.z[self.n_qubits + q] = 1 << q  # stabilizer Z_q

    @property
    def nnz(self) -> int:
        # Stabilizer states may be dense in computational basis; avoid implying sparsity.
        return -1

    def ensure_qubit(self, q: int) -> None:
        if q < 0 or q >= self.n_qubits:
            raise QuantumError(f"qubit index {q} out of range for {self.n_qubits} qubits")

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def ensure_qubits(self, qs: Sequence[int]) -> None:
        for q in qs:
            self.ensure_qubit(q)
        if len(set(qs)) != len(tuple(qs)):
            raise QuantumError(f"gate qubits must be distinct, got {qs}")

    def _row(self, i: int) -> tuple[int, int, int]:
        return self.x[i], self.z[i], self.phase[i]

    def _set_row(self, i: int, row: tuple[int, int, int]) -> None:
        self.x[i], self.z[i], self.phase[i] = row[0], row[1], row[2] % 4

    def _multiply_rows(self, a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
        x1, z1, p1 = a
        x2, z2, p2 = b
        return x1 ^ x2, z1 ^ z2, (p1 + p2 + _phase_delta(x1, z1, x2, z2)) % 4

    def _rowmul(self, target: int, source: int) -> None:
        self._set_row(target, self._multiply_rows(self._row(target), self._row(source)))

    def _apply_h(self, q: int) -> None:
        m = 1 << q
        for i in range(2 * self.n_qubits):
            xb = 1 if self.x[i] & m else 0
            zb = 1 if self.z[i] & m else 0
            if xb and zb:
                self.phase[i] = (self.phase[i] + 2) % 4
            if xb != zb:
                self.x[i] ^= m
                self.z[i] ^= m

    def _apply_s(self, q: int) -> None:
        m = 1 << q
        for i in range(2 * self.n_qubits):
            xb = 1 if self.x[i] & m else 0
            zb = 1 if self.z[i] & m else 0
            if xb and zb:
                self.phase[i] = (self.phase[i] + 2) % 4
            if xb:
                self.z[i] ^= m

    def _apply_x(self, q: int) -> None:
        m = 1 << q
        for i in range(2 * self.n_qubits):
            if self.z[i] & m:
                self.phase[i] = (self.phase[i] + 2) % 4

    def _apply_z(self, q: int) -> None:
        m = 1 << q
        for i in range(2 * self.n_qubits):
            if self.x[i] & m:
                self.phase[i] = (self.phase[i] + 2) % 4

    def _apply_y(self, q: int) -> None:
        m = 1 << q
        for i in range(2 * self.n_qubits):
            xb = bool(self.x[i] & m)
            zb = bool(self.z[i] & m)
            if xb ^ zb:
                self.phase[i] = (self.phase[i] + 2) % 4

    def _apply_cnot(self, c: int, t: int) -> None:
        cm = 1 << c
        tm = 1 << t
        for i in range(2 * self.n_qubits):
            xc = 1 if self.x[i] & cm else 0
            zt = 1 if self.z[i] & tm else 0
            xt = 1 if self.x[i] & tm else 0
            zc = 1 if self.z[i] & cm else 0
            if xc and zt and (xt ^ zc ^ 1):
                self.phase[i] = (self.phase[i] + 2) % 4
            if xc:
                self.x[i] ^= tm
            if zt:
                self.z[i] ^= cm

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        if params:
            raise QuantumError(f"{name} is parameterized and cannot run on the stabilizer backend")
        validate_gate_arity(name, qidx, params)
        if name not in CLIFFORD_GATES:
            raise QuantumError(f"{name} is non-Clifford or unsupported by the stabilizer backend")
        self.ensure_qubits(qidx)
        if name == "I":
            pass
        elif name == "H":
            self._apply_h(qidx[0])
        elif name == "S":
            self._apply_s(qidx[0])
        elif name == "Sdg":
            self._apply_s(qidx[0]); self._apply_s(qidx[0]); self._apply_s(qidx[0])
        elif name == "X":
            self._apply_x(qidx[0])
        elif name == "Y":
            self._apply_y(qidx[0])
        elif name == "Z":
            self._apply_z(qidx[0])
        elif name == "CNOT":
            self._apply_cnot(qidx[0], qidx[1])
        elif name == "CZ":
            self._apply_h(qidx[1]); self._apply_cnot(qidx[0], qidx[1]); self._apply_h(qidx[1])
        elif name == "SWAP":
            a, b = qidx
            self._apply_cnot(a, b); self._apply_cnot(b, a); self._apply_cnot(a, b)
        self.history.append(GateOp(name, qidx, ()))

    def measure(self, q: int | QubitRef, *, collapse: bool = True) -> int:
        if not collapse:
            # A non-collapsing stabilizer measurement is a query. We implement it by
            # copying the tableau so the caller gets a nondestructive result.
            tmp = self.copy()
            return tmp.measure(q, collapse=True)
        q = qubit_index(q)
        self.ensure_qubit(q)
        m = 1 << q
        p = None
        for row in range(self.n_qubits, 2 * self.n_qubits):
            if self.x[row] & m:
                p = row
                break
        if p is not None:
            outcome = self.rng.randrange(2)
            for row in range(2 * self.n_qubits):
                if row != p and (self.x[row] & m):
                    self._rowmul(row, p)
            self.x[p - self.n_qubits] = self.x[p]
            self.z[p - self.n_qubits] = self.z[p]
            self.phase[p - self.n_qubits] = self.phase[p]
            self.x[p] = 0
            self.z[p] = m
            self.phase[p] = 2 * outcome
            return outcome
        acc = (0, 0, 0)
        for row in range(self.n_qubits):
            if self.x[row] & m:
                acc = self._multiply_rows(acc, self._row(row + self.n_qubits))
        return (acc[2] // 2) & 1

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        if shots <= 0:
            raise QuantumError("shots must be positive")
        counts: dict[str, int] = {}
        for _ in range(shots):
            tmp = self.copy()
            tmp.rng = Random(self.rng.randrange(1 << 63))
            bits = [str(tmp.measure(q)) for q in reversed(range(self.n_qubits))]
            key = "".join(bits)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def copy(self) -> "StabilizerEngine":
        out = StabilizerEngine(self.n_qubits, seed=None)
        out.x = list(self.x)
        out.z = list(self.z)
        out.phase = list(self.phase)
        out.history = list(self.history)
        out.rng.setstate(self.rng.getstate())
        return out

    def probabilities(self) -> dict[str, float]:
        # Exact enumeration is exponential; keep this safe.
        if self.n_qubits > 20:
            raise QuantumError("probabilities() on stabilizer backend is limited to <=20 qubits; use measure_all(shots)")
        shots = 4096
        counts = self.measure_all(shots)
        return {k: v / shots for k, v in counts.items()}

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)

    # Convenience methods
    def I(self, q): self.apply("I", q)
    def X(self, q): self.apply("X", q)
    def Y(self, q): self.apply("Y", q)
    def Z(self, q): self.apply("Z", q)
    def H(self, q): self.apply("H", q)
    def S(self, q): self.apply("S", q)
    def Sdg(self, q): self.apply("Sdg", q)
    def CNOT(self, c, t): self.apply("CNOT", c, t)
    def CX(self, c, t): self.CNOT(c, t)
    def CZ(self, c, t): self.apply("CZ", c, t)
    def SWAP(self, a, b): self.apply("SWAP", a, b)
    def H_all(self, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.H(q)
