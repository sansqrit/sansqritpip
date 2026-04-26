"""Sansqrit: adaptive quantum DSL and simulator toolkit.

The top-level package is intentionally lightweight. Heavy simulator backends
(NumPy MPS, density matrix, distributed workers, QEC, optional vendor SDKs)
are imported lazily so commands such as ``sansqrit --help`` and
``from sansqrit.dsl import translate`` stay fast and reliable.
"""
from __future__ import annotations

__version__ = "0.3.6"

_LAZY_EXPORTS = {
    "QuantumEngine": (".engine", "QuantumEngine"),
    "EngineConfig": (".engine", "EngineConfig"),
    "bell_state": (".engine", "bell_state"),
    "ghz_state": (".engine", "ghz_state"),
    "Circuit": (".circuit", "Circuit"),
    "run_code": (".dsl", "run_code"),
    "run_file": (".dsl", "run_file"),
    "translate": (".dsl", "translate"),
    "QuantumRegister": (".types", "QuantumRegister"),
    "QubitRef": (".types", "QubitRef"),
    "SansqritError": (".errors", "SansqritError"),
    "SansqritSyntaxError": (".errors", "SansqritSyntaxError"),
    "SansqritRuntimeError": (".errors", "SansqritRuntimeError"),
    "QuantumError": (".errors", "QuantumError"),
    "StabilizerEngine": (".stabilizer", "StabilizerEngine"),
    "DensityMatrixEngine": (".density", "DensityMatrixEngine"),
    "HierarchicalTensorEngine": (".hierarchical", "HierarchicalTensorEngine"),
    "optimize_operations": (".optimizer", "optimize_operations"),
    "StabilizerCode": (".qec", "StabilizerCode"),
    "LogicalQubit": (".qec", "LogicalQubit"),
    "get_code": (".qec", "get_code"),
    "logical_qubit": (".qec", "logical_qubit"),
    "analyze_operations": (".planner", "analyze_operations"),
    "analyze_features": (".planner", "analyze_features"),
    "explain_backend_plan": (".planner", "explain_backend_plan"),
    "BackendPlan": (".planner", "BackendPlan"),
    "CircuitFeatures": (".planner", "CircuitFeatures"),
    "dense_memory_estimate": (".architecture", "dense_memory_estimate"),
    "execution_flow_mermaid": (".architecture", "execution_flow_mermaid"),
    "architecture_layers": (".architecture", "architecture_layers"),
    "doctor": (".diagnostics", "doctor"),
    "backends": (".diagnostics", "backends"),
    "troubleshoot": (".diagnostics", "troubleshoot"),
    "export_for_hardware": (".hardware", "export_for_hardware"),
    "hardware_targets": (".hardware", "hardware_targets"),
    "scenario_info": (".scenarios", "scenario_info"),
    "load_scenarios": (".scenarios", "load_scenarios"),
    "sample_scenarios": (".scenarios", "sample_scenarios"),
    "export_scenarios": (".scenarios", "export_scenarios"),
}

__all__ = sorted(["__version__", "algorithms", "qec", *_LAZY_EXPORTS.keys()])


def __getattr__(name: str):
    if name in {"algorithms", "qec"}:
        import importlib
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    if name in _LAZY_EXPORTS:
        import importlib
        module_name, attr = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_name, __name__)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
