"""Runtime helpers exposed to translated Sansqrit programs."""
from __future__ import annotations

import builtins as _py_builtins
import csv
import json
from contextlib import AbstractContextManager
from functools import reduce as _py_reduce
from math import *  # noqa: F403,F401 - intended for DSL globals
from pathlib import Path
from statistics import mean as _mean
from typing import Any, Callable, Iterable

from .engine import QuantumEngine, bell_state, ghz_state
from .errors import SansqritRuntimeError
from .types import QuantumRegister, QubitRef
from . import algorithms as _alg

_current_engine: QuantumEngine | None = None
_last_engine: QuantumEngine | None = None

PI = pi
TAU = tau
E = e
HBAR = 1.054_571_817e-34
PLANCK = 6.626_070_15e-34
LIGHT_SPEED = 299_792_458.0
BOLTZMANN = 1.380_649e-23
AVOGADRO = 6.022_140_76e23

class Pipeable:
    def __init__(self, func: Callable[[Any], Any]):
        self.func = func
    def __call__(self, value: Any) -> Any:
        return self.func(value)


def __pipe__(value: Any, stage: Any) -> Any:
    if isinstance(stage, Pipeable):
        return stage(value)
    if callable(stage):
        return stage(value)
    raise SansqritRuntimeError(f"pipeline stage is not callable: {stage!r}")


def map(fn: Callable[[Any], Any], seq: Iterable[Any] | None = None):  # noqa: A001 - DSL builtin
    if seq is None:
        return Pipeable(lambda value: [_py_builtins.map(fn, value)][0] and [fn(x) for x in value])
    return [fn(x) for x in seq]


def filter(fn: Callable[[Any], bool], seq: Iterable[Any] | None = None):  # noqa: A001
    if seq is None:
        return Pipeable(lambda value: [x for x in value if fn(x)])
    return [x for x in seq if fn(x)]


def reduce(fn: Callable[[Any, Any], Any], seq: Iterable[Any] | None = None, initial: Any = None):  # noqa: A001
    def apply(value: Iterable[Any]):
        items = list(value)
        if not items and initial is None:
            raise SansqritRuntimeError("reduce() of empty sequence with no initial value")
        if initial is None:
            return _py_reduce(fn, items)
        return _py_reduce(fn, items, initial)
    if seq is None:
        return Pipeable(apply)
    return apply(seq)


def sort(seq: Iterable[Any], reverse: bool = False):
    return sorted(seq, reverse=reverse)


def enumerate(seq: Iterable[Any]):  # noqa: A001
    return list(_py_builtins.enumerate(seq))


def zip(a: Iterable[Any], b: Iterable[Any]):  # noqa: A001
    return list(_py_builtins.zip(a, b))


def sum(seq: Iterable[Any]):  # noqa: A001
    return _py_builtins.sum(seq)


def mean(seq: Iterable[float]) -> float:
    items = list(seq)
    if not items:
        raise SansqritRuntimeError("mean() of empty sequence")
    return float(_mean(items))


def range_step(start: float, stop: float, step: float) -> list[float]:
    if step == 0:
        raise SansqritRuntimeError("range_step step cannot be zero")
    out = []
    x = start
    if step > 0:
        while x < stop:
            out.append(x)
            x += step
    else:
        while x > stop:
            out.append(x)
            x += step
    return out


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: str, text: Any) -> None:
    Path(path).write_text(str(text), encoding="utf-8")


def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, obj: Any) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class simulate(AbstractContextManager):
    def __init__(self, n_qubits: int | None = None, *, engine: str = "sparse", backend: str | None = None,
                 qubits: int | None = None, n_shards: int = 1, workers: int = 1,
                 seed: int | None = None, use_lookup: bool = True, max_bond_dim: int | None = None,
                 cutoff: float = 0.0, addresses: list | None = None, block_size: int = 10):
        self.n_qubits = n_qubits or qubits or 1
        self.backend = backend or engine
        self.n_shards = n_shards
        self.workers = workers
        self.seed = seed
        self.use_lookup = use_lookup
        self.max_bond_dim = max_bond_dim
        self.cutoff = cutoff
        self.addresses = addresses
        self.block_size = block_size
        self.engine_obj = None
        self.previous: QuantumEngine | None = None

    def __enter__(self) -> QuantumEngine:
        global _current_engine, _last_engine
        self.previous = _current_engine
        self.engine_obj = QuantumEngine.create(self.n_qubits, backend=self.backend, n_shards=self.n_shards,
                                               workers=self.workers, use_lookup=self.use_lookup, seed=self.seed,
                                               max_bond_dim=self.max_bond_dim, cutoff=self.cutoff, addresses=self.addresses,
                                               block_size=self.block_size)
        _current_engine = self.engine_obj
        _last_engine = self.engine_obj
        return self.engine_obj

    def __exit__(self, exc_type, exc, tb) -> bool:
        global _current_engine
        _current_engine = self.previous
        return False


