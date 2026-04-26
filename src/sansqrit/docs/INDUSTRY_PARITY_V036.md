# Sansqrit v0.3.6 Industry-Parity Upgrade Notes

Author/Maintainer: **Karthik V**

This release adds a stronger adaptive execution planner, production-oriented distributed sparse execution APIs, optional Stim/PyMatching QEC bridges, GPU/cuQuantum capability adapters, richer OpenQASM 3 builders, and expanded conformance verification hooks.

## Why these features were added

Modern quantum platforms do not use one simulator for every circuit. They choose among dense state vectors, density matrices, stabilizer/tableau methods, matrix-product-state/tensor-network methods, GPU acceleration, hardware exports, and resource-estimation workflows. Sansqrit now exposes a comparable planning layer while keeping its simple DSL.

## Adaptive planner

Use:

```bash
sansqrit plan program.sq --json
```

or in DSL:

```sansqrit
print(plan_backend(120, [("H", [0], []), ("CNOT", [0, 1], [])]))
print(explain_backend(120, [("H", [0], []), ("CNOT", [0, 1], [])]))
```

The planner extracts:

- qubit count
- gate count
- Clifford/non-Clifford count
- estimated depth
- connected-component sizes
- cross-block bridge edges
- dense memory estimate
- density-matrix memory estimate
- sparse-amplitude estimate
- safe backend recommendation

Backend choices include:

- `sparse`
- `sharded`
- `sparse_sharded`
- `hierarchical`
- `mps`
- `stabilizer`
- `extended_stabilizer`
- `density`
- `gpu`
- `distributed`

## Distributed execution

Built-in TCP sparse workers support:

- compressed payloads
- batched gate application
- checkpoint/restore
- capability discovery
- optional Ray/Dask/MPI metadata hooks

Start workers:

```bash
sansqrit worker --host 0.0.0.0 --port 8765
```

Use from Python:

```python
from sansqrit.cluster import DistributedSparseEngine
eng = DistributedSparseEngine.from_addresses(120, [("worker1", 8765), ("worker2", 8765)])
eng.apply_batch([
    ("H", (0,), ()),
    ("CNOT", (0, 1), ()),
])
eng.checkpoint("./checkpoint")
```

This remains mathematically correct by keeping an authoritative sparse state. Large production clusters should add worker-local kernels and pairwise shard exchange for gate families whose partner amplitudes are colocated.

## GPU and cuQuantum layer

Use:

```bash
sansqrit gpu --qubits 28 --type dense
```

DSL:

```sansqrit
print(gpu_capabilities())
print(cuquantum_recommendation(28, "dense"))
```

The package does not hard-depend on CUDA. It detects:

- CuPy
- cuQuantum
- cuStateVec target
- cuTensorNet target
- cuDensityMat target

## OpenQASM 3 advanced support

Sansqrit now includes a text builder for:

- mid-circuit measurements
- classical bit control
- delays/timing
- barriers
- pragmas
- extern declarations
- calibration blocks

DSL:

```sansqrit
print(qasm3_mid_circuit_template(2))
```

Python:

```python
from sansqrit.qasm import Qasm3Builder
print(Qasm3Builder(2).gate("h", [0]).measure(0, 0).if_bit(0, 1, "x q[1];").text())
```

## QEC production bridges

Sansqrit adds optional integrations and planning utilities:

```sansqrit
print(qec_stim_surface_task(3, 3, 0.001))
print(qec_threshold_sweep())
print(qec_logical_resource_estimate(100, 1000, 5, 10))
```

It supports built-in educational codes and external production pathways:

- bit-flip
- phase-flip
- repetition codes
- Shor 9-qubit
- Steane 7-qubit
- 5-qubit perfect code
- surface-code lattice helpers
- Stim generated surface-code memory experiments when Stim is installed
- PyMatching-compatible MWPM adapter when a matching graph is supplied

## Formal verification

The verification layer now attempts:

- Qiskit probability comparison
- Cirq probability comparison
- Braket local simulator/export check
- Stim Clifford parse check

CLI:

```bash
sansqrit verify program.sq
```

DSL:

```sansqrit
simulate(2) {
    q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    print(conformance_report())
}
```

## Large 120+ qubit design rule

For 120+ qubits, Sansqrit avoids false dense claims. It chooses:

- stabilizer for Clifford-only circuits
- extended-stabilizer for mostly Clifford circuits
- hierarchical tensor shards when components are <=10 qubits
- MPS when cross-block entanglement is limited
- sparse/sharded/distributed when active amplitudes stay sparse
- hardware export when classical simulation is not appropriate

Dense 120-qubit state-vector simulation remains physically infeasible because it requires `2^120` amplitudes.
