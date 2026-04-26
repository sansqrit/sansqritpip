from math import isclose

from sansqrit import QuantumEngine
from sansqrit.lookup import DEFAULT_LOOKUP, packaged_metadata


def test_packaged_lookup_metadata_and_files_available():
    meta = packaged_metadata()
    assert meta["format"] == "sansqrit-precomputed-lookup-v1"
    assert meta["max_embedded_qubits"] == 10
    assert DEFAULT_LOOKUP.has_single("H")
    assert DEFAULT_LOOKUP.has_two("CNOT")
    assert DEFAULT_LOOKUP.has_embedded_single(10, 7, "H")


def test_embedded_lookup_path_matches_matrix_path():
    a = QuantumEngine.create(10, use_lookup=True)
    b = QuantumEngine.create(10, use_lookup=False)
    for e in (a, b):
        e.H(7)
        e.SX(3)
        e.SXdg(3)
        e.X(9)
        e.CNOT(7, 9)
    assert a.probabilities() == b.probabilities()
    assert isclose(a.probabilities()["1000000000"], 0.5, abs_tol=1e-12)
    assert isclose(a.probabilities()["0010000000"], 0.5, abs_tol=1e-12)
