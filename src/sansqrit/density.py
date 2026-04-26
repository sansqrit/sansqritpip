"""Sparse density-matrix simulator and noise channels."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from random import Random
from typing import Sequence

from .errors import QuantumError
from .gates import GateOp, SINGLE_GATES, TWO_GATES, canonical_gate_name, matrix_2x2, matrix_4x4, validate_gate_arity
from .sparse import conventional_bitstring
from .types import QuantumRegister, QubitRef, qubit_index


def _prune(target: dict[tuple[int, int], complex], key: tuple[int, int], value: complex, eps: float) -> None:
    if abs(value) <= eps:
        return
    old = target.get(key, 0j) + value
    if abs(old) <= eps:
        target.pop(key, None)
    else:
        target[key] = old


def _single_images(state: int, q: int, m: tuple[complex, complex, complex, complex], eps: float) -> list[tuple[int, complex]]:
    m00, m01, m10, m11 = m
    bit = (state >> q) & 1
    partner = state ^ (1 << q)
    if bit == 0:
        return [(state, m00), (partner, m10)]
    return [(partner, m01), (state, m11)]


def _two_images(state: int, q0: int, q1: int, mat: list[list[complex]], eps: float) -> list[tuple[int, complex]]:
    b0 = (state >> q0) & 1
    b1 = (state >> q1) & 1
    col = (b0 << 1) | b1
    base = state & ~(1 << q0) & ~(1 << q1)
    out = []
    for row in range(4):
        amp = mat[row][col]
        if abs(amp) > eps:
            nb0 = (row >> 1) & 1
            nb1 = row & 1
            out.append((base | (nb0 << q0) | (nb1 << q1), amp))
    return out


@dataclass
class DensityMatrixEngine:
    """Sparse density matrix backend for small noisy simulations."""
    n_qubits: int
    seed: int | None = None
    eps: float = 1e-14
    rho: dict[tuple[int, int], complex] = field(default_factory=dict)
    history: list[GateOp] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.n_qubits <= 0:
            raise QuantumError("DensityMatrixEngine requires at least one qubit")
        if not self.rho:
            self.rho = {(0, 0): 1+0j}
        self.rng = Random(self.seed)

    @property
    def nnz(self) -> int:
        return len(self.rho)

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def ensure_qubits(self, qs: Sequence[int]) -> None:
        for q in qs:
            if q < 0 or q >= self.n_qubits:
                raise QuantumError(f"qubit index {q} out of range for {self.n_qubits} qubits")
        if len(set(qs)) != len(tuple(qs)):
            raise QuantumError(f"gate qubits must be distinct, got {qs}")

    def _apply_images(self, ket_images, bra_images) -> None:
        out: dict[tuple[int, int], complex] = {}
        for (ket, bra), value in self.rho.items():
            for nk, ck in ket_images(ket):
                for nb, cb in bra_images(bra):
                    _prune(out, (nk, nb), ck * value * cb.conjugate(), self.eps)
        self.rho = out

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        self.ensure_qubits(qidx)
        if name in SINGLE_GATES:
            mat = matrix_2x2(name, params)
            q = qidx[0]
            self._apply_images(lambda s: _single_images(s, q, mat, self.eps), lambda s: _single_images(s, q, mat, self.eps))
        elif name in TWO_GATES:
            mat = matrix_4x4(name, params)
            q0, q1 = qidx
            self._apply_images(lambda s: _two_images(s, q0, q1, mat, self.eps), lambda s: _two_images(s, q0, q1, mat, self.eps))
        else:
            raise QuantumError(f"density backend currently supports one- and two-qubit gates, got {name}")
        self.history.append(GateOp(name, qidx, params))

    def apply_kraus(self, q: int | QubitRef, kraus: Sequence[tuple[complex, complex, complex, complex]], label: str = "kraus") -> None:
        q = qubit_index(q)
        self.ensure_qubits((q,))
        out: dict[tuple[int, int], complex] = {}
        for k in kraus:
            for (ket, bra), value in self.rho.items():
                for nk, ck in _single_images(ket, q, k, self.eps):
                    for nb, cb in _single_images(bra, q, k, self.eps):
                        _prune(out, (nk, nb), ck * value * cb.conjugate(), self.eps)
        self.rho = out
        self.history.append(GateOp(label, (q,), ()))

    def bit_flip(self, q: int | QubitRef, p: float) -> None:
        self._validate_probability(p)
        self.apply_kraus(q, ((sqrt(1-p),0j,0j,sqrt(1-p)), (0j,sqrt(p),sqrt(p),0j)), "bit_flip")

    def phase_flip(self, q: int | QubitRef, p: float) -> None:
        self._validate_probability(p)
        self.apply_kraus(q, ((sqrt(1-p),0j,0j,sqrt(1-p)), (sqrt(p),0j,0j,-sqrt(p))), "phase_flip")

    def amplitude_damping(self, q: int | QubitRef, gamma: float) -> None:
        self._validate_probability(gamma)
        self.apply_kraus(q, ((1+0j,0j,0j,sqrt(1-gamma)), (0j,sqrt(gamma),0j,0j)), "amplitude_damping")

    def depolarize(self, q: int | QubitRef, p: float) -> None:
        self._validate_probability(p)
        s0 = sqrt(1-p)
        sp = sqrt(p/3)
        self.apply_kraus(q, ((s0,0j,0j,s0), (0j,sp,sp,0j), (0j,-1j*sp,1j*sp,0j), (sp,0j,0j,-sp)), "depolarize")

    def _validate_probability(self, p: float) -> None:
        if not (0.0 <= p <= 1.0):
            raise QuantumError(f"probability must be in [0,1], got {p}")

    def trace(self) -> complex:
        return sum(v for (i, j), v in self.rho.items() if i == j)

    def probabilities(self) -> dict[str, float]:
        probs = {conventional_bitstring(i, self.n_qubits): max(0.0, float(v.real))
                 for (i, j), v in self.rho.items() if i == j and abs(v) > self.eps}
        return dict(sorted(probs.items()))

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        if shots <= 0:
            raise QuantumError("shots must be positive")
        probs = self.probabilities()
        keys = list(probs)
        weights = [probs[k] for k in keys]
        total = sum(weights) or 1.0
        cum = []
        acc = 0.0
        for w in weights:
            acc += w / total
            cum.append(acc)
        counts: dict[str, int] = {}
        for _ in range(shots):
            r = self.rng.random()
            idx = 0
            while idx < len(cum)-1 and cum[idx] < r:
                idx += 1
            counts[keys[idx]] = counts.get(keys[idx], 0) + 1
        return dict(sorted(counts.items()))

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2([op for op in self.history if op.name not in {"bit_flip","phase_flip","amplitude_damping","depolarize","kraus"}], self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3([op for op in self.history if op.name not in {"bit_flip","phase_flip","amplitude_damping","depolarize","kraus"}], self.n_qubits, include_measure=include_measure)

    # Common aliases
    def H(self, q): self.apply("H", q)
    def X(self, q): self.apply("X", q)
    def Y(self, q): self.apply("Y", q)
    def Z(self, q): self.apply("Z", q)
    def S(self, q): self.apply("S", q)
    def T(self, q): self.apply("T", q)
    def Rx(self, q, theta): self.apply("Rx", q, params=(theta,))
    def Ry(self, q, theta): self.apply("Ry", q, params=(theta,))
    def Rz(self, q, theta): self.apply("Rz", q, params=(theta,))
    def CNOT(self, c, t): self.apply("CNOT", c, t)
    def CX(self, c, t): self.CNOT(c, t)
    def CZ(self, c, t): self.apply("CZ", c, t)
