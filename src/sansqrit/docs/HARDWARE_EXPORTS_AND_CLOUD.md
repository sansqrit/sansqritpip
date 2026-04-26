# Hardware exports and cloud-provider workflows

Sansqrit can export circuit payloads but does not manage cloud credentials.

## Built-in export paths

- `export_qasm2()`
- `export_qasm3()`
- `export_hardware("qiskit")`
- `export_hardware("ibm")`
- `export_hardware("cirq")`
- `export_hardware("braket")`
- `export_hardware("azure")`
- `export_hardware("pennylane")`
- `hardware_targets()`
- `hardware_payload_summary()`

## Qiskit / IBM

Install:

```bash
pip install "sansqrit[qiskit]"
```

Use `export_hardware("qiskit")` for a `QuantumCircuit` when Qiskit is installed. Otherwise Sansqrit returns an OpenQASM 3 fallback payload.

## Amazon Braket

Install:

```bash
pip install "sansqrit[braket]"
```

Use `export_hardware("braket")` for a Braket `Circuit` when the SDK is installed.

## Azure Quantum

Sansqrit emits an OpenQASM 3/Azure-style payload. Submit it using your QDK, Qiskit or Cirq Azure workflow.

## PennyLane

Install:

```bash
pip install "sansqrit[pennylane]"
```

Use `export_hardware("pennylane")` to get a callable quantum function that can be wrapped by a PennyLane QNode.
