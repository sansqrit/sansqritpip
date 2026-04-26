"""Local sharding utilities.

Sansqrit's sharding is correctness-first: the engine keeps an authoritative
sparse state, and shards are partitions of that state for inspection and future
worker placement. Gate application can operate over chunks in threaded mode and
then re-partition the resulting sparse map.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShardInfo:
    shard_id: int
    nnz: int


@dataclass
class ShardedState:
    n_shards: int = 1
    shards: dict[int, dict[int, complex]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.n_shards <= 0:
            raise ValueError("n_shards must be positive")
        self.shards = {i: {} for i in range(self.n_shards)}

    def shard_for(self, basis_state: int) -> int:
        # Hash by full basis-state integer. This stays valid even for huge qubit
        # indexes because Python ints are arbitrary precision.
        return hash(basis_state) % self.n_shards

    def repartition(self, amplitudes: dict[int, complex]) -> None:
        self.shards = {i: {} for i in range(self.n_shards)}
        for state, amp in amplitudes.items():
            self.shards[self.shard_for(state)][state] = amp

    def merge(self) -> dict[int, complex]:
        out: dict[int, complex] = {}
        for shard in self.shards.values():
            out.update(shard)
        return out

    def info(self) -> list[ShardInfo]:
        return [ShardInfo(i, len(self.shards.get(i, {}))) for i in range(self.n_shards)]
