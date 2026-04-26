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



def cmd_doctor(args: argparse.Namespace) -> int:
    from .diagnostics import doctor_text
    print(doctor_text())
    return 0

def cmd_backends(args: argparse.Namespace) -> int:
    from .diagnostics import backends
    for b in backends():
        status = "available" if b.available else f"missing; {b.install_hint}"
        print(f"{b.name}: {status} — {b.purpose}")
    return 0

def cmd_estimate(args: argparse.Namespace) -> int:
    import json
    from .diagnostics import estimate
    print(json.dumps(estimate(args.qubits), indent=2, sort_keys=True))
    return 0

def cmd_architecture(args: argparse.Namespace) -> int:
    from .architecture import execution_flow_mermaid, architecture_layers, explain_120_qubits_dense
    print("# Sansqrit execution architecture")
    print(execution_flow_mermaid())
    print("\n# 120-qubit dense note")
    print(explain_120_qubits_dense())
    print("\n# Layers")
    for layer in architecture_layers():
        print(f"- {layer['layer']}: {layer['purpose']}")
    return 0

def cmd_troubleshoot(args: argparse.Namespace) -> int:
    from .diagnostics import troubleshoot
    for item in troubleshoot(args.topic):
        print(f"Symptom: {item['symptom']}\nCause: {item['cause']}\nFix: {item['fix']}\n")
    return 0

def cmd_hardware(args: argparse.Namespace) -> int:
    from .hardware import hardware_targets
    for t in hardware_targets():
        print(f"{t['provider']}: {', '.join(t['export_modes'])} — {t['notes']} ({t['install_hint']})")
    return 0


def cmd_dataset(args: argparse.Namespace) -> int:
    import json
    from .dataset import dataset_info, available_splits, sample_records, export_dataset
    if args.dataset_command == "info":
        print(json.dumps(dataset_info(), indent=2, sort_keys=True))
    elif args.dataset_command == "splits":
        for split in available_splits():
            print(split)
    elif args.dataset_command == "sample":
        for record in sample_records(args.split, args.n):
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    elif args.dataset_command == "export":
        summary = export_dataset(args.output, splits=args.splits, limit=args.limit)
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        raise SystemExit("dataset command required")
    return 0


def cmd_scenarios(args: argparse.Namespace) -> int:
    import json
    from .scenarios import scenario_info, sample_scenarios, export_scenarios
    if args.scenario_command == "info":
        print(json.dumps(scenario_info(), indent=2, sort_keys=True))
    elif args.scenario_command == "sample":
        for record in sample_scenarios(args.n, domain=args.domain):
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    elif args.scenario_command == "export":
        print(json.dumps(export_scenarios(args.output, limit=args.limit, domain=args.domain), indent=2, sort_keys=True))
    else:
        raise SystemExit("scenarios command required")
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
    doctor = sub.add_parser("doctor", help="show environment, lookup data and optional backend availability")
    doctor.set_defaults(func=cmd_doctor)
    backs = sub.add_parser("backends", help="list simulator and interoperability backends")
    backs.set_defaults(func=cmd_backends)
    estimate = sub.add_parser("estimate", help="estimate dense memory and recommend large-qubit strategies")
    estimate.add_argument("qubits", type=int)
    estimate.set_defaults(func=cmd_estimate)
    arch = sub.add_parser("architecture", help="print the Sansqrit execution flow and architecture layers")
    arch.set_defaults(func=cmd_architecture)
    trouble = sub.add_parser("troubleshoot", help="show troubleshooting guidance")
    trouble.add_argument("topic", nargs="?", default=None)
    trouble.set_defaults(func=cmd_troubleshoot)
    hardware = sub.add_parser("hardware", help="list hardware export targets")
    hardware.set_defaults(func=cmd_hardware)

    scenarios = sub.add_parser("scenarios", help="inspect/export the 500-record real-world Sansqrit scenario corpus")
    ssub = scenarios.add_subparsers(dest="scenario_command", required=True)
    sinfo = ssub.add_parser("info", help="print scenario corpus metadata")
    sinfo.set_defaults(func=cmd_scenarios)
    ssample = ssub.add_parser("sample", help="print scenario records")
    ssample.add_argument("-n", type=int, default=3)
    ssample.add_argument("--domain")
    ssample.set_defaults(func=cmd_scenarios)
    sexport = ssub.add_parser("export", help="export scenario records as JSONL")
    sexport.add_argument("--output", required=True)
    sexport.add_argument("--limit", type=int)
    sexport.add_argument("--domain")
    sexport.set_defaults(func=cmd_scenarios)
    dataset = sub.add_parser("dataset", help="inspect or export the packaged AI/ML training dataset")
    dsub = dataset.add_subparsers(dest="dataset_command", required=True)
    dinfo = dsub.add_parser("info", help="print dataset manifest")
    dinfo.set_defaults(func=cmd_dataset)
    dsplits = dsub.add_parser("splits", help="list packaged dataset splits")
    dsplits.set_defaults(func=cmd_dataset)
    dsample = dsub.add_parser("sample", help="print JSON records from a split")
    dsample.add_argument("--split", default="sft_train", choices=["sft_train", "sft_eval", "preference", "real_world_scenarios"])
    dsample.add_argument("-n", type=int, default=3)
    dsample.set_defaults(func=cmd_dataset)
    dexport = dsub.add_parser("export", help="export packaged gzip JSONL splits as plain JSONL files")
    dexport.add_argument("--output", required=True)
    dexport.add_argument("--splits", nargs="*", choices=["sft_train", "sft_eval", "preference", "real_world_scenarios"])
    dexport.add_argument("--limit", type=int)
    dexport.set_defaults(func=cmd_dataset)
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
