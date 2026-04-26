"""Production-oriented TCP distributed sparse backend for Sansqrit.

The backend uses a tiny JSON-lines protocol implemented with ordinary sockets.
It supports compressed payloads, batched gate application and checkpoint/restore.
It avoids heavyweight dependencies but exposes Ray/Dask/MPI capability detection
for users who want to orchestrate workers externally.
"""
from __future__ import annotations

import base64
import gzip
import importlib.util
import json
import os
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence, Any

from .errors import QuantumError
from .gates import GateOp, canonical_gate_name, validate_gate_arity
from .sparse import SparseState
from .types import QuantumRegister, QubitRef, qubit_index


def encode_state(state: dict[int, complex]) -> dict[str, list[float]]:
    return {str(k): [float(v.real), float(v.imag)] for k, v in state.items()}


def decode_state(payload: dict[str, list[float]]) -> dict[int, complex]:
    return {int(k): complex(v[0], v[1]) for k, v in payload.items()}


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def encode_compressed_payload(payload: dict) -> dict:
    return {"cmd": "compressed", "codec": "gzip+base64", "payload": base64.b64encode(gzip.compress(_json_bytes(payload))).decode("ascii")}


def decode_compressed_payload(envelope: dict) -> dict:
    if envelope.get("cmd") != "compressed":
        return envelope
    if envelope.get("codec") != "gzip+base64":
        raise QuantumError(f"unsupported compression codec {envelope.get('codec')!r}")
    return json.loads(gzip.decompress(base64.b64decode(envelope["payload"])).decode("utf-8"))


class _ShardStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.state: dict[int, complex] = {}
        self.n_qubits = 0
        self.shutdown = False


