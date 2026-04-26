"""Diagnostics, logging and troubleshooting helpers for Sansqrit."""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import platform
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from . import __version__
from .architecture import dense_memory_estimate, lookup_architecture, scenario_table

_LOGGER = logging.getLogger("sansqrit")

@dataclass(frozen=True)
class BackendAvailability:
    name: str
    available: bool
    install_hint: str
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def optional_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def backends() -> list[BackendAvailability]:
    return [
        BackendAvailability("sparse", True, "built in", "Sparse state-vector dictionary for low-nonzero states."),
        BackendAvailability("sharded", True, "built in", "Partitions sparse amplitudes across local shards."),
        BackendAvailability("threaded", True, "built in", "Threaded sparse updates for large sparse maps."),
        BackendAvailability("hierarchical", True, "built in; numpy optional improves speed", "10-qubit dense blocks with MPS bridge promotion."),
        BackendAvailability("mps", True, "built in; numpy optional improves speed", "Matrix-product-state simulation for low-entanglement circuits."),
        BackendAvailability("stabilizer", True, "built in", "Clifford tableau simulation for large Clifford circuits."),
        BackendAvailability("density", True, "built in", "Density-matrix and noise-channel simulation for small circuits."),
        BackendAvailability("gpu", optional_available("cupy"), "pip install 'sansqrit[gpu]'", "Optional CuPy/CUDA dense vector backend."),
        BackendAvailability("qiskit", optional_available("qiskit"), "pip install 'sansqrit[qiskit]'", "Qiskit circuit export and verification."),
        BackendAvailability("cirq", optional_available("cirq"), "pip install 'sansqrit[cirq]'", "Cirq circuit export and verification."),
        BackendAvailability("braket", optional_available("braket"), "pip install 'sansqrit[braket]'", "Amazon Braket SDK export/local simulator workflow."),
        BackendAvailability("pennylane", optional_available("pennylane"), "pip install 'sansqrit[pennylane]'", "PennyLane QNode/QML integration."),
        BackendAvailability("stim", optional_available("stim"), "pip install stim", "Optional fast stabilizer/QEC circuit checks."),
        BackendAvailability("pymatching", optional_available("pymatching"), "pip install pymatching", "Optional MWPM surface-code/repetition-code decoding."),
    ]


def doctor() -> dict[str, Any]:
    data_dir = Path(__file__).resolve().parent / "data"
    docs_dir = Path(__file__).resolve().parent / "docs"
    examples_dir = Path(__file__).resolve().parent / "examples"
    return {
        "sansqrit_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
        "lookup_data_present": data_dir.exists() and any(data_dir.iterdir()),
        "lookup_files": sorted(p.name for p in data_dir.glob("*")) if data_dir.exists() else [],
        "docs_count": len(list(docs_dir.glob("*.md"))) if docs_dir.exists() else 0,
        "examples_count": len(list(examples_dir.glob("*.sq"))) if examples_dir.exists() else 0,
        "backends": [b.to_dict() for b in backends()],
        "lookup_policy": lookup_architecture(),
    }


def doctor_text() -> str:
    d = doctor()
    lines = [
        f"Sansqrit {d['sansqrit_version']}",
        f"Python {d['python']}",
        f"Platform {d['platform']}",
        f"Lookup data: {'yes' if d['lookup_data_present'] else 'no'} ({', '.join(d['lookup_files'])})",
        f"Packaged docs: {d['docs_count']}",
        f"Packaged examples: {d['examples_count']}",
        "Backends:",
    ]
    for b in d["backends"]:
        status = "available" if b["available"] else f"missing; {b['install_hint']}"
        lines.append(f"  - {b['name']}: {status} — {b['purpose']}")
    return "\n".join(lines)


def configure_logging(level: str = "INFO", path: str | None = None) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    handlers: list[logging.Handler]
    handlers = [logging.FileHandler(path, encoding="utf-8")] if path else [logging.StreamHandler()]
    logging.basicConfig(level=lvl, handlers=handlers, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    _LOGGER.setLevel(lvl)


def log_event(event: str, **fields: Any) -> None:
    _LOGGER.info("%s %s", event, json.dumps(fields, sort_keys=True, default=str))


def troubleshoot(topic: str | None = None) -> list[dict[str, str]]:
    items = [
        {"symptom": "120-qubit run is slow", "cause": "state may be expanding beyond sparse/low-entanglement assumptions", "fix": "run plan_backend(), use stabilizer/MPS/hierarchical, avoid h_all on non-Clifford dense circuits"},
        {"symptom": "lookup files not visible", "cause": "old wheel version or editable install without package data", "fix": "upgrade to packaged lookup release and check importlib.resources.files('sansqrit').joinpath('data')"},
        {"symptom": "Qiskit export fails", "cause": "unsupported gate or missing qiskit optional extra", "fix": "install sansqrit[qiskit], export QASM3 as fallback, or decompose unsupported gate"},
        {"symptom": "distributed backend errors", "cause": "workers not running or host/port blocked", "fix": "start sansqrit worker on each node, open ports, pass addresses=[('host', port)]"},
        {"symptom": "density backend memory explosion", "cause": "density matrices scale as 4^n", "fix": "use it for small noisy circuits; use stabilizer noise or sampling approximations for large circuits"},
        {"symptom": "surface-code decoder is not production-grade", "cause": "built-in decoder is educational", "fix": "install pymatching and use the MWPM-compatible adapter when available"},
        {"symptom": "GPU backend not available", "cause": "CuPy/CUDA not installed or no compatible GPU", "fix": "install sansqrit[gpu] with a matching CUDA runtime; otherwise use sparse/MPS/stabilizer"},
    ]
    if topic:
        t = topic.lower()
        items = [x for x in items if t in x["symptom"].lower() or t in x["cause"].lower() or t in x["fix"].lower()]
    return items


def estimate(qubits: int) -> dict[str, Any]:
    return {"dense": dense_memory_estimate(qubits).to_dict(), "recommended_scenarios": scenario_table()}
