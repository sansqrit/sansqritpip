"""Core quantum reference types used by Sansqrit."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List

from .errors import QuantumError

@dataclass(frozen=True)
class QubitRef:
    """A reference to a qubit index inside a quantum register."""
    index: int
    register_id: int = 0

    def __post_init__(self) -> None:
        if self.index < 0:
            raise QuantumError(f"qubit index must be non-negative, got {self.index}")

    def __repr__(self) -> str:
        return f"q[{self.index}]"

class QuantumRegister:
    """A simple addressable quantum register.

    Register indexing is little-endian: q[0] is the least-significant bit in
    basis-state integer encodings. Bitstrings are displayed most-significant
    bit first, as usual in quantum-computing examples.
    """

    def __init__(self, n_qubits: int, register_id: int = 0) -> None:
        if not isinstance(n_qubits, int) or n_qubits <= 0:
            raise QuantumError(f"quantum_register expects a positive integer, got {n_qubits!r}")
        self.n_qubits = n_qubits
        self.register_id = register_id

    def __len__(self) -> int:
        return self.n_qubits

    def __iter__(self) -> Iterator[QubitRef]:
        for i in range(self.n_qubits):
            yield QubitRef(i, self.register_id)

    def __getitem__(self, index: int | slice) -> QubitRef | List[QubitRef]:
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(self.n_qubits))]
        if not isinstance(index, int):
            raise QuantumError(f"register index must be int or slice, got {type(index).__name__}")
        if index < 0 or index >= self.n_qubits:
            raise QuantumError(f"qubit index {index} out of range for register of size {self.n_qubits}")
        return QubitRef(index, self.register_id)

    def indices(self) -> list[int]:
        return list(range(self.n_qubits))

    def __repr__(self) -> str:
        return f"QuantumRegister({self.n_qubits})"


def qubit_index(q: int | QubitRef) -> int:
    """Return an integer qubit index from either an int or QubitRef."""
    if isinstance(q, QubitRef):
        return q.index
    if isinstance(q, int) and q >= 0:
        return q
    raise QuantumError(f"expected qubit reference or non-negative int, got {q!r}")
