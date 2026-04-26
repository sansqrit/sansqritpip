# Sansqrit 0.3.6 Validation Report

Author/maintainer: Karthik V

## Completed checks in this environment

- Python source syntax compilation passed for all `src/sansqrit/*.py` modules.
- DSL translation/compilation passed for all 820 root `.sq` examples.
- Targeted smoke checks passed for the adaptive planner, GPU/cuQuantum planning helpers, advanced OpenQASM 3 template generation, distributed capability reporting, QEC Stim/PyMatching planning helpers, and formal verification report scaffolding.
- The wheel archive was tested with `unzip -t` and reported no compressed-data errors.
- The wheel contains 820 packaged `.sq` examples, 21 packaged Markdown docs, training/scenario datasets, and lookup data files.

## Optional integration checks

The following are adapter-level in this build environment and require optional extras plus user credentials/hardware to execute end-to-end:

- Qiskit / Qiskit Aer
- Cirq / qsim
- Amazon Braket
- Azure Quantum
- PennyLane
- Stim
- PyMatching
- Ray / Dask / MPI
- CuPy / NVIDIA cuQuantum

Install extras such as `sansqrit[qiskit]`, `sansqrit[braket]`, `sansqrit[qec]`, `sansqrit[cuquantum]`, or `sansqrit[all]` in a normal development environment for provider-level conformance tests.
