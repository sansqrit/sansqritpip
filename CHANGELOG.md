# Changelog

## 0.3.2 - QEC framework release

Author/maintainer metadata set to **Karthik V**.

Added:

- Dedicated `sansqrit.qec` module.
- QEC code registry: bit-flip, phase-flip, repetition, Shor 9, Steane 7, five-qubit perfect code, and surface-code helper layouts.
- `LogicalQubit` abstraction.
- Stabilizer syndrome extraction circuit generation.
- Syndrome measurement and correction pipeline.
- Decoder interface with repetition, lookup, and educational surface-code decoders.
- Logical gate helpers: logical X/Z/H/S/CNOT.
- QEC DSL runtime functions.
- Backend planner and lookup profile helper modules.
- QEC docs and examples.

Notes:

- The surface-code decoder is educational and interface-compatible, not a high-performance MWPM decoder.
- Dense arbitrary 120+ qubit simulation remains infeasible; use stabilizer/MPS/sparse-sharded planning.


## 0.4.0

- Added packaged precomputed lookup data under `sansqrit/data/`.
- Added static single-qubit 2x2 matrix JSON tables.
- Added static two-qubit 4x4 matrix JSON tables.
- Added gzipped embedded full-register transition tables for all static single-qubit gates on 1..10 qubits and every target position.
- Updated the sparse engine middle layer to use embedded lookup tables before arithmetic fallback.
- Added documentation and tests for packaged lookup files.

# Changelog

## 0.3.0

- Expanded the package README into a complete tutorial and reference.
- Added a 250-program Sansqrit example corpus across quantum algorithms, physics, chemistry, finance, cybersecurity, communications, robotics, climate, logistics, QML, stabilizer, MPS, sparse, noisy, hybrid, and distributed patterns.
- Added 150-qubit sparse real-time application examples that avoid dense expansion.
- Added full DSL syntax tables, backend selection guidance, AI/ML training notes, and PyPI publishing steps.
- Packaged examples and documentation inside the wheel for code-generation and AI tooling.

## 0.1.0

Initial Python package release.

- Sparse quantum state-vector backend.
- Local sharded backend and threaded single-qubit update path.
- Precomputed lookup table support for static one-qubit gates.
- Sansqrit `.sq` DSL translator and CLI.
- Circuit builder and OpenQASM 2/3 export.
- Gate set equivalent to the corrected Rust Sansqrit core plus common aliases.
- Reference algorithms and 100 example programs.
