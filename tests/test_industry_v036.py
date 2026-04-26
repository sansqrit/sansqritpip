from sansqrit.circuit import Circuit
from sansqrit.planner import analyze_operations, analyze_features
from sansqrit.qasm import qasm3_mid_circuit_template, Qasm3Builder
from sansqrit.gpu import gpu_capabilities, estimate_gpu_statevector_memory
from sansqrit.qec import qec_threshold_sweep_template, logical_resource_estimate
from sansqrit.hardware import hardware_targets


def test_adaptive_planner_extended_stabilizer():
    c = Circuit(120).H(0).CNOT(0, 1).add("T", 2)
    plan = analyze_operations(c.n_qubits, c.operations)
    assert plan.backend == "extended_stabilizer"
    assert plan.non_clifford_gates == 1


def test_planner_hierarchical_components():
    ops = [("H", [0], []), ("CNOT", [0, 1], []), ("H", [20], []), ("CNOT", [20, 21], [])]
    plan = analyze_operations(160, ops)
    assert plan.backend == "hierarchical"
    assert analyze_features(160, ops).max_component_size <= 2


def test_qasm3_mid_circuit_template():
    text = qasm3_mid_circuit_template(2)
    assert "if (c[0] == 1)" in text
    assert "delay[100ns]" in text
    assert "measure" in text


def test_gpu_capability_helpers():
    caps = gpu_capabilities()
    assert "cuquantum" in caps
    assert estimate_gpu_statevector_memory(4)["statevector_bytes"] == 16 * 16


def test_qec_planning_helpers():
    assert qec_threshold_sweep_template([3], [0.001])[0]["decoder"] == "PyMatching MWPM"
    assert logical_resource_estimate(10, 100, code_distance=3)["total_physical_qubits"] > 0


def test_hardware_targets_include_new_paths():
    providers = {t["provider"] for t in hardware_targets()}
    assert {"cudaq", "stim", "pymatching", "qir"}.issubset(providers)
