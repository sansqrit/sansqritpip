"""Sparse state-vector backend for Sansqrit.

The backend stores only non-zero amplitudes in ``dict[int, complex]``. Python
integers are arbitrary precision, so qubit indexes are not limited to 64/128
bits. Practical limits are memory, runtime and state-vector growth.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from math import sqrt
from random import Random
from typing import Iterable, Sequence

from .errors import QuantumError
from .gates import matrix_2x2, matrix_4x4

DEFAULT_EPS = 1e-14


def bit_of(state: int, qubit: int) -> int:
    return (state >> qubit) & 1


def flip_bit(state: int, qubit: int) -> int:
    return state ^ (1 << qubit)


def bitstring(state: int, n_qubits: int) -> str:
    return format(state, f"0{n_qubits}b")[::-1][::-1] if n_qubits >= 0 else str(state)


def conventional_bitstring(state: int, n_qubits: int) -> str:
    return "".join("1" if bit_of(state, q) else "0" for q in reversed(range(n_qubits)))


def _prune_into(target: dict[int, complex], key: int, value: complex, eps: float) -> None:
    if abs(value) <= eps:
        return
    old = target.get(key, 0j) + value
    if abs(old) <= eps:
        target.pop(key, None)
    else:
        target[key] = old


def _apply_single_chunk(items: list[tuple[int, complex]], qubit: int, matrix: tuple[complex, complex, complex, complex], eps: float) -> dict[int, complex]:
    m00, m01, m10, m11 = matrix
    out: dict[int, complex] = {}
    for state, amp in items:
        partner = state ^ (1 << qubit)
        if ((state >> qubit) & 1) == 0:
            _prune_into(out, state, m00 * amp, eps)
            _prune_into(out, partner, m10 * amp, eps)
        else:
            _prune_into(out, partner, m01 * amp, eps)
            _prune_into(out, state, m11 * amp, eps)
    return out


def _merge_dicts(dicts: Iterable[dict[int, complex]], eps: float) -> dict[int, complex]:
    merged: dict[int, complex] = {}
    for d in dicts:
        for k, v in d.items():
            _prune_into(merged, k, v, eps)
    return merged


@dataclass
class SparseState:
    """Sparse quantum state vector.

    Parameters
    ----------
    n_qubits:
        Number of addressable qubits.
    amplitudes:
        Mapping from basis-state integer to amplitude. If omitted, initialize
        to |0...0>.
    eps:
        Pruning threshold for tiny amplitudes.
    """
    n_qubits: int
    amplitudes: dict[int, complex] | None = None
    eps: float = DEFAULT_EPS

    def __post_init__(self) -> None:
        if not isinstance(self.n_qubits, int) or self.n_qubits <= 0:
            raise QuantumError(f"n_qubits must be a positive integer, got {self.n_qubits!r}")
        if self.amplitudes is None:
            self.amplitudes = {0: 1+0j}
        else:
            self.amplitudes = {int(k): complex(v) for k, v in self.amplitudes.items() if abs(v) > self.eps}
            if not self.amplitudes:
                raise QuantumError("state cannot have zero norm")
        self.normalize()

    def copy(self) -> "SparseState":
        return SparseState(self.n_qubits, dict(self.amplitudes), self.eps)

    @property
    def nnz(self) -> int:
        return len(self.amplitudes or {})

    def norm2(self) -> float:
        return float(sum(abs(a) ** 2 for a in (self.amplitudes or {}).values()))

    def normalize(self) -> None:
        norm2 = self.norm2()
        if norm2 <= 0:
            raise QuantumError("cannot normalize a zero-norm state")
        scale = 1 / sqrt(norm2)
        self.amplitudes = {k: v * scale for k, v in (self.amplitudes or {}).items() if abs(v * scale) > self.eps}

    def ensure_qubit(self, qubit: int) -> None:
        if qubit < 0 or qubit >= self.n_qubits:
            raise QuantumError(f"qubit index {qubit} out of range for {self.n_qubits} qubits")

    def ensure_qubits(self, qubits: Sequence[int]) -> None:
        for q in qubits:
            self.ensure_qubit(q)
        if len(set(qubits)) != len(tuple(qubits)):
            raise QuantumError(f"gate qubits must be distinct, got {qubits}")

    def set_basis(self, state: int) -> None:
        if state < 0:
            raise QuantumError("basis index must be non-negative")
        if state.bit_length() > self.n_qubits:
            raise QuantumError(f"basis index {state} exceeds {self.n_qubits} qubits")
        self.amplitudes = {state: 1+0j}

    def probabilities(self, *, bitstrings: bool = True) -> dict[str, float] | dict[int, float]:
        probs: dict[str, float] | dict[int, float] = {}
        for state, amp in sorted((self.amplitudes or {}).items()):
            key = conventional_bitstring(state, self.n_qubits) if bitstrings else state
            probs[key] = abs(amp) ** 2
        return probs

    def top(self, k: int = 10) -> list[tuple[str, complex, float]]:
        rows = []
        for state, amp in sorted((self.amplitudes or {}).items(), key=lambda kv: abs(kv[1]) ** 2, reverse=True)[:k]:
            rows.append((conventional_bitstring(state, self.n_qubits), amp, abs(amp) ** 2))
        return rows


    def apply_precomputed_transition(self, transition_rows: list[list[tuple[int, complex]]]) -> None:
        """Apply a packaged full-register sparse transition lookup.

        ``transition_rows[input_state]`` contains ``(output_state, coeff)`` pairs.
        This is used for n<=10 precomputed embedded single-qubit gates.
        """
        max_state = 1 << self.n_qubits
        if len(transition_rows) != max_state:
            raise QuantumError(f"transition table has {len(transition_rows)} rows, expected {max_state}")
        out: dict[int, complex] = {}
        for state, amp in (self.amplitudes or {}).items():
            if state < 0 or state >= max_state:
                raise QuantumError(f"basis state {state} out of range for {self.n_qubits} qubits")
            for dst, coeff in transition_rows[state]:
                _prune_into(out, int(dst), coeff * amp, self.eps)
        self.amplitudes = out or {0: 0j}
        self.normalize()

    def apply_single_matrix(self, qubit: int, matrix: tuple[complex, complex, complex, complex], *, workers: int = 1, parallel_threshold: int = 4096) -> None:
        self.ensure_qubit(qubit)
        items = list((self.amplitudes or {}).items())
        if workers and workers > 1 and len(items) >= parallel_threshold:
            chunks = [items[i::workers] for i in range(workers)]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                parts = list(pool.map(lambda c: _apply_single_chunk(c, qubit, matrix, self.eps), chunks))
            self.amplitudes = _merge_dicts(parts, self.eps)
        else:
            self.amplitudes = _apply_single_chunk(items, qubit, matrix, self.eps)
        self.normalize()

    def apply_single(self, name: str, qubit: int, params: Sequence[float] = (), *, workers: int = 1, parallel_threshold: int = 4096) -> None:
        self.apply_single_matrix(qubit, matrix_2x2(name, params), workers=workers, parallel_threshold=parallel_threshold)

    def apply_two_matrix(self, q0: int, q1: int, matrix: list[list[complex]]) -> None:
        self.ensure_qubits((q0, q1))
        groups: dict[int, list[complex]] = {}
        for state, amp in (self.amplitudes or {}).items():
            b0 = (state >> q0) & 1
            b1 = (state >> q1) & 1
            idx = (b0 << 1) | b1
            base = state & ~(1 << q0) & ~(1 << q1)
            if base not in groups:
                groups[base] = [0j, 0j, 0j, 0j]
            groups[base][idx] += amp
        out: dict[int, complex] = {}
        for base, vec in groups.items():
            res = [sum(matrix[r][c] * vec[c] for c in range(4)) for r in range(4)]
            for idx, amp in enumerate(res):
                if abs(amp) <= self.eps:
                    continue
                b0 = (idx >> 1) & 1
                b1 = idx & 1
                state = base | (b0 << q0) | (b1 << q1)
                _prune_into(out, state, amp, self.eps)
        self.amplitudes = out or {0: 0j}
        self.normalize()

    def apply_two(self, name: str, q0: int, q1: int, params: Sequence[float] = ()) -> None:
        self.apply_two_matrix(q0, q1, matrix_4x4(name, params))

    def apply_ccz(self, q0: int, q1: int, q2: int) -> None:
        self.ensure_qubits((q0, q1, q2))
        mask = (1 << q0) | (1 << q1) | (1 << q2)
        self.amplitudes = {s: (-a if (s & mask) == mask else a) for s, a in (self.amplitudes or {}).items()}

    def apply_mcx(self, controls: Sequence[int], target: int) -> None:
        self.ensure_qubits(tuple(controls) + (target,))
        cmask = sum(1 << q for q in controls)
        out: dict[int, complex] = {}
        for state, amp in (self.amplitudes or {}).items():
            new_state = state ^ (1 << target) if (state & cmask) == cmask else state
            _prune_into(out, new_state, amp, self.eps)
        self.amplitudes = out

    def apply_mcz(self, qubits: Sequence[int]) -> None:
        self.ensure_qubits(tuple(qubits))
        mask = sum(1 << q for q in qubits)
        self.amplitudes = {s: (-a if (s & mask) == mask else a) for s, a in (self.amplitudes or {}).items()}

    def apply_swap_controlled(self, control: int, a: int, b: int) -> None:
        self.ensure_qubits((control, a, b))
        out: dict[int, complex] = {}
        for state, amp in (self.amplitudes or {}).items():
            if ((state >> control) & 1) and (((state >> a) & 1) != ((state >> b) & 1)):
                state = state ^ (1 << a) ^ (1 << b)
            _prune_into(out, state, amp, self.eps)
        self.amplitudes = out

    def measure_qubit(self, qubit: int, *, rng: Random | None = None, collapse: bool = True) -> int:
        self.ensure_qubit(qubit)
        rng = rng or Random()
        p1 = sum(abs(a) ** 2 for s, a in (self.amplitudes or {}).items() if ((s >> qubit) & 1))
        result = 1 if rng.random() < p1 else 0
        if collapse:
            self.amplitudes = {s: a for s, a in (self.amplitudes or {}).items() if ((s >> qubit) & 1) == result}
            self.normalize()
        return result

    def sample(self, shots: int = 1, *, rng: Random | None = None) -> dict[str, int]:
        if shots <= 0:
            raise QuantumError("shots must be positive")
        rng = rng or Random()
        states = list((self.amplitudes or {}).keys())
        weights = [abs((self.amplitudes or {})[s]) ** 2 for s in states]
        cumulative = []
        total = 0.0
        for w in weights:
            total += w
            cumulative.append(total)
        counts: dict[str, int] = {}
        for _ in range(shots):
            r = rng.random() * total
            idx = 0
            while idx < len(cumulative) - 1 and cumulative[idx] < r:
                idx += 1
            key = conventional_bitstring(states[idx], self.n_qubits)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def expectation_z(self, qubit: int) -> float:
        self.ensure_qubit(qubit)
        return sum((1 if ((s >> qubit) & 1) == 0 else -1) * abs(a) ** 2 for s, a in (self.amplitudes or {}).items())

    def expectation_zz(self, q0: int, q1: int) -> float:
        self.ensure_qubits((q0, q1))
        total = 0.0
        for state, amp in (self.amplitudes or {}).items():
            z0 = 1 if ((state >> q0) & 1) == 0 else -1
            z1 = 1 if ((state >> q1) & 1) == 0 else -1
            total += z0 * z1 * abs(amp) ** 2
        return total
