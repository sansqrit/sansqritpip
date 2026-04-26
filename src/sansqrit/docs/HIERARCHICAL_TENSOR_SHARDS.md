# Sansqrit Hierarchical Tensor Shards

Version 0.3.3 adds a safe implementation of the common idea: **simulate a large logical register as many small dense blocks, then promote to a tensor network when blocks become entangled**.

## Why this exists

A 120-qubit dense state vector has `2^120` amplitudes, which is not physically practical on local hardware. However, many useful programs do not immediately create global dense entanglement. They contain local dynamics, independent blocks, sparse activity, or low-entanglement bridge operations.

The hierarchical backend exploits that structure.

```text
120 logical qubits
    ↓
12 local dense blocks of 10 qubits each
    ↓
local gates use dense 1024-amplitude vectors and packaged lookup matrices
    ↓
first cross-block entangling bridge promotes to MPS
    ↓
MPS tracks correlations with bond dimensions instead of one 2^120 vector
```

## Important correctness rule

Sansqrit does **not** blindly treat twelve 10-qubit blocks as independent after a cross-block gate. That would be wrong.

For example:

```sansqrit
cx q[9], q[10]
```

creates a bridge between block 0 and block 1. After this, the backend promotes into MPS mode so the correlation is represented accurately.

## Memory example

For `block_size=10`, one local block has:

```text
2^10 = 1024 complex amplitudes
1024 × 16 bytes ≈ 16 KiB with complex128
```

A 120-qubit separable block state has 12 blocks:

```text
12 × 16 KiB ≈ 192 KiB for raw block vectors
```

This is only valid while the global state factors across those blocks.

## DSL usage

```sansqrit
simulate(120, engine="hierarchical", block_size=10, max_bond_dim=null, cutoff=0.0) {
    q = quantum_register(120)

    shard block_A [0..9]
    shard block_B [10..19]

    apply H on block_A
    apply X on block_B

    # Cross-block bridge. This promotes the backend to MPS safely.
    apply CNOT on q[9], q[10] bridge_mode=sparse

    info = hierarchical_report()
    print(info)
}
```

Equivalent Python:

```python
from sansqrit import QuantumEngine

engine = QuantumEngine.create(120, backend="hierarchical", block_size=10, max_bond_dim=None, cutoff=0.0)
q = engine.quantum_register()
for i in range(10):
    engine.H(q[i])
for i in range(10, 20):
    engine.X(q[i])
engine.CNOT(q[9], q[10])
print(engine.hierarchical_report())
```

## Runtime modes

`mode="blocks"` means the state is still a product of dense local blocks.

`mode="mps"` means a bridge gate has created cross-block entanglement and the state was promoted to the MPS backend.

## Accuracy

Block mode is exact.

MPS bridge mode is exact if:

```text
max_bond_dim = None
cutoff = 0.0
```

If you set a finite bond dimension or nonzero cutoff, Sansqrit may truncate small singular values to save memory/time. That can be useful for approximation but is no longer exact.

## Lookup usage

Inside each 10-qubit block, static primitive gates use packaged lookup matrices:

```text
H, X, Y, Z, S, Sdg, T, Tdg, SX, SXdg
CNOT, CZ, CY, CH, CSX, SWAP, iSWAP, SqrtSWAP, fSWAP, DCX, ECR, MS
```

The backend reports lookup counters via:

```sansqrit
lookup_profile()
hierarchical_report()
```

## Recommended use cases

Good fits:

- 120+ qubit programs with local block dynamics.
- Independent 10-qubit components.
- Low-entanglement bridges between neighboring blocks.
- Real-time sparse/logical applications that should not materialize a global dense vector.
- Workloads where the programmer wants explicit block mapping.

Poor fits:

- Random all-to-all dense circuits.
- `h_all` followed by many nonlocal entanglers.
- Circuits with rapidly growing MPS bond dimension.

Use `engine="stabilizer"` for large Clifford-only circuits and `engine="sparse"` or `engine="sharded"` for oracle-style sparse state maps.
