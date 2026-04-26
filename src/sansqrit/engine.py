"""High-level Sansqrit quantum engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import pi
from random import Random
from typing import Sequence

from .errors import QuantumError
from .gates import (
    SINGLE_GATES, TWO_GATES, THREE_GATES, MULTI_GATES,
    GateOp, canonical_gate_name, matrix_2x2, validate_gate_arity,
)
from .lookup import DEFAULT_LOOKUP, LookupTable
from .sharding import ShardedState, ShardInfo
from .sparse import SparseState
from .types import QuantumRegister, QubitRef, qubit_index
from .profiler import LookupProfile


@dataclass
class EngineConfig:
    backend: str = "sparse"
    n_shards: int = 1
    workers: int = 1
    use_lookup: bool = True
    parallel_threshold: int = 4096
    seed: int | None = None
    eps: float = 1e-14


@dataclass
class QuantumEngine:
    """Sparse, sharded and optionally threaded state-vector simulator.

    ``backend`` can be ``"sparse"``, ``"sharded"`` or ``"threaded"``.
    All modes use the same sparse representation. ``sharded`` additionally
    partitions the authoritative state into local shards after every operation;
    ``threaded`` uses ``ThreadPoolExecutor`` for large single-qubit transforms.
    """
    n_qubits: int
    config: EngineConfig = field(default_factory=EngineConfig)
    lookup: LookupTable = field(default_factory=lambda: DEFAULT_LOOKUP)

    def __post_init__(self) -> None:
        if self.n_qubits <= 0:
            raise QuantumError("QuantumEngine requires at least one qubit")
        self.state = SparseState(self.n_qubits, eps=self.config.eps)
        self.history: list[GateOp] = []
        self.profile = LookupProfile()
        self.rng = Random(self.config.seed)
        if self.config.backend == "threaded" and self.config.workers <= 1:
            self.config.workers = 2
        if self.config.backend == "sharded" and self.config.n_shards <= 1:
            self.config.n_shards = 4
        self.sharded = ShardedState(self.config.n_shards)
        self._sync_shards()

    @classmethod
    def create(cls, n_qubits: int, *, backend: str = "sparse", n_shards: int = 1,
               workers: int = 1, use_lookup: bool = True, seed: int | None = None,
               eps: float = 1e-14, **kwargs):
        """Create an engine by backend name.

        Built-in backends:
        - sparse/threaded/sharded: sparse state-vector family;
        - stabilizer/clifford: large Clifford tableau backend;
        - mps/tensor: matrix-product-state tensor backend;
        - density/noisy: sparse density matrix with noise channels;
        - gpu/cupy: optional dense CuPy state-vector backend;
        - distributed/cluster: TCP worker-backed sparse backend;
        - hierarchical/tensor-shards: 10-qubit dense local blocks with MPS bridge promotion.
        """
        backend = backend or "sparse"
        if backend in {"stabilizer", "clifford"}:
            from .stabilizer import StabilizerEngine
            return StabilizerEngine(n_qubits, seed=seed)
        if backend in {"hierarchical", "hierarchical-tensor", "tensor-shards", "block-tensor"}:
            from .hierarchical import HierarchicalTensorEngine
            return HierarchicalTensorEngine(
                n_qubits,
                block_size=int(kwargs.get("block_size", 10)),
                use_lookup=use_lookup,
                max_bond_dim=kwargs.get("max_bond_dim", None),
                cutoff=kwargs.get("cutoff", 0.0),
                seed=seed,
                eps=eps,
            )
        if backend in {"mps", "tensor", "tensor-network"}:
            from .mps import MPSEngine
            return MPSEngine(n_qubits, max_bond_dim=kwargs.get("max_bond_dim", 128),
                             cutoff=kwargs.get("cutoff", eps), seed=seed)
        if backend in {"density", "density-matrix", "noisy"}:
            from .density import DensityMatrixEngine
            return DensityMatrixEngine(n_qubits, seed=seed, eps=eps)
        if backend in {"gpu", "cupy", "cuda"}:
            from .gpu import CuPyStateVectorEngine
            return CuPyStateVectorEngine(n_qubits, seed=seed)
        if backend in {"distributed", "cluster"}:
            from .cluster import DistributedSparseEngine
            addresses = kwargs.get("addresses") or kwargs.get("workers_addresses")
            if not addresses:
                raise QuantumError("distributed backend requires addresses=[('host', port), ...]")
            return DistributedSparseEngine.from_addresses(n_qubits, addresses, eps=eps)
        return cls(n_qubits, EngineConfig(backend=backend, n_shards=n_shards, workers=workers,
                                          use_lookup=use_lookup, seed=seed, eps=eps))

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def reset(self) -> None:
        self.state = SparseState(self.n_qubits, eps=self.config.eps)
        self.history.clear()
        self._sync_shards()

    @property
    def nnz(self) -> int:
        return self.state.nnz

    def _sync_shards(self) -> None:
        self.sharded.repartition(self.state.amplitudes or {})

    def shard_info(self) -> list[ShardInfo]:
        self._sync_shards()
        return self.sharded.info()

    def lookup_report(self) -> dict:
        """Return lookup/sharding profiling counters for diagnostics."""
        return self.profile.to_dict()

    def lookup_report_text(self) -> str:
        return self.profile.report()

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        if name in SINGLE_GATES:
            if (
                self.config.use_lookup
                and not params
                and self.lookup.has_embedded_single(self.n_qubits, qidx[0], name)
            ):
                # Fast middle-layer path: packaged precomputed full-register
                # transition table for n<=10 static single-qubit gates.
                self.profile.embedded_single_hits += 1
                self.state.apply_precomputed_transition(
                    self.lookup.embedded_single_transition(self.n_qubits, qidx[0], name)
                )
            else:
                if self.config.use_lookup and self.lookup.has_single(name) and not params:
                    self.profile.static_single_hits += 1
                    matrix = self.lookup.matrix(name)
                else:
                    self.profile.runtime_fallbacks += 1
                    matrix = matrix_2x2(name, params)
                workers = self.config.workers if self.config.backend in {"threaded", "sharded"} else 1
                self.state.apply_single_matrix(qidx[0], matrix, workers=workers, parallel_threshold=self.config.parallel_threshold)
        elif name in TWO_GATES:
            if self.config.use_lookup and not params and self.lookup.has_two(name):
                self.profile.static_two_hits += 1
                self.state.apply_two_matrix(qidx[0], qidx[1], self.lookup.matrix4(name))
            else:
                self.profile.runtime_fallbacks += 1
                self.state.apply_two(name, qidx[0], qidx[1], params)
        elif name in THREE_GATES:
            if name == "Toffoli":
                self.state.apply_mcx(qidx[:2], qidx[2])
            elif name == "Fredkin":
                self.state.apply_swap_controlled(qidx[0], qidx[1], qidx[2])
            elif name == "CCZ":
                self.state.apply_ccz(qidx[0], qidx[1], qidx[2])
            else:
                raise QuantumError(f"unsupported three-qubit gate {name}")
        elif name in MULTI_GATES:
            if name in {"MCX", "C3X", "C4X"}:
                self.state.apply_mcx(qidx[:-1], qidx[-1])
            elif name == "MCZ":
                self.state.apply_mcz(qidx)
            else:
                raise QuantumError(f"unsupported multi-qubit gate {name}")
        else:
            raise QuantumError(f"unknown gate {name}")
        self.history.append(GateOp(name, qidx, params))
        self._sync_shards()

    # Convenience gate methods -------------------------------------------------
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
    def CCX(self, a, b, c): self.Toffoli(a, b, c)
    def Fredkin(self, c, a, b): self.apply("Fredkin", c, a, b)
    def CSWAP(self, c, a, b): self.Fredkin(c, a, b)
    def CCZ(self, a, b, c): self.apply("CCZ", a, b, c)
    def MCX(self, *qs): self.apply("MCX", *qs)
    def MCZ(self, *qs): self.apply("MCZ", *qs)
    def C3X(self, a, b, c, t): self.apply("C3X", a, b, c, t)
    def C4X(self, a, b, c, d, t): self.apply("C4X", a, b, c, d, t)

    # Higher-level helpers -----------------------------------------------------
    def H_all(self, qubits: Sequence[int | QubitRef] | None = None) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        for q in qs:
            self.H(q)

    def Rx_all(self, theta: float, qubits: Sequence[int | QubitRef] | None = None) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        for q in qs:
            self.Rx(q, theta)

    def Ry_all(self, theta: float, qubits: Sequence[int | QubitRef] | None = None) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        for q in qs:
            self.Ry(q, theta)

    def Rz_all(self, theta: float, qubits: Sequence[int | QubitRef] | None = None) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        for q in qs:
            self.Rz(q, theta)

    def qft(self, qubits: Sequence[int | QubitRef] | QuantumRegister | None = None, *, swaps: bool = True) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        n = len(qs)
        for j in range(n):
            self.H(qs[j])
            for k in range(j + 1, n):
                angle = pi / (2 ** (k - j))
                self.CP(qs[k], qs[j], angle)
        if swaps:
            for i in range(n // 2):
                self.SWAP(qs[i], qs[n - i - 1])

    def iqft(self, qubits: Sequence[int | QubitRef] | QuantumRegister | None = None, *, swaps: bool = True) -> None:
        qs = [qubit_index(q) for q in qubits] if qubits is not None else list(range(self.n_qubits))
        n = len(qs)
        if swaps:
            for i in range(n // 2):
                self.SWAP(qs[i], qs[n - i - 1])
        for j in reversed(range(n)):
            for k in reversed(range(j + 1, n)):
                angle = -pi / (2 ** (k - j))
                self.CP(qs[k], qs[j], angle)
            self.H(qs[j])

    def measure(self, q: int | QubitRef, *, collapse: bool = True) -> int:
        value = self.state.measure_qubit(qubit_index(q), rng=self.rng, collapse=collapse)
        self._sync_shards()
        return value

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        return self.state.sample(shots, rng=self.rng)

    def probabilities(self) -> dict[str, float]:
        return self.state.probabilities(bitstrings=True)  # type: ignore[return-value]

    def expectation_z(self, q: int | QubitRef) -> float:
        return self.state.expectation_z(qubit_index(q))

    def expectation_zz(self, q0: int | QubitRef, q1: int | QubitRef) -> float:
        return self.state.expectation_zz(qubit_index(q0), qubit_index(q1))

    def amplitudes(self) -> dict[int, complex]:
        return dict(self.state.amplitudes or {})

    def top(self, k: int = 10):
        return self.state.top(k)

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)


def bell_state(*, backend: str = "sparse", seed: int | None = None) -> QuantumEngine:
    e = QuantumEngine.create(2, backend=backend, seed=seed)
    e.H(0)
    e.CNOT(0, 1)
    return e


def ghz_state(n_qubits: int, *, backend: str = "sparse", seed: int | None = None) -> QuantumEngine:
    e = QuantumEngine.create(n_qubits, backend=backend, seed=seed)
    e.H(0)
    for i in range(n_qubits - 1):
        e.CNOT(i, i + 1)
    return e
