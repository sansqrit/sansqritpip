# Sansqrit v0.3.4/v0.3.5 Design and Bug Audit

Author/maintainer metadata: **Karthik V**

Audit date: 2026-04-26

## Executive summary

I tested the latest Sansqrit package and found that the overall architecture is directionally good: sparse + sharded + lookup + hierarchical tensor shards + MPS + stabilizer + QEC + hardware export is the right high-level design for a large-logical-qubit DSL.

However, the v0.3.4 package should not be treated as production-complete. I found three concrete correctness/release issues and fixed them in the rebuilt v0.3.5 package:

1. MPS non-adjacent two-qubit gates were wrong when the first qubit index was greater than the second, e.g. `CNOT(3, 0)`.
2. `export_hardware("pennylane")` raised an exception when PennyLane was not installed, while other providers returned a QASM fallback.
3. Distributed TCP worker request threads could keep waiting for more input, making some subprocess-style tests hang after use.

I also updated metadata/dependency policy in v0.3.5:

- version bumped to `0.3.5`;
- author/maintainer kept as `Karthik V`;
- core dependency changed to include `numpy>=1.26`, because MPS/hierarchical functionality is advertised as a primary feature;
- placeholder `example.com` project URLs replaced with PyPI links;
- wheel metadata retains optional extras for Qiskit, Cirq, Braket, PennyLane, GPU, Stim, and PyMatching.

## Test results

### v0.3.4 baseline tests

- Included test suite: 23 tests passed, 0 failed.
- Python source compilation: passed.
- Example translation/compilation: 800 examples compiled, 0 failed.
- Example execution: 797 examples passed, 3 failed.

The 3 failing examples were:

- `745_scenario_hardware_calibration_05.sq`
- `751_scenario_hardware_calibration_11.sq`
- `757_scenario_hardware_calibration_17.sq`

Cause: each example called `export_hardware("pennylane")`; without PennyLane installed, the package raised `QuantumError` instead of returning a fallback payload.

### Extra audit tests beyond bundled tests

I added targeted checks not covered by the original test suite:

- Sparse vs sharded equivalence on a mixed 6-qubit circuit.
- MPS vs sparse equivalence for non-adjacent `CNOT(3, 0)`.
- MPS vs sparse equivalence on a mixed circuit with non-adjacent CNOT, SWAP, RZZ, Ry.
- Hierarchical bridge promotion sanity.
- 150-qubit sparse/sharded state sanity.
- Wheel content inspection.
- Training/scenario dataset manifest and count checks.

### v0.3.5 fixed package validation

- Included test suite: 23 tests passed, 0 failed.
- Example translation/compilation: 800 examples compiled, 0 failed.
- Former PennyLane-failing examples: all passed with fallback payloads.
- MPS reversed non-adjacent CNOT test: passed.
- Mixed MPS vs sparse test: passed.
- Wheel contains:
  - 34 Python modules
  - 800 packaged `.sq` examples
  - 19 packaged markdown docs
  - 10 packaged data/training/lookup files
  - no `__pycache__` or `.pyc` files

`twine check` was not run because `twine` is not installed in this container.

## Bugs fixed in v0.3.5

### 1. MPS non-adjacent reversed two-qubit gates

Problem:

```sansqrit
q = quantum_register(4)
H(q[3])
CNOT(q[3], q[0])
```

The MPS backend produced the wrong target correlation when `q0 > q1` and the two sites were non-adjacent.

Fix:

- transform the 4x4 matrix into swapped site order with `SWAP @ U @ SWAP`;
- then reuse the left-to-right MPS two-site path.

### 2. PennyLane export fallback

Problem:

```sansqrit
print(export_hardware("pennylane"))
```

raised an exception when PennyLane was missing.

Fix:

- PennyLane now matches Qiskit/Cirq/Braket behavior:
  - use native adapter when installed;
  - otherwise return an OpenQASM 3 fallback payload plus install hint.

### 3. Distributed worker subprocess hang risk

Problem:

The TCP worker request handler could continue waiting for additional input on the same request connection.

Fix:

- worker server now has `daemon_threads = True`;
- client calls `sock.shutdown(socket.SHUT_WR)` after sending one JSON request.

## Design analysis

## What is strong

### Sparse + sharded is the right foundation

Sansqrit correctly avoids claiming arbitrary dense 120-qubit simulation. Sparse state maps plus sharding are appropriate for large logical registers when the active amplitude count remains small.

