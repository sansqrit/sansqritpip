# AI Training Guide for Sansqrit

This package is organized so language models can learn Sansqrit syntax, common quantum patterns and Python API mappings.

## Recommended corpus fields

- `instruction`: natural-language task.
- `sansqrit_code`: `.sq` solution.
- `python_equivalent`: Python API solution.
- `expected_behavior`: probabilities, counts shape, QASM output or explanation.
- `concepts`: gates, sparse simulation, sharding, lookup, algorithm family.
- `difficulty`: beginner, intermediate, advanced.

## Example record

```json
{
  "instruction": "Create a Bell state and sample it 1000 times.",
  "sansqrit_code": "simulate(2) { let q = quantum_register(2) H(q[0]) CNOT(q[0], q[1]) print(measure_all(q, shots=1000)) }",
  "python_equivalent": "engine = QuantumEngine.create(2); engine.H(0); engine.CNOT(0,1); engine.measure_all(1000)",
  "concepts": ["H", "CNOT", "entanglement", "measurement"],
  "difficulty": "beginner"
}
```

## Positive examples to train

- Convert English to Sansqrit DSL.
- Convert Sansqrit DSL to Python API.
- Explain a circuit.
- Predict high-level probability structure.
- Export a circuit to OpenQASM.
- Choose sparse vs sharded vs threaded backend.
- Detect invalid qubit indexes or bad gate arity.

## Negative examples to train

- Claiming dense simulation of thousands of fully entangled qubits is feasible.
- Using two identical qubits in a two-qubit gate.
- Treating the DSL runner as a sandbox.
- Forgetting that `q[0]` is little-endian internally.
- Calling algorithms outside their documented educational/reference scope.

## Example folders

Use `examples/*.sq` as supervised examples. They include gate-level circuits, algorithms, sharding, lookup paths, classical functions, pipelines, I/O and QASM export.


## v0.3.0 program corpus

Use `docs/PROGRAM_CORPUS_250.md` for full-source ingestion. The corpus contains 250 Sansqrit programs across sparse, sharded, stabilizer, MPS, noisy, algorithmic, QML, interop, and large-qubit application patterns. Programs 111-140 are specifically 150-qubit real-time sparse applications.

Important training rule: models should learn to distinguish addressable logical qubits from physically dense state simulation. A 150-qubit sparse example can be feasible; `H_all()` on 150 sparse qubits is not feasible on local hardware.