class _ThreadedWorker:
    def __init__(self, host: str, port: int):
        self.store = _ShardStore()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen()
        self.server_address = self.sock.getsockname()
        self._closed = threading.Event()
        self._threads: list[threading.Thread] = []

    def serve_forever(self) -> None:  # pragma: no cover - server loop
        self.sock.settimeout(0.2)
        try:
            while not self.store.shutdown:
                try:
                    conn, _addr = self.sock.accept()
                except socket.timeout:
                    continue
                t = threading.Thread(target=self._handle_conn, args=(conn,), daemon=True)
                self._threads.append(t)
                t.start()
        finally:
            self.server_close()
            self._closed.set()

    def _handle_conn(self, conn: socket.socket) -> None:
        with conn:
            data = b""
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
                if b"\n" in chunk:
                    break
            line = data.split(b"\n", 1)[0]
            try:
                req = decode_compressed_payload(json.loads(line.decode("utf-8"))) if line else {}
                resp = self._dispatch(req)
            except Exception as exc:
                resp = {"ok": False, "error": str(exc)}
            conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))

    def _dispatch(self, req: dict) -> dict:
        cmd = req.get("cmd")
        if cmd == "ping":
            return {"ok": True, "message": "pong"}
        if cmd == "set_state":
            with self.store.lock:
                self.store.n_qubits = int(req["n_qubits"])
                self.store.state = decode_state(req.get("state", {}))
                return {"ok": True, "nnz": len(self.store.state)}
        if cmd == "get_state":
            with self.store.lock:
                return {"ok": True, "n_qubits": self.store.n_qubits, "state": encode_state(self.store.state)}
        if cmd == "info":
            with self.store.lock:
                return {"ok": True, "n_qubits": self.store.n_qubits, "nnz": len(self.store.state), "protocol": "sansqrit-jsonl-v2", "compression": "gzip+base64", "checkpoint": True}
        if cmd == "clear":
            with self.store.lock:
                self.store.state.clear()
            return {"ok": True}
        if cmd == "checkpoint":
            path = Path(req.get("path") or f"sansqrit_worker_{os.getpid()}_{int(time.time())}.json.gz")
            with self.store.lock:
                data = {"n_qubits": self.store.n_qubits, "state": encode_state(self.store.state)}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(_json_bytes(data)))
            return {"ok": True, "path": str(path), "nnz": len(data["state"])}
        if cmd == "restore":
            data = json.loads(gzip.decompress(Path(req["path"]).read_bytes()).decode("utf-8"))
            with self.store.lock:
                self.store.n_qubits = int(data["n_qubits"])
                self.store.state = decode_state(data.get("state", {}))
                return {"ok": True, "nnz": len(self.store.state)}
        if cmd == "shutdown":
            self.store.shutdown = True
            return {"ok": True}
        return {"ok": False, "error": f"unknown command {cmd!r}"}

    def shutdown(self) -> None:
        self.store.shutdown = True
        try:
            with socket.create_connection(self.server_address, timeout=0.2) as s:
                s.sendall(b'{"cmd":"shutdown"}\n')
        except OSError:
            pass
        self._closed.wait(1.0)
        for t in list(self._threads):
            t.join(timeout=0.2)

    def server_close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def serve_worker(host: str = "0.0.0.0", port: int = 8765) -> None:
    server = _ThreadedWorker(host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def start_worker_in_thread(host: str = "127.0.0.1", port: int = 0):
    server = _ThreadedWorker(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address


@dataclass
class WorkerClient:
    host: str
    port: int
    timeout: float = 10.0
    compression: bool = False

    def request(self, payload: dict) -> dict:
        if self.compression:
            payload = encode_compressed_payload(payload)
        data = (json.dumps(payload) + "\n").encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall(data)
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            line = sock.makefile("rb").readline()
        if not line:
            raise QuantumError(f"worker {self.host}:{self.port} returned no response")
        resp = json.loads(line.decode("utf-8"))
        if not resp.get("ok"):
            raise QuantumError(f"worker {self.host}:{self.port} error: {resp.get('error')}")
        return resp


def worker_capabilities(client: WorkerClient) -> dict:
    return client.request({"cmd": "info"})


def distributed_capabilities() -> dict:
    return {
        "tcp_sparse_workers": True,
        "compressed_payloads": True,
        "batched_gate_application": True,
        "checkpoint_restore": True,
        "ray_available": importlib.util.find_spec("ray") is not None,
        "dask_available": importlib.util.find_spec("dask") is not None,
        "mpi4py_available": importlib.util.find_spec("mpi4py") is not None,
        "notes": "TCP mode is built in. Ray/Dask/MPI are optional orchestration adapters for production clusters.",
    }



class DistributedSparseEngine:
    """Multi-worker sparse engine with compressed transfers and batching."""
    def __init__(self, n_qubits: int, workers: list[WorkerClient], eps: float = 1e-14, history: list[GateOp] | None = None):
        self.n_qubits = int(n_qubits)
        self.workers = list(workers)
        self.eps = float(eps)
        self.history = list(history or [])
        if not self.workers:
            raise QuantumError("DistributedSparseEngine requires at least one worker")
        self._set_global_state({0: 1+0j})

    @classmethod
    def from_addresses(cls, n_qubits: int, addresses: Iterable[str | tuple[str, int] | tuple[str, int, bool]], **kwargs):
        clients = []
        for item in addresses:
            if isinstance(item, str):
                host, port_s = item.rsplit(":", 1)
                clients.append(WorkerClient(host, int(port_s)))
            else:
                compression = bool(item[2]) if len(item) > 2 else False  # type: ignore[arg-type]
                clients.append(WorkerClient(str(item[0]), int(item[1]), compression=compression))
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

    def _normalize_op(self, name: str, qubits: Sequence[int], params: Sequence[float] = ()) -> GateOp:
        gname = canonical_gate_name(name)
        qidx = tuple(int(q) for q in qubits)
        p = tuple(float(x) for x in params)
        validate_gate_arity(gname, qidx, p)
        return GateOp(gname, qidx, p)

    def _apply_to_state(self, state: SparseState, op: GateOp) -> None:
        if op.name in {"I", "X", "Y", "Z", "H", "S", "Sdg", "T", "Tdg", "SX", "SXdg", "Rx", "Ry", "Rz", "Phase", "U1", "U2", "U3"}:
            state.apply_single(op.name, op.qubits[0], op.params)
        elif op.name in {"CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "iSWAP", "ISWAP", "SqrtSWAP", "fSWAP", "FSWAP", "DCX", "CRx", "CRy", "CRz", "CP", "CU", "RXX", "RYY", "RZZ", "RZX", "ECR", "MS"}:
            state.apply_two(op.name, op.qubits[0], op.qubits[1], op.params)
        elif op.name in {"Toffoli", "CCX"}:
            state.apply_mcx(op.qubits[:2], op.qubits[2])
        elif op.name in {"Fredkin", "CSWAP"}:
            state.apply_swap_controlled(op.qubits[0], op.qubits[1], op.qubits[2])
        elif op.name == "CCZ":
            state.apply_ccz(op.qubits[0], op.qubits[1], op.qubits[2])
        elif op.name in {"MCX", "C3X", "C4X"}:
            state.apply_mcx(op.qubits[:-1], op.qubits[-1])
        elif op.name == "MCZ":
            state.apply_mcz(op.qubits)
        else:
            raise QuantumError(f"unsupported distributed gate {op.name}")

    def apply(self, name: str, *qubits: int | QubitRef, params: Sequence[float] = ()) -> None:
        self.apply_batch([self._normalize_op(name, tuple(qubit_index(q) for q in qubits), params)])

    def apply_batch(self, operations: Sequence[GateOp | tuple]) -> None:
        state = SparseState(self.n_qubits, self._get_global_state(), self.eps)
        normalized: list[GateOp] = []
        for op in operations:
            if isinstance(op, GateOp):
                g = self._normalize_op(op.name, op.qubits, op.params)
            else:
                g = self._normalize_op(str(op[0]), tuple(op[1]), tuple(op[2] if len(op) > 2 else ()))
            self._apply_to_state(state, g)
            normalized.append(g)
        self._set_global_state(state.amplitudes or {})
        self.history.extend(normalized)

    def checkpoint(self, directory: str) -> dict[str, Any]:
        Path(directory).mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {"n_qubits": self.n_qubits, "workers": [], "history": [(op.name, op.qubits, op.params) for op in self.history]}
        for idx, client in enumerate(self.workers):
            path = str(Path(directory) / f"worker_{idx}.json.gz")
            resp = client.request({"cmd": "checkpoint", "path": path})
            manifest["workers"].append({"host": client.host, "port": client.port, "path": resp["path"], "nnz": resp.get("nnz", 0)})
        (Path(directory) / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    def restore(self, directory: str) -> dict[str, Any]:
        manifest = json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8"))
        for client, w in zip(self.workers, manifest.get("workers", [])):
            client.request({"cmd": "restore", "path": w["path"]})
        self.history = [GateOp(str(name), tuple(qs), tuple(params)) for name, qs, params in manifest.get("history", [])]
        return manifest

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
