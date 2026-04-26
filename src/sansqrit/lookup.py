"""Packaged precomputed lookup tables for Sansqrit.

Sansqrit ships lookup data inside the wheel under ``sansqrit/data``.
The runtime uses these tables as a middle-layer accelerator before falling
back to arithmetic matrix application.

Included tables in v0.4:
- static 2x2 matrices for all non-parametric single-qubit gates;
- static 4x4 matrices for all non-parametric two-qubit gates;
- embedded sparse transition tables for every n=1..10, every target qubit,
  and every static single-qubit gate.

The embedded table means that for a 10-qubit or smaller sparse engine, a gate
like ``H q[7]`` can be applied by direct basis-transition lookup instead of
constructing the transition in the hot path. For larger systems, Sansqrit uses
the same matrix math fallback because full embedded tables scale exponentially.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Sequence

from .gates import STATIC_SINGLE_GATES, matrix_2x2, matrix_4x4, TWO_GATES, canonical_gate_name


def _encode_complex(z: complex) -> list[float]:
    return [float(z.real), float(z.imag)]


def _decode_complex(x: Sequence[float]) -> complex:
    return complex(float(x[0]), float(x[1]))


def _resource_text(name: str) -> str:
    return files("sansqrit").joinpath("data", name).read_text(encoding="utf-8")


def _resource_bytes(name: str) -> bytes:
    return files("sansqrit").joinpath("data", name).read_bytes()


@lru_cache(maxsize=1)
def packaged_metadata() -> dict:
    """Return metadata for the lookup files bundled in the installed package."""
    try:
        return json.loads(_resource_text("lookup_metadata.json"))
    except Exception:
        return {
            "format": "generated-fallback",
            "max_embedded_qubits": 0,
            "notes": ["packaged lookup metadata unavailable; using generated fallback matrices"],
        }


@lru_cache(maxsize=1)
def _load_packaged_single_matrices() -> dict[str, tuple[complex, complex, complex, complex]]:
    try:
        payload = json.loads(_resource_text("lookup_static_gates.json"))
        return {k: tuple(_decode_complex(z) for z in vals) for k, vals in payload.items()}  # type: ignore[return-value]
    except Exception:
        return {name: matrix_2x2(name) for name in sorted(STATIC_SINGLE_GATES)}


@lru_cache(maxsize=1)
def _load_packaged_two_matrices() -> dict[str, list[list[complex]]]:
    try:
        payload = json.loads(_resource_text("lookup_two_qubit_static_gates.json"))
        return {k: [[_decode_complex(z) for z in row] for row in rows] for k, rows in payload.items()}
    except Exception:
        out: dict[str, list[list[complex]]] = {}
        for name in TWO_GATES:
            cname = canonical_gate_name(name)
            try:
                out[cname] = matrix_4x4(cname, ())
            except Exception:
                pass
        return out


@lru_cache(maxsize=1)
def _load_embedded_single() -> dict[str, list[list[tuple[int, complex]]]]:
    """Load gzipped embedded transitions lazily.

    The JSON on disk stores ``[[out_state, [re, im]], ...]`` rows. This function
    converts them to Python complex numbers once per process.
    """
    try:
        raw = gzip.decompress(_resource_bytes("lookup_embedded_single_upto_10.json.gz"))
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    out: dict[str, list[list[tuple[int, complex]]]] = {}
    for key, rows in payload.items():
        out[key] = [[(int(dst), _decode_complex(coeff)) for dst, coeff in pairs] for pairs in rows]
    return out


@dataclass
class LookupTable:
    """Lookup table facade used by engines.

    The facade prefers packaged data files. It still supports JSON import/export
    for users who want to build custom hardware-specific lookup packs.
    """
    matrices: dict[str, tuple[complex, complex, complex, complex]] = field(default_factory=dict)
    two_matrices: dict[str, list[list[complex]]] = field(default_factory=dict)
    max_embedded_qubits: int = 10

    @classmethod
    def standard(cls) -> "LookupTable":
        meta = packaged_metadata()
        return cls(
            matrices=dict(_load_packaged_single_matrices()),
            two_matrices=dict(_load_packaged_two_matrices()),
            max_embedded_qubits=int(meta.get("max_embedded_qubits", 10) or 10),
        )

    def has_single(self, name: str) -> bool:
        return canonical_gate_name(name) in self.matrices

    def matrix(self, name: str) -> tuple[complex, complex, complex, complex]:
        return self.matrices[canonical_gate_name(name)]

    def has_two(self, name: str) -> bool:
        return canonical_gate_name(name) in self.two_matrices

    def matrix4(self, name: str) -> list[list[complex]]:
        return self.two_matrices[canonical_gate_name(name)]

    def has_embedded_single(self, n_qubits: int, qubit: int, name: str) -> bool:
        name = canonical_gate_name(name)
        if n_qubits < 1 or n_qubits > self.max_embedded_qubits:
            return False
        return f"{n_qubits}:{qubit}:{name}" in _load_embedded_single()

    def embedded_single_transition(self, n_qubits: int, qubit: int, name: str) -> list[list[tuple[int, complex]]]:
        """Return precomputed full-register transition rows for n<=10."""
        key = f"{n_qubits}:{qubit}:{canonical_gate_name(name)}"
        table = _load_embedded_single()
        if key not in table:
            raise KeyError(f"no embedded lookup table for {key}")
        return table[key]

    def transition(self, name: str, bit: int) -> tuple[tuple[int, complex], tuple[int, complex]]:
        """Return local basis-bit transition for |bit> under a static single-qubit gate."""
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
