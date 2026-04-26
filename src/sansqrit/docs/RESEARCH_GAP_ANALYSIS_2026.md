# Sansqrit research gap analysis and implemented additions

This document summarizes research-informed gaps observed from current quantum tooling and how Sansqrit v0.3.3 addresses them.

## Observed industry patterns

- Multi-method simulators choose between statevector, density matrix, stabilizer, extended stabilizer and MPS-style methods.
- OpenQASM 3 is a major interchange language for modern quantum circuit workflows.
- Cloud providers expose Python SDKs or integrations rather than a single universal hardware submission API.
- QEC tooling often combines fast stabilizer simulation with specialized decoders such as MWPM.
- GPU/tensor-network tools accelerate selected dense or tensor workloads but cannot bypass exponential dense-state growth.

## Additions included

1. Architecture/estimator module with dense-memory estimates and execution-flow diagrams.
2. Diagnostics module with `doctor`, backend availability, troubleshooting and logging helpers.
3. Hardware export module with Qiskit, Cirq, Braket, Azure-style OpenQASM and PennyLane pathways.
4. AI/ML dataset helper module for JSONL training examples.
5. Optional QEC adapter points for Stim text output and PyMatching-style decoders.
6. Complete README and packaged `COMPLETE_ARCHITECTURE_AND_DSL_REFERENCE.md`.
7. Additional 120+ qubit examples using sparse, sharded, hierarchical, MPS and stabilizer-safe patterns.

## Honest limitations

- Built-in surface-code decoding remains educational unless optional external decoder objects are provided.
- Distributed sparse execution is correctness-first; HPC-grade MPI/Ray/Dask work remains future scope.
- Dense arbitrary 120-qubit statevector simulation is not feasible on ordinary local hardware.
- Cloud job submission still requires user-owned provider credentials and SDK configuration.
