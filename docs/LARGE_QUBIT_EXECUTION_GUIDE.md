# Large-qubit execution guide

## 120+ logical qubits

Use large qubit counts only with structure-aware modes:

- `sparse` when active amplitudes stay small.
- `sharded` when active amplitudes should be partitioned.
- `hierarchical` when the circuit decomposes into <=10-qubit blocks.
- `mps` when entanglement is local/low.
- `stabilizer` for Clifford circuits.
- `density` only for small noisy circuits.
- `gpu` for small/medium dense vectors if CuPy/CUDA is installed.
- `distributed` for sparse shard orchestration.

## Dense warning

`H_all` on 120 non-stabilizer statevector qubits is not feasible as a dense vector.

## Diagnostics

```bash
sansqrit estimate 120
sansqrit architecture
sansqrit doctor
```

Inside DSL:

```sansqrit
print(estimate_qubits(120))
print(explain_120_qubits_dense())
print(lookup_profile())
```
