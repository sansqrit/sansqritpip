"""Lightweight profiling counters for lookup/sharding/optimizer diagnostics."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class LookupProfile:
    static_single_hits: int = 0
    embedded_single_hits: int = 0
    static_two_hits: int = 0
    runtime_fallbacks: int = 0
    shard_syncs: int = 0

    def to_dict(self):
        return asdict(self)

    def report(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self.to_dict().items())
