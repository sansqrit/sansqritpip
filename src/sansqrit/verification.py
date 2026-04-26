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


def verify_with_braket(circuit: Circuit, *, shots: int = 0, atol: float = 1e-8) -> VerificationResult:
    """Verify Braket exportability and optionally local-simulator probabilities.

    If the Braket SDK/local simulator is unavailable, this returns a failed result
    with install guidance instead of breaking package imports.
    """
    try:
        from braket.devices import LocalSimulator
        from .interop import to_braket
    except Exception as exc:
        return VerificationResult("braket", False, float("nan"), "Amazon Braket SDK not installed: " + str(exc))
    try:
        bc = to_braket(circuit)
        if shots and shots > 0:
            result = LocalSimulator().run(bc, shots=shots).result()
            counts = result.measurement_counts
            total = sum(counts.values()) or 1
            probs = {k: v / total for k, v in counts.items()}
            sans_counts = circuit.run(backend="sparse", shots=shots).copy()
            sans_probs = {k: v / shots for k, v in sans_counts.items()}
            res = compare_probabilities(sans_probs, probs, atol=max(atol, 0.05))
            return VerificationResult("braket", res.passed, res.max_delta, "LocalSimulator sampled comparison")
        return VerificationResult("braket", True, 0.0, "Braket circuit object export succeeded")
    except Exception as exc:
        return VerificationResult("braket", False, float("nan"), str(exc))


def verify_with_stim(circuit: Circuit, *, atol: float = 1e-8) -> VerificationResult:
    """Verify Clifford circuits with Stim when installed.

    Stim is measurement/syndrome oriented; this helper currently verifies that a
    Sansqrit Clifford circuit can be converted into a Stim-like text stream and
    parsed by Stim if available.
    """
    try:
        import stim
    except Exception as exc:
        return VerificationResult("stim", False, float("nan"), "Stim not installed: " + str(exc))
    try:
        lines = []
        for op in circuit.operations:
            name = op.name
            if name == "CNOT": name = "CX"
            if name in {"H", "X", "Y", "Z", "S", "CX", "CZ", "SWAP"}:
                lines.append(name + " " + " ".join(str(q) for q in op.qubits))
            else:
                return VerificationResult("stim", False, float("nan"), f"non-Stim/unsupported gate {op.name}")
        stim.Circuit("\n".join(lines))
        return VerificationResult("stim", True, 0.0, "Stim parsed Clifford circuit")
    except Exception as exc:
        return VerificationResult("stim", False, float("nan"), str(exc))


def conformance_report(circuit: Circuit, *, atol: float = 1e-8) -> dict:
    """Run all available cross-framework checks and return a JSON-safe report."""
    checks = [verify_with_qiskit, verify_with_cirq]
    results = []
    for fn in checks:
        try:
            r = fn(circuit, atol=atol)
        except Exception as exc:
            r = VerificationResult(fn.__name__.replace("verify_with_", ""), False, float("nan"), str(exc))
        results.append(r.__dict__)
    results.append(verify_with_braket(circuit, atol=atol).__dict__)
    results.append(verify_with_stim(circuit, atol=atol).__dict__)
    return {"n_qubits": circuit.n_qubits, "operations": len(circuit.operations), "results": results}

# Override all-available to include newer adapters.
def verify_all_available(circuit: Circuit, *, atol: float = 1e-8) -> list[VerificationResult]:  # type: ignore[override]
    out: list[VerificationResult] = []
    for fn in (verify_with_qiskit, verify_with_cirq):
        try:
            out.append(fn(circuit, atol=atol))
        except Exception as exc:
            out.append(VerificationResult(fn.__name__.replace("verify_with_", ""), False, float("nan"), str(exc)))
    out.append(verify_with_braket(circuit, atol=atol))
    out.append(verify_with_stim(circuit, atol=atol))
    return out
