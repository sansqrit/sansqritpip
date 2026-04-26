"""Hardware export helpers for Sansqrit circuits.

Sansqrit cannot submit cloud jobs without the user's credentials and provider
configuration. This module produces provider-ready objects/payloads when optional
SDKs are installed, and always provides OpenQASM payloads as a portable fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .circuit import Circuit
from .errors import QuantumError
from .qasm import export_qasm2, export_qasm3
from .interop import to_qiskit, to_cirq, to_braket, apply_to_pennylane

@dataclass(frozen=True)
class HardwareTarget:
    provider: str
    export_modes: tuple[str, ...]
    notes: str
    install_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

TARGETS = {
    "qiskit": HardwareTarget("qiskit", ("qiskit.QuantumCircuit", "openqasm2", "openqasm3"), "IBM/Qiskit ecosystem; use provider runtime separately.", "pip install 'sansqrit[qiskit]'"),
    "ibm": HardwareTarget("ibm", ("qiskit.QuantumCircuit", "openqasm3"), "IBM Quantum via Qiskit Runtime; credentials are managed outside Sansqrit.", "pip install 'sansqrit[qiskit]'"),
    "cirq": HardwareTarget("cirq", ("cirq.Circuit", "openqasm3"), "Google/Cirq-style circuit object and simulators.", "pip install 'sansqrit[cirq]'"),
    "braket": HardwareTarget("braket", ("braket.circuits.Circuit", "openqasm3"), "Amazon Braket SDK local/cloud devices; credentials configured by AWS SDK.", "pip install 'sansqrit[braket]'"),
    "aws": HardwareTarget("aws", ("braket.circuits.Circuit", "openqasm3"), "Alias for Amazon Braket.", "pip install 'sansqrit[braket]'"),
    "azure": HardwareTarget("azure", ("openqasm3", "qiskit/cirq object"), "Azure Quantum can receive Qiskit/Cirq workflows through QDK integrations.", "install qdk/qiskit/cirq per Azure instructions"),
    "pennylane": HardwareTarget("pennylane", ("callable quantum function",), "PennyLane QNode/QML workflows; device selected by the user.", "pip install 'sansqrit[pennylane]'"),
    "openqasm2": HardwareTarget("openqasm2", ("text",), "Portable OpenQASM 2 text.", "built in"),
    "openqasm3": HardwareTarget("openqasm3", ("text",), "Portable OpenQASM 3 text.", "built in"),
}


def hardware_targets() -> list[dict[str, Any]]:
    return [t.to_dict() for t in TARGETS.values()]


def _as_circuit(circuit_or_engine: Any) -> Circuit:
    if isinstance(circuit_or_engine, Circuit):
        return circuit_or_engine
    if hasattr(circuit_or_engine, "history") and hasattr(circuit_or_engine, "n_qubits"):
        return Circuit(circuit_or_engine.n_qubits, list(circuit_or_engine.history))
    if hasattr(circuit_or_engine, "operations") and hasattr(circuit_or_engine, "n_qubits"):
        return Circuit(circuit_or_engine.n_qubits, list(circuit_or_engine.operations))
    raise QuantumError("expected a Sansqrit Circuit or engine with history")


def export_for_hardware(circuit_or_engine: Any, provider: str, *, include_measure: bool = True) -> Any:
    provider_key = provider.lower().replace("-", "_")
    if provider_key == "aws":
        provider_key = "braket"
    circ = _as_circuit(circuit_or_engine)
    if provider_key == "openqasm2":
        return export_qasm2(circ.operations, circ.n_qubits, include_measure=include_measure)
    if provider_key in {"openqasm3", "azure"}:
        return {"provider": provider_key, "format": "openqasm3", "shots_parameter": "provider-specific", "qasm": export_qasm3(circ.operations, circ.n_qubits, include_measure=include_measure), "notes": TARGETS.get(provider_key, TARGETS["openqasm3"]).notes}
    if provider_key in {"qiskit", "ibm"}:
        try:
            return to_qiskit(circ)
        except Exception:
            return {"provider": provider_key, "format": "openqasm3", "qasm": export_qasm3(circ.operations, circ.n_qubits, include_measure=include_measure), "install_hint": TARGETS["qiskit"].install_hint}
    if provider_key == "cirq":
        try:
            return to_cirq(circ)
        except Exception:
            return {"provider": provider_key, "format": "openqasm3", "qasm": export_qasm3(circ.operations, circ.n_qubits, include_measure=include_measure), "install_hint": TARGETS["cirq"].install_hint}
    if provider_key == "braket":
        try:
            return to_braket(circ)
        except Exception:
            return {"provider": provider_key, "format": "openqasm3", "qasm": export_qasm3(circ.operations, circ.n_qubits, include_measure=include_measure), "install_hint": TARGETS["braket"].install_hint}
    if provider_key == "pennylane":
        return apply_to_pennylane(circ)
    raise QuantumError(f"unknown hardware provider {provider!r}; known: {sorted(TARGETS)}")


def hardware_payload_summary(circuit_or_engine: Any) -> dict[str, Any]:
    circ = _as_circuit(circuit_or_engine)
    return {"n_qubits": circ.n_qubits, "n_operations": len(circ.operations), "recommended_export_order": ["qiskit", "openqasm3", "braket", "cirq", "pennylane"], "targets": hardware_targets()}
