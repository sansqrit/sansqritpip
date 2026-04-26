# Python API Reference

## QuantumEngine

```python
from sansqrit import QuantumEngine
engine = QuantumEngine.create(n_qubits=5, backend="sparse")
```

Options:

- `backend`: `"sparse"`, `"sharded"`, or `"threaded"`.
- `n_shards`: local partition count for sharded mode.
- `workers`: worker thread count for large single-qubit transforms.
- `use_lookup`: use precomputed static-gate matrices.
- `seed`: deterministic sampling seed.

Core methods:

```python
engine.H(0)
engine.CNOT(0, 1)
engine.RZZ(1, 2, 0.5)
engine.H_all()
engine.qft([0, 1, 2])
engine.measure(0)
engine.measure_all(1000)
engine.probabilities()
engine.expectation_z(0)
engine.expectation_zz(0, 1)
engine.export_qasm2()
engine.export_qasm3()
engine.shard_info()
```

## Circuit

```python
from sansqrit import Circuit
c = Circuit(2).H(0).CNOT(0, 1)
engine = c.run()
counts = c.run(shots=1000)
print(c.qasm3())
```

## DSL runner

```python
from sansqrit import run_code, run_file, translate
run_file("program.sq")
print(translate(open("program.sq").read()))
```

## Algorithms module

```python
from sansqrit.algorithms import grover_search, qaoa_maxcut, vqe_h2
```

The algorithms module contains readable reference implementations and toy hybrid algorithms for examples, education and model training.


# Advanced Python APIs

```python
from sansqrit import Circuit, QuantumEngine, StabilizerEngine, DensityMatrixEngine
from sansqrit.mps import MPSEngine
from sansqrit.hybrid import HybridEngine
from sansqrit.cluster import DistributedSparseEngine
from sansqrit.optimizer import optimize_operations
from sansqrit.interop import to_qiskit, to_cirq, to_braket, apply_to_pennylane
from sansqrit.verification import verify_all_available
```

## Backends

- `QuantumEngine.create(n, backend="sparse")`
- `QuantumEngine.create(n, backend="sharded", n_shards=8)`
- `QuantumEngine.create(n, backend="threaded", workers=8)`
- `QuantumEngine.create(n, backend="stabilizer")`
- `QuantumEngine.create(n, backend="mps", max_bond_dim=128)`
- `QuantumEngine.create(n, backend="density")`
- `QuantumEngine.create(n, backend="gpu")`
- `QuantumEngine.create(n, backend="distributed", addresses=["host:8765"])`

## Optimizer

`optimized_ops, report = optimize_operations(circuit.operations)`

The report includes `before`, `after`, `removed`, and the set of passes used.

## Verification

`verify_all_available(circuit)` attempts Qiskit and Cirq comparisons if installed.
