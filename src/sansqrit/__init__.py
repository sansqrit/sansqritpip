"""Sansqrit: simplified Python DSL and sparse quantum simulator.

Main entry points:

- ``QuantumEngine`` for direct Python use.
- ``Circuit`` for circuit construction and QASM export.
- ``run_code`` / ``run_file`` for the Sansqrit DSL.
"""
from .engine import QuantumEngine, EngineConfig, bell_state, ghz_state
from .circuit import Circuit
from .dsl import run_code, run_file, translate
from .types import QuantumRegister, QubitRef
from .errors import SansqritError, SansqritSyntaxError, SansqritRuntimeError, QuantumError
from . import algorithms
from .stabilizer import StabilizerEngine
from .density import DensityMatrixEngine
from .optimizer import optimize_operations

__all__ = [
    "QuantumEngine", "EngineConfig", "Circuit", "QuantumRegister", "QubitRef",
    "bell_state", "ghz_state", "run_code", "run_file", "translate", "algorithms",
    "SansqritError", "SansqritSyntaxError", "SansqritRuntimeError", "QuantumError",
    "StabilizerEngine", "DensityMatrixEngine", "optimize_operations",
]

__version__ = "0.3.0"
