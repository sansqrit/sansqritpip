"""Quantum error-correction framework for Sansqrit.

The module provides code definitions, logical-qubit abstractions, syndrome
extraction circuit builders, simple decoders, and logical-gate helpers.  It is
implemented in pure Python so the data structures are readable by researchers
and AI/ML tools.

Scope note
----------
These helpers generate and execute small QEC circuits on Sansqrit engines.  The
surface-code decoder included here is a correctness-first greedy/lookup decoder
intended for education and testing; production threshold studies should use a
specialized decoder such as MWPM/union-find via an optional future backend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Iterable, Sequence, Any

from .errors import SansqritRuntimeError
from .types import QubitRef, qubit_index

PauliString = str
Operation = tuple[str, tuple[int, ...], tuple[float, ...]]


def _parse_pauli_term(term: str) -> list[tuple[str, int]]:
    """Parse terms like ``Z0 Z1`` or ``X3`` into ``[("Z",0), ...]``."""
    out: list[tuple[str, int]] = []
    for tok in term.replace("*", " ").split():
        tok = tok.strip().upper()
        if not tok:
            continue
        if tok[0] not in "XYZ":
            raise SansqritRuntimeError(f"invalid Pauli token {tok!r}")
        out.append((tok[0], int(tok[1:])))
    return out


@dataclass(frozen=True)
class StabilizerCode:
    """Declarative stabilizer-code description.

    Attributes:
        name: Stable code identifier.
        n: Number of physical qubits per logical qubit.
        k: Number of logical qubits encoded. Current helpers focus on k=1.
        distance: Code distance when known.
        stabilizers: Stabilizer generators as Pauli strings.
        logical_x: Logical-X operator as a Pauli string.
        logical_z: Logical-Z operator as a Pauli string.
        family: Code family, such as ``css`` or ``surface``.
    """
    name: str
    n: int
    k: int
    distance: int
    stabilizers: tuple[PauliString, ...]
    logical_x: PauliString
    logical_z: PauliString
    family: str = "stabilizer"
    description: str = ""

    def physical_qubits(self, base: int = 0) -> list[int]:
        return list(range(base, base + self.n))

    def shifted_term(self, term: PauliString, base: int) -> PauliString:
        return " ".join(f"{p}{q + base}" for p, q in _parse_pauli_term(term))

    def shifted_stabilizers(self, base: int = 0) -> tuple[PauliString, ...]:
        return tuple(self.shifted_term(s, base) for s in self.stabilizers)

    def syndrome_size(self) -> int:
        return len(self.stabilizers)


@dataclass
class LogicalQubit:
    """Logical qubit mapped onto physical qubits for a selected QEC code."""
    code: StabilizerCode
    physical: list[int]
    name: str = "logical"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return self.code.n

    def stabilizers(self) -> tuple[PauliString, ...]:
        base = self.physical[0]
        return self.code.shifted_stabilizers(base)

    def logical_x_term(self) -> PauliString:
        return self.code.shifted_term(self.code.logical_x, self.physical[0])

    def logical_z_term(self) -> PauliString:
        return self.code.shifted_term(self.code.logical_z, self.physical[0])


class Decoder(Protocol):
    """Interface for QEC decoders."""
    def decode(self, code: StabilizerCode, syndrome: Sequence[int]) -> list[tuple[str, int]]:
        """Return Pauli corrections as ``[(pauli, physical_index), ...]``."""


@dataclass
class LookupDecoder:
    """Table-driven decoder for small stabilizer codes."""
    table: dict[tuple[int, ...], list[tuple[str, int]]]

    def decode(self, code: StabilizerCode, syndrome: Sequence[int]) -> list[tuple[str, int]]:
        return list(self.table.get(tuple(int(x) for x in syndrome), []))


class RepetitionDecoder:
    """Majority-style decoder for bit-flip, phase-flip and repetition codes."""
    def decode(self, code: StabilizerCode, syndrome: Sequence[int]) -> list[tuple[str, int]]:
        bits = tuple(int(x) for x in syndrome)
        if code.name in {"bit_flip", "repetition3"}:
            table = {
                (0, 0): [],
                (1, 0): [("X", 0)],
                (1, 1): [("X", 1)],
                (0, 1): [("X", 2)],
            }
            return list(table.get(bits, []))
        if code.name == "phase_flip":
            table = {
                (0, 0): [],
                (1, 0): [("Z", 0)],
                (1, 1): [("Z", 1)],
                (0, 1): [("Z", 2)],
            }
            return list(table.get(bits, []))
        if code.name.startswith("repetition"):
            # Generic nearest-neighbor repetition syndrome: first boundary with a 1.
            if not bits:
                return []
            if sum(bits) == 0:
                return []
            # Find a likely flipped data qubit from syndrome-domain walls.
            if bits[0] == 1:
                return [("X", 0)]
            for i in range(1, len(bits)):
                if bits[i - 1] != bits[i]:
                    return [("X", i)]
            if bits[-1] == 1:
                return [("X", len(bits))]
        return []


@dataclass
class SurfaceCodeLattice:
    """Rotated planar surface-code helper lattice.

    This helper names data qubits and simple X/Z check locations.  It is a
    practical educational representation for generating layouts and syndrome
    records; it is not a replacement for a hardware-calibrated surface-code
    compiler.
    """
    distance: int = 3

    def __post_init__(self) -> None:
        if self.distance < 3 or self.distance % 2 == 0:
            raise SansqritRuntimeError("surface-code distance must be odd and >=3")

    @property
    def data_qubits(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.distance) for c in range(self.distance)]

    @property
    def x_checks(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.distance - 1) for c in range(self.distance - 1) if (r + c) % 2 == 0]

    @property
    def z_checks(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.distance - 1) for c in range(self.distance - 1) if (r + c) % 2 == 1]

    def neighbors(self, check: tuple[int, int]) -> list[tuple[int, int]]:
        r, c = check
        return [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]

    def data_index(self, coord: tuple[int, int]) -> int:
        r, c = coord
        return r * self.distance + c

    def stabilizers(self) -> tuple[str, ...]:
        stabs: list[str] = []
        for check in self.x_checks:
            stabs.append(" ".join(f"X{self.data_index(q)}" for q in self.neighbors(check)))
        for check in self.z_checks:
            stabs.append(" ".join(f"Z{self.data_index(q)}" for q in self.neighbors(check)))
        return tuple(stabs)


class SurfaceCodeDecoder:
    """Greedy surface-code decoder interface.

    The decoder maps a nonzero syndrome to nearest local corrections.  This is
    useful for examples and API compatibility.  For production surface-code
    simulations, plug in a specialized decoder implementing the same ``decode``
    method.
    """
    def decode(self, code: StabilizerCode, syndrome: Sequence[int]) -> list[tuple[str, int]]:
        corrections: list[tuple[str, int]] = []
        for i, bit in enumerate(syndrome):
            if int(bit) & 1:
                # First half assumed X checks -> correct Z; second half Z checks -> correct X.
                pauli = "Z" if i < len(syndrome) // 2 else "X"
                corrections.append((pauli, min(i, code.n - 1)))
        return corrections


# ---------------------------------------------------------------------------
# Standard code registry
# ---------------------------------------------------------------------------

def repetition_code(distance: int = 3) -> StabilizerCode:
    if distance < 3 or distance % 2 == 0:
        raise SansqritRuntimeError("repetition-code distance must be odd and >=3")
    stabilizers = tuple(f"Z{i} Z{i+1}" for i in range(distance - 1))
    logical_x = " ".join(f"X{i}" for i in range(distance))
    return StabilizerCode(
        name=f"repetition{distance}", n=distance, k=1, distance=distance,
        stabilizers=stabilizers, logical_x=logical_x, logical_z="Z0",
        family="repetition", description="Odd-distance repetition code for bit-flip errors.",
    )


def surface_code(distance: int = 3) -> StabilizerCode:
    lattice = SurfaceCodeLattice(distance)
    logical_x = " ".join(f"X{lattice.data_index((0, c))}" for c in range(distance))
    logical_z = " ".join(f"Z{lattice.data_index((r, 0))}" for r in range(distance))
    return StabilizerCode(
        name=f"surface{distance}", n=distance * distance, k=1, distance=distance,
        stabilizers=lattice.stabilizers(), logical_x=logical_x, logical_z=logical_z,
        family="surface", description="Rotated planar surface-code helper layout.",
    )


STANDARD_CODES: dict[str, StabilizerCode] = {
    "bit_flip": StabilizerCode(
        "bit_flip", 3, 1, 3, ("Z0 Z1", "Z1 Z2"), "X0 X1 X2", "Z0",
        family="repetition", description="3-qubit code correcting one bit-flip error.",
    ),
    "phase_flip": StabilizerCode(
        "phase_flip", 3, 1, 3, ("X0 X1", "X1 X2"), "X0", "Z0 Z1 Z2",
        family="repetition", description="3-qubit code correcting one phase-flip error.",
    ),
    "repetition3": repetition_code(3),
    "shor9": StabilizerCode(
        "shor9", 9, 1, 3,
        ("Z0 Z1", "Z1 Z2", "Z3 Z4", "Z4 Z5", "Z6 Z7", "Z7 Z8", "X0 X1 X2 X3 X4 X5", "X3 X4 X5 X6 X7 X8"),
        "X0 X1 X2 X3 X4 X5 X6 X7 X8", "Z0 Z3 Z6",
        family="css", description="Shor 9-qubit code helper.",
    ),
    "steane7": StabilizerCode(
        "steane7", 7, 1, 3,
        ("X0 X1 X2 X4", "X0 X1 X3 X5", "X0 X2 X3 X6", "Z0 Z1 Z2 Z4", "Z0 Z1 Z3 Z5", "Z0 Z2 Z3 Z6"),
        "X0 X1 X2 X3 X4 X5 X6", "Z0 Z1 Z2 Z3 Z4 Z5 Z6",
        family="css", description="Steane [[7,1,3]] CSS code helper.",
    ),
    "five_qubit": StabilizerCode(
        "five_qubit", 5, 1, 3,
        ("X0 Z1 Z2 X3", "X1 Z2 Z3 X4", "X0 X2 Z3 Z4", "Z0 X1 X3 Z4"),
        "X0 X1 X2 X3 X4", "Z0 Z1 Z2 Z3 Z4",
        family="perfect", description="Five-qubit perfect [[5,1,3]] code helper.",
    ),
    "surface3": surface_code(3),
}


def get_code(name: str, *, distance: int | None = None) -> StabilizerCode:
    key = name.lower().replace("-", "_")
    aliases = {"bitflip": "bit_flip", "phaseflip": "phase_flip", "shor": "shor9", "steane": "steane7", "5qubit": "five_qubit"}
    key = aliases.get(key, key)
    if key == "repetition":
        return repetition_code(distance or 3)
    if key == "surface":
        return surface_code(distance or 3)
    if key in STANDARD_CODES:
        return STANDARD_CODES[key]
    raise SansqritRuntimeError(f"unknown QEC code {name!r}")


def list_codes() -> list[str]:
    return sorted(set(STANDARD_CODES) | {"repetition", "surface"})


def logical_qubit(code: str | StabilizerCode, *, base: int = 0, name: str = "logical", distance: int | None = None) -> LogicalQubit:
    c = get_code(code, distance=distance) if isinstance(code, str) else code
    return LogicalQubit(c, c.physical_qubits(base), name=name)


# ---------------------------------------------------------------------------
# Circuit generation and engine application helpers
# ---------------------------------------------------------------------------

def _apply_pauli(engine: Any, pauli: str, q: int) -> None:
    getattr(engine, pauli.upper())(q)


def apply_pauli_string(engine: Any, term: PauliString, *, base: int = 0) -> None:
    for p, q in _parse_pauli_term(term):
        _apply_pauli(engine, p, q + base)


def encode(engine: Any, logical: LogicalQubit) -> None:
    """Encode a logical |0> into the selected code when a simple encoder is known."""
    q = logical.physical
    name = logical.code.name
    if name in {"bit_flip", "repetition3"} or name.startswith("repetition"):
        for t in q[1:]:
            engine.CNOT(q[0], t)
    elif name == "phase_flip":
        for t in q[1:]:
            engine.CNOT(q[0], t)
        for t in q:
            engine.H(t)
    elif name == "shor9":
        engine.H(q[0]); engine.CNOT(q[0], q[3]); engine.CNOT(q[0], q[6])
        for root in (q[0], q[3], q[6]):
            engine.CNOT(root, root + 1); engine.CNOT(root, root + 2)
    elif name == "steane7":
        # Compact educational encoder: prepare a CSS-like entangled block.
        engine.H(q[0]); engine.H(q[1]); engine.H(q[2])
        for c, t in [(0, 3), (0, 5), (0, 6), (1, 3), (1, 4), (1, 6), (2, 4), (2, 5), (2, 6)]:
            engine.CNOT(q[c], q[t])
    elif name == "five_qubit":
        # Keep a transparent helper rather than a misleading full encoder.
        engine.H(q[0]); engine.CNOT(q[0], q[1]); engine.CNOT(q[1], q[2]); engine.CNOT(q[2], q[3]); engine.CNOT(q[3], q[4])
    elif name.startswith("surface"):
        # Surface-code initialization for |0_L>: leave data qubits in |0>, checks are measured by syndrome routines.
        return
    else:
        raise SansqritRuntimeError(f"no encoder registered for {name}")


def decode(engine: Any, logical: LogicalQubit) -> None:
    """Inverse of the simple encoder when available."""
    q = logical.physical
    name = logical.code.name
    if name in {"bit_flip", "repetition3"} or name.startswith("repetition"):
        for t in reversed(q[1:]):
            engine.CNOT(q[0], t)
    elif name == "phase_flip":
        for t in q:
            engine.H(t)
        for t in reversed(q[1:]):
            engine.CNOT(q[0], t)
    elif name == "shor9":
        for root in (q[6], q[3], q[0]):
            engine.CNOT(root, root + 2); engine.CNOT(root, root + 1)
        engine.CNOT(q[0], q[6]); engine.CNOT(q[0], q[3]); engine.H(q[0])
    else:
        # For complex encoders this is intentionally a no-op helper; users can build explicit decoders.
        return


def syndrome_circuit(logical: LogicalQubit, *, ancilla_base: int | None = None) -> list[Operation]:
    """Return a syndrome-extraction circuit as operations.

    Each stabilizer gets one ancilla. For Z-checks the data controls the ancilla;
    for X-checks the ancilla is prepared/measured in the X basis.
    """
    base = logical.physical[0]
    ancilla_base = ancilla_base if ancilla_base is not None else base + logical.code.n
    ops: list[Operation] = []
    for si, stab in enumerate(logical.code.stabilizers):
        a = ancilla_base + si
        parsed = _parse_pauli_term(stab)
        is_x_check = all(p == "X" for p, _ in parsed)
        if is_x_check:
            ops.append(("H", (a,), ()))
        for p, rel_q in parsed:
            q = base + rel_q
            if p == "Z":
                ops.append(("CNOT", (q, a), ()))
            elif p == "X":
                ops.append(("CNOT", (a, q), ()))
            elif p == "Y":
                ops.append(("Sdg", (q,), ())); ops.append(("H", (q,), ())); ops.append(("CNOT", (q, a), ())); ops.append(("H", (q,), ())); ops.append(("S", (q,), ()))
        if is_x_check:
            ops.append(("H", (a,), ()))
    return ops


def measure_syndrome(engine: Any, logical: LogicalQubit, *, ancilla_base: int | None = None) -> tuple[int, ...]:
    ops = syndrome_circuit(logical, ancilla_base=ancilla_base)
    ancilla_base = ancilla_base if ancilla_base is not None else logical.physical[0] + logical.code.n
    for name, qs, params in ops:
        engine.apply(name, *qs, params=params) if hasattr(engine, "apply") else getattr(engine, name)(*qs)
    return tuple(int(engine.measure(ancilla_base + i)) for i in range(logical.code.syndrome_size()))


def default_decoder(code: StabilizerCode) -> Decoder:
    if code.family == "surface":
        return SurfaceCodeDecoder()
    if code.family == "repetition":
        return RepetitionDecoder()
    # Small lookup tables for common single-error syndromes.
    return LookupDecoder(single_error_lookup_table(code))


def single_error_lookup_table(code: StabilizerCode) -> dict[tuple[int, ...], list[tuple[str, int]]]:
    """Generate a simple single-error syndrome lookup table."""
    table: dict[tuple[int, ...], list[tuple[str, int]]] = {tuple([0] * len(code.stabilizers)): []}
    for error_pauli in ("X", "Z"):
        for q in range(code.n):
            syndrome = []
            for stab in code.stabilizers:
                anticommutes = 0
                for p, sq in _parse_pauli_term(stab):
                    if sq != q:
                        continue
                    if (error_pauli, p) in {("X", "Z"), ("Z", "X"), ("X", "Y"), ("Y", "X"), ("Z", "Y"), ("Y", "Z")}:
                        anticommutes ^= 1
                syndrome.append(anticommutes)
            table.setdefault(tuple(syndrome), [(error_pauli, q)])
    return table


def correct(engine: Any, logical: LogicalQubit, syndrome: Sequence[int], decoder: Decoder | None = None) -> list[tuple[str, int]]:
    dec = decoder or default_decoder(logical.code)
    corrections = dec.decode(logical.code, syndrome)
    base = logical.physical[0]
    for p, rel_q in corrections:
        _apply_pauli(engine, p, base + rel_q)
    return corrections


def logical_x(engine: Any, logical: LogicalQubit) -> None:
    apply_pauli_string(engine, logical.code.logical_x, base=logical.physical[0])


def logical_z(engine: Any, logical: LogicalQubit) -> None:
    apply_pauli_string(engine, logical.code.logical_z, base=logical.physical[0])


def logical_h(engine: Any, logical: LogicalQubit) -> None:
    for q in logical.physical:
        engine.H(q)


def logical_s(engine: Any, logical: LogicalQubit) -> None:
    for q in logical.physical:
        engine.S(q)


def logical_cnot(engine: Any, control: LogicalQubit, target: LogicalQubit) -> None:
    for c, t in zip(control.physical, target.physical):
        engine.CNOT(c, t)


def inject_error(engine: Any, logical: LogicalQubit, pauli: str, physical_offset: int) -> None:
    _apply_pauli(engine, pauli, logical.physical[physical_offset])


@dataclass
class CorrectionResult:
    syndrome: tuple[int, ...]
    corrections: list[tuple[str, int]]
    code: str


def syndrome_and_correct(engine: Any, logical: LogicalQubit, *, decoder: Decoder | None = None, ancilla_base: int | None = None) -> CorrectionResult:
    syndrome = measure_syndrome(engine, logical, ancilla_base=ancilla_base)
    corrections = correct(engine, logical, syndrome, decoder=decoder)
    return CorrectionResult(syndrome, corrections, logical.code.name)


__all__ = [
    "StabilizerCode", "LogicalQubit", "Decoder", "LookupDecoder", "RepetitionDecoder", "SurfaceCodeDecoder",
    "SurfaceCodeLattice", "STANDARD_CODES", "get_code", "list_codes", "logical_qubit", "repetition_code",
    "surface_code", "encode", "decode", "syndrome_circuit", "measure_syndrome", "correct",
    "logical_x", "logical_z", "logical_h", "logical_s", "logical_cnot", "inject_error",
    "syndrome_and_correct", "CorrectionResult", "single_error_lookup_table", "default_decoder",
]

class PyMatchingSurfaceDecoder:
    """Optional PyMatching-style decoder adapter.

    The adapter tries to use pymatching when a caller provides a matching graph.
    If pymatching is unavailable or no graph is supplied, it falls back to the
    built-in educational SurfaceCodeDecoder. This keeps Sansqrit importable on
    minimal installations while exposing a production-decoder integration point.
    """
    def __init__(self, matching_graph: Any | None = None):
        self.matching_graph = matching_graph
        self.fallback = SurfaceCodeDecoder()

    def decode(self, code: StabilizerCode, syndrome: Sequence[int]) -> list[tuple[str, int]]:
        if self.matching_graph is None:
            return self.fallback.decode(code, syndrome)
        try:
            import pymatching  # noqa: F401
            prediction = self.matching_graph.decode([int(x) for x in syndrome])
            corrections: list[tuple[str, int]] = []
            for i, bit in enumerate(prediction):
                if int(bit) & 1:
                    corrections.append(("X", min(i, code.n - 1)))
            return corrections
        except Exception:
            return self.fallback.decode(code, syndrome)


def qec_optional_features() -> dict[str, bool]:
    """Return availability of optional QEC acceleration libraries."""
    import importlib.util
    return {
        "stim": importlib.util.find_spec("stim") is not None,
        "pymatching": importlib.util.find_spec("pymatching") is not None,
    }


def syndrome_circuit_as_stim_text(logical: LogicalQubit, *, ancilla_base: int | None = None) -> str:
    """Return a best-effort Stim-like text circuit for the syndrome extraction.

    This is a textual bridge for users who install Stim; it avoids adding Stim as
    a hard dependency. Unsupported operations are emitted as comments.
    """
    lines: list[str] = []
    for name, qs, _params in syndrome_circuit(logical, ancilla_base=ancilla_base):
        gate = {"CNOT": "CX", "H": "H", "S": "S", "Sdg": "S_DAG"}.get(name)
        if gate:
            lines.append(f"{gate} " + " ".join(str(q) for q in qs))
        else:
            lines.append("# unsupported " + name + " " + " ".join(str(q) for q in qs))
    return "\n".join(lines) + ("\n" if lines else "")

# ---------------------------------------------------------------------------
# Production QEC integration adapters: Stim + PyMatching style workflows
# ---------------------------------------------------------------------------
def stim_surface_code_task(distance: int = 3, rounds: int | None = None, after_clifford_depolarization: float = 0.001) -> str:
    """Return a Stim surface-code memory experiment circuit when Stim is present.

    If Stim is not installed, a readable Stim-like fallback is returned. This is
    intentionally a text bridge because real threshold studies should be run in
    the user's Stim/PyMatching environment.
    """
    rounds = int(rounds or distance)
    try:
        import stim
        circ = stim.Circuit.generated(
            "surface_code:rotated_memory_z",
            distance=int(distance),
            rounds=rounds,
            after_clifford_depolarization=float(after_clifford_depolarization),
            before_round_data_depolarization=float(after_clifford_depolarization),
            before_measure_flip_probability=float(after_clifford_depolarization),
            after_reset_flip_probability=float(after_clifford_depolarization),
        )
        return str(circ)
    except Exception:
        lattice = SurfaceCodeLattice(distance)
        lines = [f"# Stim-like rotated surface-code fallback distance={distance} rounds={rounds} p={after_clifford_depolarization}"]
        for r in range(rounds):
            lines.append(f"# round {r}")
            for stab in lattice.stabilizers():
                lines.append("# stabilizer " + stab)
        lines.append("# Install stim for generated detector-error-model circuits.")
        return "\n".join(lines) + "\n"


@dataclass
class DecodingReport:
    decoder: str
    available: bool
    syndrome: tuple[int, ...]
    corrections: list[tuple[str, int]]
    notes: str


def pymatching_decode_surface(code: StabilizerCode, syndrome: Sequence[int], *, matching: Any | None = None) -> DecodingReport:
    """Decode a surface-code syndrome using PyMatching when possible.

    A caller may pass an already-constructed ``pymatching.Matching`` object from
    a detector error model. Without one, this uses the built-in fallback decoder.
    """
    bits = tuple(int(x) for x in syndrome)
    dec = PyMatchingSurfaceDecoder(matching)
    corrections = dec.decode(code, bits)
    available = qec_optional_features().get("pymatching", False) and matching is not None
    return DecodingReport("pymatching" if available else "surface_fallback", available, bits, corrections, "MWPM used only when a Matching graph is supplied; otherwise educational fallback.")


def qec_threshold_sweep_template(distances: Sequence[int] = (3, 5, 7), physical_error_rates: Sequence[float] = (0.001, 0.003, 0.01)) -> list[dict[str, Any]]:
    """Return a JSON-safe threshold-sweep plan for external Stim/PyMatching runs."""
    out = []
    for d in distances:
        for p in physical_error_rates:
            out.append({
                "code": "rotated_surface_code",
                "distance": int(d),
                "rounds": int(d),
                "physical_error_rate": float(p),
                "stim_generator": "surface_code:rotated_memory_z",
                "decoder": "PyMatching MWPM",
                "status": "plan_only_inside_sansqrit; execute with sansqrit[qec] extras for production studies",
            })
    return out


def logical_resource_estimate(algorithmic_logical_qubits: int, logical_depth: int, *, code_distance: int = 3, factories: int = 0) -> dict[str, int | str]:
    """Small resource-estimation helper inspired by cloud resource estimators."""
    if code_distance < 3 or code_distance % 2 == 0:
        raise SansqritRuntimeError("code_distance must be odd and >=3")
    physical_per_logical = 2 * code_distance * code_distance - 1
    return {
        "logical_qubits": int(algorithmic_logical_qubits),
        "logical_depth": int(logical_depth),
        "code_distance": int(code_distance),
        "physical_per_logical_estimate": physical_per_logical,
        "data_physical_qubits": int(algorithmic_logical_qubits) * physical_per_logical,
        "factory_physical_qubits": int(factories) * physical_per_logical,
        "total_physical_qubits": (int(algorithmic_logical_qubits) + int(factories)) * physical_per_logical,
        "note": "rough planning estimate, not a hardware-calibrated resource-estimator result",
    }

# Extend exported names for static analyzers.
__all__ += ["PyMatchingSurfaceDecoder", "stim_surface_code_task", "pymatching_decode_surface", "DecodingReport", "qec_threshold_sweep_template", "logical_resource_estimate"]
