"""Sansqrit: simplified Python DSL and sparse quantum simulator.

Main entry points:

- ``QuantumEngine`` for direct Python use.
- ``Circuit`` for circuit construction and QASM export.
- ``run_code`` / ``run_file`` for the Sansqrit DSL.
"""

__version__ = "0.3.4"

from .engine import QuantumEngine, EngineConfig, bell_state, ghz_state
from .circuit import Circuit
from .dsl import run_code, run_file, translate
from .types import QuantumRegister, QubitRef
from .errors import SansqritError, SansqritSyntaxError, SansqritRuntimeError, QuantumError
from . import algorithms
from .stabilizer import StabilizerEngine
from .density import DensityMatrixEngine
from .hierarchical import HierarchicalTensorEngine
from .optimizer import optimize_operations
from . import qec
from .qec import StabilizerCode, LogicalQubit, get_code, logical_qubit
from .planner import analyze_operations, BackendPlan
from .architecture import dense_memory_estimate, execution_flow_mermaid, architecture_layers
from .diagnostics import doctor, backends, troubleshoot
from .hardware import export_for_hardware, hardware_targets

__all__ = [
    "QuantumEngine", "EngineConfig", "Circuit", "QuantumRegister", "QubitRef",
    "bell_state", "ghz_state", "run_code", "run_file", "translate", "algorithms",
    "SansqritError", "SansqritSyntaxError", "SansqritRuntimeError", "QuantumError",
    "StabilizerEngine", "DensityMatrixEngine", "HierarchicalTensorEngine", "optimize_operations",
    "qec", "StabilizerCode", "LogicalQubit", "get_code", "logical_qubit",
    "analyze_operations", "BackendPlan", "dense_memory_estimate", "execution_flow_mermaid",
    "architecture_layers", "doctor", "backends", "troubleshoot",
    "export_for_hardware", "hardware_targets",
]


from .scenarios import scenario_info, load_scenarios, sample_scenarios, export_scenarios
