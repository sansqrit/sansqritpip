from sansqrit import QuantumEngine
from sansqrit.dsl import run_code


def test_hierarchical_local_matches_sparse():
    h = QuantumEngine.create(4, backend="hierarchical", block_size=2, max_bond_dim=None, cutoff=0.0)
    s = QuantumEngine.create(4, backend="sparse")
    ops = [("H", (0,), ()), ("X", (1,), ()), ("CNOT", (0, 1), ()), ("Z", (3,), ())]
    for name, qs, params in ops:
        h.apply(name, *qs, params=params)
        s.apply(name, *qs, params=params)
    hp = h.probabilities()
    sp = s.probabilities()
    assert set(hp) == set(sp)
    for k in sp:
        assert abs(hp[k] - sp[k]) < 1e-10
    assert h.hierarchical_report()["mode"] == "blocks"


def test_hierarchical_bridge_promotes_and_matches_sparse_probabilities():
    h = QuantumEngine.create(4, backend="hierarchical", block_size=2, max_bond_dim=None, cutoff=0.0)
    s = QuantumEngine.create(4, backend="sparse")
    ops = [("H", (1,), ()), ("CNOT", (1, 2), ()), ("Z", (2,), ())]
    for name, qs, params in ops:
        h.apply(name, *qs, params=params)
        s.apply(name, *qs, params=params)
    assert h.hierarchical_report()["mode"] == "mps"
    hp = h.probabilities()
    sp = s.probabilities()
    assert set(hp) == set(sp)
    for k in sp:
        assert abs(hp[k] - sp[k]) < 1e-10


def test_hierarchical_dsl_shard_apply_syntax():
    env = run_code('''
simulate(20, engine="hierarchical", block_size=10, max_bond_dim=null, cutoff=0.0) {
    q = quantum_register(20)
    shard block_A [0..9]
    apply H on block_A
    report = hierarchical_report()
}
''')
    report = env["report"]
    assert report["mode"] == "blocks"
    assert report["blocks"] == 2
    assert report["local_gate_count"] == 10
