from math import pi, isclose

from sansqrit import QuantumEngine, Circuit, run_code
from sansqrit.algorithms import grover_search, bernstein_vazirani, hhl_solve, bb84_qkd


def test_bell_state_probabilities():
    e = QuantumEngine.create(2, seed=7)
    e.H(0)
    e.CNOT(0, 1)
    probs = e.probabilities()
    assert isclose(probs["00"], 0.5, abs_tol=1e-12)
    assert isclose(probs["11"], 0.5, abs_tol=1e-12)


def test_lookup_sxdg_inverse():
    e = QuantumEngine.create(1)
    e.SX(0)
    e.SXdg(0)
    probs = e.probabilities()
    assert isclose(probs["0"], 1.0, abs_tol=1e-12)


def test_sharded_matches_sparse():
    a = QuantumEngine.create(4, backend="sparse", seed=1)
    b = QuantumEngine.create(4, backend="sharded", n_shards=4, workers=2, seed=1)
    for e in (a, b):
        e.H_all()
        e.CNOT(0, 3)
        e.RZZ(1, 2, pi/5)
        e.qft([0, 1, 2, 3])
    assert a.probabilities() == b.probabilities()


def test_dsl_run():
    env = run_code('''
simulate(2) {
  let q = quantum_register(2)
  H(q[0])
  CNOT(q[0], q[1])
  let p = probabilities(q)
}
''')
    assert env["p"]["00"] > 0.49
    assert env["p"]["11"] > 0.49


def test_circuit_qasm():
    c = Circuit(2).H(0).CNOT(0, 1)
    qasm = c.qasm2()
    assert "OPENQASM 2.0" in qasm
    assert "cx q[0], q[1];" in qasm


def test_algorithms_smoke():
    assert bernstein_vazirani("101") == [1, 0, 1]
    assert hhl_solve([[2, 0], [0, 4]], [2, 8]).solution == [1.0, 2.0]
    a, b, qber = bb84_qkd(8, seed=3)
    assert len(a) == len(b)
    assert 0 <= qber <= 1
