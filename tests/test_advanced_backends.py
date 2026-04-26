from sansqrit import Circuit
from sansqrit.stabilizer import StabilizerEngine
from sansqrit.density import DensityMatrixEngine
from sansqrit.cluster import start_worker_in_thread, DistributedSparseEngine


def test_stabilizer_large_clifford_bell_pair():
    e = StabilizerEngine(128, seed=123)
    e.H(0)
    e.CNOT(0, 127)
    counts = e.measure_all(32)
    assert set(counts).issubset({"0" * 128, "1" + "0" * 126 + "1"})


def test_hybrid_selects_stabilizer_for_clifford():
    c = Circuit(2).H(0).CNOT(0, 1)
    e = c.run(backend="hybrid", seed=1)
    assert e.hybrid_report.selected_backend == "stabilizer"


def test_mps_matches_sparse_for_bell_probabilities():
    c = Circuit(2).H(0).CNOT(0, 1)
    mps = c.run(backend="mps", seed=1).probabilities()
    sparse = c.run(backend="sparse", seed=1).probabilities()
    assert set(mps) == set(sparse)
    assert all(abs(mps[k] - sparse[k]) < 1e-12 for k in sparse)


def test_density_trace_preserved_by_noise():
    e = DensityMatrixEngine(1, seed=1)
    e.H(0)
    e.depolarize(0, 0.2)
    assert abs(e.trace() - 1) < 1e-9


def test_optimizer_cancels_inverse_operations():
    c, report = Circuit(1).H(0).H(0).Rz(0, 0.5).Rz(0, -0.5).optimize()
    assert report.after == 0
    assert c.operations == []


def test_distributed_sparse_local_worker_matches_sparse():
    server, thread, addr = start_worker_in_thread(port=0)
    try:
        e = DistributedSparseEngine.from_addresses(2, [addr])
        e.apply("H", 0)
        e.apply("CNOT", 0, 1)
        assert e.probabilities() == Circuit(2).H(0).CNOT(0, 1).run().probabilities()
    finally:
        try:
            del e
        except Exception:
            pass
        server.shutdown()
        server.server_close()
        thread.join(1)
