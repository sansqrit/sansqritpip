"""Matrix Product State backend for low-entanglement circuits.

The MPS backend uses NumPy and truncating SVD. It is intended for circuits where
entanglement entropy stays modest. It can address many qubits, but large bond
sizes still grow exponentially for highly entangled circuits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Sequence

from .errors import QuantumError
from .gates import GateOp, SINGLE_GATES, TWO_GATES, canonical_gate_name, matrix_2x2, matrix_4x4, validate_gate_arity
from .types import QuantumRegister, QubitRef, qubit_index

try:  # optional dependency
    import numpy as np
except Exception:  # pragma: no cover - exercised when numpy absent
    np = None  # type: ignore


def _need_numpy():
    if np is None:
        raise QuantumError("MPS backend requires NumPy. Install with: pip install sansqrit[tensor]")


def _as_np2(matrix: tuple[complex, complex, complex, complex]):
    return np.array([[matrix[0], matrix[1]], [matrix[2], matrix[3]]], dtype=np.complex128)


def _as_np4(matrix: list[list[complex]]):
    return np.array(matrix, dtype=np.complex128).reshape(2, 2, 2, 2)


@dataclass
class MPSEngine:
    """Tensor-network/MPS simulator with SVD truncation."""
    n_qubits: int
    max_bond_dim: int | None = 128
    cutoff: float = 1e-12
    seed: int | None = None
    tensors: list = field(init=False)
    history: list[GateOp] = field(default_factory=list)

    def __post_init__(self) -> None:
        _need_numpy()
        if self.n_qubits <= 0:
            raise QuantumError("MPSEngine requires at least one qubit")
        self.rng = Random(self.seed)
        self.tensors = []
        for _ in range(self.n_qubits):
            t = np.zeros((1, 2, 1), dtype=np.complex128)
            t[0, 0, 0] = 1.0
            self.tensors.append(t)

    @property
    def nnz(self) -> int:
        return -1

    @property
    def max_current_bond(self) -> int:
        return max((t.shape[2] for t in self.tensors[:-1]), default=1)

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def ensure_qubits(self, qs: Sequence[int]) -> None:
        for q in qs:
            if q < 0 or q >= self.n_qubits:
                raise QuantumError(f"qubit index {q} out of range for {self.n_qubits} qubits")
        if len(set(qs)) != len(tuple(qs)):
            raise QuantumError(f"gate qubits must be distinct, got {qs}")

    def _apply_single_matrix(self, q: int, matrix: tuple[complex, complex, complex, complex]) -> None:
        self.ensure_qubits((q,))
        u = _as_np2(matrix)
        a = self.tensors[q]
        # new[l,p_out,r] = sum_p_in U[p_out,p_in] * A[l,p_in,r]
        self.tensors[q] = np.einsum("op,lpr->lor", u, a, optimize=True)

    def _apply_adjacent_matrix(self, left: int, matrix: list[list[complex]]) -> None:
        self.ensure_qubits((left, left + 1))
        a = self.tensors[left]
        b = self.tensors[left + 1]
        theta = np.einsum("lpm,mqr->lpqr", a, b, optimize=True)
        u = _as_np4(matrix)
        theta = np.einsum("abpq,lpqr->labr", u, theta, optimize=True)
        ldim, _, _, rdim = theta.shape
        mat = theta.reshape(ldim * 2, 2 * rdim)
        U, S, Vh = np.linalg.svd(mat, full_matrices=False)
        keep = len(S)
        if self.cutoff > 0:
            keep = int(np.sum(S > self.cutoff)) or 1
        if self.max_bond_dim is not None:
            keep = min(keep, int(self.max_bond_dim))
        U = U[:, :keep]
        S = S[:keep]
        Vh = Vh[:keep, :]
        self.tensors[left] = U.reshape(ldim, 2, keep)
        self.tensors[left + 1] = (np.diag(S) @ Vh).reshape(keep, 2, rdim)

    def _swap_adjacent(self, left: int) -> None:
        self._apply_adjacent_matrix(left, matrix_4x4("SWAP"))

    def _apply_two_matrix(self, q0: int, q1: int, matrix: list[list[complex]]) -> None:
        self.ensure_qubits((q0, q1))
        if abs(q0 - q1) == 1:
            if q0 < q1:
                self._apply_adjacent_matrix(q0, matrix)
            else:
                swap = matrix_4x4("SWAP")
                # Transform matrix from order (q0,q1) to site order (q1,q0).
                m = np.array(swap, dtype=np.complex128) @ np.array(matrix, dtype=np.complex128) @ np.array(swap, dtype=np.complex128)
                self._apply_adjacent_matrix(q1, m.tolist())
            return
        # Bring q1 next to q0 with SWAP network, apply, then uncompute the swaps.
        if q0 < q1:
            for pos in range(q1 - 1, q0, -1):
                self._swap_adjacent(pos)
            self._apply_adjacent_matrix(q0, matrix)
            for pos in range(q0 + 1, q1):
                self._swap_adjacent(pos)
        else:
            for pos in range(q1, q0 - 1):
                self._swap_adjacent(pos)
            self._apply_two_matrix(q0, q1 + 1, matrix)
            for pos in range(q0 - 1, q1 - 1, -1):
                self._swap_adjacent(pos)

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        if name in SINGLE_GATES:
            self._apply_single_matrix(qidx[0], matrix_2x2(name, params))
        elif name in TWO_GATES:
            self._apply_two_matrix(qidx[0], qidx[1], matrix_4x4(name, params))
        else:
            raise QuantumError(f"MPS backend currently supports one- and two-qubit gates, got {name}")
        self.history.append(GateOp(name, qidx, params))

    def _norm_with_projection(self, assignments: dict[int, int] | None = None) -> float:
        assignments = assignments or {}
        env = np.array([[1.0 + 0j]], dtype=np.complex128)
        for site, a in enumerate(self.tensors):
            allowed = [assignments[site]] if site in assignments else [0, 1]
            new = np.zeros((a.shape[2], a.shape[2]), dtype=np.complex128)
            for p in allowed:
                ap = a[:, p, :]
                new += ap.conj().T @ env @ ap
            env = new
        return max(0.0, float(env[0, 0].real))

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        if shots <= 0:
            raise QuantumError("shots must be positive")
        counts: dict[str, int] = {}
        for _ in range(shots):
            assign: dict[int, int] = {}
            base_norm = 1.0
            for q in range(self.n_qubits):
                p0 = self._norm_with_projection({**assign, q: 0}) / max(base_norm, 1e-300)
                bit = 0 if self.rng.random() < p0 else 1
                assign[q] = bit
                base_norm *= p0 if bit == 0 else (1 - p0)
                base_norm = max(base_norm, 1e-300)
            key = "".join(str(assign[q]) for q in reversed(range(self.n_qubits)))
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def probabilities(self) -> dict[str, float]:
        if self.n_qubits > 20:
            raise QuantumError("probabilities() on MPS backend is limited to <=20 qubits; use measure_all(shots)")
        out = {}
        for basis in range(1 << self.n_qubits):
            assign = {q: (basis >> q) & 1 for q in range(self.n_qubits)}
            p = self._norm_with_projection(assign)
            if p > self.cutoff:
                out[format(basis, f"0{self.n_qubits}b")] = p
        return dict(sorted(out.items()))


    def H_all(self, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.H(q)

    def qft(self, qubits=None, *, swaps: bool = True):
        from math import pi
        qs = list(qubits) if qubits is not None else list(range(self.n_qubits))
        n = len(qs)
        for j in range(n):
            self.H(qs[j])
            for k in range(j + 1, n):
                self.apply("CP", qs[k], qs[j], params=(pi / (2 ** (k - j)),))
        if swaps:
            for i in range(n // 2):
                self.SWAP(qs[i], qs[n - i - 1])

    def iqft(self, qubits=None, *, swaps: bool = True):
        from math import pi
        qs = list(qubits) if qubits is not None else list(range(self.n_qubits))
        n = len(qs)
        if swaps:
            for i in range(n // 2):
                self.SWAP(qs[i], qs[n - i - 1])
        for j in reversed(range(n)):
            for k in reversed(range(j + 1, n)):
                self.apply("CP", qs[k], qs[j], params=(-pi / (2 ** (k - j)),))
            self.H(qs[j])

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)

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
    def SWAP(self, a, b): self.apply("SWAP", a, b)
