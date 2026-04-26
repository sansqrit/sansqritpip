# Sansqrit DSL Reference

Sansqrit source files use the `.sq` extension. The Python implementation translates Sansqrit into Python and runs it with Sansqrit quantum builtins. It is intended for trusted local programs.

## Program shape

```python
simulate(2) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    print(measure_all(q, shots=1000))
}
```

## Engine selection

```python
simulate(8, engine="sparse") { }
simulate(8, engine="sharded", n_shards=4, workers=2) { }
simulate(8, engine="threaded", workers=4) { }
```

## Variables

```python
let x = 1
const EPS = 1e-9
x += 1
x -= 1
x *= 2
x /= 2
```

## Literals

```python
true
false
None
1
1.5
"text"
[1, 2, 3]
{"key": "value"}
(1, 2)
```

## Functions

```python
fn square(x) {
    return x * x
}

let cube = fn(x) => x * x * x
```

## Pipelines

```python
let xs = [1, 2, 3, 4]
let ys = xs |> map(fn(x) => x * x)
let zs = ys |> filter(fn(x) => x > 4)
let total = zs |> sum
let folded = xs |> reduce(fn(a, b) => a + b)
```

## Control flow

```python
if x > 0 {
    print("positive")
} else if x == 0 {
    print("zero")
} else {
    print("negative")
}

for i in range(10) {
    print(i)
}

while error > 1e-6 {
    error = error / 2
}
```

## Quantum register

```python
let q = quantum_register(5)
q[0]
q[4]
```

Qubits are little-endian internally: `q[0]` is the least-significant bit. Displayed bitstrings are conventional most-significant-bit first.

## Gates

### Single-qubit

```python
I(q[0]); X(q[0]); Y(q[0]); Z(q[0]); H(q[0])
S(q[0]); Sdg(q[0]); T(q[0]); Tdg(q[0])
SX(q[0]); SXdg(q[0])
Rx(q[0], PI / 2); Ry(q[0], PI / 2); Rz(q[0], PI / 2)
Phase(q[0], PI / 4); U1(q[0], PI / 4)
U2(q[0], 0.1, 0.2); U3(q[0], 0.1, 0.2, 0.3)
```

### Two-qubit

```python
CNOT(q[0], q[1]); CX(q[0], q[1])
CZ(q[0], q[1]); CY(q[0], q[1]); CH(q[0], q[1])
CSX(q[0], q[1]); SWAP(q[0], q[1]); iSWAP(q[0], q[1])
SqrtSWAP(q[0], q[1]); fSWAP(q[0], q[1]); DCX(q[0], q[1])
CRx(q[0], q[1], PI/3); CRy(q[0], q[1], PI/3); CRz(q[0], q[1], PI/3)
CP(q[0], q[1], PI/3); CU(q[0], q[1], 0.1, 0.2, 0.3)
RXX(q[0], q[1], PI/4); RYY(q[0], q[1], PI/4); RZZ(q[0], q[1], PI/4)
RZX(q[0], q[1], PI/4); ECR(q[0], q[1]); MS(q[0], q[1])
```

### Three and multi-qubit

```python
Toffoli(q[0], q[1], q[2]); CCX(q[0], q[1], q[2])
Fredkin(q[0], q[1], q[2]); CSWAP(q[0], q[1], q[2])
CCZ(q[0], q[1], q[2])
MCX(q[0], q[1], q[2], q[3])
MCZ(q[0], q[1], q[2])
C3X(q[0], q[1], q[2], q[3])
C4X(q[0], q[1], q[2], q[3], q[4])
```

## Circuit helpers

```python
H_all()
Rx_all(PI / 4)
Ry_all(PI / 4)
Rz_all(PI / 4)
qft(q)
iqft(q)
```

## Measurement

```python
measure(q[0])
measure_all(q, shots=1000)
probabilities(q)
expectation_z(q[0])
expectation_zz(q[0], q[1])
engine_nnz()
shards()
```

## Algorithms

```python
grover_search(3, 5, shots=512)
grover_search_multi(4, [3, 12], shots=512)
shor_factor(15)
vqe_h2(0.735, max_iter=32)
qaoa_maxcut(4, [(0,1), (1,2), (2,3), (3,0)], p=1, shots=256)
quantum_phase_estimation(0.3125, 5, shots=256)
hhl_solve([[2, 0], [0, 4]], [2, 8])
bernstein_vazirani("101101")
simon_algorithm("101")
deutsch_jozsa(4, "balanced")
quantum_counting(6, 7, 5)
teleport(1)
superdense_coding(1, 0)
bb84_qkd(24, eavesdropper=false)
amplitude_estimation(0.37, 5)
variational_classifier([0.1, 0.5, 1.2], layers=3)
```

## I/O

```python
write_file("out.txt", "hello")
let text = read_file("out.txt")
write_json("data.json", {"shots": 1000})
let obj = read_json("data.json")
write_csv("data.csv", [{"gate": "H", "q": 0}])
let rows = read_csv("data.csv")
```


# Advanced backend syntax

```sansqrit
simulate(1000, engine="stabilizer") { H(0); CNOT(0, 999) }
simulate(64, engine="mps", max_bond_dim=128, cutoff=1e-12) { H(0) }
simulate(3, engine="density") { H(0); noise_depolarize(0, 0.01) }
simulate(20, engine="gpu") { H(0); CNOT(0, 1) }
```

Additional functions:

- `noise_depolarize(q, p)`
- `noise_bit_flip(q, p)`
- `noise_phase_flip(q, p)`
- `noise_amplitude_damping(q, gamma)`
- `engine_nnz()` for sparse nonzero count; stabilizer/MPS may return `-1` because they do not store computational-basis sparse amplitudes.

Use Python API for hybrid and cluster orchestration:

```python
Circuit(150).H(0).CNOT(0, 149).run(backend="hybrid")
DistributedSparseEngine.from_addresses(150, ["host1:8765", "host2:8765"])
```