def current_engine() -> QuantumEngine:
    if _current_engine is None:
        raise SansqritRuntimeError("quantum operation requires a simulate block or active QuantumEngine")
    return _current_engine


def quantum_register(n_qubits: int) -> QuantumRegister:
    global _current_engine, _last_engine
    if _current_engine is None or _current_engine.n_qubits != n_qubits:
        _current_engine = QuantumEngine.create(n_qubits)
        _last_engine = _current_engine
    return _current_engine.quantum_register()

def last_engine() -> QuantumEngine | None:
    return _last_engine


def _gate(name: str, *args: Any, params: tuple[float, ...] = ()) -> None:
    current_engine().apply(name, *args, params=params)

# Gate functions exposed to DSL ------------------------------------------------
def I(q): _gate("I", q)
def X(q): _gate("X", q)
def Y(q): _gate("Y", q)
def Z(q): _gate("Z", q)
def H(q): _gate("H", q)
def S(q): _gate("S", q)
def Sdg(q): _gate("Sdg", q)
def T(q): _gate("T", q)
def Tdg(q): _gate("Tdg", q)
def SX(q): _gate("SX", q)
def SXdg(q): _gate("SXdg", q)
def Rx(q, theta): _gate("Rx", q, params=(theta,))
def Ry(q, theta): _gate("Ry", q, params=(theta,))
def Rz(q, theta): _gate("Rz", q, params=(theta,))
def Phase(q, theta): _gate("Phase", q, params=(theta,))
def U1(q, theta): _gate("U1", q, params=(theta,))
def U2(q, phi, lam): _gate("U2", q, params=(phi, lam))
def U3(q, theta, phi, lam): _gate("U3", q, params=(theta, phi, lam))
def CNOT(c, t): _gate("CNOT", c, t)
def CX(c, t): CNOT(c, t)
def CZ(c, t): _gate("CZ", c, t)
def CY(c, t): _gate("CY", c, t)
def CH(c, t): _gate("CH", c, t)
def CSX(c, t): _gate("CSX", c, t)
def SWAP(a, b): _gate("SWAP", a, b)
def iSWAP(a, b): _gate("iSWAP", a, b)
def SqrtSWAP(a, b): _gate("SqrtSWAP", a, b)
def fSWAP(a, b): _gate("fSWAP", a, b)
def DCX(a, b): _gate("DCX", a, b)
def CRx(c, t, theta): _gate("CRx", c, t, params=(theta,))
def CRy(c, t, theta): _gate("CRy", c, t, params=(theta,))
def CRz(c, t, theta): _gate("CRz", c, t, params=(theta,))
def CP(c, t, theta): _gate("CP", c, t, params=(theta,))
def CU(c, t, theta, phi, lam): _gate("CU", c, t, params=(theta, phi, lam))
def RXX(a, b, theta): _gate("RXX", a, b, params=(theta,))
def RYY(a, b, theta): _gate("RYY", a, b, params=(theta,))
def RZZ(a, b, theta): _gate("RZZ", a, b, params=(theta,))
def RZX(a, b, theta): _gate("RZX", a, b, params=(theta,))
def ECR(a, b): _gate("ECR", a, b)
def MS(a, b): _gate("MS", a, b)
def Toffoli(a, b, c): _gate("Toffoli", a, b, c)
def CCX(a, b, c): Toffoli(a, b, c)
def Fredkin(c, a, b): _gate("Fredkin", c, a, b)
def CSWAP(c, a, b): Fredkin(c, a, b)
def CCZ(a, b, c): _gate("CCZ", a, b, c)
def MCX(*qs): _gate("MCX", *qs)
def MCZ(*qs): _gate("MCZ", *qs)
def C3X(a, b, c, t): _gate("C3X", a, b, c, t)
def C4X(a, b, c, d, t): _gate("C4X", a, b, c, d, t)

