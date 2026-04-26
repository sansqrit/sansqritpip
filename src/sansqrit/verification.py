"""Formal-ish cross-check helpers against known simulators.

These helpers are optional and run only when the target SDK is installed. They
are intended for CI/regression testing, not mathematical proof certificates.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from .circuit import Circuit
from .errors import QuantumError
from .interop import to_cirq, to_qiskit


@dataclass(frozen=True)
class VerificationResult:
    backend: str
    passed: bool
    max_delta: float
    details: str


def compare_probabilities(a: dict[str, float], b: dict[str, float], *, atol: float = 1e-8) -> VerificationResult:
    keys = set(a) | set(b)
    max_delta = max((abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys), default=0.0)
    return VerificationResult("probabilities", max_delta <= atol, max_delta, f"{len(keys)} basis states compared")


def verify_with_qiskit(circuit: Circuit, *, atol: float = 1e-8) -> VerificationResult:
    try:
        from qiskit.quantum_info import Statevector
    except Exception as exc:
        raise QuantumError("Qiskit verification requires qiskit. Install with: pip install sansqrit[qiskit]") from exc
    sans = circuit.run(backend="sparse").probabilities()
    qc = to_qiskit(circuit)
    sv = Statevector.from_instruction(qc)
    probs = sv.probabilities_dict()
    result = compare_probabilities(sans, {k: float(v) for k, v in probs.items()}, atol=atol)
    return VerificationResult("qiskit", result.passed, result.max_delta, result.details)


def verify_with_cirq(circuit: Circuit, *, atol: float = 1e-8) -> VerificationResult:
    try:
        import cirq
    except Exception as exc:
        raise QuantumError("Cirq verification requires cirq. Install with: pip install sansqrit[cirq]") from exc
    sans = circuit.run(backend="sparse").probabilities()
    cc = to_cirq(circuit)
    result = cirq.Simulator().simulate(cc)
    probs = {}
    for i, amp in enumerate(result.final_state_vector):
        p = abs(complex(amp)) ** 2
        if p > atol:
            probs[format(i, f"0{circuit.n_qubits}b")] = p
    res = compare_probabilities(sans, probs, atol=atol)
    return VerificationResult("cirq", res.passed, res.max_delta, res.details)


def verify_all_available(circuit: Circuit, *, atol: float = 1e-8) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    for fn in (verify_with_qiskit, verify_with_cirq):
        try:
            results.append(fn(circuit, atol=atol))
        except Exception as exc:
            results.append(VerificationResult(fn.__name__.replace("verify_with_", ""), False, float("nan"), str(exc)))
    return results
