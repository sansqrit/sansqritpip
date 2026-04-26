from sansqrit import QuantumEngine, run_code
from sansqrit.qec import logical_qubit, get_code, encode, inject_error, syndrome_and_correct, decode, SurfaceCodeLattice
from sansqrit.planner import analyze_operations


def test_bit_flip_qec_pipeline_corrects_single_x():
    e = QuantumEngine.create(5, seed=1)
    l = logical_qubit("bit_flip")
    encode(e, l)
    inject_error(e, l, "X", 1)
    result = syndrome_and_correct(e, l, ancilla_base=3)
    assert result.syndrome == (1, 1)
    assert result.corrections == [("X", 1)]
    decode(e, l)
    probs = e.probabilities()
    assert any(k.endswith("000") and v > 0.99 for k, v in probs.items())


def test_qec_code_registry_and_surface_lattice():
    assert get_code("shor9").n == 9
    assert get_code("steane7").syndrome_size() == 6
    lattice = SurfaceCodeLattice(3)
    assert len(lattice.data_qubits) == 9
    assert lattice.stabilizers()


def test_qec_dsl_helpers_available():
    env = run_code('''
simulate(5) {
  let q = quantum_register(5)
  let l = qec_logical("bit_flip")
  qec_encode(l)
  qec_inject_error(l, "X", 2)
  let r = qec_syndrome_and_correct(l, ancilla_base=3)
}
''')
    assert tuple(env["r"].syndrome) == (0, 1)


def test_planner_selects_stabilizer_for_large_clifford():
    ops = [("H", (0,), ()), ("CNOT", (0, 99), ())]
    plan = analyze_operations(100, ops)
    assert plan.backend == "stabilizer"