def H_all(qubits=None): current_engine().H_all(qubits)
def Rx_all(theta, qubits=None): current_engine().Rx_all(theta, qubits)
def Ry_all(theta, qubits=None): current_engine().Ry_all(theta, qubits)
def Rz_all(theta, qubits=None): current_engine().Rz_all(theta, qubits)
def qft(q=None): current_engine().qft(q)
def iqft(q=None): current_engine().iqft(q)
def measure(q): return current_engine().measure(q)
def measure_all(q=None, shots: int = 1): return current_engine().measure_all(shots)
def probabilities(q=None): return current_engine().probabilities()
def expectation_z(q): return current_engine().expectation_z(q)
def expectation_zz(a, b): return current_engine().expectation_zz(a, b)
def engine_nnz(): return current_engine().nnz
def export_qasm2(path: str | None = None):
    text = current_engine().export_qasm2()
    if path: write_file(path, text)
    return text
def export_qasm3(path: str | None = None):
    text = current_engine().export_qasm3()
    if path: write_file(path, text)
    return text

def shards():
    info = current_engine().shard_info()
    out = []
    for s in info:
        out.append(s if isinstance(s, dict) else s.__dict__)
    return out


class ShardMapping:
    def __init__(self, name: str, start: int, end: int):
        self.name = name
        self.start = int(start)
        self.end = int(end)
    def __iter__(self):
        return iter(range(self.start, self.end + 1))
    def __len__(self):
        return self.end - self.start + 1
    def __repr__(self):
        return f"ShardMapping({self.name!r}, {self.start}..{self.end})"

def shard(name: str, start: int, end: int):
    return ShardMapping(name, start, end)

def apply_block(gate: str, block: ShardMapping, *params):
    for q in block:
        current_engine().apply(gate, q, params=tuple(float(p) for p in params))

def hierarchical_report():
    engine = current_engine()
    if hasattr(engine, "hierarchical_report"):
        return engine.hierarchical_report()
    return {"backend": type(engine).__name__, "hierarchical": False}


def noise_depolarize(q, p):
    engine = current_engine()
    if not hasattr(engine, "depolarize"):
        raise SansqritRuntimeError("noise_depolarize requires simulate(..., engine='density')")
    return engine.depolarize(q, p)

def noise_bit_flip(q, p):
    engine = current_engine()
    if not hasattr(engine, "bit_flip"):
        raise SansqritRuntimeError("noise_bit_flip requires simulate(..., engine='density')")
    return engine.bit_flip(q, p)

def noise_phase_flip(q, p):
    engine = current_engine()
    if not hasattr(engine, "phase_flip"):
        raise SansqritRuntimeError("noise_phase_flip requires simulate(..., engine='density')")
    return engine.phase_flip(q, p)

def noise_amplitude_damping(q, gamma):
    engine = current_engine()
    if not hasattr(engine, "amplitude_damping"):
        raise SansqritRuntimeError("noise_amplitude_damping requires simulate(..., engine='density')")
    return engine.amplitude_damping(q, gamma)

def optimize_circuit(circuit):
    return circuit.optimize()

def verify_circuit(circuit):
    from .verification import verify_all_available
    return verify_all_available(circuit)

def to_qiskit(circuit):
    from .interop import to_qiskit as _to_qiskit
    return _to_qiskit(circuit)

def to_cirq(circuit):
    from .interop import to_cirq as _to_cirq
    return _to_cirq(circuit)

def to_braket(circuit):
    from .interop import to_braket as _to_braket
    return _to_braket(circuit)

def to_pennylane(circuit):
    from .interop import apply_to_pennylane
    return apply_to_pennylane(circuit)

# Algorithm aliases for DSL
grover_search = _alg.grover_search
grover_search_multi = _alg.grover_search_multi
shor_factor = _alg.shor_factor
vqe_h2 = _alg.vqe_h2
qaoa_maxcut = _alg.qaoa_maxcut
quantum_phase_estimation = _alg.quantum_phase_estimation
hhl_solve = _alg.hhl_solve
bernstein_vazirani = _alg.bernstein_vazirani
simon_algorithm = _alg.simon_algorithm
deutsch_jozsa = _alg.deutsch_jozsa
quantum_counting = _alg.quantum_counting
swap_test = _alg.swap_test
teleport = _alg.teleport
superdense_coding = _alg.superdense_coding
bb84_qkd = _alg.bb84_qkd
amplitude_estimation = _alg.amplitude_estimation
variational_classifier = _alg.variational_classifier


