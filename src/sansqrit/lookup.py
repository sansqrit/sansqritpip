"""Precomputed lookup tables for gate matrices and local transitions.

The pure-Python simulator uses this module for non-parametric single-qubit
matrix lookup. The table is intentionally simple and serializable; it can be
extended later with hardware-specific kernels or mmap-backed numeric blobs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .gates import STATIC_SINGLE_GATES, matrix_2x2


def _encode_complex(z: complex) -> list[float]:
    return [float(z.real), float(z.imag)]


def _decode_complex(x: Sequence[float]) -> complex:
    return complex(float(x[0]), float(x[1]))


@dataclass
class LookupTable:
    """Lookup table for precomputed single-qubit matrices."""
    matrices: dict[str, tuple[complex, complex, complex, complex]] = field(default_factory=dict)

    @classmethod
    def standard(cls) -> "LookupTable":
        return cls({name: matrix_2x2(name) for name in sorted(STATIC_SINGLE_GATES)})

    def has_single(self, name: str) -> bool:
        return name in self.matrices

    def matrix(self, name: str) -> tuple[complex, complex, complex, complex]:
        return self.matrices[name]

    def transition(self, name: str, bit: int) -> tuple[tuple[int, complex], tuple[int, complex]]:
        """Return basis-bit transition for |bit> under a static single-qubit gate."""
        m00, m01, m10, m11 = self.matrix(name)
        if bit == 0:
            return (0, m00), (1, m10)
        if bit == 1:
            return (0, m01), (1, m11)
        raise ValueError("bit must be 0 or 1")

    def to_json(self, path: str | Path) -> None:
        payload = {k: [_encode_complex(z) for z in v] for k, v in self.matrices.items()}
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "LookupTable":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls({k: tuple(_decode_complex(z) for z in vals) for k, vals in payload.items()})


DEFAULT_LOOKUP = LookupTable.standard()
