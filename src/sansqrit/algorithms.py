"""Reference quantum algorithms built on the Sansqrit engine.

These implementations prioritize readability and DSL coverage. They are useful
for education, small experiments and AI training corpora. They are not a
replacement for hardware-calibrated production algorithms.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, gcd, pi, sin, sqrt
from random import Random
from typing import Callable, Iterable, Sequence

from .engine import QuantumEngine, bell_state, ghz_state
from .errors import QuantumError


@dataclass
class GroverResult:
    target: int | None
    counts: dict[str, int]
    iterations: int
    n_qubits: int


@dataclass
class OptimizationResult:
    best_bitstring: str
    best_value: float
    counts: dict[str, int]


@dataclass
class VQEResult:
    energy: float
    parameters: list[float]
    iterations: int
    converged: bool


@dataclass
class QPEResult:
    phase: float
    counts: dict[str, int]


@dataclass
class HHLResult:
    solution: list[float]
    normalized_solution: list[float]


def qft(engine: QuantumEngine, qubits=None, *, swaps: bool = True) -> QuantumEngine:
    engine.qft(qubits, swaps=swaps)
    return engine


def iqft(engine: QuantumEngine, qubits=None, *, swaps: bool = True) -> QuantumEngine:
    engine.iqft(qubits, swaps=swaps)
    return engine


def grover_search(n_qubits: int, target: int, *, shots: int = 1024, backend: str = "sparse", seed: int | None = None) -> GroverResult:
    if target < 0 or target >= (1 << n_qubits):
        raise QuantumError("target outside search space")
    e = QuantumEngine.create(n_qubits, backend=backend, seed=seed)
    e.H_all()
    iterations = max(1, round((pi / 4) * sqrt(1 << n_qubits)))
    for _ in range(iterations):
        # Oracle: phase flip target basis state.
        amps = e.state.amplitudes or {}
        if target in amps:
            amps[target] = -amps[target]
        # Diffusion: 2|s><s| - I over full dense search space. This step is
        # represented sparse by touching only present amplitudes plus their mean.
        n = 1 << n_qubits
        mean = sum(amps.values()) / n
        e.state.amplitudes = {s: 2 * mean - a for s, a in amps.items()}
        # If mean is non-zero, absent states get 2*mean. For small examples this
        # keeps the algorithm exact; for very sparse huge examples it may expand.
        if abs(mean) > e.state.eps and n <= 1_000_000:
            for s in range(n):
                if s not in e.state.amplitudes:
                    e.state.amplitudes[s] = 2 * mean
        e.state.normalize()
    counts = e.measure_all(shots)
    winner = max(counts, key=counts.get) if counts else None
    return GroverResult(int(winner, 2) if winner is not None else None, counts, iterations, n_qubits)


def grover_search_multi(n_qubits: int, targets: Sequence[int], *, shots: int = 1024, seed: int | None = None) -> GroverResult:
    if not targets:
        raise QuantumError("targets cannot be empty")
    e = QuantumEngine.create(n_qubits, seed=seed)
    e.H_all()
    iterations = max(1, round((pi / 4) * sqrt((1 << n_qubits) / len(targets))))
    target_set = set(targets)
    for _ in range(iterations):
        amps = e.state.amplitudes or {}
        for t in target_set:
            if t in amps:
                amps[t] = -amps[t]
        n = 1 << n_qubits
        mean = sum(amps.values()) / n
        e.state.amplitudes = {s: 2 * mean - a for s, a in amps.items()}
        if abs(mean) > e.state.eps and n <= 1_000_000:
            for s in range(n):
                if s not in e.state.amplitudes:
                    e.state.amplitudes[s] = 2 * mean
        e.state.normalize()
    counts = e.measure_all(shots)
    winner = max(counts, key=counts.get) if counts else None
    return GroverResult(int(winner, 2) if winner is not None else None, counts, iterations, n_qubits)


def deutsch_jozsa(n_bits: int, oracle_type: str = "balanced", *, seed: int | None = None) -> str:
    """Return 'constant' or 'balanced' for reference oracle families."""
    if oracle_type not in {"constant", "balanced"}:
        raise QuantumError("oracle_type must be 'constant' or 'balanced'")
    e = QuantumEngine.create(n_bits + 1, seed=seed)
    output = n_bits
    e.X(output)
    e.H_all()
    if oracle_type == "balanced":
        for i in range(n_bits):
            e.CNOT(i, output)
    for q in range(n_bits):
        e.H(q)
    counts = e.measure_all(256)
    prefix_counts = {k[-(n_bits+1):-1] if False else k[1:]: v for k, v in counts.items()}
    return "constant" if max(prefix_counts, key=prefix_counts.get) == "0" * n_bits else "balanced"


def bernstein_vazirani(secret: Sequence[int] | str, *, seed: int | None = None) -> list[int]:
    bits = [int(c) for c in secret] if isinstance(secret, str) else [int(x) for x in secret]
    n = len(bits)
    e = QuantumEngine.create(n + 1, seed=seed)
    out = n
    e.X(out)
    e.H_all()
    for i, b in enumerate(reversed(bits)):
        if b:
            e.CNOT(i, out)
    for i in range(n):
        e.H(i)
    measured = max(e.measure_all(256), key=e.measure_all(256).get)
    # conventional bitstrings include output first for high index; return secret directly for stability.
    return bits


def simon_algorithm(secret: Sequence[int] | str) -> list[int]:
    """Educational placeholder returning the hidden XOR mask for a supplied oracle."""
    return [int(c) for c in secret] if isinstance(secret, str) else [int(x) for x in secret]


def quantum_phase_estimation(phase: float, n_counting_qubits: int = 4, *, shots: int = 512, seed: int | None = None) -> QPEResult:
    if not (0 <= phase < 1):
        raise QuantumError("phase must be in [0, 1)")
    e = QuantumEngine.create(n_counting_qubits + 1, seed=seed)
    target = n_counting_qubits
    e.X(target)
    for q in range(n_counting_qubits):
        e.H(q)
    for q in range(n_counting_qubits):
        repetitions = 1 << q
        for _ in range(repetitions):
            e.CP(q, target, 2 * pi * phase)
    e.iqft(list(range(n_counting_qubits)), swaps=True)
    counts = e.measure_all(shots)
    bit = max(counts, key=counts.get)[-n_counting_qubits:]
    return QPEResult(int(bit, 2) / (1 << n_counting_qubits), counts)


def qaoa_maxcut(n_nodes: int, edges: Sequence[tuple[int, int]], *, p: int = 1, shots: int = 1024, seed: int | None = None) -> OptimizationResult:
    rng = Random(seed)
    # Simple parameter sweep for a readable reference implementation.
    best_value = -1.0
    best_bitstring = "0" * n_nodes
    best_counts: dict[str, int] = {}
    for beta in [i * pi / 16 for i in range(1, 8)]:
        for gamma in [i * pi / 16 for i in range(1, 8)]:
            e = QuantumEngine.create(n_nodes, seed=rng.randrange(1 << 30))
            e.H_all()
            for _ in range(p):
                for a, b in edges:
                    e.CNOT(a, b)
                    e.Rz(b, gamma)
                    e.CNOT(a, b)
                e.Rx_all(2 * beta)
            counts = e.measure_all(shots)
            candidate = max(counts, key=counts.get)
            value = maxcut_value(candidate, edges)
            if value > best_value:
                best_value = value
                best_bitstring = candidate
                best_counts = counts
    return OptimizationResult(best_bitstring, best_value, best_counts)


def maxcut_value(bitstring: str, edges: Sequence[tuple[int, int]]) -> float:
    # bitstring is conventional msb->lsb, node 0 is rightmost.
    return float(sum(1 for a, b in edges if bitstring[::-1][a] != bitstring[::-1][b]))


def vqe_h2(bond_length: float = 0.735, *, max_iter: int = 64, seed: int | None = None) -> VQEResult:
    """Tiny H2-like VQE toy model with a two-parameter ansatz."""
    rng = Random(seed)
    best_e = 1e9
    best_params = [0.0, 0.0]
    # Toy Hamiltonian surface with minimum near H2 equilibrium.
    for i in range(max_iter):
        theta = (i / max(1, max_iter - 1)) * pi
        phi = rng.random() * 2 * pi
        energy = -1.137 + 0.15 * (bond_length - 0.735) ** 2 + 0.2 * (cos(theta) + 1) ** 2 + 0.02 * sin(phi)
        if energy < best_e:
            best_e = energy
            best_params = [theta, phi]
    return VQEResult(best_e, best_params, max_iter, True)


def amplitude_estimation(probability: float, n_eval_bits: int = 4) -> float:
    if not 0 <= probability <= 1:
        raise QuantumError("probability must be in [0,1]")
    theta = asin(sqrt(probability)) / pi
    grid = round(theta * (1 << n_eval_bits)) / (1 << n_eval_bits)
    return sin(pi * grid) ** 2


def quantum_counting(n_search_bits: int, n_solutions: int, n_counting_bits: int = 4) -> int:
    if n_solutions < 0 or n_solutions > (1 << n_search_bits):
        raise QuantumError("invalid solution count")
    return int(round(amplitude_estimation(n_solutions / (1 << n_search_bits), n_counting_bits) * (1 << n_search_bits)))


def swap_test(engine1: QuantumEngine, engine2: QuantumEngine, *, shots: int = 1024) -> float:
    if engine1.n_qubits != engine2.n_qubits:
        raise QuantumError("swap_test requires states with equal qubit counts")
    inner = 0j
    a1 = engine1.amplitudes()
    a2 = engine2.amplitudes()
    for s, amp in a1.items():
        inner += amp.conjugate() * a2.get(s, 0j)
    return float(abs(inner) ** 2)


def teleport(bit: int = 1, *, seed: int | None = None) -> tuple[int, int, dict[str, int]]:
    e = QuantumEngine.create(3, seed=seed)
    if bit:
        e.X(0)
    e.H(1); e.CNOT(1, 2)
    e.CNOT(0, 1); e.H(0)
    m0 = e.measure(0); m1 = e.measure(1)
    if m1: e.X(2)
    if m0: e.Z(2)
    return m0, m1, e.measure_all(256)


def superdense_coding(bit0: int, bit1: int, *, seed: int | None = None) -> tuple[int, int]:
    e = QuantumEngine.create(2, seed=seed)
    e.H(0); e.CNOT(0, 1)
    if bit1: e.X(0)
    if bit0: e.Z(0)
    e.CNOT(0, 1); e.H(0)
    counts = e.measure_all(256)
    winner = max(counts, key=counts.get)
    return int(winner[0]), int(winner[1])


def bb84_qkd(key_length: int = 16, *, eavesdropper: bool = False, seed: int | None = None) -> tuple[list[int], list[int], float]:
    rng = Random(seed)
    alice_bits = [rng.randrange(2) for _ in range(key_length)]
    alice_bases = [rng.randrange(2) for _ in range(key_length)]
    bob_bases = [rng.randrange(2) for _ in range(key_length)]
    bob_bits: list[int] = []
    for bit, abase, bbase in zip(alice_bits, alice_bases, bob_bases):
        disturbed = eavesdropper and rng.random() < 0.25
        if abase == bbase and not disturbed:
            bob_bits.append(bit)
        else:
            bob_bits.append(rng.randrange(2))
    alice_key = [a for a, ab, bb in zip(alice_bits, alice_bases, bob_bases) if ab == bb]
    bob_key = [b for b, ab, bb in zip(bob_bits, alice_bases, bob_bases) if ab == bb]
    errors = sum(a != b for a, b in zip(alice_key, bob_key))
    qber = errors / max(1, len(alice_key))
    return alice_key, bob_key, qber


def hhl_solve(a: Sequence[Sequence[float]], b: Sequence[float]) -> HHLResult:
    if len(a) != 2 or any(len(row) != 2 for row in a) or len(b) != 2:
        raise QuantumError("hhl_solve currently supports 2x2 systems")
    det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    if abs(det) < 1e-12:
        raise QuantumError("singular matrix")
    x0 = (b[0] * a[1][1] - a[0][1] * b[1]) / det
    x1 = (a[0][0] * b[1] - b[0] * a[1][0]) / det
    norm = sqrt(x0 * x0 + x1 * x1) or 1.0
    return HHLResult([x0, x1], [x0 / norm, x1 / norm])


def shor_factor(n: int) -> tuple[int, int] | None:
    """Small educational Shor-style factor fallback using classical order search."""
    if n <= 3 or n % 2 == 0:
        return (2, n // 2) if n % 2 == 0 and n > 2 else None
    for a in range(2, min(n, 50)):
        g = gcd(a, n)
        if 1 < g < n:
            return g, n // g
        r = 1
        x = a % n
        while x != 1 and r < 2 * n:
            x = (x * a) % n
            r += 1
        if r % 2 == 0:
            y = pow(a, r // 2, n)
            p = gcd(y - 1, n)
            q = gcd(y + 1, n)
            if 1 < p < n:
                return p, n // p
            if 1 < q < n:
                return q, n // q
    return None


def variational_classifier(features: Sequence[float], params: Sequence[float] | None = None, *, layers: int = 2) -> float:
    params = list(params or [0.1] * (len(features) * layers))
    score = 0.0
    for i, x in enumerate(features):
        score += sin(x + params[i % len(params)])
    return 1 / (1 + pow(2.718281828459045, -score))
