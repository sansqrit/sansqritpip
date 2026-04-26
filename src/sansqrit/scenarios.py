"""Real-world Sansqrit scenario corpus utilities.

The corpus is packaged as gzip JSONL under ``sansqrit/data/training`` and is
intended for supervised fine-tuning, RAG, benchmark prompting, and documentation
training. Each record includes a natural-language question, an answer/explanation,
and a complete Sansqrit program.
"""
from __future__ import annotations

import gzip
import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterator

SCENARIO_SPLIT = "sansqrit_real_world_scenarios_v1.jsonl.gz"


def _path():
    return files("sansqrit").joinpath("data/training").joinpath(SCENARIO_SPLIT)


def scenario_info() -> dict[str, Any]:
    rows = list(load_scenarios(limit=None))
    domains = sorted({r.get("domain", "unknown") for r in rows})
    backends = sorted({r.get("expected_backend", "unknown") for r in rows})
    return {
        "name": "Sansqrit real-world scenario corpus v1",
        "records": len(rows),
        "domains": domains,
        "backend_patterns": backends,
        "file": SCENARIO_SPLIT,
        "author": "Karthik V",
        "schema": "real-world-scenario-v1",
    }


def load_scenarios(*, limit: int | None = None, domain: str | None = None) -> Iterator[dict[str, Any]]:
    yielded = 0
    path = _path()
    with path.open("rb") as raw:
        with gzip.open(raw, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if domain is not None and row.get("domain") != domain:
                    continue
                yield row
                yielded += 1
                if limit is not None and yielded >= limit:
                    break


def sample_scenarios(n: int = 5, *, domain: str | None = None) -> list[dict[str, Any]]:
    return list(load_scenarios(limit=n, domain=domain))


def export_scenarios(output_path: str | Path, *, limit: int | None = None, domain: str | None = None) -> dict[str, Any]:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as f:
        for row in load_scenarios(limit=limit, domain=domain):
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return {"path": str(out), "records": count, "domain": domain}
