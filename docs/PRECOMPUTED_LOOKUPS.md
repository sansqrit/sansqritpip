# Sansqrit Precomputed Lookup Tables

Sansqrit v0.4.0 ships precomputed lookup files inside the Python wheel under
`sansqrit/data/`.

Included files:

- `lookup_metadata.json` — table schema, version, and limits.
- `lookup_static_gates.json` — precomputed 2x2 matrices for all static single-qubit gates.
- `lookup_two_qubit_static_gates.json` — precomputed 4x4 matrices for all static two-qubit gates that do not need parameters.
- `lookup_embedded_single_upto_10.json.gz` — embedded basis-transition tables for every register size from 1 to 10 qubits, every target qubit position, and every static single-qubit gate.

## Why not every possible circuit product?

A phrase like "all possible matrix multiplications up to 10 qubits" can mean an
infinite or combinatorially explosive set. Parametric gates such as `Rx(theta)`
have continuous parameters, and even a finite static gate alphabet has an
astronomical number of possible circuit products as sequence length grows.

Sansqrit therefore packages the practical exhaustive tables:

1. Every static primitive matrix.
2. Every static primitive embedded single-qubit transition for n=1..10.
3. Static two-qubit primitive matrices.

Runtime then performs sequence fusion/caching and arithmetic fallback where the
state space or parameters make prepackaging impractical.

## Runtime lookup path

For `QuantumEngine.create(n, use_lookup=True)`:

- if `n <= 10` and the gate is static single-qubit, Sansqrit uses the packaged
  full-register transition table;
- if the gate is static two-qubit, Sansqrit uses the packaged 4x4 matrix;
- otherwise it computes the needed matrix at runtime.

For `n > 10`, Sansqrit still uses packaged primitive matrices but not full
embedded transition tables, because embedded full-register tables scale as
`2^n`.

## Inspect installed lookup data

```bash
python - <<'PY'
from importlib.resources import files
import sansqrit
root = files('sansqrit').joinpath('data')
for path in root.iterdir():
    print(path.name)
PY
```

```bash
python - <<'PY'
from sansqrit.lookup import packaged_metadata, DEFAULT_LOOKUP
print(packaged_metadata())
print(DEFAULT_LOOKUP.has_embedded_single(10, 7, 'H'))
PY
```
