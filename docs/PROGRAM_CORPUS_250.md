# Sansqrit 250-Program Training Corpus

Each program is also available as an executable `.sq` file under `examples/` and `sansqrit/examples/` inside the wheel.

## 001_bell_state.sq

```sansqrit
# Bell state with sparse simulation
simulate(2) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    let probs = probabilities(q)
    print(probs)
    print(measure_all(q, shots=512))
}
```

## 002_ghz_chain_8.sq

```sansqrit
# 8-qubit GHZ state
simulate(8, engine="sparse") {
    let q = quantum_register(8)
    H(q[0])
    for i in range(7) {
        CNOT(q[i], q[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=512))
}
```

## 003_qft_three_qubits.sq

```sansqrit
simulate(3) {
    let q = quantum_register(3)
    X(q[0])
    qft(q)
    print(probabilities(q))
}
```

## 004_inverse_qft_roundtrip.sq

```sansqrit
simulate(4) {
    let q = quantum_register(4)
    X(q[0])
    X(q[2])
    qft(q)
    iqft(q)
    print(probabilities(q))
}
```

## 005_sharded_bell.sq

```sansqrit
simulate(2, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    print(shards())
    print(measure_all(q, shots=256))
}
```

## 006_threaded_superposition.sq

```sansqrit
simulate(12, engine="threaded", workers=4) {
    let q = quantum_register(12)
    H_all()
    Rz_all(PI / 8)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 007_lookup_sx_inverse.sq

```sansqrit
simulate(1) {
    let q = quantum_register(1)
    SX(q[0])
    SXdg(q[0])
    print(probabilities(q))
}
```

## 008_toffoli_adder_bit.sq

```sansqrit
simulate(3) {
    let q = quantum_register(3)
    X(q[0])
    X(q[1])
    Toffoli(q[0], q[1], q[2])
    print(probabilities(q))
}
```

## 009_fredkin_swap.sq

```sansqrit
simulate(3) {
    let q = quantum_register(3)
    X(q[0])
    X(q[1])
    Fredkin(q[0], q[1], q[2])
    print(probabilities(q))
}
```

## 010_rzz_entangler.sq

```sansqrit
simulate(2) {
    let q = quantum_register(2)
    H(q[0])
    H(q[1])
    RZZ(q[0], q[1], PI / 3)
    print(probabilities(q))
}
```

## 011_ms_gate.sq

```sansqrit
simulate(2) {
    let q = quantum_register(2)
    MS(q[0], q[1])
    print(probabilities(q))
}
```

## 012_qasm_export.sq

```sansqrit
simulate(2) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    let text = export_qasm3()
    print(text)
}
```

## 013_pipeline_statistics.sq

```sansqrit
let xs = [1, 2, 3, 4, 5, 6]
let squares = xs |> map(fn(x) => x * x)
let big = squares |> filter(fn(x) => x > 10)
let total = big |> sum
print(squares)
print(big)
print(total)
```

## 014_classical_function.sq

```sansqrit
fn energy(theta) {
    return -cos(theta) + 0.1 * sin(2 * theta)
}
let values = [energy(x * PI / 16) for x in range(16)]
print(values)
print(min(values))
```

## 015_json_csv_io.sq

```sansqrit
let rows = [{"gate": "H", "qubit": 0}, {"gate": "CNOT", "qubit": 1}]
write_json("sansqrit_example.json", {"rows": rows, "shots": 128})
let payload = read_json("sansqrit_example.json")
print(payload)
```

## 016_grover_search.sq

```sansqrit
let result = grover_search(3, 5, shots=512)
print(result)
```

## 017_grover_multi.sq

```sansqrit
let result = grover_search_multi(4, [3, 12], shots=512)
print(result)
```

## 018_bernstein_vazirani.sq

```sansqrit
let secret = bernstein_vazirani("101101")
print(secret)
```

## 019_deutsch_jozsa_balanced.sq

```sansqrit
let result = deutsch_jozsa(4, "balanced")
print(result)
```

## 020_deutsch_jozsa_constant.sq

```sansqrit
let result = deutsch_jozsa(4, "constant")
print(result)
```

## 021_qaoa_triangle.sq

```sansqrit
let result = qaoa_maxcut(3, [(0,1), (1,2), (0,2)], p=1, shots=256)
print(result)
```

## 022_qaoa_square.sq

```sansqrit
let result = qaoa_maxcut(4, [(0,1), (1,2), (2,3), (3,0)], p=1, shots=256)
print(result)
```

## 023_vqe_h2.sq

```sansqrit
let result = vqe_h2(0.735, max_iter=32)
print(result)
```

## 024_phase_estimation.sq

```sansqrit
let result = quantum_phase_estimation(0.3125, 5, shots=256)
print(result)
```

## 025_hhl_2x2.sq

```sansqrit
let result = hhl_solve([[2, 0], [0, 4]], [2, 8])
print(result)
```

## 026_teleport_one.sq

```sansqrit
let result = teleport(1)
print(result)
```

## 027_superdense_coding.sq

```sansqrit
let result = superdense_coding(1, 0)
print(result)
```

## 028_bb84_qkd.sq

```sansqrit
let key = bb84_qkd(24, eavesdropper=false)
print(key)
```

## 029_bb84_with_eavesdropper.sq

```sansqrit
let key = bb84_qkd(24, eavesdropper=true)
print(key)
```

## 030_shor_factor_15.sq

```sansqrit
let factors = shor_factor(15)
print(factors)
```

## 031_amplitude_estimation.sq

```sansqrit
let estimate = amplitude_estimation(0.37, 5)
print(estimate)
```

## 032_quantum_counting.sq

```sansqrit
let estimate = quantum_counting(6, 7, 5)
print(estimate)
```

## 033_variational_classifier.sq

```sansqrit
let score = variational_classifier([0.1, 0.5, 1.2], layers=3)
print(score)
```

## 034_variational_pattern_34.sq

```sansqrit
# Generated variational circuit pattern 34
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Ry(q[0], PI / 8)
    Rz(q[1], PI / 2)
    Rx(q[2], PI / 3)
    Ry(q[3], PI / 4)
    Rz(q[4], PI / 5)
    Rx(q[5], PI / 6)
    Ry(q[6], PI / 7)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    # layer 1
    Rz(q[0], PI / 2)
    Rx(q[1], PI / 3)
    Ry(q[2], PI / 4)
    Rz(q[3], PI / 5)
    Rx(q[4], PI / 6)
    Ry(q[5], PI / 7)
    Rz(q[6], PI / 8)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 035_variational_pattern_35.sq

