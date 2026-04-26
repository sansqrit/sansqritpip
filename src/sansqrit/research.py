"""Research-informed feature matrix for Sansqrit."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class ResearchGap:
    area: str
    industry_pattern: str
    sansqrit_support: str
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def research_gaps() -> list[dict[str, Any]]:
    gaps = [
        ResearchGap("Auto backend selection", "Qiskit Aer automatic/method selection", "planner.py and engine('auto') guidance", "make engine('auto') execute planner output automatically for every run"),
        ResearchGap("MPS/tensor networks", "MPS/tensor methods for low-entanglement circuits", "mps.py and hierarchical bridge promotion", "add bond-dimension telemetry and canonicalization checks"),
        ResearchGap("Stabilizer/QEC speed", "Stim-style high-performance stabilizer/QEC workflows", "pure-Python stabilizer + optional stim detection", "optional stim adapter for very large QEC sampling"),
        ResearchGap("Surface-code decoding", "MWPM via PyMatching", "educational greedy decoder + optional availability detection", "full pymatching graph construction for surface code lattices"),
        ResearchGap("Hardware workflows", "Qiskit/Cirq/Braket/Azure/PennyLane ecosystems", "QASM and object exporters", "credential-free job templates and provider capability validation"),
        ResearchGap("GPU acceleration", "cuQuantum/cuStateVec/cuTensorNet", "optional CuPy backend", "optional cuQuantum tensor network path when installed"),
        ResearchGap("Formal verification", "equivalence checking and simulator cross-validation", "verification.py with installed SDK comparisons", "decision-diagram equivalence backend"),
    ]
    return [g.to_dict() for g in gaps]
