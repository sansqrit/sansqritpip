"""Small real TCP distributed sparse backend.

This module provides a correctness-first multi-node mode. Workers store sparse
state shards over TCP. The coordinator gathers shards for each gate, applies the
operation with the reference sparse engine, and repartitions. This is a real
multi-process/multi-machine protocol, but it is intentionally conservative and
not an MPI-grade high-performance simulator yet.
"""
from __future__ import annotations

import json
import socket
import socketserver
import threading
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .errors import QuantumError
from .gates import GateOp, canonical_gate_name, validate_gate_arity
from .sparse import SparseState
from .types import QuantumRegister, QubitRef, qubit_index


def encode_state(state: dict[int, complex]) -> dict[str, list[float]]:
    return {str(k): [float(v.real), float(v.imag)] for k, v in state.items()}


def decode_state(payload: dict[str, list[float]]) -> dict[int, complex]:
    return {int(k): complex(v[0], v[1]) for k, v in payload.items()}


class _ShardStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.state: dict[int, complex] = {}
        self.n_qubits = 0


class ShardWorkerHandler(socketserver.StreamRequestHandler):
    store = _ShardStore()

    def handle(self) -> None:  # pragma: no cover - exercised by integration tests/manual cluster
        for line in self.rfile:
            try:
                req = json.loads(line.decode("utf-8"))
                cmd = req.get("cmd")
                if cmd == "ping":
                    self._send({"ok": True, "message": "pong"})
                elif cmd == "set_state":
                    with self.store.lock:
                        self.store.n_qubits = int(req["n_qubits"])
                        self.store.state = decode_state(req.get("state", {}))
                    self._send({"ok": True, "nnz": len(self.store.state)})
                elif cmd == "get_state":
                    with self.store.lock:
                        self._send({"ok": True, "n_qubits": self.store.n_qubits, "state": encode_state(self.store.state)})
                elif cmd == "info":
                    with self.store.lock:
                        self._send({"ok": True, "n_qubits": self.store.n_qubits, "nnz": len(self.store.state)})
                elif cmd == "clear":
                    with self.store.lock:
                        self.store.state.clear()
                    self._send({"ok": True})
                elif cmd == "shutdown":
                    self._send({"ok": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                else:
                    self._send({"ok": False, "error": f"unknown command {cmd!r}"})
            except Exception as exc:
                self._send({"ok": False, "error": str(exc)})

    def _send(self, payload: dict) -> None:
        self.wfile.write((json.dumps(payload) + "\n").encode("utf-8"))
        self.wfile.flush()


class ShardWorkerServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def serve_worker(host: str = "0.0.0.0", port: int = 8765) -> None:
    """Run a shard worker process forever until it receives shutdown."""
    with ShardWorkerServer((host, port), ShardWorkerHandler) as server:
        server.serve_forever()


def start_worker_in_thread(host: str = "127.0.0.1", port: int = 0):
    """Start an in-process worker for tests and local demos."""
    server = ShardWorkerServer((host, port), ShardWorkerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address


@dataclass
class WorkerClient:
    host: str
    port: int
    timeout: float = 10.0

    def request(self, payload: dict) -> dict:
        data = (json.dumps(payload) + "\n").encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall(data)
            file = sock.makefile("rb")
            line = file.readline()
        if not line:
            raise QuantumError(f"worker {self.host}:{self.port} returned no response")
        resp = json.loads(line.decode("utf-8"))
        if not resp.get("ok"):
            raise QuantumError(f"worker {self.host}:{self.port} error: {resp.get('error')}")
        return resp


@dataclass
class DistributedSparseEngine:
    """Correctness-first multi-node sparse engine."""
    n_qubits: int
    workers: list[WorkerClient]
    eps: float = 1e-14
    history: list[GateOp] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.workers:
            raise QuantumError("DistributedSparseEngine requires at least one worker")
        self._set_global_state({0: 1+0j})

    @classmethod
    def from_addresses(cls, n_qubits: int, addresses: Iterable[str | tuple[str, int]], **kwargs):
        clients = []
        for item in addresses:
            if isinstance(item, str):
                host, port_s = item.rsplit(":", 1)
                clients.append(WorkerClient(host, int(port_s)))
            else:
                clients.append(WorkerClient(item[0], int(item[1])))
        return cls(n_qubits, clients, **kwargs)

    def _partition(self, state: dict[int, complex]) -> list[dict[int, complex]]:
        parts = [dict() for _ in self.workers]
        for basis, amp in state.items():
            parts[basis % len(parts)][basis] = amp
        return parts

    def _set_global_state(self, state: dict[int, complex]) -> None:
        for client, shard in zip(self.workers, self._partition(state)):
            client.request({"cmd": "set_state", "n_qubits": self.n_qubits, "state": encode_state(shard)})

    def _get_global_state(self) -> dict[int, complex]:
        state: dict[int, complex] = {}
        for client in self.workers:
            resp = client.request({"cmd": "get_state"})
            state.update(decode_state(resp.get("state", {})))
        return state

    @property
    def nnz(self) -> int:
        return len(self._get_global_state())

    def quantum_register(self) -> QuantumRegister:
        return QuantumRegister(self.n_qubits)

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        name = canonical_gate_name(name)
        qidx = tuple(qubit_index(q) for q in qubits)
        params = tuple(float(p) for p in params)
        validate_gate_arity(name, qidx, params)
        state = SparseState(self.n_qubits, self._get_global_state(), self.eps)
        if name in {"I", "X", "Y", "Z", "H", "S", "Sdg", "T", "Tdg", "SX", "SXdg", "Rx", "Ry", "Rz", "Phase", "U1", "U2", "U3"}:
            state.apply_single(name, qidx[0], params)
        elif name in {"CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "iSWAP", "ISWAP", "SqrtSWAP", "fSWAP", "FSWAP", "DCX", "CRx", "CRy", "CRz", "CP", "CU", "RXX", "RYY", "RZZ", "RZX", "ECR", "MS"}:
            state.apply_two(name, qidx[0], qidx[1], params)
        elif name in {"Toffoli", "CCX"}:
            state.apply_mcx(qidx[:2], qidx[2])
        elif name in {"Fredkin", "CSWAP"}:
            state.apply_swap_controlled(qidx[0], qidx[1], qidx[2])
        elif name == "CCZ":
            state.apply_ccz(qidx[0], qidx[1], qidx[2])
        elif name in {"MCX", "C3X", "C4X"}:
            state.apply_mcx(qidx[:-1], qidx[-1])
        elif name == "MCZ":
            state.apply_mcz(qidx)
        else:
            raise QuantumError(f"unsupported distributed gate {name}")
        self._set_global_state(state.amplitudes or {})
        self.history.append(GateOp(name, qidx, params))

    def probabilities(self) -> dict[str, float]:
        return SparseState(self.n_qubits, self._get_global_state(), self.eps).probabilities()  # type: ignore[return-value]

    def measure_all(self, shots: int = 1) -> dict[str, int]:
        return SparseState(self.n_qubits, self._get_global_state(), self.eps).sample(shots)

    def export_qasm2(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm2
        return export_qasm2(self.history, self.n_qubits, include_measure=include_measure)

    def export_qasm3(self, include_measure: bool = False) -> str:
        from .qasm import export_qasm3
        return export_qasm3(self.history, self.n_qubits, include_measure=include_measure)
