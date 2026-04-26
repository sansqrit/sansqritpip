"""Packaged AI/ML training dataset utilities for Sansqrit.

The package ships compressed JSONL files under ``sansqrit/data/training``.
They are intentionally easy to consume from fine-tuning, RAG, evaluation,
preference-training and data-audit scripts.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, asdict
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable, Iterator

DATASET_VERSION = "sansqrit-synthetic-training-v1"
TRAINING_PACKAGE_DIR = "data/training"
_SPLITS = {
    "sft_train": "sansqrit_sft_train_v1.jsonl.gz",
    "sft_eval": "sansqrit_sft_eval_v1.jsonl.gz",
    "preference": "sansqrit_preference_v1.jsonl.gz",
    "real_world_scenarios": "sansqrit_real_world_scenarios_v1.jsonl.gz",
}

@dataclass(frozen=True)
class TrainingRecord:
    instruction: str
    input: str
    output: str
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _training_dir():
    return files("sansqrit").joinpath(TRAINING_PACKAGE_DIR)


def dataset_path(split: str) -> str:
    """Return the importlib resource path-like string for a packaged split."""
    if split not in _SPLITS:
        raise KeyError(f"unknown dataset split {split!r}; expected one of {sorted(_SPLITS)}")
    return str(_training_dir().joinpath(_SPLITS[split]))


def dataset_info() -> dict[str, Any]:
    """Return the packaged dataset manifest."""
    manifest = _training_dir().joinpath("manifest.json")
    return json.loads(manifest.read_text(encoding="utf-8"))


def available_splits() -> list[str]:
    """Return available packaged dataset split names."""
    return list(_SPLITS)


def load_training_records(split: str = "sft_train", *, limit: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield records from a packaged compressed JSONL split.

    Parameters
    ----------
    split:
        One of ``sft_train``, ``sft_eval`` or ``preference``.
    limit:
        Optional maximum number of records to yield.
    """
    if split not in _SPLITS:
        raise KeyError(f"unknown dataset split {split!r}; expected one of {sorted(_SPLITS)}")
    path = _training_dir().joinpath(_SPLITS[split])
    yielded = 0
    # Use Traversable.open() so records load correctly from wheels/zip imports.
    with path.open("rb") as raw:
        with gzip.open(raw, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                yield json.loads(line)
                yielded += 1
                if limit is not None and yielded >= limit:
                    break


def export_dataset(output_dir: str | Path, *, splits: Iterable[str] | None = None, limit: int | None = None) -> dict[str, Any]:
    """Export packaged records to plain JSONL files.

    This is useful for training pipelines that do not want to read gzip files
    from package resources.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    chosen = list(splits or _SPLITS)
    summary: dict[str, Any] = {"output_dir": str(out), "files": []}
    for split in chosen:
        target = out / f"{split}.jsonl"
        count = 0
        with target.open("w", encoding="utf-8") as f:
            for record in load_training_records(split, limit=limit):
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
        summary["files"].append({"split": split, "path": str(target), "records": count})
    (out / "manifest.json").write_text(json.dumps(dataset_info(), indent=2, sort_keys=True), encoding="utf-8")
    return summary


def sample_records(split: str = "sft_train", n: int = 5) -> list[dict[str, Any]]:
    """Return the first ``n`` records from a split."""
    return list(load_training_records(split, limit=n))


def builtin_training_records() -> list[TrainingRecord]:
    """Small in-memory seed records kept for backwards compatibility."""
    return [
        TrainingRecord("Write a Bell state in Sansqrit", "", "q = quantum_register(2)\nH(q[0])\nCNOT(q[0], q[1])\nprint(measure_all())", ("syntax", "bell")),
        TrainingRecord("Write a 120-qubit sparse sensor example", "Use sharded sparse backend", "simulate(120, engine='sharded', n_shards=12) {\n    q = quantum_register(120)\n    X(q[119])\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(lookup_profile())\n}", ("large-qubit", "sparse")),
    ]


def generate_jsonl(path: str | Path, records: Iterable[TrainingRecord] | None = None) -> None:
    """Write seed records or custom records to a plain JSONL file."""
    recs = list(records or builtin_training_records())
    p = Path(path)
    p.write_text("\n".join(json.dumps(r.to_dict(), sort_keys=True) for r in recs) + "\n", encoding="utf-8")


def examples_to_training_records(examples_dir: str | Path) -> list[TrainingRecord]:
    root = Path(examples_dir)
    records: list[TrainingRecord] = []
    for p in sorted(root.glob("*.sq")):
        code = p.read_text(encoding="utf-8")
        records.append(TrainingRecord(instruction=f"Explain or generate the Sansqrit example {p.name}", input="", output=code, tags=("example", p.stem)))
    return records
