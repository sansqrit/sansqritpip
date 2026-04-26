"""Architecture descriptions, estimators and execution-flow helpers for Sansqrit.

This module is intentionally data-oriented: documentation generators, AI/ML
training tools and CLI commands can import the same structured descriptions that
humans see in the README.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import log10
from typing import Any

BYTES_PER_COMPLEX128 = 16

@dataclass(frozen=True)
class MemoryEstimate:
    qubits: int
    dense_amplitudes: int | str
    dense_bytes: int | str
    dense_human: str
    sparse_basis_keys: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def human_bytes(n: int | str) -> str:
    if isinstance(n, str):
        return n
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.3g} {unit}"
        value /= 1024.0
    return f"{value:.3g} YB"


def dense_memory_estimate(qubits: int, *, bytes_per_amplitude: int = BYTES_PER_COMPLEX128) -> MemoryEstimate:
    if qubits < 0:
        raise ValueError("qubits must be non-negative")
    if qubits <= 60:
        amps: int | str = 1 << qubits
        bytes_: int | str = amps * bytes_per_amplitude
        human = human_bytes(bytes_)
    else:
        amps = f"2^{qubits} ≈ 1e{qubits * log10(2):.2f}"
        bytes_ = "astronomical"
        human = "astronomical"
    sparse = "stores only nonzero amplitudes as {basis_index: complex_amplitude}"
    explanation = (
        "Dense state-vector memory scales as 2^n. Sparse/sharded, stabilizer, "
        "MPS and hierarchical tensor modes avoid materializing a dense vector when "
        "the circuit has exploitable structure."
    )
    return MemoryEstimate(qubits, amps, bytes_, human, sparse, explanation)


def execution_flow_mermaid() -> str:
    return """flowchart TD
    A[Sansqrit .sq DSL] --> B[Translator / Parser]
    B --> C[Circuit History + Runtime Engine]
    C --> D[Optimizer Passes]
    D --> E[Adaptive Planner]
    E -->|Sparse / few amplitudes| F[Sparse State Map]
    E -->|Large sparse| G[Sharded Sparse State]
    E -->|Independent <=10q blocks| H[Hierarchical Tensor Shards]
    E -->|Cross-block low entanglement| I[MPS Bridge]
    E -->|Clifford circuit| J[Stabilizer Tableau]
    E -->|Noisy small circuit| K[Density Matrix]
    E -->|GPU available and dense small| L[CuPy / GPU Statevector]
    E -->|Cluster configured| M[TCP Distributed Sparse Workers]
    F --> N[Lookup Matrices + Sparse Updates]
    G --> N
    H --> O[Packaged 1..10q Embedded Lookups]
    I --> P[Tensor SVD / Bond Update]
    J --> Q[Tableau Update]
    K --> R[Kraus / Noise Channels]
    L --> S[GPU Vector Operations]
    M --> T[Shard Exchange / Coordinator]
    N --> U[Measurement / QASM / Hardware Export]
    O --> U
    P --> U
    Q --> U
    R --> U
    S --> U
    T --> U"""


def architecture_layers() -> list[dict[str, Any]]:
    return [
        {"layer": "DSL", "purpose": "Scientist-facing simplified Sansqrit syntax", "examples": ["q = quantum_register(120)", "H(q[0])", "apply CNOT on q[9], q[10] bridge_mode=sparse"]},
        {"layer": "Translator", "purpose": "Converts .sq to a restricted Python runtime model", "examples": ["simulate blocks", "pipeline operator", "shard declarations"]},
        {"layer": "Circuit history", "purpose": "Records gate operations for QASM, interop, verification and optimization", "examples": ["GateOp(name, qubits, params)"]},
        {"layer": "Planner", "purpose": "Selects sparse, sharded, hierarchical, stabilizer, MPS, density, GPU or distributed backend", "examples": ["plan_backend(120, ops)"]},
        {"layer": "Lookup", "purpose": "Loads packaged precomputed matrices and embedded <=10 qubit transitions", "examples": ["H/X/SX single-gate lookup", "CNOT/CZ/SWAP 4x4 lookup", "10-qubit embedded transition maps"]},
        {"layer": "Sparse/sharded", "purpose": "Stores only active basis amplitudes and partitions them across shards/workers", "examples": ["basis integer -> complex amplitude"]},
        {"layer": "Hierarchical tensor shards", "purpose": "Uses dense 10-qubit local blocks and promotes bridge entanglement to MPS", "examples": ["12 blocks for 120 qubits", "MPS bridge for q[9]-q[10]"]},
        {"layer": "QEC", "purpose": "Logical qubits, stabilizer codes, syndrome extraction, decoders and correction", "examples": ["bit_flip", "shor9", "steane7", "surface3"]},
        {"layer": "Hardware export", "purpose": "OpenQASM 2/3 plus Qiskit/Cirq/Braket/PennyLane adapters and provider payloads", "examples": ["export_qasm3", "export_hardware('braket')"]},
    ]


def scenario_table() -> list[dict[str, str]]:
    return [
        {"scenario": "120q sparse oracle / few active states", "recommended": "sparse or sharded", "why": "State stays as a small map of nonzero amplitudes."},
        {"scenario": "120q independent 10q blocks", "recommended": "hierarchical", "why": "Each block can use dense 1024-amplitude vectors and packaged embedded lookup."},
        {"scenario": "120q cross-block low entanglement", "recommended": "hierarchical with MPS bridge", "why": "Blocks stay compact while bonds store correlations."},
        {"scenario": "1000q Clifford circuit", "recommended": "stabilizer", "why": "Tableau simulation avoids dense amplitudes."},
        {"scenario": "Noisy <=12q detailed channel simulation", "recommended": "density", "why": "Density matrices capture mixed states/noise but scale as 4^n."},
        {"scenario": "Dense arbitrary 120q statevector", "recommended": "not feasible", "why": "2^120 amplitudes cannot be stored or streamed on normal hardware."},
    ]


def explain_120_qubits_dense() -> str:
    est = dense_memory_estimate(120)
    return (
        "A true dense 120-qubit state has 2^120 complex amplitudes. "
        f"At complex128 precision, the memory estimate is {est.dense_human}; "
        "therefore Sansqrit avoids dense expansion unless the circuit is small. "
        "For large circuits it uses sparse maps, sharded maps, stabilizer tableau, "
        "MPS/tensor-network bonds, or independent 10-qubit hierarchical blocks."
    )


def lookup_architecture() -> dict[str, Any]:
    return {
        "packaged_files": [
            "sansqrit/data/lookup_static_gates.json",
            "sansqrit/data/lookup_two_qubit_static_gates.json",
            "sansqrit/data/lookup_embedded_single_upto_10.json.gz",
            "sansqrit/data/lookup_metadata.json",
        ],
        "runtime_policy": [
            "if n<=10 and static single-qubit gate: use embedded transition table",
            "else if static single-qubit gate: use 2x2 packaged matrix",
            "else if static two-qubit gate: use 4x4 packaged matrix",
            "else compute runtime matrix and optionally cache fused blocks",
        ],
        "limitation": "Lookup reduces constant factors but cannot remove exponential dense-state growth.",
    }


def package_positioning() -> dict[str, Any]:
    return {
        "honest_scope": "Sansqrit is an educational/research DSL and local simulator toolkit, not a replacement for production cloud accounts or calibrated hardware compilers.",
        "industry_alignment": [
            "OpenQASM 2/3 export",
            "Qiskit/Cirq/Braket/PennyLane adapters",
            "multiple simulator backends",
            "planner diagnostics",
            "QEC examples and logical abstractions",
            "hardware export payloads",
        ],
        "large_qubit_claim": "Supports 120+ logical qubit programs when the circuit remains sparse, Clifford-structured, low-entanglement, or decomposable into independent blocks.",
    }
