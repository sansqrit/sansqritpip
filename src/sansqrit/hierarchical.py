"""Hierarchical tensor-shard backend for large logical registers.

This backend implements the safe version of the common "120 qubits as twelve
10-qubit shards" idea.

Representation
--------------
* While gates stay inside fixed blocks, each block is a dense local tensor/vector
  of size ``2 ** block_size``. A 120-qubit register with ``block_size=10`` uses
  twelve 1024-amplitude vectors instead of one impossible ``2**120`` vector.
* Static local gates use the packaged Sansqrit lookup matrices where available.
* If a gate touches qubits in different blocks, the backend does **not** pretend
  the blocks are still independent. It promotes the block product state into the
  exact MPS backend and applies the bridge gate there. This keeps results
  accurate for low-entanglement bridge circuits and avoids the mathematically
  wrong "independent 10-qubit simulators" shortcut.

The backend is exact while in block mode. After promotion to MPS, accuracy is
exact when ``max_bond_dim=None`` and ``cutoff=0``. Truncation can be enabled for
speed/memory by setting a finite ``max_bond_dim`` or positive ``cutoff``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from random import Random
from typing import Sequence, Any

from .errors import QuantumError
from .gates import (
    GateOp,
    SINGLE_GATES,
    TWO_GATES,
    THREE_GATES,
    MULTI_GATES,
    canonical_gate_name,
    matrix_2x2,
    matrix_4x4,
    validate_gate_arity,
)
from .lookup import DEFAULT_LOOKUP, LookupTable
from .profiler import LookupProfile
from .sparse import SparseState, conventional_bitstring
from .types import QuantumRegister, QubitRef, qubit_index

try:  # optional dependency; required for this backend
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore


def _need_numpy():
    if np is None:
        raise QuantumError("hierarchical backend requires NumPy. Install with: pip install sansqrit[tensor]")


@dataclass(frozen=True)
class TensorShard:
    """A fixed logical block in a hierarchical tensor simulation."""

    id: int
    start: int
    end: int

    @property
    def n_qubits(self) -> int:
        return self.end - self.start

    @property
    def dim(self) -> int:
        return 1 << self.n_qubits

    def contains(self, q: int) -> bool:
        return self.start <= q < self.end

    def local(self, q: int) -> int:
        if not self.contains(q):
            raise QuantumError(f"qubit {q} is not in shard {self.id} [{self.start}..{self.end-1}]")
        return q - self.start

    def to_dict(self) -> dict[str, int]:
        return {"id": self.id, "start": self.start, "end": self.end, "n_qubits": self.n_qubits, "dim": self.dim}


@dataclass
class HierarchicalReport:
    backend: str
    mode: str
    n_qubits: int
    block_size: int
    blocks: int
    local_gate_count: int
    bridge_gate_count: int
    promoted_to_mps: bool
    max_bond_dim: int | None
    cutoff: float

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _apply_single_dense(vec, n: int, q: int, matrix: tuple[complex, complex, complex, complex]):
    m00, m01, m10, m11 = matrix
    out = vec.copy()
    bit = 1 << q
    step = bit << 1
    dim = 1 << n
    for base in range(0, dim, step):
        for off in range(bit):
            i0 = base + off
            i1 = i0 + bit
            a0 = vec[i0]
            a1 = vec[i1]
            out[i0] = m00 * a0 + m01 * a1
            out[i1] = m10 * a0 + m11 * a1
    return out


def _apply_two_dense(vec, n: int, q0: int, q1: int, matrix: list[list[complex]]):
    if q0 == q1:
        raise QuantumError("two-qubit gate qubits must be distinct")
    out = vec.copy()
    mask0 = 1 << q0
    mask1 = 1 << q1
    dim = 1 << n
    for base in range(dim):
        if (base & mask0) or (base & mask1):
            continue
        idxs = [
            base,
            base | mask1,
            base | mask0,
            base | mask0 | mask1,
        ]
        vin = [vec[i] for i in idxs]
        vout = [sum(matrix[r][c] * vin[c] for c in range(4)) for r in range(4)]
        for i, amp in zip(idxs, vout):
            out[i] = amp
    return out


def _dense_to_sparse(vec, eps: float) -> dict[int, complex]:
    return {i: complex(a) for i, a in enumerate(vec.tolist()) if abs(a) > eps}


def _sparse_to_dense(amps: dict[int, complex], n: int):
    out = np.zeros(1 << n, dtype=np.complex128)
    for i, a in amps.items():
        out[int(i)] = a
    return out


def _vector_to_mps_tensors(vec, n_qubits: int, *, cutoff: float = 0.0, max_bond_dim: int | None = None):
    """Convert a little-endian dense vector into MPS tensors in site order q0..qN."""
    _need_numpy()
    psi = np.asarray(vec, dtype=np.complex128).reshape([2] * n_qubits, order="F")
    tensors = []
    left_dim = 1
    rest = psi
    for site in range(n_qubits - 1):
        rest = rest.reshape(left_dim * 2, -1)
        U, S, Vh = np.linalg.svd(rest, full_matrices=False)
        keep = len(S)
        if cutoff and cutoff > 0:
            keep = int(np.sum(S > cutoff)) or 1
        if max_bond_dim is not None:
            keep = min(keep, int(max_bond_dim))
        U = U[:, :keep]
        S = S[:keep]
        Vh = Vh[:keep, :]
        tensors.append(U.reshape(left_dim, 2, keep))
        rest = (np.diag(S) @ Vh)
        left_dim = keep
    tensors.append(rest.reshape(left_dim, 2, 1))
    return tensors


@dataclass
class HierarchicalTensorEngine:
    """Block-dense + MPS-bridge backend.

    Parameters
    ----------
    n_qubits:
        Logical qubit count. 120 qubits with ``block_size=10`` creates 12 local
        dense blocks.
    block_size:
        Maximum number of qubits per local dense block. The packaged embedded
        lookups are currently available up to 10 qubits, so 10 is the default.
    max_bond_dim:
        Maximum MPS bond dimension after a bridge gate. Use ``None`` for exact
        no-truncation MPS evolution.
    cutoff:
        SVD singular-value cutoff after bridge promotion. Use 0 for exact.
    """

    n_qubits: int
    block_size: int = 10
    use_lookup: bool = True
    max_bond_dim: int | None = None
    cutoff: float = 0.0
    seed: int | None = None
    eps: float = 1e-14
    lookup: LookupTable = field(default_factory=lambda: DEFAULT_LOOKUP)

    def __post_init__(self) -> None:
        _need_numpy()
        if self.n_qubits <= 0:
            raise QuantumError("HierarchicalTensorEngine requires at least one qubit")
        if self.block_size <= 0:
            raise QuantumError("block_size must be positive")
        if self.block_size > 10:
            # The algorithm works for larger blocks, but this warning-as-error keeps
            # package memory realistic and aligned with packaged 10-qubit lookups.
            raise QuantumError("block_size > 10 is disabled by default; use <=10 for packaged lookup blocks")
        self.rng = Random(self.seed)
        self.blocks: list[TensorShard] = []
        self.vectors: list[Any] = []
        start = 0
        block_id = 0
        while start < self.n_qubits:
            end = min(self.n_qubits, start + self.block_size)
            shard = TensorShard(block_id, start, end)
            self.blocks.append(shard)
            vec = np.zeros(shard.dim, dtype=np.complex128)
            vec[0] = 1.0 + 0j
            self.vectors.append(vec)
            start = end
            block_id += 1
        self.history: list[GateOp] = []
        self.mode = "blocks"
        self.mps_engine = None
        self.profile = LookupProfile()
        self.local_gate_count = 0
        self.bridge_gate_count = 0

    @property
    def nnz(self) -> int:
        if self.mode == "mps":
            return -1
        count = 1
        for vec in self.vectors:
            count *= int(np.count_nonzero(np.abs(vec) > self.eps))
        return int(count)

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def ensure_qubits(self, qs: Sequence[int]) -> None:
        for q in qs:
            if q < 0 or q >= self.n_qubits:
                raise QuantumError(f"qubit index {q} out of range for {self.n_qubits} qubits")
        if len(set(qs)) != len(tuple(qs)):
            raise QuantumError(f"gate qubits must be distinct, got {qs}")

    def _block_for(self, q: int) -> TensorShard:
        self.ensure_qubits((q,))
        return self.blocks[q // self.block_size]

    def _same_block(self, qs: Sequence[int]) -> TensorShard | None:
        if not qs:
            return None
        block = self._block_for(qs[0])
        return block if all(block.contains(q) for q in qs) else None

    def _promote_to_mps(self) -> None:
        if self.mode == "mps":
            return
        from .mps import MPSEngine

        engine = MPSEngine(self.n_qubits, max_bond_dim=self.max_bond_dim, cutoff=self.cutoff, seed=self.seed)
        tensors = []
        for shard, vec in zip(self.blocks, self.vectors):
            tensors.extend(_vector_to_mps_tensors(vec, shard.n_qubits, cutoff=self.cutoff, max_bond_dim=self.max_bond_dim))
        engine.tensors = tensors
        engine.history = list(self.history)
        self.mps_engine = engine
        self.mode = "mps"

    def _apply_local_sparse_fallback(self, shard: TensorShard, name: str, qidx: tuple[int, ...], params: tuple[float, ...]) -> None:
        local_qs = tuple(q - shard.start for q in qidx)
        state = SparseState(shard.n_qubits, _dense_to_sparse(self.vectors[shard.id], self.eps), eps=self.eps)
        if name in THREE_GATES:
            if name == "Toffoli":
                state.apply_mcx(local_qs[:2], local_qs[2])
            elif name == "Fredkin":
                state.apply_swap_controlled(local_qs[0], local_qs[1], local_qs[2])
            elif name == "CCZ":
                state.apply_ccz(local_qs[0], local_qs[1], local_qs[2])
            else:
                raise QuantumError(f"unsupported local three-qubit gate {name}")
        elif name in MULTI_GATES:
            if name in {"MCX", "C3X", "C4X"}:
                state.apply_mcx(local_qs[:-1], local_qs[-1])
            elif name == "MCZ":
                state.apply_mcz(local_qs)
            else:
                raise QuantumError(f"unsupported local multi-qubit gate {name}")
        else:
            raise QuantumError(f"unsupported local fallback gate {name}")
        self.vectors[shard.id] = _sparse_to_dense(state.amplitudes or {}, shard.n_qubits)

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        self.ensure_qubits(qidx)
        if self.mode == "mps":
            self.bridge_gate_count += 1 if len({self._block_for(q).id for q in qidx}) > 1 else 0
            self.mps_engine.apply(name, *qidx, params=params)
            self.history.append(GateOp(name, qidx, params))
            return

        shard = self._same_block(qidx)
        if shard is None:
            # Correct bridge handling: promote to MPS instead of treating 10-qubit
            # blocks as independent after entanglement crosses a boundary.
            self.bridge_gate_count += 1
            self._promote_to_mps()
            self.mps_engine.apply(name, *qidx, params=params)
            self.history.append(GateOp(name, qidx, params))
            return

        if name in SINGLE_GATES:
            local_q = qidx[0] - shard.start
            if self.use_lookup and not params and self.lookup.has_single(name):
                self.profile.static_single_hits += 1
                matrix = self.lookup.matrix(name)
            else:
                self.profile.runtime_fallbacks += 1
                matrix = matrix_2x2(name, params)
            self.vectors[shard.id] = _apply_single_dense(self.vectors[shard.id], shard.n_qubits, local_q, matrix)
        elif name in TWO_GATES:
            local0 = qidx[0] - shard.start
            local1 = qidx[1] - shard.start
            if self.use_lookup and not params and self.lookup.has_two(name):
                self.profile.static_two_hits += 1
                matrix = self.lookup.matrix4(name)
            else:
                self.profile.runtime_fallbacks += 1
                matrix = matrix_4x4(name, params)
            self.vectors[shard.id] = _apply_two_dense(self.vectors[shard.id], shard.n_qubits, local0, local1, matrix)
        elif name in THREE_GATES or name in MULTI_GATES:
            self.profile.runtime_fallbacks += 1
            self._apply_local_sparse_fallback(shard, name, qidx, params)
        else:
            raise QuantumError(f"unknown gate {name}")
        self.local_gate_count += 1
        self.history.append(GateOp(name, qidx, params))

    # Convenience methods mirror QuantumEngine.
    def I(self, q): self.apply("I", q)
    def X(self, q): self.apply("X", q)
    def Y(self, q): self.apply("Y", q)
    def Z(self, q): self.apply("Z", q)
    def H(self, q): self.apply("H", q)
    def S(self, q): self.apply("S", q)
    def Sdg(self, q): self.apply("Sdg", q)
    def T(self, q): self.apply("T", q)
    def Tdg(self, q): self.apply("Tdg", q)
    def SX(self, q): self.apply("SX", q)
    def SXdg(self, q): self.apply("SXdg", q)
    def Rx(self, q, theta): self.apply("Rx", q, params=(theta,))
    def Ry(self, q, theta): self.apply("Ry", q, params=(theta,))
    def Rz(self, q, theta): self.apply("Rz", q, params=(theta,))
    def Phase(self, q, theta): self.apply("Phase", q, params=(theta,))
    def U1(self, q, theta): self.apply("U1", q, params=(theta,))
    def U2(self, q, phi, lam): self.apply("U2", q, params=(phi, lam))
    def U3(self, q, theta, phi, lam): self.apply("U3", q, params=(theta, phi, lam))
    def CNOT(self, c, t): self.apply("CNOT", c, t)
    def CX(self, c, t): self.apply("CNOT", c, t)
    def CZ(self, c, t): self.apply("CZ", c, t)
    def CY(self, c, t): self.apply("CY", c, t)
    def CH(self, c, t): self.apply("CH", c, t)
    def CSX(self, c, t): self.apply("CSX", c, t)
    def SWAP(self, a, b): self.apply("SWAP", a, b)
    def iSWAP(self, a, b): self.apply("iSWAP", a, b)
    def SqrtSWAP(self, a, b): self.apply("SqrtSWAP", a, b)
    def fSWAP(self, a, b): self.apply("fSWAP", a, b)
    def DCX(self, a, b): self.apply("DCX", a, b)
    def CRx(self, c, t, theta): self.apply("CRx", c, t, params=(theta,))
    def CRy(self, c, t, theta): self.apply("CRy", c, t, params=(theta,))
    def CRz(self, c, t, theta): self.apply("CRz", c, t, params=(theta,))
    def CP(self, c, t, theta): self.apply("CP", c, t, params=(theta,))
    def CU(self, c, t, theta, phi, lam): self.apply("CU", c, t, params=(theta, phi, lam))
    def RXX(self, a, b, theta): self.apply("RXX", a, b, params=(theta,))
    def RYY(self, a, b, theta): self.apply("RYY", a, b, params=(theta,))
    def RZZ(self, a, b, theta): self.apply("RZZ", a, b, params=(theta,))
    def RZX(self, a, b, theta): self.apply("RZX", a, b, params=(theta,))
    def ECR(self, a, b): self.apply("ECR", a, b)
    def MS(self, a, b): self.apply("MS", a, b)
    def Toffoli(self, a, b, c): self.apply("Toffoli", a, b, c)
    def Fredkin(self, c, a, b): self.apply("Fredkin", c, a, b)
    def CCZ(self, a, b, c): self.apply("CCZ", a, b, c)
    def MCX(self, *qs): self.apply("MCX", *qs)
    def MCZ(self, *qs): self.apply("MCZ", *qs)
    def C3X(self, a, b, c, t): self.apply("C3X", a, b, c, t)
    def C4X(self, a, b, c, d, t): self.apply("C4X", a, b, c, d, t)

    def H_all(self, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.H(q)

    def Rx_all(self, theta, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.Rx(q, theta)

    def Ry_all(self, theta, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.Ry(q, theta)

    def Rz_all(self, theta, qubits=None):
        qs = qubits if qubits is not None else range(self.n_qubits)
        for q in qs:
            self.Rz(q, theta)

    def qft(self, qubits=None, *, swaps: bool = True):
        # QFT creates broad long-range entanglement; MPS is the safe bridge path.
        self._promote_to_mps()
        return self.mps_engine.qft(qubits, swaps=swaps)

    def iqft(self, qubits=None, *, swaps: bool = True):
        self._promote_to_mps()
        return self.mps_engine.iqft(qubits, swaps=swaps)

    def reset(self) -> None:
        self.__post_init__()

    def shard_info(self) -> list[dict[str, Any]]:
        if self.mode == "mps":
            return [
                {"id": b.id, "start": b.start, "end": b.end, "n_qubits": b.n_qubits, "dim": b.dim, "mode": "promoted_mps"}
                for b in self.blocks
            ]
        return [
            {**b.to_dict(), "mode": "dense_block", "active_amplitudes": int(np.count_nonzero(np.abs(v) > self.eps))}
            for b, v in zip(self.blocks, self.vectors)
        ]

    def hierarchical_report(self) -> dict[str, Any]:
        rep = HierarchicalReport(
            backend="hierarchical_tensor",
            mode=self.mode,
            n_qubits=self.n_qubits,
            block_size=self.block_size,
            blocks=len(self.blocks),
            local_gate_count=self.local_gate_count,
            bridge_gate_count=self.bridge_gate_count,
            promoted_to_mps=self.mode == "mps",
            max_bond_dim=self.max_bond_dim,
            cutoff=self.cutoff,
        ).to_dict()
        if self.mode == "mps" and hasattr(self.mps_engine, "max_current_bond"):
            rep["current_mps_bond"] = self.mps_engine.max_current_bond
        rep["lookup"] = self.lookup_report()
        return rep

    def lookup_report(self) -> dict[str, Any]:
        out = self.profile.to_dict()
        out.update({"backend": "hierarchical_tensor", "mode": self.mode})
        return out

    def lookup_report_text(self) -> str:
        return str(self.lookup_report())

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        if self.mode == "mps":
            return self.mps_engine.measure_all(shots)
        if shots <= 0:
            raise QuantumError("shots must be positive")
        # Independent block sampling is exact while no bridge entanglement exists.
        block_states = []
        block_cdfs = []
        for vec in self.vectors:
            probs = np.abs(vec) ** 2
            states = list(range(len(probs)))
            cumulative = []
            total = 0.0
            for p in probs:
                total += float(p)
                cumulative.append(total)
            block_states.append(states)
            block_cdfs.append(cumulative)
        counts: dict[str, int] = {}
        for _ in range(shots):
            global_state = 0
            for shard, states, cdf in zip(self.blocks, block_states, block_cdfs):
                r = self.rng.random() * max(cdf[-1], 1e-300)
                idx = 0
                while idx < len(cdf) - 1 and cdf[idx] < r:
                    idx += 1
                global_state |= states[idx] << shard.start
            key = conventional_bitstring(global_state, self.n_qubits)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def measure(self, q: int | QubitRef) -> int:
        qidx = qubit_index(q)
        counts = self.measure_all(1)
        bitstring = next(iter(counts))
        # conventional bitstring is MSB first
        return int(bitstring[self.n_qubits - 1 - qidx])

    def probabilities(self) -> dict[str, float]:
        if self.mode == "mps":
            return self.mps_engine.probabilities()
        if self.n_qubits > 20:
            raise QuantumError("probabilities() on hierarchical block mode is limited to <=20 qubits; use measure_all(shots)")
        out: dict[str, float] = {"": 1.0}
        for shard, vec in zip(self.blocks, self.vectors):
            next_out: dict[str, float] = {}
            for prefix, p0 in out.items():
                for state, amp in enumerate(vec):
                    p = float(abs(amp) ** 2)
                    if p <= self.eps:
                        continue
                    # Local conventional bitstring for the block, then append low-to-high blocks.
                    key = conventional_bitstring(state, shard.n_qubits) + prefix
                    next_out[key] = next_out.get(key, 0.0) + p0 * p
            out = next_out
        return dict(sorted(out.items()))

    def expectation_z(self, q: int | QubitRef) -> float:
        qidx = qubit_index(q)
        if self.mode == "mps":
            return self.mps_engine.expectation_z(qidx)
        shard = self._block_for(qidx)
        local = qidx - shard.start
        vec = self.vectors[shard.id]
        total = 0.0
        for state, amp in enumerate(vec):
            z = 1 if ((state >> local) & 1) == 0 else -1
            total += z * float(abs(amp) ** 2)
        return total

    def expectation_zz(self, a: int | QubitRef, b: int | QubitRef) -> float:
        q0, q1 = qubit_index(a), qubit_index(b)
        if self.mode == "mps":
            return self.mps_engine.expectation_zz(q0, q1)
        s0, s1 = self._block_for(q0), self._block_for(q1)
        if s0.id != s1.id:
            return self.expectation_z(q0) * self.expectation_z(q1)
        l0, l1 = q0 - s0.start, q1 - s0.start
        total = 0.0
        for state, amp in enumerate(self.vectors[s0.id]):
            z0 = 1 if ((state >> l0) & 1) == 0 else -1
            z1 = 1 if ((state >> l1) & 1) == 0 else -1
            total += z0 * z1 * float(abs(amp) ** 2)
        return total

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)
