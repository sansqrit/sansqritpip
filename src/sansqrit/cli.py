"""Command line interface for Sansqrit."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .dsl import run_file, translate
from .engine import QuantumEngine
from .runtime import last_engine


def cmd_run(args: argparse.Namespace) -> int:
    run_file(args.file)
    return 0


def cmd_translate(args: argparse.Namespace) -> int:
    text = Path(args.file).read_text(encoding="utf-8")
    print(translate(text, filename=args.file))
    return 0


def cmd_qasm(args: argparse.Namespace) -> int:
    env = run_file(args.file)
    engine = env.get("__engine__") if isinstance(env.get("__engine__"), QuantumEngine) else last_engine()
    if not isinstance(engine, QuantumEngine):
        raise SystemExit("no simulate block found; cannot export QASM")
    qasm = engine.export_qasm3() if args.version == "3" else engine.export_qasm2()
    if args.output:
        Path(args.output).write_text(qasm, encoding="utf-8")
    else:
        print(qasm)
    return 0


def cmd_examples(args: argparse.Namespace) -> int:
    print("Examples are included in the source distribution under examples/.")
    print("Try: sansqrit run examples/001_bell_state.sq")
    return 0

def cmd_worker(args: argparse.Namespace) -> int:
    from .cluster import serve_worker
    print(f"Starting Sansqrit shard worker on {args.host}:{args.port}")
    serve_worker(args.host, args.port)
    return 0

def cmd_verify(args: argparse.Namespace) -> int:
    # Run the DSL, then verify the captured circuit against installed SDKs when possible.
    env = run_file(args.file)
    engine = env.get("__engine__") or last_engine()
    if engine is None or not hasattr(engine, "history"):
        raise SystemExit("no simulate block found; cannot verify")
    from .circuit import Circuit
    from .verification import verify_all_available
    circuit = Circuit(engine.n_qubits, list(engine.history))
    for result in verify_all_available(circuit):
        status = "PASS" if result.passed else "SKIP/FAIL"
        print(f"{status} {result.backend}: max_delta={result.max_delta} {result.details}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sansqrit", description="Sansqrit quantum DSL")
    p.add_argument("--version", action="version", version=f"sansqrit {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a .sq program")
    run.add_argument("file")
    run.set_defaults(func=cmd_run)
    tr = sub.add_parser("translate", help="print translated Python")
    tr.add_argument("file")
    tr.set_defaults(func=cmd_translate)
    qasm = sub.add_parser("qasm", help="run a .sq program and export its circuit")
    qasm.add_argument("file")
    qasm.add_argument("-o", "--output")
    qasm.add_argument("--version", choices=["2", "3"], default="3")
    qasm.set_defaults(func=cmd_qasm)
    ex = sub.add_parser("examples", help="show example information")
    ex.set_defaults(func=cmd_examples)
    worker = sub.add_parser("worker", help="start a TCP distributed sparse shard worker")
    worker.add_argument("--host", default="0.0.0.0")
    worker.add_argument("--port", type=int, default=8765)
    worker.set_defaults(func=cmd_worker)
    verify = sub.add_parser("verify", help="cross-check a .sq circuit against installed quantum SDKs")
    verify.add_argument("file")
    verify.set_defaults(func=cmd_verify)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 CLI display
        print(f"sansqrit: error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