def make_globals() -> dict[str, Any]:
    env = {name: obj for name, obj in globals().items() if not name.startswith("_")}
    env.update({
        "len": len, "int": int, "float": float, "str": str, "bool": bool,
        "abs": abs, "min": min, "max": max, "round": round, "pow": pow,
        "print": print, "list": list, "dict": dict, "set": set, "tuple": tuple,
        "range": range, "__pipe__": __pipe__,
        "true": True, "false": False, "None": None,
    })
    return env

# QEC helpers exposed to DSL --------------------------------------------------
def qec_code(name: str, distance: int | None = None):
    from .qec import get_code
    return get_code(name, distance=distance)

def qec_codes():
    from .qec import list_codes
    return list_codes()

def qec_logical(code: str = "bit_flip", base: int = 0, name: str = "logical", distance: int | None = None):
    from .qec import logical_qubit
    return logical_qubit(code, base=base, name=name, distance=distance)

def qec_encode(logical):
    from .qec import encode
    return encode(current_engine(), logical)

def qec_decode(logical):
    from .qec import decode
    return decode(current_engine(), logical)

def qec_syndrome(logical, ancilla_base: int | None = None):
    from .qec import measure_syndrome
    return measure_syndrome(current_engine(), logical, ancilla_base=ancilla_base)

def qec_correct(logical, syndrome):
    from .qec import correct
    return correct(current_engine(), logical, syndrome)

def qec_syndrome_and_correct(logical, ancilla_base: int | None = None):
    from .qec import syndrome_and_correct
    return syndrome_and_correct(current_engine(), logical, ancilla_base=ancilla_base)

def qec_inject_error(logical, pauli: str, physical_offset: int):
    from .qec import inject_error
    return inject_error(current_engine(), logical, pauli, physical_offset)

def logical_x(logical):
    from .qec import logical_x as _logical_x
    return _logical_x(current_engine(), logical)

def logical_z(logical):
    from .qec import logical_z as _logical_z
    return _logical_z(current_engine(), logical)

def logical_h(logical):
    from .qec import logical_h as _logical_h
    return _logical_h(current_engine(), logical)

def logical_s(logical):
    from .qec import logical_s as _logical_s
    return _logical_s(current_engine(), logical)

def logical_cx(control, target):
    from .qec import logical_cnot
    return logical_cnot(current_engine(), control, target)

def qec_surface_lattice(distance: int = 3):
    from .qec import SurfaceCodeLattice
    return SurfaceCodeLattice(distance)

def qec_syndrome_circuit(logical, ancilla_base: int | None = None):
    from .qec import syndrome_circuit
    return syndrome_circuit(logical, ancilla_base=ancilla_base)

def lookup_profile():
    engine = current_engine()
    if hasattr(engine, "lookup_report"):
        return engine.lookup_report()
    return {"backend": type(engine).__name__, "lookup_profile": "not supported"}

def plan_backend(circuit_or_n_qubits, operations=None):
    from .planner import analyze_operations
    if hasattr(circuit_or_n_qubits, "operations"):
        return analyze_operations(circuit_or_n_qubits.n_qubits, circuit_or_n_qubits.operations).to_dict()
    return analyze_operations(int(circuit_or_n_qubits), operations or []).to_dict()

# Architecture, hardware, diagnostics and AI-training helpers -----------------
def sansqrit_doctor():
    from .diagnostics import doctor
    return doctor()

def sansqrit_backends():
    from .diagnostics import backends
    return [b.to_dict() for b in backends()]

def estimate_qubits(n_qubits: int):
    from .diagnostics import estimate
    return estimate(int(n_qubits))

def execution_flow():
    from .architecture import execution_flow_mermaid
    return execution_flow_mermaid()

def architecture_layers():
    from .architecture import architecture_layers as _layers
    return _layers()

def lookup_architecture():
    from .architecture import lookup_architecture as _lookup_architecture
    return _lookup_architecture()

def explain_120_qubits_dense():
    from .architecture import explain_120_qubits_dense as _explain
    return _explain()

def hardware_targets():
    from .hardware import hardware_targets as _targets
    return _targets()

