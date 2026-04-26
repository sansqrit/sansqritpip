# Sansqrit Quantum Error Correction Framework

Sansqrit v0.3.2 adds a dedicated QEC layer for teaching, prototyping, AI training corpora, and small simulator validation. It includes code definitions, logical qubit objects, syndrome extraction circuits, decoder interfaces, logical gate helpers, and noise/correction examples.

## Included codes

| Code | Identifier | Physical qubits | Distance | Purpose |
|---|---:|---:|---:|---|
| 3-qubit bit-flip | `bit_flip` | 3 | 3 | Correct one X error |
| 3-qubit phase-flip | `phase_flip` | 3 | 3 | Correct one Z error |
| Repetition code | `repetition`, `repetition3`, `repetition5`, ... | odd d | d | Scalable repetition helper |
| Shor code | `shor9` | 9 | 3 | Classic bit+phase protection |
| Steane code | `steane7` | 7 | 3 | CSS stabilizer code |
| Five-qubit code | `five_qubit` | 5 | 3 | Perfect [[5,1,3]] code helper |
| Surface code | `surface`, `surface3`, ... | d² | d | Rotated planar layout helper |

## Python API

```python
from sansqrit import QuantumEngine
from sansqrit.qec import logical_qubit, encode, inject_error, syndrome_and_correct, decode

engine = QuantumEngine.create(5, backend="sparse")
logical = logical_qubit("bit_flip", base=0)
encode(engine, logical)
inject_error(engine, logical, "X", 1)
result = syndrome_and_correct(engine, logical, ancilla_base=3)
decode(engine, logical)
print(result.syndrome, result.corrections)
```

## Sansqrit DSL syntax

```sansqrit
simulate(5) {
  let q = quantum_register(5)
  let l = qec_logical("bit_flip", base=0)
  qec_encode(l)
  qec_inject_error(l, "X", 1)
  let result = qec_syndrome_and_correct(l, ancilla_base=3)
  qec_decode(l)
  let counts = measure_all(q)
}
```

## QEC functions exposed to the DSL

```text
qec_codes()
qec_code(name, distance=null)
qec_logical(code="bit_flip", base=0, name="logical", distance=null)
qec_encode(logical)
qec_decode(logical)
qec_syndrome(logical, ancilla_base=null)
qec_correct(logical, syndrome)
qec_syndrome_and_correct(logical, ancilla_base=null)
qec_inject_error(logical, pauli, physical_offset)
logical_x(logical)
logical_z(logical)
logical_h(logical)
logical_s(logical)
logical_cx(control_logical, target_logical)
qec_surface_lattice(distance=3)
qec_syndrome_circuit(logical, ancilla_base=null)
```

## Decoder interface

A decoder implements:

```python
class Decoder:
    def decode(self, code, syndrome):
        return [("X", 1), ("Z", 4)]
```

Sansqrit includes:

- `RepetitionDecoder`
- `LookupDecoder`
- `SurfaceCodeDecoder`

The included surface-code decoder is a greedy educational decoder. It is intentionally replaceable; production surface-code threshold research should plug in a specialized MWPM or union-find decoder through the same interface.

## Stabilizer syndrome extraction

`syndrome_circuit(logical)` returns gate tuples that extract each stabilizer onto an ancilla. Z checks use data-to-ancilla CNOTs. X checks use ancilla preparation/measurement in the X basis. This lets AI tools inspect how stabilizer checks are converted into circuits.

## Logical gate helpers

Sansqrit exposes logical Pauli and transversal helper gates:

```text
logical_x, logical_z, logical_h, logical_s, logical_cx
```

Where transversal gates are not universally valid for all codes, these helpers are educational primitives; code-specific fault-tolerant compilation should be added as later specialized passes.