```sansqrit
# Generated variational circuit pattern 35
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Rz(q[0], PI / 2)
    Rx(q[1], PI / 3)
    Ry(q[2], PI / 4)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    # layer 1
    Rx(q[0], PI / 3)
    Ry(q[1], PI / 4)
    Rz(q[2], PI / 5)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    # layer 2
    Ry(q[0], PI / 4)
    Rz(q[1], PI / 5)
    Rx(q[2], PI / 6)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 036_variational_pattern_36.sq

```sansqrit
# Generated variational circuit pattern 36
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Rx(q[0], PI / 3)
    Ry(q[1], PI / 4)
    Rz(q[2], PI / 5)
    Rx(q[3], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 037_variational_pattern_37.sq

```sansqrit
# Generated variational circuit pattern 37
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Ry(q[0], PI / 4)
    Rz(q[1], PI / 5)
    Rx(q[2], PI / 6)
    Ry(q[3], PI / 7)
    Rz(q[4], PI / 8)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    # layer 1
    Rz(q[0], PI / 5)
    Rx(q[1], PI / 6)
    Ry(q[2], PI / 7)
    Rz(q[3], PI / 8)
    Rx(q[4], PI / 2)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 038_variational_pattern_38.sq

```sansqrit
# Generated variational circuit pattern 38
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Rz(q[0], PI / 5)
    Rx(q[1], PI / 6)
    Ry(q[2], PI / 7)
    Rz(q[3], PI / 8)
    Rx(q[4], PI / 2)
    Ry(q[5], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    # layer 1
    Rx(q[0], PI / 6)
    Ry(q[1], PI / 7)
    Rz(q[2], PI / 8)
    Rx(q[3], PI / 2)
    Ry(q[4], PI / 3)
    Rz(q[5], PI / 4)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    # layer 2
    Ry(q[0], PI / 7)
    Rz(q[1], PI / 8)
    Rx(q[2], PI / 2)
    Ry(q[3], PI / 3)
    Rz(q[4], PI / 4)
    Rx(q[5], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 039_variational_pattern_39.sq

```sansqrit
# Generated variational circuit pattern 39
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Rx(q[0], PI / 6)
    Ry(q[1], PI / 7)
    Rz(q[2], PI / 8)
    Rx(q[3], PI / 2)
    Ry(q[4], PI / 3)
    Rz(q[5], PI / 4)
    Rx(q[6], PI / 5)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 040_variational_pattern_40.sq

```sansqrit
# Generated variational circuit pattern 40
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Ry(q[0], PI / 7)
    Rz(q[1], PI / 8)
    Rx(q[2], PI / 2)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    # layer 1
    Rz(q[0], PI / 8)
    Rx(q[1], PI / 2)
    Ry(q[2], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 041_variational_pattern_41.sq

```sansqrit
# Generated variational circuit pattern 41
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Rz(q[0], PI / 8)
    Rx(q[1], PI / 2)
    Ry(q[2], PI / 3)
    Rz(q[3], PI / 4)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    # layer 1
    Rx(q[0], PI / 2)
    Ry(q[1], PI / 3)
    Rz(q[2], PI / 4)
    Rx(q[3], PI / 5)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    # layer 2
    Ry(q[0], PI / 3)
    Rz(q[1], PI / 4)
    Rx(q[2], PI / 5)
    Ry(q[3], PI / 6)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 042_variational_pattern_42.sq

```sansqrit
# Generated variational circuit pattern 42
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Rx(q[0], PI / 2)
    Ry(q[1], PI / 3)
    Rz(q[2], PI / 4)
    Rx(q[3], PI / 5)
    Ry(q[4], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 043_variational_pattern_43.sq

```sansqrit
# Generated variational circuit pattern 43
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Ry(q[0], PI / 3)
    Rz(q[1], PI / 4)
    Rx(q[2], PI / 5)
    Ry(q[3], PI / 6)
    Rz(q[4], PI / 7)
    Rx(q[5], PI / 8)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    # layer 1
    Rz(q[0], PI / 4)
    Rx(q[1], PI / 5)
    Ry(q[2], PI / 6)
    Rz(q[3], PI / 7)
    Rx(q[4], PI / 8)
    Ry(q[5], PI / 2)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 044_variational_pattern_44.sq

```sansqrit
# Generated variational circuit pattern 44
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Rz(q[0], PI / 4)
    Rx(q[1], PI / 5)
    Ry(q[2], PI / 6)
    Rz(q[3], PI / 7)
    Rx(q[4], PI / 8)
    Ry(q[5], PI / 2)
    Rz(q[6], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    # layer 1
    Rx(q[0], PI / 5)
    Ry(q[1], PI / 6)
    Rz(q[2], PI / 7)
    Rx(q[3], PI / 8)
    Ry(q[4], PI / 2)
    Rz(q[5], PI / 3)
    Rx(q[6], PI / 4)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    # layer 2
    Ry(q[0], PI / 6)
    Rz(q[1], PI / 7)
    Rx(q[2], PI / 8)
    Ry(q[3], PI / 2)
    Rz(q[4], PI / 3)
    Rx(q[5], PI / 4)
    Ry(q[6], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 045_variational_pattern_45.sq

```sansqrit
# Generated variational circuit pattern 45
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Rx(q[0], PI / 5)
    Ry(q[1], PI / 6)
    Rz(q[2], PI / 7)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 046_variational_pattern_46.sq

```sansqrit
# Generated variational circuit pattern 46
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Ry(q[0], PI / 6)
    Rz(q[1], PI / 7)
    Rx(q[2], PI / 8)
    Ry(q[3], PI / 2)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    # layer 1
    Rz(q[0], PI / 7)
    Rx(q[1], PI / 8)
    Ry(q[2], PI / 2)
    Rz(q[3], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 047_variational_pattern_47.sq

```sansqrit
# Generated variational circuit pattern 47
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Rz(q[0], PI / 7)
    Rx(q[1], PI / 8)
    Ry(q[2], PI / 2)
    Rz(q[3], PI / 3)
    Rx(q[4], PI / 4)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    # layer 1
    Rx(q[0], PI / 8)
    Ry(q[1], PI / 2)
    Rz(q[2], PI / 3)
    Rx(q[3], PI / 4)
    Ry(q[4], PI / 5)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    # layer 2
    Ry(q[0], PI / 2)
    Rz(q[1], PI / 3)
    Rx(q[2], PI / 4)
    Ry(q[3], PI / 5)
    Rz(q[4], PI / 6)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 048_variational_pattern_48.sq

```sansqrit
# Generated variational circuit pattern 48
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Rx(q[0], PI / 8)
    Ry(q[1], PI / 2)
    Rz(q[2], PI / 3)
    Rx(q[3], PI / 4)
    Ry(q[4], PI / 5)
    Rz(q[5], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 049_variational_pattern_49.sq

```sansqrit
# Generated variational circuit pattern 49
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Ry(q[0], PI / 2)
    Rz(q[1], PI / 3)
    Rx(q[2], PI / 4)
    Ry(q[3], PI / 5)
    Rz(q[4], PI / 6)
    Rx(q[5], PI / 7)
    Ry(q[6], PI / 8)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    # layer 1
    Rz(q[0], PI / 3)
    Rx(q[1], PI / 4)
    Ry(q[2], PI / 5)
    Rz(q[3], PI / 6)
    Rx(q[4], PI / 7)
    Ry(q[5], PI / 8)
    Rz(q[6], PI / 2)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 050_variational_pattern_50.sq

```sansqrit
# Generated variational circuit pattern 50
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Rz(q[0], PI / 3)
    Rx(q[1], PI / 4)
    Ry(q[2], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    # layer 1
    Rx(q[0], PI / 4)
    Ry(q[1], PI / 5)
    Rz(q[2], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    # layer 2
    Ry(q[0], PI / 5)
    Rz(q[1], PI / 6)
    Rx(q[2], PI / 7)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 051_variational_pattern_51.sq

```sansqrit
# Generated variational circuit pattern 51
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Rx(q[0], PI / 4)
    Ry(q[1], PI / 5)
    Rz(q[2], PI / 6)
    Rx(q[3], PI / 7)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 052_variational_pattern_52.sq

```sansqrit
# Generated variational circuit pattern 52
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Ry(q[0], PI / 5)
    Rz(q[1], PI / 6)
    Rx(q[2], PI / 7)
    Ry(q[3], PI / 8)
    Rz(q[4], PI / 2)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    # layer 1
    Rz(q[0], PI / 6)
    Rx(q[1], PI / 7)
    Ry(q[2], PI / 8)
    Rz(q[3], PI / 2)
    Rx(q[4], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 053_variational_pattern_53.sq

```sansqrit
# Generated variational circuit pattern 53
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Rz(q[0], PI / 6)
    Rx(q[1], PI / 7)
    Ry(q[2], PI / 8)
    Rz(q[3], PI / 2)
    Rx(q[4], PI / 3)
    Ry(q[5], PI / 4)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    # layer 1
    Rx(q[0], PI / 7)
    Ry(q[1], PI / 8)
    Rz(q[2], PI / 2)
    Rx(q[3], PI / 3)
    Ry(q[4], PI / 4)
    Rz(q[5], PI / 5)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    # layer 2
    Ry(q[0], PI / 8)
    Rz(q[1], PI / 2)
    Rx(q[2], PI / 3)
    Ry(q[3], PI / 4)
    Rz(q[4], PI / 5)
    Rx(q[5], PI / 6)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 054_variational_pattern_54.sq

```sansqrit
# Generated variational circuit pattern 54
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Rx(q[0], PI / 7)
    Ry(q[1], PI / 8)
    Rz(q[2], PI / 2)
    Rx(q[3], PI / 3)
    Ry(q[4], PI / 4)
    Rz(q[5], PI / 5)
    Rx(q[6], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 055_variational_pattern_55.sq

```sansqrit
# Generated variational circuit pattern 55
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Ry(q[0], PI / 8)
    Rz(q[1], PI / 2)
    Rx(q[2], PI / 3)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    # layer 1
    Rz(q[0], PI / 2)
    Rx(q[1], PI / 3)
    Ry(q[2], PI / 4)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 056_variational_pattern_56.sq

```sansqrit
# Generated variational circuit pattern 56
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Rz(q[0], PI / 2)
    Rx(q[1], PI / 3)
    Ry(q[2], PI / 4)
    Rz(q[3], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    # layer 1
    Rx(q[0], PI / 3)
    Ry(q[1], PI / 4)
    Rz(q[2], PI / 5)
    Rx(q[3], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    # layer 2
    Ry(q[0], PI / 4)
    Rz(q[1], PI / 5)
    Rx(q[2], PI / 6)
    Ry(q[3], PI / 7)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 057_variational_pattern_57.sq

```sansqrit
# Generated variational circuit pattern 57
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Rx(q[0], PI / 3)
    Ry(q[1], PI / 4)
    Rz(q[2], PI / 5)
    Rx(q[3], PI / 6)
    Ry(q[4], PI / 7)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 058_variational_pattern_58.sq

```sansqrit
# Generated variational circuit pattern 58
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Ry(q[0], PI / 4)
    Rz(q[1], PI / 5)
    Rx(q[2], PI / 6)
    Ry(q[3], PI / 7)
    Rz(q[4], PI / 8)
    Rx(q[5], PI / 2)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    # layer 1
    Rz(q[0], PI / 5)
    Rx(q[1], PI / 6)
    Ry(q[2], PI / 7)
    Rz(q[3], PI / 8)
    Rx(q[4], PI / 2)
    Ry(q[5], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 059_variational_pattern_59.sq

```sansqrit
# Generated variational circuit pattern 59
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Rz(q[0], PI / 5)
    Rx(q[1], PI / 6)
    Ry(q[2], PI / 7)
    Rz(q[3], PI / 8)
    Rx(q[4], PI / 2)
    Ry(q[5], PI / 3)
    Rz(q[6], PI / 4)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    # layer 1
    Rx(q[0], PI / 6)
    Ry(q[1], PI / 7)
    Rz(q[2], PI / 8)
    Rx(q[3], PI / 2)
    Ry(q[4], PI / 3)
    Rz(q[5], PI / 4)
    Rx(q[6], PI / 5)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    # layer 2
    Ry(q[0], PI / 7)
    Rz(q[1], PI / 8)
    Rx(q[2], PI / 2)
    Ry(q[3], PI / 3)
    Rz(q[4], PI / 4)
    Rx(q[5], PI / 5)
    Ry(q[6], PI / 6)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 060_variational_pattern_60.sq

```sansqrit
# Generated variational circuit pattern 60
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Rx(q[0], PI / 6)
    Ry(q[1], PI / 7)
    Rz(q[2], PI / 8)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 061_variational_pattern_61.sq

```sansqrit
# Generated variational circuit pattern 61
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Ry(q[0], PI / 7)
    Rz(q[1], PI / 8)
    Rx(q[2], PI / 2)
    Ry(q[3], PI / 3)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    # layer 1
    Rz(q[0], PI / 8)
    Rx(q[1], PI / 2)
    Ry(q[2], PI / 3)
    Rz(q[3], PI / 4)
    RZZ(q[0], q[1], PI / 4)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 062_variational_pattern_62.sq

```sansqrit
# Generated variational circuit pattern 62
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Rz(q[0], PI / 8)
    Rx(q[1], PI / 2)
    Ry(q[2], PI / 3)
    Rz(q[3], PI / 4)
    Rx(q[4], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    # layer 1
    Rx(q[0], PI / 2)
    Ry(q[1], PI / 3)
    Rz(q[2], PI / 4)
    Rx(q[3], PI / 5)
    Ry(q[4], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    # layer 2
    Ry(q[0], PI / 3)
    Rz(q[1], PI / 4)
    Rx(q[2], PI / 5)
    Ry(q[3], PI / 6)
    Rz(q[4], PI / 7)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 6)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 3)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 063_variational_pattern_63.sq

```sansqrit
# Generated variational circuit pattern 63
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Rx(q[0], PI / 2)
    Ry(q[1], PI / 3)
    Rz(q[2], PI / 4)
    Rx(q[3], PI / 5)
    Ry(q[4], PI / 6)
    Rz(q[5], PI / 7)
    RZZ(q[0], q[1], PI / 6)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 3)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 5)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 064_variational_pattern_64.sq

```sansqrit
# Generated variational circuit pattern 64
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Ry(q[0], PI / 3)
    Rz(q[1], PI / 4)
    Rx(q[2], PI / 5)
    Ry(q[3], PI / 6)
    Rz(q[4], PI / 7)
    Rx(q[5], PI / 8)
    Ry(q[6], PI / 2)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    # layer 1
    Rz(q[0], PI / 4)
    Rx(q[1], PI / 5)
    Ry(q[2], PI / 6)
    Rz(q[3], PI / 7)
    Rx(q[4], PI / 8)
    Ry(q[5], PI / 2)
    Rz(q[6], PI / 3)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 3)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 5)
    CNOT(q[4], q[5])
    RZZ(q[5], q[6], PI / 7)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 065_variational_pattern_65.sq

```sansqrit
# Generated variational circuit pattern 65
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Rz(q[0], PI / 4)
    Rx(q[1], PI / 5)
    Ry(q[2], PI / 6)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    # layer 1
    Rx(q[0], PI / 5)
    Ry(q[1], PI / 6)
    Rz(q[2], PI / 7)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    # layer 2
    Ry(q[0], PI / 6)
    Rz(q[1], PI / 7)
    Rx(q[2], PI / 8)
    RZZ(q[0], q[1], PI / 3)
    CNOT(q[1], q[2])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 066_variational_pattern_66.sq

```sansqrit
# Generated variational circuit pattern 66
simulate(4, engine="sparse") {
    let q = quantum_register(4)
    H_all()
    # layer 0
    Rx(q[0], PI / 5)
    Ry(q[1], PI / 6)
    Rz(q[2], PI / 7)
    Rx(q[3], PI / 8)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 5)
    CNOT(q[2], q[3])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 067_variational_pattern_67.sq

```sansqrit
# Generated variational circuit pattern 67
simulate(5, engine="sparse") {
    let q = quantum_register(5)
    H_all()
    # layer 0
    Ry(q[0], PI / 6)
    Rz(q[1], PI / 7)
    Rx(q[2], PI / 8)
    Ry(q[3], PI / 2)
    Rz(q[4], PI / 3)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    # layer 1
    Rz(q[0], PI / 7)
    Rx(q[1], PI / 8)
    Ry(q[2], PI / 2)
    Rz(q[3], PI / 3)
    Rx(q[4], PI / 4)
    RZZ(q[0], q[1], PI / 5)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 7)
    CNOT(q[3], q[4])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 068_variational_pattern_68.sq

```sansqrit
# Generated variational circuit pattern 68
simulate(6, engine="sparse") {
    let q = quantum_register(6)
    H_all()
    # layer 0
    Rz(q[0], PI / 7)
    Rx(q[1], PI / 8)
    Ry(q[2], PI / 2)
    Rz(q[3], PI / 3)
    Rx(q[4], PI / 4)
    Ry(q[5], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    # layer 1
    Rx(q[0], PI / 8)
    Ry(q[1], PI / 2)
    Rz(q[2], PI / 3)
    Rx(q[3], PI / 4)
    Ry(q[4], PI / 5)
    Rz(q[5], PI / 6)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    # layer 2
    Ry(q[0], PI / 2)
    Rz(q[1], PI / 3)
    Rx(q[2], PI / 4)
    Ry(q[3], PI / 5)
    Rz(q[4], PI / 6)
    Rx(q[5], PI / 7)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 7)
    CNOT(q[2], q[3])
    RZZ(q[3], q[4], PI / 4)
    CNOT(q[4], q[5])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 069_variational_pattern_69.sq

```sansqrit
# Generated variational circuit pattern 69
simulate(7, engine="sparse") {
    let q = quantum_register(7)
    H_all()
    # layer 0
    Rx(q[0], PI / 8)
    Ry(q[1], PI / 2)
    Rz(q[2], PI / 3)
    Rx(q[3], PI / 4)
    Ry(q[4], PI / 5)
    Rz(q[5], PI / 6)
    Rx(q[6], PI / 7)
    RZZ(q[0], q[1], PI / 7)
    CNOT(q[1], q[2])
    RZZ(q[2], q[3], PI / 4)
    CNOT(q[3], q[4])
    RZZ(q[4], q[5], PI / 6)
    CNOT(q[5], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 070_variational_pattern_70.sq

```sansqrit
# Generated variational circuit pattern 70
simulate(3, engine="sparse") {
    let q = quantum_register(3)
    H_all()
    # layer 0
    Ry(q[0], PI / 2)
    Rz(q[1], PI / 3)
    Rx(q[2], PI / 4)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    # layer 1
    Rz(q[0], PI / 3)
    Rx(q[1], PI / 4)
    Ry(q[2], PI / 5)
    CNOT(q[0], q[1])
    RZZ(q[1], q[2], PI / 4)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 071_phase_kickback.sq

```sansqrit
# phase_kickback example 71
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    X(q[0])
    H_all()
    for i in range(6) {
        CP(q[i + 1], q[0], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 072_hidden_shift.sq

```sansqrit
# hidden_shift example 72
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H_all()
    for i in range(4) {
        Rz(q[i], PI / (i + 2))
    }
    for i in range(3) {
        CNOT(q[i], q[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 073_qft_phase_grid.sq

```sansqrit
# qft_phase_grid example 73
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    X(q[0])
    X(q[2])
    qft(q)
    Rz(q[1], PI / 7)
    iqft(q)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 074_entangled_ladder.sq

```sansqrit
# entangled_ladder example 74
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H(q[0])
    for i in range(5) {
        CNOT(q[i], q[i + 1])
        RZZ(q[i], q[i + 1], PI / 5)
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 075_hardware_efficient_ansatz.sq

```sansqrit
# hardware_efficient_ansatz example 75
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    for layer in range(3) {
        for i in range(7) {
            Ry(q[i], PI / (layer + i + 2))
            Rz(q[i], PI / (layer + i + 3))
        }
        for i in range(6) {
            CNOT(q[i], q[i + 1])
        }
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 076_maxcut_ansatz.sq

```sansqrit
# maxcut_ansatz example 76
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H_all()
    for i in range(3) {
        RZZ(q[i], q[i + 1], PI / 4)
    }
    Rx_all(PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 077_qml_feature_map.sq

```sansqrit
# qml_feature_map example 77
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    let x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7][: 5]
    for i in range(5) {
        H(q[i])
        Rz(q[i], x[i])
    }
    for i in range(4) {
        RZZ(q[i], q[i + 1], x[i] * x[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 078_controlled_rotation_bank.sq

```sansqrit
# controlled_rotation_bank example 78
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H(q[0])
    for i in range(1, 6) {
        CRz(q[0], q[i], PI / (i + 1))
        CRx(q[0], q[i], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 079_multi_control_demo.sq

```sansqrit
# multi_control_demo example 79
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    for i in range(6) {
        X(q[i])
    }
    MCX(q[0], q[1], q[2], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 080_sparse_large_index.sq

```sansqrit
# sparse_large_index example 80
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H(q[0])
    CNOT(q[0], q[3])
    RZZ(q[0], q[3], PI / 9)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 081_phase_kickback.sq

```sansqrit
# phase_kickback example 81
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    X(q[0])
    H_all()
    for i in range(4) {
        CP(q[i + 1], q[0], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 082_hidden_shift.sq

```sansqrit
# hidden_shift example 82
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H_all()
    for i in range(6) {
        Rz(q[i], PI / (i + 2))
    }
    for i in range(5) {
        CNOT(q[i], q[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 083_qft_phase_grid.sq

```sansqrit
# qft_phase_grid example 83
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    X(q[0])
    X(q[2])
    qft(q)
    Rz(q[1], PI / 7)
    iqft(q)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 084_entangled_ladder.sq

```sansqrit
# entangled_ladder example 84
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H(q[0])
    for i in range(3) {
        CNOT(q[i], q[i + 1])
        RZZ(q[i], q[i + 1], PI / 5)
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 085_hardware_efficient_ansatz.sq

```sansqrit
# hardware_efficient_ansatz example 85
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    for layer in range(3) {
        for i in range(5) {
            Ry(q[i], PI / (layer + i + 2))
            Rz(q[i], PI / (layer + i + 3))
        }
        for i in range(4) {
            CNOT(q[i], q[i + 1])
        }
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 086_maxcut_ansatz.sq

```sansqrit
# maxcut_ansatz example 86
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H_all()
    for i in range(5) {
        RZZ(q[i], q[i + 1], PI / 4)
    }
    Rx_all(PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 087_qml_feature_map.sq

```sansqrit
# qml_feature_map example 87
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    let x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7][: 7]
    for i in range(7) {
        H(q[i])
        Rz(q[i], x[i])
    }
    for i in range(6) {
        RZZ(q[i], q[i + 1], x[i] * x[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 088_controlled_rotation_bank.sq

```sansqrit
# controlled_rotation_bank example 88
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H(q[0])
    for i in range(1, 4) {
        CRz(q[0], q[i], PI / (i + 1))
        CRx(q[0], q[i], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 089_multi_control_demo.sq

```sansqrit
# multi_control_demo example 89
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    for i in range(4) {
        X(q[i])
    }
    MCX(q[0], q[1], q[2], q[4])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 090_sparse_large_index.sq

```sansqrit
# sparse_large_index example 90
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H(q[0])
    CNOT(q[0], q[5])
    RZZ(q[0], q[5], PI / 9)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 091_phase_kickback.sq

```sansqrit
# phase_kickback example 91
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    X(q[0])
    H_all()
    for i in range(6) {
        CP(q[i + 1], q[0], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 092_hidden_shift.sq

```sansqrit
# hidden_shift example 92
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H_all()
    for i in range(4) {
        Rz(q[i], PI / (i + 2))
    }
    for i in range(3) {
        CNOT(q[i], q[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 093_qft_phase_grid.sq

```sansqrit
# qft_phase_grid example 93
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    X(q[0])
    X(q[2])
    qft(q)
    Rz(q[1], PI / 7)
    iqft(q)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 094_entangled_ladder.sq

```sansqrit
# entangled_ladder example 94
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H(q[0])
    for i in range(5) {
        CNOT(q[i], q[i + 1])
        RZZ(q[i], q[i + 1], PI / 5)
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 095_hardware_efficient_ansatz.sq

```sansqrit
# hardware_efficient_ansatz example 95
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    for layer in range(3) {
        for i in range(7) {
            Ry(q[i], PI / (layer + i + 2))
            Rz(q[i], PI / (layer + i + 3))
        }
        for i in range(6) {
            CNOT(q[i], q[i + 1])
        }
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 096_maxcut_ansatz.sq

```sansqrit
# maxcut_ansatz example 96
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H_all()
    for i in range(3) {
        RZZ(q[i], q[i + 1], PI / 4)
    }
    Rx_all(PI / 6)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 097_qml_feature_map.sq

```sansqrit
# qml_feature_map example 97
simulate(5, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(5)
    let x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7][: 5]
    for i in range(5) {
        H(q[i])
        Rz(q[i], x[i])
    }
    for i in range(4) {
        RZZ(q[i], q[i + 1], x[i] * x[i + 1])
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 098_controlled_rotation_bank.sq

```sansqrit
# controlled_rotation_bank example 98
simulate(6, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(6)
    H(q[0])
    for i in range(1, 6) {
        CRz(q[0], q[i], PI / (i + 1))
        CRx(q[0], q[i], PI / (i + 2))
    }
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 099_multi_control_demo.sq

```sansqrit
# multi_control_demo example 99
simulate(7, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(7)
    for i in range(6) {
        X(q[i])
    }
    MCX(q[0], q[1], q[2], q[6])
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 100_sparse_large_index.sq

```sansqrit
# sparse_large_index example 100
simulate(4, engine="sharded", n_shards=4, workers=2) {
    let q = quantum_register(4)
    H(q[0])
    CNOT(q[0], q[3])
    RZZ(q[0], q[3], PI / 9)
    print(engine_nnz())
    print(measure_all(q, shots=128))
}
```

## 101_stabilizer_ghz_1000.sq

```sansqrit
# 1000-qubit Clifford GHZ smoke test; exact tableau, no dense expansion.
simulate(1000, engine="stabilizer", seed=7) {
    H(0)
    for i in range(0, 999) {
        CNOT(i, i + 1)
    }
    print(measure_all(shots=8))
}
```

## 102_mps_low_entanglement_chain.sq

```sansqrit
# Low-entanglement MPS chain with small bond dimension.
simulate(32, engine="mps", max_bond_dim=32, seed=3) {
    for i in range(0, 32) {
        Ry(i, 0.1)
    }
    for i in range(0, 31) {
        CNOT(i, i + 1)
    }
    print(measure_all(shots=16))
}
```

## 103_density_depolarizing_noise.sq

```sansqrit
# Density-matrix noisy Bell state with depolarizing noise.
simulate(2, engine="density", seed=5) {
    H(0)
    CNOT(0, 1)
    noise_depolarize(0, 0.05)
    noise_depolarize(1, 0.05)
    print(probabilities())
}
```

## 104_density_amplitude_damping.sq

```sansqrit
# Amplitude damping drives |1> toward |0>.
simulate(1, engine="density", seed=5) {
    X(0)
    noise_amplitude_damping(0, 0.30)
    print(probabilities())
}
```

## 105_hybrid_backend_selection.sq

```sansqrit
# Hybrid chooses stabilizer for Clifford circuits and sparse/MPS otherwise.
simulate(4, engine="stabilizer", seed=11) {
    H(0)
    CNOT(0, 1)
    CNOT(1, 2)
    CNOT(2, 3)
    print(measure_all(shots=8))
}
```

## 106_optimizer_cancel_rotations.sq

```sansqrit
# Optimizer is available from Python API; in DSL use direct simplified code.
simulate(1, seed=1) {
    H(0)
    H(0)
    Rz(0, 0.25)
    Rz(0, -0.25)
    print(probabilities())
}
```

## 107_gpu_backend_small.sq

```sansqrit
# GPU backend syntax reference. Uncomment the simulate block after installing sansqrit[gpu].
# simulate(3, engine="gpu", seed=1) {
#     H(0)
#     CNOT(0, 1)
#     Rz(2, 0.4)
#     print(measure_all(shots=8))
# }
print("GPU example: install sansqrit[gpu], then uncomment the simulate block.")
```

## 108_qiskit_interop_reference.sq

```sansqrit
# Interop is primarily Python API: sansqrit.interop.to_qiskit(Circuit(...)).
# DSL can still export QASM for external tools.
simulate(2, seed=2) {
    H(0)
    CNOT(0, 1)
    print(export_qasm3())
}
```

## 109_large_sparse_150_qubits.sq

```sansqrit
# 150 logical qubits with sparse state. Avoid H_all on all 150 unless you expect expansion.
simulate(150, engine="sparse", seed=9) {
    X(149)
    H(0)
    CNOT(0, 149)
    print(engine_nnz())
    print(measure_all(shots=8))
}
```

## 110_mps_qft_lite.sq

```sansqrit
# Small QFT-style tensor run. For large QFT, bond growth may require high max_bond_dim.
simulate(8, engine="mps", max_bond_dim=64, seed=4) {
    X(0)
    qft()
    print(measure_all(shots=16))
}
```

## 111_150q_sensor_fusion_111.sq

```sansqrit
# Example 111: 150-qubit real-time sensor fusion anomaly flag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=111) {
    let q = quantum_register(150)
    X(q[32])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[32], q[102])
    Rz(q[99], PI / 23)
    Phase(q[149], PI / 33)
    print("real-time sensor fusion anomaly flag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 112_150q_satellite_telemetry_112.sq

```sansqrit
# Example 112: 150-qubit satellite telemetry sparse state update.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=112) {
    let q = quantum_register(150)
    X(q[39])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[39], q[115])
    Rz(q[116], PI / 16)
    Phase(q[149], PI / 34)
    print("satellite telemetry sparse state update")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 113_150q_network_intrusion_113.sq

```sansqrit
# Example 113: 150-qubit network intrusion signature superposition.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=113) {
    let q = quantum_register(150)
    X(q[46])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[46], q[128])
    Rz(q[133], PI / 17)
    Phase(q[149], PI / 35)
    print("network intrusion signature superposition")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 114_150q_portfolio_risk_114.sq

```sansqrit
# Example 114: 150-qubit portfolio risk qubit flagging.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=114) {
    let q = quantum_register(150)
    X(q[53])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[53], q[141])
    Rz(q[1], PI / 18)
    Phase(q[149], PI / 36)
    print("portfolio risk qubit flagging")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 115_150q_drug_screening_115.sq

```sansqrit
# Example 115: 150-qubit drug candidate sparse oracle marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=115) {
    let q = quantum_register(150)
    X(q[60])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[60], q[5])
    Rz(q[18], PI / 19)
    Phase(q[149], PI / 32)
    print("drug candidate sparse oracle marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 116_150q_battery_material_116.sq

```sansqrit
# Example 116: 150-qubit battery material candidate phase tag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=116) {
    let q = quantum_register(150)
    X(q[67])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[67], q[18])
    Rz(q[35], PI / 20)
    Phase(q[149], PI / 33)
    print("battery material candidate phase tag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 117_150q_smart_grid_117.sq

```sansqrit
# Example 117: 150-qubit smart grid load-balancing state flag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=117) {
    let q = quantum_register(150)
    X(q[74])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[74], q[31])
    Rz(q[52], PI / 21)
    Phase(q[149], PI / 34)
    print("smart grid load-balancing state flag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 118_150q_robotics_path_118.sq

```sansqrit
# Example 118: 150-qubit robotics path branch marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=118) {
    let q = quantum_register(150)
    X(q[81])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[81], q[44])
    Rz(q[69], PI / 22)
    Phase(q[149], PI / 35)
    print("robotics path branch marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 119_150q_climate_event_119.sq

```sansqrit
# Example 119: 150-qubit climate event sparse alert.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=119) {
    let q = quantum_register(150)
    X(q[88])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[88], q[57])
    Rz(q[86], PI / 23)
    Phase(q[149], PI / 36)
    print("climate event sparse alert")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 120_150q_factory_quality_120.sq

```sansqrit
# Example 120: 150-qubit factory quality-control qubit register.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=120) {
    let q = quantum_register(150)
    X(q[95])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[95], q[70])
    Rz(q[103], PI / 16)
    Phase(q[149], PI / 32)
    print("factory quality-control qubit register")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 121_150q_traffic_routing_121.sq

```sansqrit
# Example 121: 150-qubit traffic routing decision bit.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=121) {
    let q = quantum_register(150)
    X(q[102])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[102], q[83])
    Rz(q[120], PI / 17)
    Phase(q[149], PI / 33)
    print("traffic routing decision bit")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 122_150q_fraud_detection_122.sq

```sansqrit
# Example 122: 150-qubit fraud detection sparse score marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=122) {
    let q = quantum_register(150)
    X(q[109])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[109], q[96])
    Rz(q[137], PI / 18)
    Phase(q[149], PI / 34)
    print("fraud detection sparse score marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 123_150q_genomics_variant_123.sq

```sansqrit
# Example 123: 150-qubit genomics variant marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=123) {
    let q = quantum_register(150)
    X(q[116])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[116], q[109])
    Rz(q[5], PI / 19)
    Phase(q[149], PI / 35)
    print("genomics variant marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 124_150q_seismic_monitor_124.sq

```sansqrit
# Example 124: 150-qubit seismic event marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=124) {
    let q = quantum_register(150)
    X(q[123])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[123], q[122])
    Rz(q[22], PI / 20)
    Phase(q[149], PI / 36)
    print("seismic event marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 125_150q_iot_edge_125.sq

```sansqrit
# Example 125: 150-qubit IoT edge telemetry marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=125) {
    let q = quantum_register(150)
    X(q[130])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[130], q[135])
    Rz(q[39], PI / 21)
    Phase(q[149], PI / 32)
    print("IoT edge telemetry marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 126_150q_cyber_key_health_126.sq

```sansqrit
# Example 126: 150-qubit cyber key health monitor.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=126) {
    let q = quantum_register(150)
    X(q[137])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[137], q[148])
    Rz(q[56], PI / 22)
    Phase(q[149], PI / 33)
    print("cyber key health monitor")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 127_150q_medical_triage_127.sq

```sansqrit
# Example 127: 150-qubit medical triage sparse decision.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=127) {
    let q = quantum_register(150)
    X(q[144])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[144], q[12])
    Rz(q[73], PI / 23)
    Phase(q[149], PI / 34)
    print("medical triage sparse decision")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 128_150q_supply_chain_128.sq

```sansqrit
# Example 128: 150-qubit supply chain disruption indicator.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=128) {
    let q = quantum_register(150)
    X(q[2])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[2], q[25])
    Rz(q[90], PI / 16)
    Phase(q[149], PI / 35)
    print("supply chain disruption indicator")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 129_150q_water_network_129.sq

```sansqrit
# Example 129: 150-qubit water network pressure anomaly.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=129) {
    let q = quantum_register(150)
    X(q[9])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[9], q[38])
    Rz(q[107], PI / 17)
    Phase(q[149], PI / 36)
    print("water network pressure anomaly")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 130_150q_energy_market_130.sq

```sansqrit
# Example 130: 150-qubit energy market sparse branch.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=130) {
    let q = quantum_register(150)
    X(q[16])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[16], q[51])
    Rz(q[124], PI / 18)
    Phase(q[149], PI / 32)
    print("energy market sparse branch")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 131_150q_sensor_fusion_131.sq

```sansqrit
# Example 131: 150-qubit real-time sensor fusion anomaly flag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=131) {
    let q = quantum_register(150)
    X(q[23])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[23], q[64])
    Rz(q[141], PI / 19)
    Phase(q[149], PI / 33)
    print("real-time sensor fusion anomaly flag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 132_150q_satellite_telemetry_132.sq

```sansqrit
# Example 132: 150-qubit satellite telemetry sparse state update.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=132) {
    let q = quantum_register(150)
    X(q[30])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[30], q[77])
    Rz(q[9], PI / 20)
    Phase(q[149], PI / 34)
    print("satellite telemetry sparse state update")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 133_150q_network_intrusion_133.sq

```sansqrit
# Example 133: 150-qubit network intrusion signature superposition.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=133) {
    let q = quantum_register(150)
    X(q[37])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[37], q[90])
    Rz(q[26], PI / 21)
    Phase(q[149], PI / 35)
    print("network intrusion signature superposition")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 134_150q_portfolio_risk_134.sq

```sansqrit
# Example 134: 150-qubit portfolio risk qubit flagging.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=134) {
    let q = quantum_register(150)
    X(q[44])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[44], q[103])
    Rz(q[43], PI / 22)
    Phase(q[149], PI / 36)
    print("portfolio risk qubit flagging")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 135_150q_drug_screening_135.sq

```sansqrit
# Example 135: 150-qubit drug candidate sparse oracle marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=135) {
    let q = quantum_register(150)
    X(q[51])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[51], q[116])
    Rz(q[60], PI / 23)
    Phase(q[149], PI / 32)
    print("drug candidate sparse oracle marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 136_150q_battery_material_136.sq

```sansqrit
# Example 136: 150-qubit battery material candidate phase tag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=136) {
    let q = quantum_register(150)
    X(q[58])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[58], q[129])
    Rz(q[77], PI / 16)
    Phase(q[149], PI / 33)
    print("battery material candidate phase tag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 137_150q_smart_grid_137.sq

```sansqrit
# Example 137: 150-qubit smart grid load-balancing state flag.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=137) {
    let q = quantum_register(150)
    X(q[65])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[65], q[142])
    Rz(q[94], PI / 17)
    Phase(q[149], PI / 34)
    print("smart grid load-balancing state flag")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 138_150q_robotics_path_138.sq

```sansqrit
# Example 138: 150-qubit robotics path branch marker.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=138) {
    let q = quantum_register(150)
    X(q[72])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[72], q[6])
    Rz(q[111], PI / 18)
    Phase(q[149], PI / 35)
    print("robotics path branch marker")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 139_150q_climate_event_139.sq

```sansqrit
# Example 139: 150-qubit climate event sparse alert.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=139) {
    let q = quantum_register(150)
    X(q[79])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[79], q[19])
    Rz(q[128], PI / 19)
    Phase(q[149], PI / 36)
    print("climate event sparse alert")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 140_150q_factory_quality_140.sq

```sansqrit
# Example 140: 150-qubit factory quality-control qubit register.
# Design rule: touch only a few sparse basis branches so this stays feasible on local hardware.
simulate(150, engine="sharded", n_shards=16, workers=4, seed=140) {
    let q = quantum_register(150)
    X(q[86])
    H(q[0])
    CNOT(q[0], q[149])
    CNOT(q[86], q[32])
    Rz(q[145], PI / 20)
    Phase(q[149], PI / 32)
    print("factory quality-control qubit register")
    print("logical_qubits", 150)
    print("nonzero_amplitudes", engine_nnz())
    print("sample", measure_all(q, shots=6))
}
```

## 141_stabilizer_clifford_comm_141.sq

```sansqrit
# Example 141: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(512, engine="stabilizer", seed=141) {
    H(423)
    S(423)
    CNOT(423, 440)
    CZ(440, 24)
    SWAP(423, 24)
    X(440)
    Z(24)
    print("clifford_comm")
    print("logical_qubits", 512)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 142_stabilizer_graph_state_142.sq

```sansqrit
# Example 142: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(768, engine="stabilizer", seed=142) {
    H(426)
    S(426)
    CNOT(426, 443)
    CZ(443, 539)
    SWAP(426, 539)
    X(443)
    Z(539)
    print("graph_state")
    print("logical_qubits", 768)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 143_stabilizer_cluster_state_143.sq

```sansqrit
# Example 143: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1024, engine="stabilizer", seed=143) {
    H(429)
    S(429)
    CNOT(429, 446)
    CZ(446, 542)
    SWAP(429, 542)
    X(446)
    Z(542)
    print("cluster_state")
    print("logical_qubits", 1024)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 144_stabilizer_parity_monitor_144.sq

```sansqrit
# Example 144: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1280, engine="stabilizer", seed=144) {
    H(432)
    S(432)
    CNOT(432, 449)
    CZ(449, 545)
    SWAP(432, 545)
    X(449)
    Z(545)
    print("parity_monitor")
    print("logical_qubits", 1280)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 145_stabilizer_surface_code_syndrome_145.sq

```sansqrit
# Example 145: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1536, engine="stabilizer", seed=145) {
    H(435)
    S(435)
    CNOT(435, 452)
    CZ(452, 548)
    SWAP(435, 548)
    X(452)
    Z(548)
    print("surface_code_syndrome")
    print("logical_qubits", 1536)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 146_stabilizer_clifford_comm_146.sq

```sansqrit
# Example 146: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1792, engine="stabilizer", seed=146) {
    H(438)
    S(438)
    CNOT(438, 455)
    CZ(455, 551)
    SWAP(438, 551)
    X(455)
    Z(551)
    print("clifford_comm")
    print("logical_qubits", 1792)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 147_stabilizer_graph_state_147.sq

```sansqrit
# Example 147: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(512, engine="stabilizer", seed=147) {
    H(441)
    S(441)
    CNOT(441, 458)
    CZ(458, 42)
    SWAP(441, 42)
    X(458)
    Z(42)
    print("graph_state")
    print("logical_qubits", 512)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 148_stabilizer_cluster_state_148.sq

```sansqrit
# Example 148: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(768, engine="stabilizer", seed=148) {
    H(444)
    S(444)
    CNOT(444, 461)
    CZ(461, 557)
    SWAP(444, 557)
    X(461)
    Z(557)
    print("cluster_state")
    print("logical_qubits", 768)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 149_stabilizer_parity_monitor_149.sq

```sansqrit
# Example 149: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1024, engine="stabilizer", seed=149) {
    H(447)
    S(447)
    CNOT(447, 464)
    CZ(464, 560)
    SWAP(447, 560)
    X(464)
    Z(560)
    print("parity_monitor")
    print("logical_qubits", 1024)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 150_stabilizer_surface_code_syndrome_150.sq

```sansqrit
# Example 150: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1280, engine="stabilizer", seed=150) {
    H(450)
    S(450)
    CNOT(450, 467)
    CZ(467, 563)
    SWAP(450, 563)
    X(467)
    Z(563)
    print("surface_code_syndrome")
    print("logical_qubits", 1280)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 151_stabilizer_clifford_comm_151.sq

```sansqrit
# Example 151: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1536, engine="stabilizer", seed=151) {
    H(453)
    S(453)
    CNOT(453, 470)
    CZ(470, 566)
    SWAP(453, 566)
    X(470)
    Z(566)
    print("clifford_comm")
    print("logical_qubits", 1536)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 152_stabilizer_graph_state_152.sq

```sansqrit
# Example 152: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1792, engine="stabilizer", seed=152) {
    H(456)
    S(456)
    CNOT(456, 473)
    CZ(473, 569)
    SWAP(456, 569)
    X(473)
    Z(569)
    print("graph_state")
    print("logical_qubits", 1792)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 153_stabilizer_cluster_state_153.sq

```sansqrit
# Example 153: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(512, engine="stabilizer", seed=153) {
    H(459)
    S(459)
    CNOT(459, 476)
    CZ(476, 60)
    SWAP(459, 60)
    X(476)
    Z(60)
    print("cluster_state")
    print("logical_qubits", 512)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 154_stabilizer_parity_monitor_154.sq

```sansqrit
# Example 154: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(768, engine="stabilizer", seed=154) {
    H(462)
    S(462)
    CNOT(462, 479)
    CZ(479, 575)
    SWAP(462, 575)
    X(479)
    Z(575)
    print("parity_monitor")
    print("logical_qubits", 768)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 155_stabilizer_surface_code_syndrome_155.sq

```sansqrit
# Example 155: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1024, engine="stabilizer", seed=155) {
    H(465)
    S(465)
    CNOT(465, 482)
    CZ(482, 578)
    SWAP(465, 578)
    X(482)
    Z(578)
    print("surface_code_syndrome")
    print("logical_qubits", 1024)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 156_stabilizer_clifford_comm_156.sq

```sansqrit
# Example 156: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1280, engine="stabilizer", seed=156) {
    H(468)
    S(468)
    CNOT(468, 485)
    CZ(485, 581)
    SWAP(468, 581)
    X(485)
    Z(581)
    print("clifford_comm")
    print("logical_qubits", 1280)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 157_stabilizer_graph_state_157.sq

```sansqrit
# Example 157: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1536, engine="stabilizer", seed=157) {
    H(471)
    S(471)
    CNOT(471, 488)
    CZ(488, 584)
    SWAP(471, 584)
    X(488)
    Z(584)
    print("graph_state")
    print("logical_qubits", 1536)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 158_stabilizer_cluster_state_158.sq

```sansqrit
# Example 158: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1792, engine="stabilizer", seed=158) {
    H(474)
    S(474)
    CNOT(474, 491)
    CZ(491, 587)
    SWAP(474, 587)
    X(491)
    Z(587)
    print("cluster_state")
    print("logical_qubits", 1792)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 159_stabilizer_parity_monitor_159.sq

```sansqrit
# Example 159: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(512, engine="stabilizer", seed=159) {
    H(477)
    S(477)
    CNOT(477, 494)
    CZ(494, 78)
    SWAP(477, 78)
    X(494)
    Z(78)
    print("parity_monitor")
    print("logical_qubits", 512)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 160_stabilizer_surface_code_syndrome_160.sq

```sansqrit
# Example 160: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(768, engine="stabilizer", seed=160) {
    H(480)
    S(480)
    CNOT(480, 497)
    CZ(497, 593)
    SWAP(480, 593)
    X(497)
    Z(593)
    print("surface_code_syndrome")
    print("logical_qubits", 768)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 161_stabilizer_clifford_comm_161.sq

```sansqrit
# Example 161: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1024, engine="stabilizer", seed=161) {
    H(483)
    S(483)
    CNOT(483, 500)
    CZ(500, 596)
    SWAP(483, 596)
    X(500)
    Z(596)
    print("clifford_comm")
    print("logical_qubits", 1024)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 162_stabilizer_graph_state_162.sq

```sansqrit
# Example 162: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1280, engine="stabilizer", seed=162) {
    H(486)
    S(486)
    CNOT(486, 503)
    CZ(503, 599)
    SWAP(486, 599)
    X(503)
    Z(599)
    print("graph_state")
    print("logical_qubits", 1280)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 163_stabilizer_cluster_state_163.sq

```sansqrit
# Example 163: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1536, engine="stabilizer", seed=163) {
    H(489)
    S(489)
    CNOT(489, 506)
    CZ(506, 602)
    SWAP(489, 602)
    X(506)
    Z(602)
    print("cluster_state")
    print("logical_qubits", 1536)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 164_stabilizer_parity_monitor_164.sq

```sansqrit
# Example 164: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(1792, engine="stabilizer", seed=164) {
    H(492)
    S(492)
    CNOT(492, 509)
    CZ(509, 605)
    SWAP(492, 605)
    X(509)
    Z(605)
    print("parity_monitor")
    print("logical_qubits", 1792)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 165_stabilizer_surface_code_syndrome_165.sq

```sansqrit
# Example 165: stabilizer backend for thousands-scale Clifford simulation.
# Clifford-only circuits use tableau memory instead of dense 2^n state vectors.
simulate(512, engine="stabilizer", seed=165) {
    H(495)
    S(495)
    CNOT(495, 0)
    CZ(0, 96)
    SWAP(495, 96)
    X(0)
    Z(96)
    print("surface_code_syndrome")
    print("logical_qubits", 512)
    print("one_shot_prefix", list(measure_all(shots=1).keys())[0][0:32])
}
```

## 166_mps_adiabatic_line_166.sq

```sansqrit
# Example 166: MPS/tensor-network low-entanglement adiabatic_line.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(24, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=166) {
    let q = quantum_register(24)
    for layer in range(4) {
        H(q[layer % 24])
        CNOT(q[layer % 24], q[(layer + 1) % 24])
        Rz(q[(layer + 1) % 24], PI / (layer + 3))
    }
    print("adiabatic_line")
    print("logical_qubits", 24)
    print("shots", measure_all(q, shots=4))
}
```

## 167_mps_qft_lite_167.sq

```sansqrit
# Example 167: MPS/tensor-network low-entanglement qft_lite.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(28, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=167) {
    let q = quantum_register(28)
    for layer in range(5) {
        H(q[layer % 28])
        CNOT(q[layer % 28], q[(layer + 1) % 28])
        Rz(q[(layer + 1) % 28], PI / (layer + 3))
    }
    print("qft_lite")
    print("logical_qubits", 28)
    print("shots", measure_all(q, shots=4))
}
```

## 168_mps_bond_dimension_probe_168.sq

```sansqrit
# Example 168: MPS/tensor-network low-entanglement bond_dimension_probe.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(32, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=168) {
    let q = quantum_register(32)
    for layer in range(3) {
        H(q[layer % 32])
        CNOT(q[layer % 32], q[(layer + 1) % 32])
        Rz(q[(layer + 1) % 32], PI / (layer + 3))
    }
    print("bond_dimension_probe")
    print("logical_qubits", 32)
    print("shots", measure_all(q, shots=4))
}
```

## 169_mps_matrix_product_feature_map_169.sq

```sansqrit
# Example 169: MPS/tensor-network low-entanglement matrix_product_feature_map.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(36, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=169) {
    let q = quantum_register(36)
    for layer in range(4) {
        H(q[layer % 36])
        CNOT(q[layer % 36], q[(layer + 1) % 36])
        Rz(q[(layer + 1) % 36], PI / (layer + 3))
    }
    print("matrix_product_feature_map")
    print("logical_qubits", 36)
    print("shots", measure_all(q, shots=4))
}
```

## 170_mps_spin_chain_170.sq

```sansqrit
# Example 170: MPS/tensor-network low-entanglement spin_chain.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(40, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=170) {
    let q = quantum_register(40)
    for layer in range(5) {
        H(q[layer % 40])
        CNOT(q[layer % 40], q[(layer + 1) % 40])
        Rz(q[(layer + 1) % 40], PI / (layer + 3))
    }
    print("spin_chain")
    print("logical_qubits", 40)
    print("shots", measure_all(q, shots=4))
}
```

## 171_mps_adiabatic_line_171.sq

```sansqrit
# Example 171: MPS/tensor-network low-entanglement adiabatic_line.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(44, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=171) {
    let q = quantum_register(44)
    for layer in range(3) {
        H(q[layer % 44])
        CNOT(q[layer % 44], q[(layer + 1) % 44])
        Rz(q[(layer + 1) % 44], PI / (layer + 3))
    }
    print("adiabatic_line")
    print("logical_qubits", 44)
    print("shots", measure_all(q, shots=4))
}
```

## 172_mps_qft_lite_172.sq

```sansqrit
# Example 172: MPS/tensor-network low-entanglement qft_lite.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(48, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=172) {
    let q = quantum_register(48)
    for layer in range(4) {
        H(q[layer % 48])
        CNOT(q[layer % 48], q[(layer + 1) % 48])
        Rz(q[(layer + 1) % 48], PI / (layer + 3))
    }
    print("qft_lite")
    print("logical_qubits", 48)
    print("shots", measure_all(q, shots=4))
}
```

## 173_mps_bond_dimension_probe_173.sq

```sansqrit
# Example 173: MPS/tensor-network low-entanglement bond_dimension_probe.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(52, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=173) {
    let q = quantum_register(52)
    for layer in range(5) {
        H(q[layer % 52])
        CNOT(q[layer % 52], q[(layer + 1) % 52])
        Rz(q[(layer + 1) % 52], PI / (layer + 3))
    }
    print("bond_dimension_probe")
    print("logical_qubits", 52)
    print("shots", measure_all(q, shots=4))
}
```

## 174_mps_matrix_product_feature_map_174.sq

```sansqrit
# Example 174: MPS/tensor-network low-entanglement matrix_product_feature_map.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(24, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=174) {
    let q = quantum_register(24)
    for layer in range(3) {
        H(q[layer % 24])
        CNOT(q[layer % 24], q[(layer + 1) % 24])
        Rz(q[(layer + 1) % 24], PI / (layer + 3))
    }
    print("matrix_product_feature_map")
    print("logical_qubits", 24)
    print("shots", measure_all(q, shots=4))
}
```

## 175_mps_spin_chain_175.sq

```sansqrit
# Example 175: MPS/tensor-network low-entanglement spin_chain.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(28, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=175) {
    let q = quantum_register(28)
    for layer in range(4) {
        H(q[layer % 28])
        CNOT(q[layer % 28], q[(layer + 1) % 28])
        Rz(q[(layer + 1) % 28], PI / (layer + 3))
    }
    print("spin_chain")
    print("logical_qubits", 28)
    print("shots", measure_all(q, shots=4))
}
```

## 176_mps_adiabatic_line_176.sq

```sansqrit
# Example 176: MPS/tensor-network low-entanglement adiabatic_line.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(32, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=176) {
    let q = quantum_register(32)
    for layer in range(5) {
        H(q[layer % 32])
        CNOT(q[layer % 32], q[(layer + 1) % 32])
        Rz(q[(layer + 1) % 32], PI / (layer + 3))
    }
    print("adiabatic_line")
    print("logical_qubits", 32)
    print("shots", measure_all(q, shots=4))
}
```

## 177_mps_qft_lite_177.sq

```sansqrit
# Example 177: MPS/tensor-network low-entanglement qft_lite.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(36, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=177) {
    let q = quantum_register(36)
    for layer in range(3) {
        H(q[layer % 36])
        CNOT(q[layer % 36], q[(layer + 1) % 36])
        Rz(q[(layer + 1) % 36], PI / (layer + 3))
    }
    print("qft_lite")
    print("logical_qubits", 36)
    print("shots", measure_all(q, shots=4))
}
```

## 178_mps_bond_dimension_probe_178.sq

```sansqrit
# Example 178: MPS/tensor-network low-entanglement bond_dimension_probe.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(40, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=178) {
    let q = quantum_register(40)
    for layer in range(4) {
        H(q[layer % 40])
        CNOT(q[layer % 40], q[(layer + 1) % 40])
        Rz(q[(layer + 1) % 40], PI / (layer + 3))
    }
    print("bond_dimension_probe")
    print("logical_qubits", 40)
    print("shots", measure_all(q, shots=4))
}
```

## 179_mps_matrix_product_feature_map_179.sq

```sansqrit
# Example 179: MPS/tensor-network low-entanglement matrix_product_feature_map.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(44, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=179) {
    let q = quantum_register(44)
    for layer in range(5) {
        H(q[layer % 44])
        CNOT(q[layer % 44], q[(layer + 1) % 44])
        Rz(q[(layer + 1) % 44], PI / (layer + 3))
    }
    print("matrix_product_feature_map")
    print("logical_qubits", 44)
    print("shots", measure_all(q, shots=4))
}
```

## 180_mps_spin_chain_180.sq

```sansqrit
# Example 180: MPS/tensor-network low-entanglement spin_chain.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(48, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=180) {
    let q = quantum_register(48)
    for layer in range(3) {
        H(q[layer % 48])
        CNOT(q[layer % 48], q[(layer + 1) % 48])
        Rz(q[(layer + 1) % 48], PI / (layer + 3))
    }
    print("spin_chain")
    print("logical_qubits", 48)
    print("shots", measure_all(q, shots=4))
}
```

## 181_mps_adiabatic_line_181.sq

```sansqrit
# Example 181: MPS/tensor-network low-entanglement adiabatic_line.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(52, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=181) {
    let q = quantum_register(52)
    for layer in range(4) {
        H(q[layer % 52])
        CNOT(q[layer % 52], q[(layer + 1) % 52])
        Rz(q[(layer + 1) % 52], PI / (layer + 3))
    }
    print("adiabatic_line")
    print("logical_qubits", 52)
    print("shots", measure_all(q, shots=4))
}
```

## 182_mps_qft_lite_182.sq

```sansqrit
# Example 182: MPS/tensor-network low-entanglement qft_lite.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(24, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=182) {
    let q = quantum_register(24)
    for layer in range(5) {
        H(q[layer % 24])
        CNOT(q[layer % 24], q[(layer + 1) % 24])
        Rz(q[(layer + 1) % 24], PI / (layer + 3))
    }
    print("qft_lite")
    print("logical_qubits", 24)
    print("shots", measure_all(q, shots=4))
}
```

## 183_mps_bond_dimension_probe_183.sq

```sansqrit
# Example 183: MPS/tensor-network low-entanglement bond_dimension_probe.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(28, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=183) {
    let q = quantum_register(28)
    for layer in range(3) {
        H(q[layer % 28])
        CNOT(q[layer % 28], q[(layer + 1) % 28])
        Rz(q[(layer + 1) % 28], PI / (layer + 3))
    }
    print("bond_dimension_probe")
    print("logical_qubits", 28)
    print("shots", measure_all(q, shots=4))
}
```

## 184_mps_matrix_product_feature_map_184.sq

```sansqrit
# Example 184: MPS/tensor-network low-entanglement matrix_product_feature_map.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(32, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=184) {
    let q = quantum_register(32)
    for layer in range(4) {
        H(q[layer % 32])
        CNOT(q[layer % 32], q[(layer + 1) % 32])
        Rz(q[(layer + 1) % 32], PI / (layer + 3))
    }
    print("matrix_product_feature_map")
    print("logical_qubits", 32)
    print("shots", measure_all(q, shots=4))
}
```

## 185_mps_spin_chain_185.sq

```sansqrit
# Example 185: MPS/tensor-network low-entanglement spin_chain.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(36, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=185) {
    let q = quantum_register(36)
    for layer in range(5) {
        H(q[layer % 36])
        CNOT(q[layer % 36], q[(layer + 1) % 36])
        Rz(q[(layer + 1) % 36], PI / (layer + 3))
    }
    print("spin_chain")
    print("logical_qubits", 36)
    print("shots", measure_all(q, shots=4))
}
```

## 186_mps_adiabatic_line_186.sq

```sansqrit
# Example 186: MPS/tensor-network low-entanglement adiabatic_line.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(40, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=186) {
    let q = quantum_register(40)
    for layer in range(3) {
        H(q[layer % 40])
        CNOT(q[layer % 40], q[(layer + 1) % 40])
        Rz(q[(layer + 1) % 40], PI / (layer + 3))
    }
    print("adiabatic_line")
    print("logical_qubits", 40)
    print("shots", measure_all(q, shots=4))
}
```

## 187_mps_qft_lite_187.sq

```sansqrit
# Example 187: MPS/tensor-network low-entanglement qft_lite.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(44, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=187) {
    let q = quantum_register(44)
    for layer in range(4) {
        H(q[layer % 44])
        CNOT(q[layer % 44], q[(layer + 1) % 44])
        Rz(q[(layer + 1) % 44], PI / (layer + 3))
    }
    print("qft_lite")
    print("logical_qubits", 44)
    print("shots", measure_all(q, shots=4))
}
```

## 188_mps_bond_dimension_probe_188.sq

```sansqrit
# Example 188: MPS/tensor-network low-entanglement bond_dimension_probe.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(48, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=188) {
    let q = quantum_register(48)
    for layer in range(5) {
        H(q[layer % 48])
        CNOT(q[layer % 48], q[(layer + 1) % 48])
        Rz(q[(layer + 1) % 48], PI / (layer + 3))
    }
    print("bond_dimension_probe")
    print("logical_qubits", 48)
    print("shots", measure_all(q, shots=4))
}
```

## 189_mps_matrix_product_feature_map_189.sq

```sansqrit
# Example 189: MPS/tensor-network low-entanglement matrix_product_feature_map.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(52, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=189) {
    let q = quantum_register(52)
    for layer in range(3) {
        H(q[layer % 52])
        CNOT(q[layer % 52], q[(layer + 1) % 52])
        Rz(q[(layer + 1) % 52], PI / (layer + 3))
    }
    print("matrix_product_feature_map")
    print("logical_qubits", 52)
    print("shots", measure_all(q, shots=4))
}
```

## 190_mps_spin_chain_190.sq

```sansqrit
# Example 190: MPS/tensor-network low-entanglement spin_chain.
# Requires optional NumPy extra: pip install sansqrit[tensor].
simulate(24, engine="mps", max_bond_dim=32, cutoff=1e-10, seed=190) {
    let q = quantum_register(24)
    for layer in range(4) {
        H(q[layer % 24])
        CNOT(q[layer % 24], q[(layer + 1) % 24])
        Rz(q[(layer + 1) % 24], PI / (layer + 3))
    }
    print("spin_chain")
    print("logical_qubits", 24)
    print("shots", measure_all(q, shots=4))
}
```

## 191_noise_readout_channel_191.sq

```sansqrit
# Example 191: density-matrix/noise model readout_channel.
simulate(2, engine="density", seed=191) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_bit_flip(q[1], 0.020)
    print("readout_channel")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 192_noise_amplitude_decay_192.sq

```sansqrit
# Example 192: density-matrix/noise model amplitude_decay.
simulate(2, engine="density", seed=192) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_amplitude_damping(q[1], 0.030)
    print("amplitude_decay")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 193_noise_phase_noise_193.sq

```sansqrit
# Example 193: density-matrix/noise model phase_noise.
simulate(2, engine="density", seed=193) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_phase_flip(q[0], 0.040)
    print("phase_noise")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 194_noise_depolarizing_benchmark_194.sq

```sansqrit
# Example 194: density-matrix/noise model depolarizing_benchmark.
simulate(2, engine="density", seed=194) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[1], 0.050)
    print("depolarizing_benchmark")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 195_noise_noisy_bell_195.sq

```sansqrit
# Example 195: density-matrix/noise model noisy_bell.
simulate(2, engine="density", seed=195) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[0], 0.010)
    print("noisy_bell")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 196_noise_readout_channel_196.sq

```sansqrit
# Example 196: density-matrix/noise model readout_channel.
simulate(2, engine="density", seed=196) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_bit_flip(q[1], 0.020)
    print("readout_channel")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 197_noise_amplitude_decay_197.sq

```sansqrit
# Example 197: density-matrix/noise model amplitude_decay.
simulate(2, engine="density", seed=197) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_amplitude_damping(q[1], 0.030)
    print("amplitude_decay")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 198_noise_phase_noise_198.sq

```sansqrit
# Example 198: density-matrix/noise model phase_noise.
simulate(2, engine="density", seed=198) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_phase_flip(q[0], 0.040)
    print("phase_noise")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 199_noise_depolarizing_benchmark_199.sq

```sansqrit
# Example 199: density-matrix/noise model depolarizing_benchmark.
simulate(2, engine="density", seed=199) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[1], 0.050)
    print("depolarizing_benchmark")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 200_noise_noisy_bell_200.sq

```sansqrit
# Example 200: density-matrix/noise model noisy_bell.
simulate(2, engine="density", seed=200) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[0], 0.010)
    print("noisy_bell")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 201_noise_readout_channel_201.sq

```sansqrit
# Example 201: density-matrix/noise model readout_channel.
simulate(2, engine="density", seed=201) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_bit_flip(q[1], 0.020)
    print("readout_channel")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 202_noise_amplitude_decay_202.sq

```sansqrit
# Example 202: density-matrix/noise model amplitude_decay.
simulate(2, engine="density", seed=202) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_amplitude_damping(q[1], 0.030)
    print("amplitude_decay")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 203_noise_phase_noise_203.sq

```sansqrit
# Example 203: density-matrix/noise model phase_noise.
simulate(2, engine="density", seed=203) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_phase_flip(q[0], 0.040)
    print("phase_noise")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 204_noise_depolarizing_benchmark_204.sq

```sansqrit
# Example 204: density-matrix/noise model depolarizing_benchmark.
simulate(2, engine="density", seed=204) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[1], 0.050)
    print("depolarizing_benchmark")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 205_noise_noisy_bell_205.sq

```sansqrit
# Example 205: density-matrix/noise model noisy_bell.
simulate(2, engine="density", seed=205) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[0], 0.010)
    print("noisy_bell")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 206_noise_readout_channel_206.sq

```sansqrit
# Example 206: density-matrix/noise model readout_channel.
simulate(2, engine="density", seed=206) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_bit_flip(q[1], 0.020)
    print("readout_channel")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 207_noise_amplitude_decay_207.sq

```sansqrit
# Example 207: density-matrix/noise model amplitude_decay.
simulate(2, engine="density", seed=207) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_amplitude_damping(q[1], 0.030)
    print("amplitude_decay")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 208_noise_phase_noise_208.sq

```sansqrit
# Example 208: density-matrix/noise model phase_noise.
simulate(2, engine="density", seed=208) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_phase_flip(q[0], 0.040)
    print("phase_noise")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 209_noise_depolarizing_benchmark_209.sq

```sansqrit
# Example 209: density-matrix/noise model depolarizing_benchmark.
simulate(2, engine="density", seed=209) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[1], 0.050)
    print("depolarizing_benchmark")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 210_noise_noisy_bell_210.sq

```sansqrit
# Example 210: density-matrix/noise model noisy_bell.
simulate(2, engine="density", seed=210) {
    let q = quantum_register(2)
    H(q[0])
    CNOT(q[0], q[1])
    noise_depolarize(q[0], 0.010)
    print("noisy_bell")
    print("probabilities", probabilities(q))
    print("shots", measure_all(q, shots=16))
}
```

## 211_algorithm_grover_cyber_signature_211.sq

```sansqrit
# Example 211: algorithm-level application - grover_cyber_signature.
let tag = "grover_cyber_signature"
print("running", tag)
print(grover_search(5, 17, shots=64, seed=211))
```

## 212_algorithm_qaoa_logistics_triangle_212.sq

```sansqrit
# Example 212: algorithm-level application - qaoa_logistics_triangle.
let tag = "qaoa_logistics_triangle"
print("running", tag)
print(qaoa_maxcut(4, [(0,1), (1,2), (2,3), (3,0)], p=1, shots=64, seed=212))
```

## 213_algorithm_vqe_molecule_scan_213.sq

```sansqrit
# Example 213: algorithm-level application - vqe_molecule_scan.
let tag = "vqe_molecule_scan"
print("running", tag)
print(vqe_h2(0.735, max_iter=16, seed=213))
```

## 214_algorithm_phase_estimation_sensor_214.sq

```sansqrit
# Example 214: algorithm-level application - phase_estimation_sensor.
let tag = "phase_estimation_sensor"
print("running", tag)
print(quantum_phase_estimation(0.3125, 4, shots=64, seed=214))
```

## 215_algorithm_hhl_toy_linear_system_215.sq

```sansqrit
# Example 215: algorithm-level application - hhl_toy_linear_system.
let tag = "hhl_toy_linear_system"
print("running", tag)
print(hhl_solve([[1.0, 0.0], [0.0, 2.0]], [1.0, 0.5]))
```

## 216_algorithm_bernstein_vazirani_secret_216.sq

```sansqrit
# Example 216: algorithm-level application - bernstein_vazirani_secret.
let tag = "bernstein_vazirani_secret"
print("running", tag)
print(bernstein_vazirani("101101"))
```

## 217_algorithm_deutsch_jozsa_balanced_217.sq

```sansqrit
# Example 217: algorithm-level application - deutsch_jozsa_balanced.
let tag = "deutsch_jozsa_balanced"
print("running", tag)
print(deutsch_jozsa(5, "balanced", seed=217))
```

## 218_algorithm_quantum_counting_inventory_218.sq

```sansqrit
# Example 218: algorithm-level application - quantum_counting_inventory.
let tag = "quantum_counting_inventory"
print("running", tag)
print(quantum_counting(8, 13, 5))
```

## 219_algorithm_amplitude_estimation_risk_219.sq

```sansqrit
# Example 219: algorithm-level application - amplitude_estimation_risk.
let tag = "amplitude_estimation_risk"
print("running", tag)
print(amplitude_estimation(0.18, 5))
```

## 220_algorithm_bb84_key_distribution_220.sq

```sansqrit
# Example 220: algorithm-level application - bb84_key_distribution.
let tag = "bb84_key_distribution"
print("running", tag)
print(bb84_qkd(16, seed=220))
```

## 221_algorithm_grover_cyber_signature_221.sq

```sansqrit
# Example 221: algorithm-level application - grover_cyber_signature.
let tag = "grover_cyber_signature"
print("running", tag)
print(grover_search(5, 17, shots=64, seed=221))
```

## 222_algorithm_qaoa_logistics_triangle_222.sq

```sansqrit
# Example 222: algorithm-level application - qaoa_logistics_triangle.
let tag = "qaoa_logistics_triangle"
print("running", tag)
print(qaoa_maxcut(4, [(0,1), (1,2), (2,3), (3,0)], p=1, shots=64, seed=222))
```

## 223_algorithm_vqe_molecule_scan_223.sq

```sansqrit
# Example 223: algorithm-level application - vqe_molecule_scan.
let tag = "vqe_molecule_scan"
print("running", tag)
print(vqe_h2(0.735, max_iter=16, seed=223))
```

## 224_algorithm_phase_estimation_sensor_224.sq

```sansqrit
# Example 224: algorithm-level application - phase_estimation_sensor.
let tag = "phase_estimation_sensor"
print("running", tag)
print(quantum_phase_estimation(0.3125, 4, shots=64, seed=224))
```

## 225_algorithm_hhl_toy_linear_system_225.sq

```sansqrit
# Example 225: algorithm-level application - hhl_toy_linear_system.
let tag = "hhl_toy_linear_system"
print("running", tag)
print(hhl_solve([[1.0, 0.0], [0.0, 2.0]], [1.0, 0.5]))
```

## 226_algorithm_bernstein_vazirani_secret_226.sq

```sansqrit
# Example 226: algorithm-level application - bernstein_vazirani_secret.
let tag = "bernstein_vazirani_secret"
print("running", tag)
print(bernstein_vazirani("101101"))
```

## 227_algorithm_deutsch_jozsa_balanced_227.sq

```sansqrit
# Example 227: algorithm-level application - deutsch_jozsa_balanced.
let tag = "deutsch_jozsa_balanced"
print("running", tag)
print(deutsch_jozsa(5, "balanced", seed=227))
```

## 228_algorithm_quantum_counting_inventory_228.sq

```sansqrit
# Example 228: algorithm-level application - quantum_counting_inventory.
let tag = "quantum_counting_inventory"
print("running", tag)
print(quantum_counting(8, 13, 5))
```

## 229_algorithm_amplitude_estimation_risk_229.sq

```sansqrit
# Example 229: algorithm-level application - amplitude_estimation_risk.
let tag = "amplitude_estimation_risk"
print("running", tag)
print(amplitude_estimation(0.18, 5))
```

## 230_algorithm_bb84_key_distribution_230.sq

```sansqrit
# Example 230: algorithm-level application - bb84_key_distribution.
let tag = "bb84_key_distribution"
print("running", tag)
print(bb84_qkd(16, seed=230))
```

## 231_qml_feature_map_231.sq

```sansqrit
# Example 231: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(6, engine="sparse", seed=231) {
    let q = quantum_register(6)
    for i in range(6) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[6-1-i] * PI / 2)
    }
    for i in range(6-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 232_qml_feature_map_232.sq

```sansqrit
# Example 232: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(7, engine="sparse", seed=232) {
    let q = quantum_register(7)
    for i in range(7) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[7-1-i] * PI / 2)
    }
    for i in range(7-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 233_qml_feature_map_233.sq

```sansqrit
# Example 233: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(8, engine="sparse", seed=233) {
    let q = quantum_register(8)
    for i in range(8) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[8-1-i] * PI / 2)
    }
    for i in range(8-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 234_qml_feature_map_234.sq

```sansqrit
# Example 234: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(6, engine="sparse", seed=234) {
    let q = quantum_register(6)
    for i in range(6) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[6-1-i] * PI / 2)
    }
    for i in range(6-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 235_qml_feature_map_235.sq

```sansqrit
# Example 235: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(7, engine="sparse", seed=235) {
    let q = quantum_register(7)
    for i in range(7) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[7-1-i] * PI / 2)
    }
    for i in range(7-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 236_qml_feature_map_236.sq

```sansqrit
# Example 236: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(8, engine="sparse", seed=236) {
    let q = quantum_register(8)
    for i in range(8) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[8-1-i] * PI / 2)
    }
    for i in range(8-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 237_qml_feature_map_237.sq

```sansqrit
# Example 237: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(6, engine="sparse", seed=237) {
    let q = quantum_register(6)
    for i in range(6) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[6-1-i] * PI / 2)
    }
    for i in range(6-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 238_qml_feature_map_238.sq

```sansqrit
# Example 238: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(7, engine="sparse", seed=238) {
    let q = quantum_register(7)
    for i in range(7) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[7-1-i] * PI / 2)
    }
    for i in range(7-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 239_qml_feature_map_239.sq

```sansqrit
# Example 239: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(8, engine="sparse", seed=239) {
    let q = quantum_register(8)
    for i in range(8) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[8-1-i] * PI / 2)
    }
    for i in range(8-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 240_qml_feature_map_240.sq

```sansqrit
# Example 240: quantum ML feature map for tabular/scientific data.
let features = [0.12, 0.31, 0.07, 0.44, 0.23, 0.19, 0.27, 0.39]
simulate(6, engine="sparse", seed=240) {
    let q = quantum_register(6)
    for i in range(6) {
        Ry(q[i], features[i] * PI)
        Rz(q[i], features[6-1-i] * PI / 2)
    }
    for i in range(6-1) {
        CNOT(q[i], q[i + 1])
    }
    print("qml_feature_map")
    print("nnz", engine_nnz())
    print(measure_all(q, shots=16))
}
```

## 241_qasm3_export_climate_circuit.sq

```sansqrit
# Example 241: export a climate-risk sparse circuit to OpenQASM 3.
simulate(5, seed=241) {
    H(0)
    CNOT(0, 4)
    Rz(3, PI/7)
    print(export_qasm3())
}
```

## 242_qasm2_export_network_circuit.sq

```sansqrit
# Example 242: export a network-routing circuit to OpenQASM 2.
simulate(4, seed=242) {
    X(1)
    H(0)
    CNOT(0, 2)
    print(export_qasm2())
}
```

## 243_distributed_cluster_template.sq

```sansqrit
# Example 243: real distributed cluster template.
# Start workers in separate shells, then uncomment the simulate block.
# python -m sansqrit.cluster --host 127.0.0.1 --port 9101
# python -m sansqrit.cluster --host 127.0.0.1 --port 9102
# simulate(12, engine="distributed", addresses=[("127.0.0.1", 9101), ("127.0.0.1", 9102)]) {
#     H(0)
#     CNOT(0, 11)
#     print(measure_all(shots=4))
# }
print("distributed cluster template included; start workers before enabling")
```

## 244_gpu_cuda_template.sq

```sansqrit
# Example 244: GPU/CuPy backend template.
# Install CUDA/CuPy extra, then uncomment.
# simulate(6, engine="gpu", seed=244) {
#     H(0)
#     CNOT(0, 5)
#     print(measure_all(shots=8))
# }
print("GPU template included; requires sansqrit[gpu] and CUDA")
```

## 245_hybrid_backend_template.sq

```sansqrit
# Example 245: hybrid backend selection template.
simulate(150, engine="sharded", n_shards=12, seed=245) {
    X(149)
    H(0)
    CNOT(0, 149)
    print("hybrid-style sparse branch", engine_nnz())
}
```

## 246_formal_verification_qasm_reference.sq

```sansqrit
# Example 246: verification through QASM export / external SDK comparison.
simulate(3, seed=246) {
    H(0)
    CNOT(0, 1)
    CNOT(1, 2)
    print(export_qasm3())
}
```

## 247_optimizer_cancel_pairs.sq

```sansqrit
# Example 247: write circuits so the optimizer can cancel inverse pairs.
simulate(4, seed=247) {
    X(0)
    X(0)
    H(1)
    H(1)
    Rz(2, PI/8)
    Rz(2, -PI/8)
    print("optimizer-friendly cancellation pattern")
    print(export_qasm3())
}
```

## 248_ai_training_minimal_pair.sq

```sansqrit
# Example 248: paired input-output style useful for AI training.
# Intent: create a Bell state and return probability dictionary.
simulate(2, seed=248) {
    H(0)
    CNOT(0, 1)
    print(probabilities())
}
```

## 249_large_sparse_oracle_150q.sq

```sansqrit
# Example 249: 150-qubit sparse oracle-style marker.
simulate(150, engine="sharded", n_shards=20, workers=4, seed=249) {
    let q = quantum_register(150)
    X(q[12])
    X(q[77])
    H(q[0])
    CNOT(q[0], q[149])
    MCZ(q[0], q[12], q[77], q[149])
    print("150q oracle marker nnz", engine_nnz())
    print(measure_all(q, shots=4))
}
```

## 250_large_stabilizer_4096q.sq

```sansqrit
# Example 250: 4096-qubit Clifford/stabilizer monitoring pattern.
simulate(4096, engine="stabilizer", seed=250) {
    H(0)
    CNOT(0, 4095)
    S(2048)
    CZ(2048, 4095)
    print("4096-qubit stabilizer circuit")
    print(list(measure_all(shots=1).keys())[0][0:64])
}
```