def export_hardware(provider: str = "openqasm3"):
    from .hardware import export_for_hardware
    return export_for_hardware(current_engine(), provider)

def hardware_payload_summary():
    from .hardware import hardware_payload_summary as _summary
    return _summary(current_engine())

def troubleshooting(topic: str | None = None):
    from .diagnostics import troubleshoot
    return troubleshoot(topic)

def research_gaps():
    from .research import research_gaps as _gaps
    return _gaps()

def write_training_jsonl(path: str):
    from .dataset import generate_jsonl
    return generate_jsonl(path)


def training_dataset_info():
    from .dataset import dataset_info
    return dataset_info()

def training_dataset_sample(split: str = "sft_train", n: int = 3):
    from .dataset import sample_records
    return sample_records(split, n)

def export_training_dataset(output_dir: str, split: str | None = None, limit: int | None = None):
    from .dataset import export_dataset
    splits = [split] if split else None
    return export_dataset(output_dir, splits=splits, limit=limit)

def enable_logging(level: str = "INFO", path: str | None = None):
    from .diagnostics import configure_logging
    return configure_logging(level, path)

def log_sansqrit_event(event: str, fields: dict | None = None):
    from .diagnostics import log_event
    return log_event(event, **(fields or {}))

def qec_optional_features():
    from .qec import qec_optional_features as _features
    return _features()

def qec_stim_syndrome_text(logical, ancilla_base: int | None = None):
    from .qec import syndrome_circuit_as_stim_text
    return syndrome_circuit_as_stim_text(logical, ancilla_base=ancilla_base)


# Real-world scenario corpus helpers ------------------------------------------
def real_world_scenarios_info():
    from .scenarios import scenario_info
    return scenario_info()

def real_world_scenario_sample(n: int = 3, domain: str | None = None):
    from .scenarios import sample_scenarios
    return sample_scenarios(n, domain=domain)

def export_real_world_scenarios(path: str, limit: int | None = None, domain: str | None = None):
    from .scenarios import export_scenarios
    return export_scenarios(path, limit=limit, domain=domain)

# v0.3.6 advanced industry/runtime helpers ----------------------------------
def explain_backend(n_qubits: int, operations=None):
    from .planner import explain_backend_plan
    return explain_backend_plan(n_qubits, operations or [])


def planner_features(n_qubits: int, operations=None):
    from .planner import analyze_features
    return analyze_features(n_qubits, operations or []).to_dict()


def distributed_capabilities():
    from .cluster import distributed_capabilities as _dc
    return _dc()


def gpu_capabilities():
    from .gpu import gpu_capabilities as _gc
    return _gc()


def gpu_memory_estimate(n_qubits: int):
    from .gpu import estimate_gpu_statevector_memory
    return estimate_gpu_statevector_memory(n_qubits)


def cuquantum_recommendation(n_qubits: int, circuit_type: str = "auto"):
    from .gpu import CuQuantumAdapter
    return CuQuantumAdapter().recommendation(n_qubits, circuit_type)


def qasm3_mid_circuit_template(n_qubits: int = 2):
    from .qasm import qasm3_mid_circuit_template as _tmpl
    return _tmpl(n_qubits)


def qasm3_advanced(path: str | None = None):
    from .qasm import export_qasm3_advanced
    text = export_qasm3_advanced(current_engine().history, current_engine().n_qubits, include_measure=True,
                                 pragmas=["sansqrit advanced qasm3 export"])
    if path:
        write_file(path, text)
    return text


def qec_stim_surface_task(distance: int = 3, rounds: int | None = None, p: float = 0.001):
    from .qec import stim_surface_code_task
    return stim_surface_code_task(distance, rounds, p)


def qec_threshold_sweep(distances=None, physical_error_rates=None):
    from .qec import qec_threshold_sweep_template
    return qec_threshold_sweep_template(distances or (3,5,7), physical_error_rates or (0.001,0.003,0.01))


def qec_logical_resource_estimate(logical_qubits: int, logical_depth: int, distance: int = 3, factories: int = 0):
    from .qec import logical_resource_estimate
    return logical_resource_estimate(logical_qubits, logical_depth, code_distance=distance, factories=factories)


def conformance_report():
    from .circuit import Circuit
    from .verification import conformance_report as _report
    e = current_engine()
    return _report(Circuit(e.n_qubits, list(e.history)))