### Hierarchical 10-qubit blocks are valid with a bridge rule

The hierarchical tensor-shard strategy is mathematically valid when:

- local operations stay inside independent 10-qubit blocks; and
- cross-block gates promote the representation to MPS/tensor-network form instead of pretending the blocks remain independent.

The package follows this direction.

### Lookup files are useful but should be treated as a middle-layer accelerator

The packaged lookup files are appropriate for:

- static single-qubit matrices;
- static two-qubit matrices;
- embedded <=10-qubit transition tables;
- small block accelerators.

They cannot make arbitrary dense 120-qubit simulation feasible.

### QEC module is useful for education and AI training

The QEC module includes logical qubits, code registries, syndrome extraction helpers, and decoder interfaces. This is useful, but the built-in surface-code decoder should remain labelled educational unless a full MWPM graph is implemented.

## What is still missing for industry-grade parity

### 1. True adaptive backend planner

Current planning is useful but should become mandatory for `engine("auto")`.

Add:

- estimated active amplitudes;
- Clifford/non-Clifford count;
- T-count/magic-state cost;
- entanglement graph;
- MPS bond-dimension estimate;
- memory estimate;
- backend decision explanation;
- safe refusal for impossible dense runs.

### 2. Real distributed execution plan

Current distributed mode is correctness-first and coordinator-driven. For real cluster performance, add:

- worker-local single-qubit gate execution;
- pairwise shard exchange for cross-shard two-qubit gates;
- batched gate execution;
- compressed amplitude transfer;
- checkpoint/restart;
- optional Ray/Dask/MPI transport.

### 3. Production QEC decoder

Add real surface-code decoding:

- construct detector graph from syndrome circuits;
- integrate PyMatching MWPM directly;
- support repeated syndrome rounds;
- support circuit-level noise;
- support logical error-rate estimation;
- export Stim detector-error models.

### 4. Formal cross-simulator verification

Add optional validation suites:

- compare small circuits against Qiskit Aer;
- compare Clifford/QEC circuits against Stim;
- compare MPS low-entanglement circuits against dense sparse/statevector for <=20 qubits;
- compare QASM export/import round trips.

### 5. Stronger OpenQASM 3 support

The exporter should eventually support:

- mid-circuit measurement;
- classical control;
- timing/delay/duration;
- calibration blocks;
- extern declarations;
- hardware-native gate set decomposition.

### 6. Benchmark suite

Add repeatable benchmarks:

- sparse 150q oracle;
- 1000q stabilizer Clifford graph;
- MPS 500q chain;
- QEC surface-code d=3/d=5;
- 20–30q dense statevector;
- lookup-hit benchmark;
- distributed sparse benchmark.

### 7. Lookup block compiler

The next improvement for lookup speed is not packaging every possible circuit. It is:

- detect static <=10-qubit blocks;
- fuse gates;
- hash the block;
- generate/cache the fused unitary or transition map;
- reuse across runs.

### 8. Data-quality tooling for AI training

The synthetic dataset should add quality gates:

- JSON schema validation;
- duplicates/near-duplicates report;
- code execution result attached to records;
- backend label verification;
- rejected-output taxonomy;
- eval set with hidden answers;
- citation/license metadata.

## Recommendation before PyPI upload

Upload the fixed package as `0.3.5`, not `0.3.4`, if `0.3.4` has already been uploaded.

Run locally before upload:

```bash
python -m pip install --upgrade build twine
python -m twine check dist/*
python -m twine upload dist/*
```

Then verify:

```bash
python -m venv /tmp/sansqrit-check
source /tmp/sansqrit-check/bin/activate
pip install sansqrit==0.3.5
sansqrit doctor
sansqrit dataset info
sansqrit scenarios info
python - <<'PY'
from sansqrit import QuantumEngine
e = QuantumEngine.create(2)
e.H(0)
e.CNOT(0, 1)
print(e.probabilities())
PY
```

## Final status

The v0.3.5 package is safer to upload than the v0.3.4 package because it fixes the concrete MPS, hardware-export, and distributed-worker issues found during the audit.

The design is promising, but for claims like "on par with Qiskit/Azure/AWS," the package should be described as an alpha/research DSL with multiple execution strategies, not yet a production cloud runtime or calibrated hardware compiler.
