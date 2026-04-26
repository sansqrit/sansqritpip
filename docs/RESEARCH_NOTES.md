# Research and Design Notes

Sansqrit Python follows common quantum SDK conventions while remaining intentionally lightweight.

## Packaging

The package uses a `pyproject.toml` and `src/` layout. This keeps import behavior closer to installed-package behavior and supports standard build frontends.

## QASM

Sansqrit exports OpenQASM 2 and OpenQASM 3 style text for common gates. Unsupported operations are emitted as comments rather than silently producing invalid QASM.

## Gate coverage

Gate names cover the original Rust Sansqrit gates plus common standard-library names: `CX`, `U1`, `U2`, `U3`, controlled rotations, `RXX/RYY/RZZ/RZX`, `ECR`, `MS`, `Toffoli/CCX`, `Fredkin/CSWAP`, `MCX/MCZ`, `C3X/C4X`.

## Sparse simulation

State is represented as a dictionary mapping basis integer to complex amplitude. This supports arbitrary qubit indexes but scales with the number of non-zero amplitudes.

## Sharding

Local sharding partitions the sparse state after each operation and preserves a single authoritative global state. This avoids the common bug where cross-shard gates lose amplitudes.

## Lookups

Lookup tables provide precomputed matrices and bit transitions for static gates. Parameterized gates are calculated on demand.

## Future work

- Process-based worker backend for CPU parallelism.
- Optional NumPy/SciPy kernels.
- Real multi-node shard orchestration.
- More complete OpenQASM 3 parser/importer.
- Noise models and density-matrix backend.
- Stabilizer backend for Clifford-heavy circuits.
